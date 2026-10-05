# Local RAG Pipeline — Design Plan

Target hardware: Apple M2 Pro, 16GB unified memory (~11GB addressable, ~8GB budget for models).
Scope: books, reports, manuals, slide decks, plain text. PDF / DOCX / PPTX / TXT / MD / EPUB.
Citations reference the section path, never page numbers.

---

## 1. Architecture

```
┌─────────────┐
│     UI      │  upload · review structure · projects · chat
└──────┬──────┘
       │ HTTP
┌──────┴──────┐
│  API layer  │  FastAPI
└──────┬──────┘
       │
   ┌───┴────────────────────────┐
   │                            │
┌──┴───────────┐        ┌───────┴──────┐
│ Ingest worker│        │ Query engine │
│ (background) │        │ (per request)│
└──┬───────────┘        └───────┬──────┘
   │                            │
   │  extract → tree →          │  hybrid search → rerank
   │  chunk → embed →           │  → generate
   │  summarise                 │
   │                            │
┌──┴────────────────────────────┴──────┐
│  Postgres 16 + pgvector + ltree       │
└───────────────────────────────────────┘

Models:  embedder (ingest only) · reranker · generator (query only)
```

Single-user, single-machine. The ingest worker is a separate process from the API
so a 40-minute book ingest doesn't block chat.

---

## 2. Data model

### 2.1 Extensions

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS ltree;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

### 2.2 Projects and documents

Documents are independent entities; projects reference them many-to-many. This
costs one join table and saves re-embedding a book that belongs in two projects.

```sql
CREATE TABLE projects (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TYPE doc_format AS ENUM ('pdf', 'docx', 'pptx', 'txt', 'md');
CREATE TYPE doc_status AS ENUM ('uploaded', 'extracting', 'awaiting_review',
                                'indexing', 'ready', 'failed');

CREATE TABLE documents (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sha256          CHAR(64) NOT NULL UNIQUE,     -- dedupe + idempotent re-ingest
    title           TEXT NOT NULL,                -- user-correctable
    author          TEXT,
    format          doc_format NOT NULL,
    original_name   TEXT NOT NULL,
    storage_path    TEXT NOT NULL,                -- original file on disk
    raw_text        TEXT,                         -- full extracted text stream
    status          doc_status NOT NULL DEFAULT 'uploaded',
    page_offset     INT NOT NULL DEFAULT 0,       -- input aid only, never displayed
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE project_documents (
    project_id  BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    added_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (project_id, document_id)
);
```

`raw_text` is kept so structure can be re-derived and chunks rebuilt without
re-parsing the original file. Reparsing a PDF is the slowest step in the pipeline.

### 2.3 The section tree

Arbitrary depth via `ltree`. `path` is structural (`3.2.1`), `title` is what the
reader sees, `display_path` is the pre-rendered breadcrumb used both for the
chunk header and for citations — one string, two purposes.

```sql
CREATE TYPE structure_source AS ENUM ('detected', 'manual');

CREATE TABLE sections (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id   BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    path          LTREE NOT NULL,                 -- e.g. 'c3.s2.ss1'
    title         TEXT NOT NULL,                  -- 'Vector Spaces'
    display_path  TEXT NOT NULL,                  -- 'Ch. 3 > 3.2 Vector Spaces'
    depth         INT  NOT NULL,
    ordinal       INT  NOT NULL,                  -- reading order within parent
    char_start    INT  NOT NULL,                  -- offsets into documents.raw_text
    char_end      INT  NOT NULL,
    source        structure_source NOT NULL DEFAULT 'detected',
    UNIQUE (document_id, path)
);

CREATE INDEX sections_path_gist ON sections USING GIST (path);
CREATE INDEX sections_doc       ON sections (document_id);
```

Subtree query — everything under chapter 3:

```sql
SELECT * FROM sections
WHERE document_id = $1 AND path <@ 'c3'
ORDER BY path;
```

### 2.4 Chunks

```sql
CREATE TABLE chunks (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id  BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    section_id   BIGINT NOT NULL REFERENCES sections(id)  ON DELETE CASCADE,
    ordinal      INT NOT NULL,
    text         TEXT NOT NULL,                   -- body only, no header
    embed_text   TEXT NOT NULL,                   -- display_path + '\n\n' + text
    char_start   INT NOT NULL,
    char_end     INT NOT NULL,
    token_count  INT NOT NULL,
    embedding    VECTOR(1024),                    -- Qwen3-Embedding-0.6B
    tsv          TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', text)) STORED
);

CREATE INDEX chunks_embedding ON chunks
    USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX chunks_tsv       ON chunks USING GIN (tsv);
CREATE INDEX chunks_doc       ON chunks (document_id);
CREATE INDEX chunks_section   ON chunks (section_id);
```

