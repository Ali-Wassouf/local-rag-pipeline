# Local RAG — project memory

Read `docs/plan.md` for the full design. Read `docs/build-phases.md` for the
current phase and its acceptance criteria. This file holds conventions and
invariants that apply to every task.

## Stack

- Backend: Python 3.12, FastAPI, SQLAlchemy 2.x (async), Alembic, Pydantic v2
- DB: Postgres 16 + pgvector + ltree + pg_trgm
- Worker: separate process, polls `ingest_jobs`. Not Celery — a plain asyncio
  loop is sufficient for single-user.
- Frontend: React 18 + TypeScript + Vite, shadcn/ui, TanStack Query, Tailwind
- Models: Ollama (generation), sentence-transformers (embedding + reranking)
- Package management: `uv` for Python, `pnpm` for JS

## Layout

```
backend/
  app/
    api/          FastAPI routers, one per resource
    models/       SQLAlchemy models
    schemas/      Pydantic request/response
    extract/      one module per format, all emit Block
    ingest/       chunking, embedding, summarisation, worker loop
    retrieval/    hybrid search, reranking, generation
    db/           session, migrations
  tests/
frontend/
  src/
    api/          generated types + TanStack Query hooks
    components/   shadcn/ui components (owned source)
    screens/
docs/
scripts/
```

## Invariants

These are load-bearing. Breaking one causes silent data loss or wrong answers,
not a crash. Do not "simplify" them away.

1. **Every retrieval query filters by `project_id`.** Join through
   `project_documents`. A query without that join is a bug even if it returns
   plausible results.
2. **Chunks never cross a section boundary.** Chunking is per-section.
3. **Page numbers never appear in output.** They exist as manual-entry input on
   the review screen only, converted to character offsets on save. Citations use
   `sections.display_path`.
4. **The section tree always covers the full document.** No gaps. If detection
   finds nothing, create one root section spanning everything.
5. **`chunks.embed_text` is embedded; `chunks.text` is displayed and
   keyword-searched.** Never embed `text` or display `embed_text`.
6. **Survey answers cite summaries, and must be labelled as such.** Never render
   a summary-derived citation as a passage the model read.
7. **Every parser emits `Block`.** No format-specific types leak past
   `app/extract/`.

## The Block IR

Every extractor returns `list[Block]`. This is the contract that lets parsers be
built independently.

```python
from typing import Literal, TypedDict

class Block(TypedDict):
    type: Literal["heading", "paragraph", "list", "table"]
    text: str
    level: int | None   # 1-6 for headings, None otherwise
    anchor: int         # page or slide number; internal only, never displayed
```

Rules: reading order preserved; tables serialised as Markdown in `text`;
repeated headers/footers stripped before emission; no empty blocks.

## Conventions

- Type hints everywhere. `mypy --strict` on `backend/app`.
- Async all the way down in FastAPI paths. The worker is async too.
- No raw SQL string interpolation. Bound parameters or SQLAlchemy constructs.
- Vector columns: `Vector(1024)`. If the embedder changes, that's a migration
  plus a full re-index, never an in-place edit.
- Tests: pytest, with a real Postgres in Docker for anything touching the DB.
  Do not mock the database — pgvector and ltree behaviour is the thing under test.
- Frontend: no `any`. API types generated from the OpenAPI schema, not hand-written.
- Commits: one logical change, conventional-commit prefix.

## Commands

```bash
just dev            # backend + worker + frontend
just test           # pytest + vitest
just db-up          # Postgres in Docker
just migrate        # alembic upgrade head
just check-models   # verify Ollama is up and dimensions match
```

## What not to do

- Do not add OCR. Scanned PDFs are out of scope; the character-count check
  rejects them by design.
- Do not add a vector store other than pgvector. One database.
- Do not introduce Redis, Celery, or a message queue. Single user, one worker.
- Do not tune chunk size, top-k, or RRF constants without a query set to measure
  against. The values in `docs/plan.md` §8 are derived from the context budget.
