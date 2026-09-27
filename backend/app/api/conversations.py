import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.api.deps import DbSession
from app.ingest.embed import embed_batch
from app.models.chunk import Chunk
from app.models.conversation import Conversation, Message, MessageCitation
from app.models.document import Document
from app.models.project import Project
from app.models.section import Section
from app.retrieval.generate import GenerationError, stream_generate
from app.retrieval.prompt import build_prompt
from app.retrieval.search import vector_search
from app.schemas.conversation import CitationRead, ConversationRead, MessageCreate, MessageRead

router = APIRouter(tags=["conversations"])


@router.post("/projects/{project_id}/conversations", response_model=ConversationRead, status_code=201)
async def create_conversation(project_id: int, db: DbSession) -> Conversation:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    conversation = Conversation(project_id=project_id)
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


@router.get("/projects/{project_id}/conversations", response_model=list[ConversationRead])
async def list_conversations(project_id: int, db: DbSession) -> list[Conversation]:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(Conversation)
        .where(Conversation.project_id == project_id)
        .order_by(Conversation.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageRead])
async def list_messages(conversation_id: int, db: DbSession) -> list[MessageRead]:
    conversation = await db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages_result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.id)
    )
    messages = list(messages_result.scalars().all())

    citations_by_message: dict[int, list[CitationRead]] = {}
    if messages:
        citations_result = await db.execute(
            select(MessageCitation, Chunk, Section, Document)
            .join(Chunk, Chunk.id == MessageCitation.chunk_id)
            .join(Section, Section.id == Chunk.section_id)
            .join(Document, Document.id == Chunk.document_id)
            .where(MessageCitation.message_id.in_([m.id for m in messages]))
            .order_by(MessageCitation.rank)
        )
        for message_citation, chunk, section, document in citations_result.all():
            citations_by_message.setdefault(message_citation.message_id, []).append(
                CitationRead(
                    chunk_id=chunk.id,
                    rank=message_citation.rank,
                    document_title=document.title,
                    display_path=section.display_path,
                )
            )

    return [
        MessageRead(
            id=m.id,
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            created_at=m.created_at,
            citations=citations_by_message.get(m.id, []),
        )
        for m in messages
    ]


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: int, payload: MessageCreate, db: DbSession
) -> StreamingResponse:
    conversation = await db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    history_result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.id)
    )
    history = [(m.role, m.content) for m in history_result.scalars().all()]

    if conversation.title is None:
        conversation.title = payload.content[:60]

    user_message = Message(conversation_id=conversation_id, role="user", content=payload.content)
    db.add(user_message)
    await db.commit()

    query_embedding = (await embed_batch([payload.content]))[0]
    results = await vector_search(db, conversation.project_id, query_embedding)
    prompt = build_prompt([chunk.embed_text for chunk, _s, _d in results], history, payload.content)

    async def event_stream() -> AsyncIterator[str]:
        collected: list[str] = []
        try:
            async for token in stream_generate(prompt):
                collected.append(token)
                yield f"data: {json.dumps({'token': token})}\n\n"
        except GenerationError as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
            return

        assistant_message = Message(
            conversation_id=conversation_id, role="assistant", content="".join(collected)
        )
        db.add(assistant_message)
        await db.flush()

        citations_payload = []
        for rank, (chunk, section, document) in enumerate(results, start=1):
            db.add(MessageCitation(message_id=assistant_message.id, chunk_id=chunk.id, rank=rank))
            citations_payload.append(
                {
                    "chunk_id": chunk.id,
                    "rank": rank,
                    "document_title": document.title,
                    "display_path": section.display_path,
                }
            )
        await db.commit()

        yield f"data: {json.dumps({'done': True, 'citations': citations_payload})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