`embed_text` is what gets embedded; `text` is what gets shown and keyword-searched.
Keeping them separate means the breadcrumb helps retrieval without polluting the
FTS index with repeated chapter titles.

### 2.5 Section summaries (the survey path)

Generated at ingest, embedded separately, searched separately.

```sql
CREATE TABLE section_summaries (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    section_id  BIGINT NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    summary     TEXT NOT NULL,
    embedding   VECTOR(1024),
    model       TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (section_id)
);

CREATE INDEX summaries_embedding ON section_summaries
    USING hnsw (embedding vector_cosine_ops);
```

Only summarise sections above a size threshold (say 1500 tokens) — summarising a
three-paragraph subsection wastes ingest time and adds nothing.

### 2.6 Embedding provenance

The vector dimension is baked into the column. Track which model produced what so
a future swap is detectable rather than silently corrupting retrieval.

```sql
CREATE TABLE embedding_runs (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model       TEXT NOT NULL,
    dimension   INT  NOT NULL,
    started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_current  BOOLEAN NOT NULL DEFAULT TRUE
);

ALTER TABLE chunks ADD COLUMN embedding_run_id BIGINT REFERENCES embedding_runs(id);
```

Swapping the embedder = new run row, new dimension, re-index everything. Budget
30–90 minutes per 5,000 pages. Decide once.

### 2.7 Jobs

```sql
CREATE TABLE ingest_jobs (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id  BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    stage        TEXT NOT NULL,        -- extract | structure | chunk | embed | summarise
    progress     REAL NOT NULL DEFAULT 0,
    error        TEXT,
    started_at   TIMESTAMPTZ,
    finished_at  TIMESTAMPTZ
);
```

### 2.8 Conversations

```sql
CREATE TABLE conversations (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title      TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE messages (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    conversation_id BIGINT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL,     -- user | assistant
    content         TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE message_citations (
    message_id BIGINT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    chunk_id   BIGINT NOT NULL REFERENCES chunks(id)   ON DELETE CASCADE,
    rank       INT NOT NULL,
    PRIMARY KEY (message_id, chunk_id)
);
```

---

## 3. Ingest pipeline

Stages run in order; each writes progress to `ingest_jobs`. Any stage can fail
the job with a message the UI displays.

**1. Store and hash.** Write file to disk, compute sha256. If it already exists,
short-circuit and just add to the project.

**2. Extract to blocks.** Every parser emits the same intermediate representation:

```python
Block = {
    "type": "heading" | "paragraph" | "list" | "table",
    "text": str,
    "level": int | None,      # for headings
    "anchor": int,            # page no. / slide no. — internal only
}
```

| Format | Library | Structure source |
|---|---|---|
| PDF  | PyMuPDF | bookmark outline; fallback to font-size heuristics |
| DOCX | python-docx | Heading 1/2/3 styles |
| PPTX | python-pptx | slide titles; body + speaker notes |
| TXT/MD | stdlib | `#` headings, or single root section |
| EPUB | ebooklib + BeautifulSoup | `h1`-`h6` tags across the spine, reading order preserved across chapter files |

Guards at this stage:
- **Scanned PDFs are out of scope.** No OCR path. A rejection check only: if
  characters-per-page is near zero, fail the job with a clear message. Without
  this the document indexes "successfully" as empty chunks and then answers
  nothing, which looks like a retrieval bug.
- **Header/footer stripping** — detect text repeating at consistent positions
  across pages and drop it, or every chunk carries the book title.
- **Tables** — serialise to Markdown, keep inline.

**3. Build the section tree.** Fold blocks into `sections` rows with `char_start`
/ `char_end` offsets into the concatenated text stream. Status → `awaiting_review`.

**4. Review (user).** Show the detected tree. Accept / edit / build manually.
Pre-filled title and author too, since PDF metadata is frequently wrong. Ten
seconds here versus forty minutes of re-processing later.

**5. Chunk.** Structure-aware, never crossing a section boundary. 700 tokens,
100 overlap (see §8). Build `embed_text` as breadcrumb + body.

**6. Embed.** Load embedder, batch through chunks, unload.

**7. Summarise.** For each section above 1500 tokens, generate a ~200-token
summary and embed it. Slowest stage; runs last so the document is chat-usable
before it finishes.

