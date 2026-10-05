# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary user: the builder themself, running the pipeline on their own machine
(Apple M2 Pro, 16GB unified memory) for personal research. Built for solo use
first, with an explicit intent to eventually let a friend or colleague
self-host their own instance — not a hosted multi-tenant product.

## Product Purpose

A local, single-user Retrieval-Augmented Generation pipeline over a personal
document corpus (books, reports, manuals, slide decks, plain text). Documents
are organized into projects; the user uploads documents, reviews/corrects the
detected section structure, and then asks questions in a chat interface that
answers using only retrieved passages from that project's documents, with
citations. Success means trustworthy, grounded answers over the user's own
material without re-reading source documents from scratch.

## Positioning

Fully local and offline: extraction, chunking, embedding, and generation all
run on-device (Ollama for embedding/generation, pgvector for storage). No
document content or query ever leaves the machine — this is a hard, durable
constraint, not a cost-driven implementation detail that could later move to
a cloud API. Citations reference a document's section path (`display_path`),
never raw page numbers, so answers stay meaningful independent of the source
file's pagination.

## Operating Context

Workflow: upload a document → automatic extraction and section-tree
detection → manual review/correction of structure on a review screen →
background ingest (chunk → embed) → attach documents to one or more
projects → open a project's chat, ask questions across one or many
conversations, with prior conversations reloadable. Corpus is described as a
mixed personal research collection — technical/reference books, papers, and
other documents — not limited to a single genre or single project.

## Capabilities and Constraints

- Supported formats: PDF, DOCX, PPTX, TXT/MD, EPUB.
- Scanned PDFs are explicitly out of scope (rejected via a character-count
  threshold); OCR will not be added.
- Every retrieval query is scoped to a project via a join table
  (`project_documents`) — documents can belong to multiple projects without
  re-embedding.
- Chunks never cross a section boundary; the section tree always covers the
  full document with no gaps.
- Current retrieval is vector-only (pgvector cosine distance); hybrid
  search/reranking/query rewriting (build-phases.md Phase 4) is planned but
  not yet implemented.
- Single background worker process (plain asyncio loop) handles ingest; no
  message queue or task broker by design (single-user).
- Target hardware envelope: ~8GB budget for locally-loaded models on 16GB
  unified memory — a real constraint on model choice and concurrency, not
  just a dev-machine detail.

## Evidence on Hand

- Real ingested corpus used during development: "Designing Data-Intensive
  Applications" by Martin Kleppmann (~600 pages) and other books under a
  "Systems Book" project.
- `evals/baseline.md`: 20 real question/answer pairs with real citations,
  generated against the live pipeline, used to measure retrieval-quality
  changes (Phase 4) against a baseline rather than by feel.
- No invented testimonials, customers, or pricing — none exist and none
  should be fabricated; this is a personal tool, not a commercial product.

## Product Principles

1. Local-first is non-negotiable: no feature may require sending document
   content or queries off-device.
2. Answers must be grounded and traceable — every answer cites the specific
   sections it drew from, and summary-derived citations are always labeled
   as summaries rather than passages the model read.
3. Correctness over convenience in retrieval: project isolation, section
   integrity, and citation accuracy are invariants, not tunable defaults.
4. Built for one real user's actual workflow (own research corpus) before
   generalizing for a second user; self-hostability by someone else is a
   design intent, not yet a support commitment.
5. Don't tune retrieval parameters (chunk size, top-k, RRF constants) without
   a measured query set — `evals/baseline.md` exists for exactly this.
