import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.api.deps import DbSession
from app.ingest.embed import embed_batch
from app.models.chunk import Chunk
from app.models.conversation import Conversation, Message, MessageCitation
from app.models.document import Document
from app.models.project import Project
from app.models.section import Section
from app.models.summary import SectionSummary
from app.retrieval.generate import GenerationError, rewrite_query, stream_generate
from app.retrieval.pipeline import retrieve
from app.retrieval.prompt import build_prompt
from app.retrieval.survey import survey_search
from app.schemas.conversation import CitationRead, ConversationRead, MessageCreate, MessageRead

SURVEY_TOP_K = 6

router = APIRouter(tags=["conversations"])


async def _get_active_conversation(db: DbSession, conversation_id: int) -> Conversation | None:
    """A soft-deleted conversation is treated as not-found everywhere except
    the deleted-list and restore endpoints — deleted means gone from every
    normal path, not just hidden from the sidebar."""
    conversation = await db.get(Conversation, conversation_id)
    if conversation is None or conversation.deleted_at is not None:
        return None
    return conversation


async def _load_citations(
    db: DbSession, message_ids: list[int]
) -> dict[int, list[CitationRead]]:
    """A citation points at exactly one of a chunk (lookup mode) or a
    section summary (survey mode) — resolved with two targeted lookups
    rather than one query with two outer joins."""
    citations_result = await db.execute(
        select(MessageCitation).where(MessageCitation.message_id.in_(message_ids)).order_by(
            MessageCitation.rank
        )
    )
    message_citations = list(citations_result.scalars().all())

    chunk_ids = [mc.chunk_id for mc in message_citations if mc.chunk_id is not None]
    chunk_info: dict[int, tuple[str, str, str]] = {}
    if chunk_ids:
        rows = await db.execute(
            select(Chunk.id, Document.title, Section.display_path, Chunk.text)
            .join(Section, Section.id == Chunk.section_id)
            .join(Document, Document.id == Chunk.document_id)
            .where(Chunk.id.in_(chunk_ids))
        )
        chunk_info = {row[0]: (row[1], row[2], row[3]) for row in rows.all()}

    summary_ids = [
        mc.section_summary_id for mc in message_citations if mc.section_summary_id is not None
    ]
    summary_info: dict[int, tuple[str, str, str]] = {}
    if summary_ids:
        rows = await db.execute(
            select(
                SectionSummary.id, Document.title, Section.display_path, SectionSummary.summary
            )
            .join(Section, Section.id == SectionSummary.section_id)
            .join(Document, Document.id == SectionSummary.document_id)
            .where(SectionSummary.id.in_(summary_ids))
        )
        summary_info = {row[0]: (row[1], row[2], row[3]) for row in rows.all()}

    citations_by_message: dict[int, list[CitationRead]] = {}
    for mc in message_citations:
        if mc.chunk_id is not None:
            title, display_path, text = chunk_info[mc.chunk_id]
            citation = CitationRead(
                chunk_id=mc.chunk_id,
                rank=mc.rank,
                document_title=title,
                display_path=display_path,
                is_summary=False,
                text=text,
            )
        else:
            assert mc.section_summary_id is not None  # CHECK constraint guarantees this
            title, display_path, text = summary_info[mc.section_summary_id]
            citation = CitationRead(
                chunk_id=None,
                text=text,
                rank=mc.rank,
                document_title=title,
                display_path=display_path,
                is_summary=True,
            )
        citations_by_message.setdefault(mc.message_id, []).append(citation)
    return citations_by_message


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
        .where(Conversation.project_id == project_id, Conversation.deleted_at.is_(None))
        .order_by(Conversation.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/projects/{project_id}/conversations/deleted", response_model=list[ConversationRead])
async def list_deleted_conversations(project_id: int, db: DbSession) -> list[Conversation]:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(Conversation)
        .where(Conversation.project_id == project_id, Conversation.deleted_at.is_not(None))
        .order_by(Conversation.deleted_at.desc())
    )
    return list(result.scalars().all())


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: int, db: DbSession) -> Response:
    conversation = await _get_active_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.deleted_at = datetime.now(UTC)
    await db.commit()
    return Response(status_code=204)


@router.post("/conversations/{conversation_id}/restore", response_model=ConversationRead)
async def restore_conversation(conversation_id: int, db: DbSession) -> Conversation:
    conversation = await db.get(Conversation, conversation_id)
    if conversation is None or conversation.deleted_at is None:
        raise HTTPException(status_code=404, detail="Deleted conversation not found")

    conversation.deleted_at = None
    await db.commit()
    await db.refresh(conversation)
    return conversation


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageRead])
async def list_messages(conversation_id: int, db: DbSession) -> list[MessageRead]:
    conversation = await _get_active_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages_result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.id)
    )
    messages = list(messages_result.scalars().all())

    citations_by_message: dict[int, list[CitationRead]] = {}
    if messages:
        citations_by_message = await _load_citations(db, [m.id for m in messages])

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
    conversation = await _get_active_conversation(db, conversation_id)
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

    standalone_question = await rewrite_query(payload.content, history)
    query_embedding = (await embed_batch([standalone_question]))[0]
    is_survey = payload.mode == "survey"

    if is_survey:
        # Survey path (docs/plan.md §4.4): summaries, not passages — no
        # keyword search/RRF/reranking, just vector search over summaries.
        survey_results = await survey_search(
            db, conversation.project_id, query_embedding, top_k=SURVEY_TOP_K
        )
        sources = [
            f"{section.display_path}\n\n{summary.summary}"
            for summary, section, _document in survey_results
        ]
    else:
        lookup_results = await retrieve(
            db, conversation.project_id, query_embedding, standalone_question
        )
        sources = [chunk.embed_text for chunk, _section, _document in lookup_results]

    # A RAG tool's whole premise is grounded answers — with zero sources to
    # draw on (survey mode before any document has summaries, e.g.), the
    # model will still cheerfully answer from its own trained knowledge and
    # invent plausible-looking citation numbers for it. Refuse rather than
    # let that happen silently; no generation call at all.
    no_sources = is_survey and not sources
    prompt = "" if no_sources else build_prompt(sources, history, standalone_question)

    async def event_stream() -> AsyncIterator[str]:
        collected: list[str] = []
        if no_sources:
            message = (
                "No summarised sections are available yet for survey mode in this "
                "project. Summaries are generated automatically once a document "
                "finishes indexing — try again shortly, or switch to Lookup mode "
                "for an answer right now."
            )
            collected.append(message)
            yield f"data: {json.dumps({'token': message})}\n\n"
        else:
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

        citations_payload: list[dict[str, object]] = []
        if is_survey:
            for rank, (summary, section, document) in enumerate(survey_results, start=1):
                db.add(
                    MessageCitation(
                        message_id=assistant_message.id,
                        section_summary_id=summary.id,
                        rank=rank,
                    )
                )
                citations_payload.append(
                    {
                        "chunk_id": None,
                        "rank": rank,
                        "document_title": document.title,
                        "display_path": section.display_path,
                        "is_summary": True,
                        "text": summary.summary,
                    }
                )
        else:
            for rank, (chunk, section, document) in enumerate(lookup_results, start=1):
                db.add(
                    MessageCitation(message_id=assistant_message.id, chunk_id=chunk.id, rank=rank)
                )
                citations_payload.append(
                    {
                        "chunk_id": chunk.id,
                        "rank": rank,
                        "document_title": document.title,
                        "display_path": section.display_path,
                        "is_summary": False,
                        "text": chunk.text,
                    }
                )
        await db.commit()

        yield f"data: {json.dumps({'done': True, 'citations': citations_payload})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