---

## 4. Retrieval

### 4.1 Project isolation

Mandatory on every query. Optional narrower filters: document, section subtree.

```sql
JOIN documents d        ON d.id = c.document_id
JOIN project_documents p ON p.document_id = d.id AND p.project_id = $PROJECT
```

### 4.2 Query rewriting

Rewrite follow-ups into standalone queries before retrieval. "What about the
second one?" retrieves garbage otherwise. One small generation call against the
last few turns.

### 4.3 Needle path

1. Vector search: top 50 by cosine on `chunks.embedding`
2. Keyword search: top 50 by `ts_rank` on `chunks.tsv`
3. Fuse with reciprocal rank fusion (`k = 60`)
4. Rerank top 50 → top 8 with the cross-encoder
5. Generate with the 8 chunks + breadcrumbs

RRF sketch:

```sql
WITH vec AS (
  SELECT c.id, ROW_NUMBER() OVER (ORDER BY c.embedding <=> $1) AS rank
  FROM chunks c JOIN ... WHERE p.project_id = $2
  ORDER BY c.embedding <=> $1 LIMIT 50
),
kw AS (
  SELECT c.id, ROW_NUMBER() OVER (ORDER BY ts_rank(c.tsv, q) DESC) AS rank
  FROM chunks c, plainto_tsquery('english', $3) q
  JOIN ... WHERE p.project_id = $2 AND c.tsv @@ q
  ORDER BY ts_rank(c.tsv, q) DESC LIMIT 50
)
SELECT id, SUM(1.0 / (60 + rank)) AS score
FROM (SELECT * FROM vec UNION ALL SELECT * FROM kw) x
GROUP BY id ORDER BY score DESC LIMIT 50;
```

### 4.4 Survey path

1. Vector search over `section_summaries` (not chunks) within the project
2. Take the top sections, pull their full summaries
3. Optionally expand to subtree summaries via `path <@ parent`
4. Generate from summaries; drill into chunks only if the user asks for specifics

### 4.5 Routing

Explicit UI toggle to start — free, never misroutes, and usage data will tell you
whether automatic classification is worth building.

### 4.6 Citations

Every answer carries `document.title` + `sections.display_path`. Chunk IDs stored
in `message_citations` for provenance and for the source-passage view.

Display: numbered markers inline at claim level, full breadcrumbs in a sources
list below. Breadcrumbs are too long to sit inline. Markers are per-claim rather
than per-answer — with a local 8B model, drift between the retrieved chunks and
the generated text is a real risk, and claim-level markers are what make it
visible.

**Survey-mode provenance.** Survey answers are generated from summaries, not
passages. A citation pointing at a section therefore points at a summary of it.
Expanding that source must show the summary text, labelled as a summary. Do not
render it as a passage the model read — it didn't.

---

## 5. Model configuration

| Slot | Model | Size | When resident |
|---|---|---|---|
| Embedder | Qwen3-Embedding-0.6B (1024-dim) | ~1.5GB | ingest only |
| Reranker | bge-reranker-base | ~0.4GB | query |
| Generator | Qwen 3 8B @ Q4_K_M | ~5GB + ~1GB KV | query |

- `OLLAMA_MAX_LOADED_MODELS=1`, short `keep_alive` so the embedder actually unloads.
- Set `num_ctx` explicitly (8192). The default is low and RAG prompts silently
  overflow it, dropping the front of your context.
- Enable the MLX backend — 10–25% faster than stock on Apple Silicon.
- Run the reranker in-process (sentence-transformers / MPS), not via Ollama.
- Expect 20–30 tok/s generation. Ingest of a 400-page book: 20–40 min with summaries.

---

## 6. Frontend

### 6.1 Stack

| Concern | Choice | Why |
|---|---|---|
| Framework | React + TypeScript + Vite | SPA against the FastAPI backend |
| Components | shadcn/ui (Radix + Tailwind) | Source copied into the repo, not a dependency — owned and editable |
| Server state | TanStack Query | Job polling, document lists, chat. Covers nearly all state here |
| Tree | react-arborist, or hand-rolled on Radix | Section review needs inline edit + reorder |
| Streaming | SSE from FastAPI | Token streaming into the chat thread |

Not Next.js: the FastAPI backend already exists, so its server layer would
duplicate it, and local-only means SSR and SEO are irrelevant.

Note on "modular": the boundaries that matter are the API contract and the block
IR, both already defined. Inside the frontend, modularity means owning the
component source, not abstracting components ahead of need.

