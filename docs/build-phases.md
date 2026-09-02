# Build phases

Each phase has a definition of done. Do not start a phase until the previous
one's criteria pass. Phases are sequential; parallelism happens *within* a phase
and only where marked.

---

## Phase 0 — skeleton

No models. Prove the plumbing.

**Tasks**
- Docker Compose: Postgres 16 with pgvector, ltree, pg_trgm
- Alembic migrations for the full schema in `docs/plan.md` §2
- FastAPI app: `POST /documents` (multipart), `GET /documents/{id}`,
  `GET /jobs/{id}`, project CRUD
- Upload writes file to disk, computes sha256, dedupes on conflict
- Worker process skeleton: claims a job, advances stage, writes progress
- Vite frontend: upload form, job status polling via TanStack Query

**Done when**
- `just db-up && just migrate` gives a clean schema from zero
- Uploading a 300-page PDF returns a job id in under a second
- Job progress visibly advances through a stubbed stage sequence in the UI
- Uploading the same file twice creates one document row, not two
- `mypy --strict` and `pytest` pass

**Parallel:** no. Everything depends on the schema.

---

## Phase 1 — extraction

**Tasks**
- `Block` type and the extractor interface in `app/extract/base.py`
- Four extractors: `pdf.py` (PyMuPDF), `docx.py` (python-docx),
  `pptx.py` (python-pptx), `text.py` (txt + md)
- Header/footer detection and stripping (PDF)
- Scanned-PDF rejection: characters-per-page below threshold fails the job
- Structure builder: blocks → `sections` rows with ltree paths and offsets
- Review screen: tree with inline editing, preview pane, chunk/token estimates,
  untitled-region rows

**Done when**
- Each extractor has fixture-based tests using a real file of that format
- A PDF with a bookmark outline produces a correct tree, unprompted
- A PDF with no outline produces exactly one root section covering all text
- A scanned PDF fails with a clear message, not an empty success
- Section offsets are contiguous and cover `[0, len(raw_text))` with no gaps
- Editing a title in the review screen persists and marks `source = 'manual'`

**Parallel: yes — this is the main opportunity.** Once `Block` and the extractor
interface are merged, the four extractors are independent: separate files, no
shared state, one test fixture each. Run them as four agents in four git
worktrees. The structure builder and the review screen depend on `Block` but not
on any specific extractor, so they can go in parallel too.

Sequence: merge the interface first, alone. Then fan out.

---

## Phase 2 — index

**Tasks**
- Chunker: per-section, 700 tokens, 100 overlap, builds `embed_text`
- Embedder wrapper (sentence-transformers, MPS), batched
- `embedding_runs` bookkeeping
- Worker stages wired end to end: extract → structure → chunk → embed
- Project detail screen: document list, add/remove, status

**Done when**
- A 300-page book ingests end to end and produces chunks with non-null embeddings
- No chunk spans two `section_id` values
- `embed_text` starts with the breadcrumb; `text` does not
- Re-uploading an already-indexed file does not re-embed
- HNSW index exists and `EXPLAIN` shows it being used

**Parallel:** limited. Chunker and embedder are separable but small. The project
screen is independent of both.

---

## Phase 3 — needle chat

Deliberately vector-only. No hybrid, no reranking. This is the baseline you will
measure phase 4 against — do not skip ahead.

**Tasks**
- Vector search with mandatory project filter
- Prompt assembly: chunks + breadcrumbs + history
- Ollama client, streaming via SSE
- Chat screen: thread, scope bar, inline markers, collapsible sources
- `message_citations` persistence

**Done when**
- A question against a project returns an answer with at least one citation
- Every citation resolves to a real chunk in that project
- A question about a document in *another* project returns nothing relevant
- Answer streams token by token, not all at once at the end
- **Save 20 real questions and their answers to `evals/baseline.md`**

**Parallel:** yes. Backend retrieval and frontend chat screen, once the response
schema is frozen. Freeze it first.

---

## Phase 4 — retrieval quality

**Tasks**
- Postgres FTS query over `chunks.tsv`
- RRF fusion (k = 60)
- Cross-encoder reranker, in-process
- Query rewriting for follow-ups

**Done when**
- The same 20 questions from phase 3 are re-run and diffed against baseline
- Hybrid-vs-vector and reranked-vs-unreranked are measured *separately*, so you
  know which earned its keep
- A follow-up question ("what about the second one?") retrieves correctly

**Parallel:** no. Each change must be measured against the previous state.

---

## Phase 5 — survey path

**Tasks**
- Section summarisation at ingest, sections over 1500 tokens, ~200-token output
- Summary embedding and search
- Lookup/Survey toggle
- Summary-labelled citations
- Backfill command for already-indexed documents

**Done when**
- "Summarise everything on topic X" returns an answer drawing on 4+ sections
- Survey citations are visibly labelled as summaries, not passages
- Backfill runs over existing documents without re-extracting
- A survey answer across two documents attributes each claim to the right one

**Parallel:** ingest-side summarisation and query-side survey retrieval, yes.

---

## Phase 6 — polish

Source-passage view, document removal and re-index, conversation list,
error-state handling in the UI. Fully parallel.
