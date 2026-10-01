# Graph Report - local-rag-pipeline  (2026-10-01)

## Corpus Check
- 180 files · ~134,298 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: (none) 7, .pptx 4, .ini 1)

## Summary
- 1661 nodes · 3334 edges · 120 communities (102 shown, 18 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 253 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3ba6f331`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- conftest.py
- Phase 4 eval — hybrid + cross-encoder reranking (full Phase 4 pipeline)
- Section
- package.json
- DocFormat
- client.ts
- test_structure.py
- test_pdf.py
- compilerOptions
- pdf.py
- models/document.py
- LtreeType
- Block
- extract
- test_conversations.py
- App.tsx
- compilerOptions
- test_text.py
- Document
- Phase 4 eval — hybrid (vector + keyword RRF), no reranking
- documents.py
- DocStatus
- Phase 3 Baseline Evals (vector-only)
- Backend API
- test_summarize.py
- test_project_documents.py
- Ingest pipeline (store → extract → tree → review → chunk → embed → summarise)
- Local RAG Pipeline
- extract
- conversations.py
- chunks table
- hooks.ts
- ChatScreen.tsx
- db service (pgvector/pgvector:pg16)
- run_async_migrations
- embed.py
- ingest/chunk.py
- Lookup/Survey routing toggle
- jobs.py
- test_documents.py
- .oxlintrc.json
- scripts
- Build Phases
- Frontend stack (React+TS+Vite, shadcn/ui, TanStack Query, SSE)
- Social Media and Documentation Icon Sprite
- vite-env.d.ts
- tsconfig.json
- Purple Gradient Geometric Branding Element
- Stacked Technology Layers Hero Illustration
- React Framework Technology
- Vite Build Tool Logo
- setup-env.sh
- rag-backend
- reciprocal_rank_fusion
- UploadScreen.tsx
- build_prompt
- bolder.md
- /impeccable hooks
- Impeccable Documenter
- structure.py
- Responsive Design
- onboard.md
- new-work.md
- SKILL.md
- The Toolkit
- projects.py
- animate.md
- live.md
- Handle `generate`
- Generate Report
- devDependencies
- test_sections.py
- New visual work
- optimize.md
- Scan mode (approach C: auto-extract, then confirm descriptive language)
- critique.md
- Simplify the Design
- Hardening Dimensions
- clarify.md
- Nielsen's 10 Heuristics
- document.md
- polish.md
- quieter.md
- dependencies
- Generate Combined Critique Report
- Init flow
- Product
- Common Cognitive Load Violations
- iOS platform
- Operate mode depth (and Read notes)
- Shape
- adapt.native.md
- Android platform
- colorize.md
- Persona-Based Design Testing
- doctor.md
- Extract Flow
- live-setup.md
- Impeccable Asset Producer
- Impeccable Finish Reviewer
- Impeccable Manual Edit Applier
- Generate Report
- Cognitive Load Assessment
- Impeccable Asset Producer
- Impeccable Finish Reviewer
- Impeccable Manual Edit Applier
- Diagnostic Scan
- Visualize: Direction Comps & Asset Production
- Impeccable Documenter
- Heuristics Scoring Guide

## God Nodes (most connected - your core abstractions)
1. `Document` - 72 edges
2. `Section` - 58 edges
3. `DocFormat` - 32 edges
4. `build_structure()` - 28 edges
5. `_make_project_with_document()` - 28 edges
6. `Chunk` - 27 edges
7. `DocStatus` - 25 edges
8. `Project` - 25 edges
9. `extract()` - 24 edges
10. `assert_valid_blocks()` - 24 edges

## Surprising Connections (you probably didn't know these)
- `How retrieval works` --references--> `rewrite_query()`  [INFERRED]
  README.md → backend/app/retrieval/generate.py
- `Scope and visitor mode` --references--> `ProjectDetailScreen()`  [INFERRED]
  .impeccable/surfaces/frontend-src-screens-chatscreen-tsx.md → frontend/src/screens/ProjectDetailScreen.tsx
- `10. What is the two-phase commit protocol?` --references--> `commit()`  [INFERRED]
  evals/hybrid-no-rerank.md → frontend/src/screens/ReviewScreen.tsx
- `Scope and visitor mode` --references--> `ReviewScreen()`  [INFERRED]
  .impeccable/surfaces/frontend-src-screens-chatscreen-tsx.md → frontend/src/screens/ReviewScreen.tsx
- `Scope and visitor mode` --references--> `UploadScreen()`  [INFERRED]
  .impeccable/surfaces/frontend-src-screens-chatscreen-tsx.md → frontend/src/screens/UploadScreen.tsx

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Ingest flow: API job -> worker -> file storage, embedder, Postgres** — docs_architecture_backend_api, docs_architecture_ingest_worker, docs_architecture_local_file_storage, docs_architecture_embedder, docs_architecture_postgres [EXTRACTED 1.00]
- **Query flow: retrieve, rerank, generate** — docs_architecture_query_engine, docs_architecture_postgres, docs_architecture_reranker, docs_architecture_generator [EXTRACTED 1.00]
- **Needle retrieval flow (project-filtered vector+keyword, RRF, rerank, generate, cite)** — docs_plan_needle_path, docs_plan_project_isolation, docs_plan_rrf_fusion, docs_plan_bge_reranker, docs_plan_qwen3_8b_generator, docs_plan_citations [EXTRACTED 1.00]
- **Baseline-then-measure retrieval improvement loop** — docs_build_phases_phase_3_needle_chat, evals_baseline, docs_build_phases_phase_4_retrieval_quality, docs_plan_rrf_fusion, docs_plan_bge_reranker [EXTRACTED 1.00]
- **Context budget jointly bounds chunk size, top-k and num_ctx** — docs_plan_chunking_700_100, docs_plan_retrieval_constants, docs_plan_model_configuration, docs_plan_multi_doc_survey_single_pass [INFERRED 0.85]
- **PDF heading detection fallback chain (outline -> heuristic -> root)** — backend_tests_extract_fixtures_outline, backend_tests_extract_fixtures_no_outline_with_heuristic, backend_tests_extract_fixtures_no_outline_no_heuristic, section_heading_detection [INFERRED 0.85]
- **PDF rejection/error edge cases** — backend_tests_extract_fixtures_corrupted, backend_tests_extract_fixtures_scanned, backend_tests_extract_fixtures_mostly_text_one_scanned_page [INFERRED 0.85]

## Communities (120 total, 18 thin omitted)

### Community 0 - "conftest.py"
Cohesion: 0.05
Nodes (51): alembic_config, asyncpg, _build_rewrite_prompt(), GenerationError, AsyncClient, Exception, Streaming client for Ollama's generate endpoint (the `rag-gen` model — qwen3:8b…, Raised when Ollama's generate endpoint fails or returns something unexpected. (+43 more)

### Community 1 - "Phase 4 eval — hybrid + cross-encoder reranking (full Phase 4 pipeline)"
Cohesion: 0.06
Nodes (32): 10. What is the two-phase commit protocol?, 11. What is linearizability?, 12. What is the difference between REST and RPC?, 13. What is a message broker used for?, 14. What is the actor model in the context of distributed systems?, 15. What is data partitioning (sharding)?, 16. How does consistent hashing help with partitioning?, 17. What is a secondary index and why is it harder to maintain in a partitioned database? (+24 more)

### Community 2 - "Section"
Cohesion: 0.11
Nodes (55): Chunk, ProjectDocument, Section, SectionSummary, AsyncSession, Candidate, The needle path (docs/plan.md §4.3): vector + keyword candidates, fused by RRF,…, retrieve() (+47 more)

### Community 3 - "package.json"
Cohesion: 0.10
Nodes (18): name, private, type, version, jsdom, oxlint, react-markdown, rehype-raw (+10 more)

### Community 4 - "DocFormat"
Cohesion: 0.21
Nodes (18): _claim_next_job(), Claim and advance one job by one stage. Returns True if work was done., run_worker_iteration(), DocFormat, IngestJob, JobStage, str, _ollama_is_running() (+10 more)

### Community 5 - "client.ts"
Cohesion: 0.09
Nodes (29): SendMessageCallbacks, ChatMode, CitationRead, ConversationRead, DocFormat, DocStatus, DocumentRead, DocumentUploadResponse (+21 more)

### Community 6 - "test_structure.py"
Cohesion: 0.24
Nodes (23): build_structure(), _assert_contiguous_and_round_trips(), _heading(), _para(), _table(), test_coverage_holds_for_empty_blocks(), test_coverage_holds_for_real_docx_extraction(), test_coverage_holds_for_real_markdown_extraction() (+15 more)

### Community 7 - "test_pdf.py"
Cohesion: 0.22
Nodes (18): extract(), Path, assert_valid_blocks(), test_anchor_equals_one_indexed_page_number(), test_corrupted_file_raises_clear_exception(), test_document_average_not_per_page_drives_the_guard(), test_font_heuristic_reading_order_preserved(), test_line_repeating_on_only_two_of_five_pages_is_not_stripped() (+10 more)

### Community 8 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 9 - "pdf.py"
Cohesion: 0.13
Nodes (21): Exception, Raised when a document has near-zero extractable text — e.g. a scanned PDF with…, ScannedDocumentError, _blocks_from_font_heuristic(), _blocks_from_outline(), _clean_row(), _guard_not_scanned(), _page_blocks() (+13 more)

### Community 10 - "models/document.py"
Cohesion: 0.24
Nodes (13): Run migrations in 'offline' mode. This configures the context with just a URL…, run_migrations_offline(), Base, Message, datetime, DeclarativeBase, enum, logging_config (+5 more)

### Community 11 - "LtreeType"
Cohesion: 0.33
Nodes (4): LtreeType, Any, Maps to Postgres LTREE. Stored and returned as plain str paths., sqlalchemy_types

### Community 12 - "Block"
Cohesion: 0.11
Nodes (20): Block, The Block IR — the only thing that may cross out of app/extract/. Every format-…, _iter_block_items(), Extractor for .docx files (python-docx). Heading N styles map to heading…, _table_to_markdown(), Extractor for .pptx files (python-pptx). Slide titles become heading blocks…, Extractor for .txt and .md files. No page concept, so `anchor` is just a…, Join block texts with `_SEPARATOR`, returning the joined string and each… (+12 more)

### Community 13 - "extract"
Cohesion: 0.27
Nodes (10): extract(), Path, test_anchor_is_sequential_block_index(), test_blank_paragraphs_are_skipped(), test_heading_styles_map_to_levels(), test_list_becomes_list_block(), test_no_heading_styles_produces_zero_headings(), test_normal_paragraphs_have_no_level() (+2 more)

### Community 14 - "test_conversations.py"
Cohesion: 0.10
Nodes (47): embed_batch(), EmbeddingError, AsyncClient, Exception, Raised when Ollama's embed endpoint fails or returns something unexpected., _client(), AsyncClient, test_embed_batch_empty_input_returns_empty_list() (+39 more)

### Community 15 - "App.tsx"
Cohesion: 0.11
Nodes (19): createProject(), listProjects(), useCreateProject(), useProjects(), App(), queryClient, View, Shell() (+11 more)

### Community 16 - "compilerOptions"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 17 - "test_text.py"
Cohesion: 0.10
Nodes (29): extract(), Path, Corrupted PDF fixture (not a real PDF; expects extraction error), Empty text fixture (no content; expects []), PDF with repeated header/footer ('My Book Title'/'Confidential Draft') to strip, Markdown headings fixture (H1/H2/H3 hierarchy), Markdown list fixture (heading + bullet list), Mostly-text PDF with one scanned page (should pass char-count check) (+21 more)

### Community 18 - "Document"
Cohesion: 0.16
Nodes (21): argparse, asyncio, get_settings(), Settings, get_db(), AsyncSession, main(), Backfill command — generates section summaries for documents that were indexed… (+13 more)

### Community 19 - "Phase 4 eval — hybrid (vector + keyword RRF), no reranking"
Cohesion: 0.06
Nodes (31): 10. What is the two-phase commit protocol?, 11. What is linearizability?, 12. What is the difference between REST and RPC?, 13. What is a message broker used for?, 14. What is the actor model in the context of distributed systems?, 15. What is data partitioning (sharding)?, 16. How does consistent hashing help with partitioning?, 17. What is a secondary index and why is it harder to maintain in a partitioned database? (+23 more)

### Community 20 - "documents.py"
Cohesion: 0.14
Nodes (22): aiofiles, delete_document(), _format_from_filename(), get_document(), _link_to_project(), list_documents(), DbSession, delete (+14 more)

### Community 21 - "DocStatus"
Cohesion: 0.20
Nodes (14): backfill(), DocStatus, str, _make_document(), _NoCloseSessionContext, AsyncSession, MonkeyPatch, Wraps the test's own db_session so backfill()'s `async with… (+6 more)

### Community 22 - "Phase 3 Baseline Evals (vector-only)"
Cohesion: 0.20
Nodes (15): Invariant: page numbers never appear in output, Invariant: every retrieval query filters by project_id, Invariant: survey answers cite labelled summaries, Phase 3 — needle chat, Chat screen (scope bar, toggle, collapsed sources), Citations (claim-level markers, breadcrumb sources), conversations and messages tables, sections.display_path breadcrumb (+7 more)

### Community 23 - "Backend API"
Cohesion: 0.20
Nodes (15): Local RAG Pipeline System Architecture Diagram, Backend API, Browser, Embedder (text to vector, ingest only), Frontend (SPA), Generator (writes answers, query only), Extraction -> Structuring -> Chunking -> Embedding, Ingest Worker (+7 more)

### Community 24 - "test_summarize.py"
Cohesion: 0.13
Nodes (25): needs_summary(), persist_section_summary(), AsyncClient, AsyncSession, Exception, Section summarisation for the survey path (docs/plan.md §2.5, §4.4, §8). Calls…, Raised when Ollama's generate endpoint fails or returns something unexpected…, Below the threshold a section is only a chunk or two, already close to being… (+17 more)

### Community 25 - "test_project_documents.py"
Cohesion: 0.37
Nodes (15): _create_document(), _create_project(), AsyncClient, AsyncSession, test_attach_404s_for_unknown_document(), test_attach_404s_for_unknown_project(), test_attach_document_is_idempotent(), test_attach_document_to_project() (+7 more)

### Community 26 - "Ingest pipeline (store → extract → tree → review → chunk → embed → summarise)"
Cohesion: 0.23
Nodes (12): Block IR (TypedDict), Invariant: section tree covers full document, Invariant: every parser emits Block, No OCR / scanned PDFs out of scope, Phase 1 — extraction, Format extractors (PyMuPDF, python-docx, python-pptx, stdlib), Header/footer stripping, Ingest pipeline (store → extract → tree → review → chunk → embed → summarise) (+4 more)

### Community 27 - "Local RAG Pipeline"
Cohesion: 0.14
Nodes (14): 1. One-time environment setup, 2. Database, 3. Install app dependencies, 4. Verify Ollama is up and dimensions match, 5. Run everything, Configuration, How retrieval works, Local RAG Pipeline (+6 more)

### Community 28 - "extract"
Cohesion: 0.23
Nodes (11): extract(), Path, _table_to_markdown(), test_anchor_is_sequential_block_index(), test_blank_slide_produces_no_blocks(), test_reading_order_is_slide_order_title_then_body(), test_slide_body_becomes_paragraphs(), test_slide_titles_become_headings() (+3 more)

### Community 29 - "conversations.py"
Cohesion: 0.16
Nodes (27): create_conversation(), delete_conversation(), _get_active_conversation(), list_conversations(), list_deleted_conversations(), list_messages(), _load_citations(), DbSession (+19 more)

### Community 30 - "chunks table"
Cohesion: 0.15
Nodes (18): Invariant: chunks never cross a section boundary, Invariant: embed_text embedded, text displayed/keyword-searched, Vector(1024) columns; embedder change = migration + re-index, Phase 2 — index, Phase 4 — retrieval quality, Phase 6 — polish, Architecture (UI / API / Ingest worker / Query engine / Postgres), bge-reranker-base cross-encoder (in-process) (+10 more)

### Community 31 - "hooks.ts"
Cohesion: 0.09
Nodes (40): attachDocumentToProject(), createConversation(), deleteConversation(), deleteDocument(), detachDocumentFromProject(), getProject(), getSections(), listAllDocuments() (+32 more)

### Community 32 - "ChatScreen.tsx"
Cohesion: 0.18
Nodes (15): listMessages(), sendMessage(), useMessages(), ChapterRow(), ChatScreen(), handleNewConversation(), handleSend(), switchConversation() (+7 more)

### Community 33 - "db service (pgvector/pgvector:pg16)"
Cohesion: 0.18
Nodes (11): just commands (dev, test, db-up, migrate, check-models), Tests use real Postgres, no DB mocks, No Redis/Celery/message queue; plain asyncio worker, db service (pgvector/pgvector:pg16), init-extensions.sql initdb mount, pgdata volume, Phase 0 — skeleton, documents table (+3 more)

### Community 34 - "run_async_migrations"
Cohesion: 0.33
Nodes (6): do_run_migrations(), In this scenario we need to create an Engine and associate a connection with…, Run migrations in 'online' mode., run_async_migrations(), run_migrations_online(), Connection

### Community 35 - "embed.py"
Cohesion: 0.35
Nodes (9): get_or_create_embedding_run(), AsyncSession, Async client for Ollama's embed endpoint. Calls Ollama over HTTP rather than…, One row per (model, dimension). Swapping embedders is a deliberate, manual re-…, EmbeddingRun, AsyncSession, test_different_model_creates_a_separate_run(), test_first_call_creates_a_new_current_run() (+1 more)

### Community 36 - "ingest/chunk.py"
Cohesion: 0.15
Nodes (25): chunk_section(), ChunkDraft, persist_chunks(), AsyncSession, Chunker: splits a section's text into overlapping token windows. A flat token-…, Slide a 700-token/100-overlap window over one section's text.…, Chunk every section and write the resulting rows. embedding and…, tokenizer() (+17 more)

### Community 37 - "Lookup/Survey routing toggle"
Cohesion: 0.47
Nodes (6): Phase 5 — survey path, Multi-document survey: single pass, no reduce step, Lookup/Survey routing toggle, section_summaries table, Summary threshold 1500 tokens, ~200-token target, Survey path (search section summaries)

### Community 38 - "jobs.py"
Cohesion: 0.16
Nodes (10): get_job(), DbSession, get, health(), get, JobRead, BaseModel, fastapi (+2 more)

### Community 39 - "test_documents.py"
Cohesion: 0.21
Nodes (18): AsyncClient, AsyncSession, test_delete_document_removes_everything(), test_delete_unknown_document_404s(), test_get_document_not_found(), test_list_all_documents(), test_reindex_409s_if_a_job_is_already_in_progress(), test_reindex_unknown_document_404s() (+10 more)

### Community 40 - ".oxlintrc.json"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 41 - "scripts"
Cohesion: 0.33
Nodes (6): scripts, build, dev, lint, preview, test

### Community 42 - "Build Phases"
Cohesion: 0.60
Nodes (3): CLAUDE.md Project Memory, Build Phases, Local RAG Pipeline Design Plan

### Community 43 - "Frontend stack (React+TS+Vite, shadcn/ui, TanStack Query, SSE)"
Cohesion: 0.67
Nodes (3): Frontend stack (React+TS+Vite, shadcn/ui, TanStack Query, SSE), frontend index.html entry (mounts #root, loads src/main.tsx), Frontend README (Vite React TS template)

### Community 44 - "Social Media and Documentation Icon Sprite"
Cohesion: 0.67
Nodes (3): Documentation Icon, Social Media Icons Collection, Social Media and Documentation Icon Sprite

### Community 63 - "reciprocal_rank_fusion"
Cohesion: 0.33
Nodes (9): Reciprocal rank fusion — combines the vector and keyword candidate lists into…, reciprocal_rank_fusion(), test_a_chunk_in_both_lists_outranks_one_in_only_one_list(), test_both_lists_empty_returns_empty(), test_chunk_only_in_keyword_list_is_still_included(), test_chunk_only_in_vector_list_is_still_included(), test_final_order_is_by_descending_fused_score(), test_output_truncated_to_top_k() (+1 more)

### Community 64 - "UploadScreen.tsx"
Cohesion: 0.28
Nodes (7): getJob(), uploadDocument(), useJob(), useUploadDocument(), STAGES, UploadScreen(), UploadScreenProps

### Community 65 - "build_prompt"
Cohesion: 0.43
Nodes (6): build_prompt(), Assembles the prompt sent to the generator: system instructions, numbered…, test_history_appears_in_order(), test_no_history_does_not_crash_or_leave_stray_markers(), test_question_is_the_final_user_turn_followed_by_assistant_cue(), test_sources_appear_verbatim_and_numbered_from_one()

### Community 66 - "bolder.md"
Cohesion: 0.33
Nodes (5): Before you finish, Scope is sovereign, The amplification, The skeleton test, Why it reads flat

### Community 67 - "/impeccable hooks"
Cohesion: 0.33
Nodes (6): Constraints, Failure modes, Flow, /impeccable hooks, Routing, Triage findings

### Community 68 - "Impeccable Documenter"
Cohesion: 0.40
Nodes (4): Impeccable Documenter, Input Contract, Output Contract, Workflow

### Community 71 - "structure.py"
Cohesion: 0.07
Nodes (42): list_sections(), DbSession, get, patch, _to_read_model(), update_section(), estimate_chunks(), find_uncovered_ranges() (+34 more)

### Community 72 - "Responsive Design"
Cohesion: 0.08
Nodes (25): Assess Adaptation Challenge, Breakpoints: Content-Driven, Content Adaptation, Desktop Adaptation (Mobile → Desktop), Detect Input Method, Not Just Screen Size, Email Adaptation (Web → Email), Implement Adaptations, Layout Adaptation Patterns (+17 more)

### Community 74 - "onboard.md"
Cohesion: 0.09
Nodes (22): Assess Onboarding Needs, Context Over Ceremony, Contextual Help, Design Onboarding Experiences, Documentation & Help, Empty State Design, Feature Discovery & Adoption, Guided Tours & Walkthroughs (+14 more)

### Community 76 - "new-work.md"
Cohesion: 0.13
Nodes (14): Recommended Actions, Craft (deprecated alias), Apply, Live-mode signature params, Set the spatial thesis, Two isolated assessments, Verify, Visitor mode (+6 more)

### Community 77 - "SKILL.md"
Cohesion: 0.15
Nodes (10): Craft floor, Refuse, Verify, Command guidance, No-argument routing: the context-aware menu, Workflow questions, Commands, How to design (+2 more)

### Community 78 - "The Toolkit"
Cohesion: 0.10
Nodes (20): Animate complex properties, Assess What "Extraordinary" Means Here, For data-heavy interfaces, For functional UI, For performance-critical UI, For visual/marketing surfaces, Implement with Discipline, Interact with the device (+12 more)

### Community 80 - "projects.py"
Cohesion: 0.20
Nodes (20): attach_document(), create_project(), delete_project(), detach_document(), get_project(), list_project_documents(), list_projects(), DbSession (+12 more)

### Community 84 - "animate.md"
Cohesion: 0.12
Nodes (14): Accessibility and control, Choose material by meaning, Find the job, Implement to the runtime, Set the motion thesis, Timing and easing, Verify, Visitor mode (+6 more)

### Community 85 - "live.md"
Cohesion: 0.12
Nodes (15): Cleanup, Exit, First-time setup, Handle `accept`, Handle `discard`, Handle fallback, Handle `manual_edit_apply`, Handle `prefetch` (+7 more)

### Community 86 - "Handle `generate`"
Cohesion: 0.12
Nodes (16): 1. Read the screenshot (if present), 2. Wrap the element, 3. Load the action's reference, 4. Plan three variants: identity first, then mode, then axes, 5. Apply the freeform prompt (if present), 6. Deliver variants, 7. Parameters (composition-sized, 0-4 per variant), 8. Signal done (+8 more)

### Community 88 - "Generate Report"
Cohesion: 0.13
Nodes (14): 1. Accessibility (A11y), 2. Performance, 3. Theming, 4. Responsive Design, 5. Implementation Integrity (CRITICAL), Audit Health Score, Detailed Findings by Severity, Diagnostic Scan (+6 more)

### Community 89 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, jsdom, oxlint, tailwindcss, @tailwindcss/typography, @tailwindcss/vite, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 91 - "test_sections.py"
Cohesion: 0.41
Nodes (13): _make_document_with_section(), AsyncClient, AsyncSession, test_list_sections_empty_for_document_without_sections(), test_list_sections_for_document(), test_list_sections_for_unknown_document_404s(), test_list_sections_includes_chunk_estimate(), test_list_sections_includes_preview_text() (+5 more)

### Community 92 - "New visual work"
Cohesion: 0.14
Nodes (14): 1. Decide what is already true, 2. Ask what will change the work, 3. Choose the right amount of invention, 4. Commit the world, 5. Record the decision, 6. Build with full commitment, 7. Inspect and finish, Both paths (+6 more)

### Community 93 - "optimize.md"
Cohesion: 0.14
Nodes (13): Animation Performance, Assess Performance Issues, Core Web Vitals Optimization, Cumulative Layout Shift (CLS < 0.1), Interaction to Next Paint (INP < 200ms), Largest Contentful Paint (LCP < 2.5s), Loading Performance, Network Optimization (+5 more)

### Community 94 - "Scan mode (approach C: auto-extract, then confirm descriptive language)"
Cohesion: 0.15
Nodes (13): Component translation rules, Narrative mapping, Scan mode (approach C: auto-extract, then confirm descriptive language), Schema, Step 1: Find the design assets, Step 2: Auto-extract what can be auto-extracted, Step 2b: Stage the frontmatter, Step 3: Ask the user for qualitative language (+5 more)

### Community 95 - "critique.md"
Cohesion: 0.17
Nodes (11): Action Summary, Ask the User, Assessment A: Design Review, Assessment B: Detector + Browser Evidence, Assessment Orchestration, Deliver the Report, Hard Invariants, Persist the Snapshot (+3 more)

### Community 96 - "Simplify the Design"
Cohesion: 0.17
Nodes (11): Assess Current State, Code Simplification, Content Simplification, Document Removed Complexity, Information Architecture, Interaction Simplification, Layout Simplification, Plan Simplification (+3 more)

### Community 97 - "Hardening Dimensions"
Cohesion: 0.17
Nodes (11): Accessibility Resilience, Assess Hardening Needs, Edge Cases & Boundary Conditions, Error Handling, Hardening Dimensions, Input Validation & Sanitization, Internationalization (i18n), Performance Resilience (+3 more)

### Community 98 - "clarify.md"
Cohesion: 0.18
Nodes (10): Actions and navigation, Audit the language, Errors and permissions, Forms, Help and instructional text, Loading, empty, and success states, Rewrite by function, Set the message hierarchy (+2 more)

### Community 99 - "Nielsen's 10 Heuristics"
Cohesion: 0.18
Nodes (11): 10. Help and Documentation, 1. Visibility of System Status, 2. Match Between System and Real World, 3. User Control and Freedom, 4. Consistency and Standards, 5. Error Prevention, 6. Recognition Rather Than Recall, 7. Flexibility and Efficiency of Use (+3 more)

### Community 100 - "document.md"
Cohesion: 0.18
Nodes (10): Pitfalls, Seed mode, Step 1: Route through new-work's workshop, Step 2: Write seed DESIGN.md, Step 3: Confirm, Style guidelines, The frontmatter: token schema, The markdown body: eight sections (canonical order) (+2 more)

### Community 101 - "polish.md"
Cohesion: 0.18
Nodes (10): 1. Establish the system, 2. Gather the evidence, 3. Triage, 4. Polish the whole path, 5. Verify and finish, Color, imagery, and icons, Content and code, Flow and hierarchy (+2 more)

### Community 102 - "quieter.md"
Cohesion: 0.18
Nodes (10): Assess Current State, Color Refinement, Composition Refinement, Motion Reduction, Plan Refinement, Refine the Design, Simplification, Verify Quality (+2 more)

### Community 103 - "dependencies"
Cohesion: 0.29
Nodes (7): dependencies, react, react-dom, react-markdown, rehype-raw, remark-gfm, @tanstack/react-query

### Community 104 - "Generate Combined Critique Report"
Cohesion: 0.20
Nodes (10): Design Health Score, Design Specificity Verdict, Generate Combined Critique Report, Minor Observations, Overall Impression, Persona Red Flags, Priority Issues, Questions to Consider (+2 more)

### Community 105 - "Init flow"
Cohesion: 0.20
Nodes (10): Completion gate, Init flow, Step 1: Load current state, Step 2: Explore the project, Step 3: Interview for product truth, Step 4: Write PRODUCT.md, Step 5: Record workflow defaults, Step 6: Wrap up or resume (+2 more)

### Community 107 - "Product"
Cohesion: 0.22
Nodes (9): Capabilities and Constraints, Evidence on Hand, Operating Context, Platform, Positioning, Product, Product Principles, Product Purpose (+1 more)

### Community 108 - "Common Cognitive Load Violations"
Cohesion: 0.22
Nodes (9): 1. The Wall of Options, 2. The Memory Bridge, 3. The Hidden Navigation, 4. The Jargon Barrier, 5. The Visual Noise Floor, 6. The Inconsistent Pattern, 7. The Multi-Task Demand, 8. The Context Switch (+1 more)

### Community 109 - "iOS platform"
Cohesion: 0.22
Nodes (9): Color & materials, Components & controls, iOS platform, Layout & structure, Motion, The iOS slop test, Touch targets, Typography (+1 more)

### Community 110 - "Operate mode depth (and Read notes)"
Cohesion: 0.22
Nodes (9): Color, Components, Layout, Motion, Operate mode depth (and Read notes), Product constraints, Product permissions, The product slop test (+1 more)

### Community 111 - "Shape"
Cohesion: 0.22
Nodes (8): Cadence, Confirm and stop, Phase 1: Discovery interview, Phase 2: Resolve the design direction, Phase 3: Write the brief, Round 1: purpose, people, and outcome, Round 2: material, behavior, and boundaries, Shape

### Community 112 - "adapt.native.md"
Cohesion: 0.25
Nodes (7): Adaptation Strategies, Assess Adaptation Challenge, Implement & Verify, Orientation & foldables, Phone → Tablet (iPad / large screens), Platform → platform (iOS ↔ Android), Web → native (porting a website or web app)

### Community 113 - "Android platform"
Cohesion: 0.25
Nodes (8): Android platform, Color & theming, Components & motion, Layout & structure, The Android slop test, Touch targets, Typography, Verifying the build

### Community 114 - "colorize.md"
Cohesion: 0.25
Nodes (7): Apply at system scale, Audit before choosing, Choose a strategy, Contrast and perception, Live-mode signature params, Verify, Visitor mode

### Community 115 - "Persona-Based Design Testing"
Cohesion: 0.25
Nodes (8): 1. Impatient Power User: "Alex", 2. Confused First-Timer: "Jordan", 3. Accessibility-Dependent User: "Sam", 4. Deliberate Stress Tester: "Riley", 5. Distracted Mobile User: "Casey", Persona-Based Design Testing, Project-Specific Personas, Selecting Personas

### Community 116 - "doctor.md"
Cohesion: 0.25
Nodes (7): Monorepo notes, Opting out of the boot check, Step 1: Run the pass, Step 2: Act by severity, Step 3: Deprecated fields are binding, Step 4: Do not overclaim on truth drift, What this owns, and what it does not

### Community 117 - "Extract Flow"
Cohesion: 0.25
Nodes (7): Extract Flow, Step 1: Discover the Design System, Step 2: Identify Patterns, Step 3: Plan Extraction, Step 4: Extract & Enrich, Step 5: Migrate, Step 6: Document

### Community 118 - "live-setup.md"
Cohesion: 0.25
Nodes (7): append-arrays, append-string, Config drift, Consent prompt (use this phrasing), CSP detection (first-time only), Troubleshooting, Write the config

### Community 119 - "Impeccable Asset Producer"
Cohesion: 0.29
Nodes (6): Core Rule, Decision Comps, Impeccable Asset Producer, Input Contract, Output Contract, The job

### Community 120 - "Impeccable Finish Reviewer"
Cohesion: 0.29
Nodes (6): Checks, in order, Disposition, Impeccable Finish Reviewer, Input Contract, Output Contract, Verdict Pass

### Community 121 - "Impeccable Manual Edit Applier"
Cohesion: 0.29
Nodes (6): Checks, Entry Atomicity, Impeccable Manual Edit Applier, Input Contract, Output Contract, Workflow

### Community 122 - "Generate Report"
Cohesion: 0.29
Nodes (7): Audit Health Score, Detailed Findings by Severity, Executive Summary, Generate Report, Patterns & Systemic Issues, Platform Conformance Verdict, Positive Findings

### Community 123 - "Cognitive Load Assessment"
Cohesion: 0.29
Nodes (7): Cognitive Load Assessment, Cognitive Load Checklist, Extraneous Load: Bad Design, Germane Load: Learning Effort, Intrinsic Load: The Task Itself, The Working Memory Rule, Three Types of Cognitive Load

### Community 124 - "Impeccable Asset Producer"
Cohesion: 0.29
Nodes (6): Core Rule, Decision Comps, Impeccable Asset Producer, Input Contract, Output Contract, The job

### Community 125 - "Impeccable Finish Reviewer"
Cohesion: 0.29
Nodes (6): Checks, in order, Disposition, Impeccable Finish Reviewer, Input Contract, Output Contract, Verdict Pass

### Community 126 - "Impeccable Manual Edit Applier"
Cohesion: 0.29
Nodes (6): Checks, Entry Atomicity, Impeccable Manual Edit Applier, Input Contract, Output Contract, Workflow

### Community 129 - "Diagnostic Scan"
Cohesion: 0.33
Nodes (6): 1. Accessibility (VoiceOver / TalkBack), 2. Performance, 3. Appearance & Theming, 4. Platform Conformance (CRITICAL), 5. Adaptivity, Diagnostic Scan

### Community 131 - "Visualize: Direction Comps & Asset Production"
Cohesion: 0.33
Nodes (5): After approval: the comp becomes a spec, Generate three compositional options, One approval point, Plates and provenance, Visualize: Direction Comps & Asset Production

### Community 133 - "Impeccable Documenter"
Cohesion: 0.40
Nodes (4): Impeccable Documenter, Input Contract, Output Contract, Workflow

### Community 135 - "Heuristics Scoring Guide"
Cohesion: 0.50
Nodes (4): Heuristics Scoring Guide, Issue Severity (P0–P3), Reference Material, Score Summary

## Ambiguous Edges - Review These
- `Ollama local model server` → `Reranker (in-process)`  [AMBIGUOUS]
  docs/architecture.svg · relation: conceptually_related_to
- `Phase 6 — polish` → `Query rewriting for follow-ups`  [AMBIGUOUS]
  docs/plan.md · relation: references

## Knowledge Gaps
- **599 isolated node(s):** `rag-backend`, `$schema`, `plugins`, `react/rules-of-hooks`, `react/only-export-components` (+594 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 807 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Ollama local model server` and `Reranker (in-process)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Phase 6 — polish` and `Query rewriting for follow-ups`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `rewrite_query()` connect `conftest.py` to `Document`, `Local RAG Pipeline`, `conversations.py`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `Local RAG Pipeline` connect `Local RAG Pipeline` to `Build Phases`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `How retrieval works` connect `Local RAG Pipeline` to `conftest.py`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 32 inferred relationships involving `Document` (e.g. with `_load_citations()` and `delete_document()`) actually correct?**
  _`Document` has 32 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `Section` (e.g. with `_load_citations()` and `reindex_document()`) actually correct?**
  _`Section` has 18 INFERRED edges - model-reasoned connections that need verification._