### 6.2 Screens

Four total. Projects list and project detail are conventional. The two below are not.

**Structure review** — shown after extraction, before indexing.

- Two panes: section tree left, text preview right.
- Inline editing, no modal. Several corrections per document is normal; a dialog
  per edit makes the step feel expensive enough to skip.
- Selecting a section previews its opening lines. A tree of titles can't tell you
  whether a boundary landed correctly — only the text can.
- Per-section chunk and token estimates, so ingest cost is visible before
  committing. An absurd count usually means detection collapsed the whole book
  into one node.
- **Uncovered spans render as explicit "untitled region" rows.** Text not covered
  by any section is never indexed. Without surfacing it, that's silent data loss.
- Page numbers appear here and nowhere else in the app — manual-override input
  only, converted to offsets on save.

**Chat** — per project.

- Scope bar showing project and document count. Isolation is a core guarantee;
  an invisible guarantee isn't trusted. Also the natural home for narrowing
  filters (this document, this chapter).
- Lookup / Survey toggle above the composer, with one line of helper text
  explaining the difference. It's a property of the question being asked, not a
  setting configured elsewhere. Without the helper text the toggle goes unused
  and survey questions just seem to work badly.
- Sources collapsed by default; expanded passages would push the answer
  off-screen.
- Document title shown on every citation, including in single-document projects —
  documents move between projects, and comparison sessions are exactly when an
  ambiguous citation costs time.

---

## 7. Build order

**Phase 0 — skeleton.** Postgres + extensions, schema, upload endpoint, hashing,
jobs table, status polling in the UI. No models yet.

**Phase 1 — extraction.** All four parsers → block IR. Scanned-PDF guard,
header/footer stripping. Structure detection. Review screen. End state: you can
upload a book and see a correct tree.

**Phase 2 — index.** Chunking, embedding, storage. Project assignment and the
project/document list view.

**Phase 3 — needle chat.** Vector search → generation → citations. Deliberately
without hybrid or reranking, so you can measure what they add.

**Phase 4 — retrieval quality.** Add keyword search + RRF, then the reranker.
Biggest quality gain per unit of effort. Measure against phase 3 on real queries.

**Phase 5 — survey path.** Section summaries at ingest, summary search, mode
toggle. Backfill summaries for already-ingested documents.

**Phase 6 — polish.** Query rewriting for follow-ups, source-passage view,
document removal and re-indexing.

---

## 8. Starting values

These are committed defaults, not findings. Each has a revisit trigger.

### Chunking — 700 tokens, 100 overlap

Derived, not guessed. It's bounded by `num_ctx = 8192` and top-k of 8:

```
8 chunks × 700          = 5600
breadcrumbs (8 × ~15)   =  120
system prompt           = ~200
rewritten query         =  ~50
conversation history    = ~300
                          ────
                          6270  → ~1900 left for the answer
```

Chunk size and top-k are jointly bounded. Raise k to 12 and you must drop to
~450 tokens, or raise `num_ctx` and pay for a larger KV cache out of an already
tight 8GB. Revisit only if answers are truncated or if reranking keeps surfacing
chunks that are missing their surrounding context.

### Summary threshold — 1500 tokens; target length ~200

Below 1500 tokens a section is two chunks, and the chunks are already close to
being their own summary — summarising adds ingest time and no retrieval value.
Revisit if survey answers miss short-but-important sections, or if summarisation
turns out to dominate ingest time.

### Manual structure entry — never an empty tree

When detection finds nothing, create one root section spanning the whole
document rather than showing an empty tree. The user splits downward from there.
Same review screen, same controls, no separate manual-entry mode. Splitting a
root is a better starting point than building a tree from zero, and it
guarantees full text coverage at every moment.

### Multi-document survey — single pass, no reduce step

Search summaries across all documents in the project, take the top 6 sections
regardless of which document they came from, generate one answer with
per-document citations. At ~200 tokens each that's 1200 tokens of context, which
fits comfortably.

Revisit if answers start blurring sources together — the failure mode to watch
for is a claim that's true of one book being attributed to another. If that
appears, add a per-document reduce step before the final synthesis.

### Retrieval constants

| Parameter | Value |
|---|---|
| Vector candidates | 50 |
| Keyword candidates | 50 |
| RRF constant `k` | 60 |
| Post-rerank top-k | 8 |
| Survey summaries | 6 |

RRF `k = 60` is the standard value from the original paper and is not worth
tuning before you have a query set to tune against.
