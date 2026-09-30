# Graph Report - local-rag-pipeline  (2026-09-30)

## Corpus Check
- 169 files · ~165,664 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 8, .pptx 4, .cmd 1)

## Summary
- 2018 nodes · 4621 edges · 135 communities (117 shown, 18 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 243 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cfba7471`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- conversations.py
- test_review.py
- documents.py
- package.json
- Document
- types.ts
- test_structure.py
- test_pdf.py
- compilerOptions
- Block
- httpx
- UploadScreen.tsx
- test_text.py
- assert_valid_blocks
- test_conversations.py
- App.tsx
- compilerOptions
- client
- extract
- embed.py
- Block IR (heading/paragraph/list/table)
- live-browser.js
- Phase 3 Baseline Evals (vector-only)
- Backend API
- chunk_section
- test_project_documents.py
- Ingest pipeline (store → extract → tree → review → chunk → embed → summarise)
- env.py
- conftest.py
- applyEditing
- Needle path (vector + keyword + RRF + rerank + generate)
- hooks.ts
- ChatScreen.tsx
- db service (pgvector/pgvector:pg16)
- handleGo
- build_prompt
- test_documents.py
- sections table (ltree section tree)
- test_projects.py
- chunks table
- .oxlintrc.json
- test_jobs.py
- CLAUDE.md Project Memory
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
- resumeSession
- setLiveState
- modern-screenshot.umd.js
- el
- renderDesignVisual
- captureElementToBlob
- initPageChat
- initGlobalBar
- Section
- Responsive Design
- scheduleAcceptCleanup
- onboard.md
- handleManualEditActivity
- new-work.md
- SKILL.md
- The Toolkit
- showToast
- jobs.py
- resolveLiveInjectionAnchor
- createLiveBrowserSessionState
- Chunk
- animate.md
- live.md
- Handle `generate`
- createLiveBrowserDomHelpers
- Generate Report
- devDependencies
- onAnnotDown
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
- showAnnotOverlay
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
- live-browser-ignores.js
- Diagnostic Scan
- /impeccable hooks
- Visualize: Direction Comps & Asset Production
- impeccable
- Impeccable Documenter
- Impeccable Documenter
- Heuristics Scoring Guide

## God Nodes (most connected - your core abstractions)
1. `Document` - 47 edges
2. `Section` - 33 edges
3. `setLiveState()` - 32 edges
4. `resumeSession()` - 32 edges
5. `connectSSE()` - 31 edges
6. `showToast()` - 30 edges
7. `el()` - 29 edges
8. `initGlobalBar()` - 29 edges
9. `build_structure()` - 28 edges
10. `handleKeyDown()` - 27 edges

## Surprising Connections (you probably didn't know these)
- `Scope and visitor mode` --references--> `ProjectDetailScreen()`  [INFERRED]
  .impeccable/surfaces/frontend-src-screens-chatscreen-tsx.md → frontend/src/screens/ProjectDetailScreen.tsx
- `Scope and visitor mode` --references--> `ProjectsListScreen()`  [INFERRED]
  .impeccable/surfaces/frontend-src-screens-chatscreen-tsx.md → frontend/src/screens/ProjectsListScreen.tsx
- `Scope and visitor mode` --references--> `UploadScreen()`  [INFERRED]
  .impeccable/surfaces/frontend-src-screens-chatscreen-tsx.md → frontend/src/screens/UploadScreen.tsx
- `Step 2: Act by severity` --references--> `init()`  [INFERRED]
  .claude/skills/impeccable/reference/doctor.md → .claude/skills/impeccable/scripts/live-browser.js
- `What this owns, and what it does not` --references--> `init()`  [INFERRED]
  .claude/skills/impeccable/reference/doctor.md → .claude/skills/impeccable/scripts/live-browser.js

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

## Communities (135 total, 18 thin omitted)

### Community 0 - "conversations.py"
Cohesion: 0.16
Nodes (27): create_conversation(), list_conversations(), list_messages(), DbSession, get, post, send_message(), event_stream() (+19 more)

### Community 1 - "test_review.py"
Cohesion: 0.18
Nodes (20): estimate_chunks(), find_uncovered_ranges(), _HasCharRange, Pure helpers for the structure review screen: preview text, a chunk/token…, Character ranges in [0, raw_text_len) not covered by any section. Ignores…, section_preview(), _close_gaps(), Stretch every section forward to touch the next one, so separators between… (+12 more)

### Community 2 - "documents.py"
Cohesion: 0.13
Nodes (28): aiofiles, get_document(), _link_to_project(), list_documents(), DbSession, get, attach_document(), create_project() (+20 more)

### Community 3 - "package.json"
Cohesion: 0.09
Nodes (22): name, private, scripts, build, dev, lint, preview, test (+14 more)

### Community 4 - "Document"
Cohesion: 0.13
Nodes (35): _format_from_filename(), post, upload_document(), get_settings(), _advance(), _claim_next_job(), AsyncSession, Ingest worker. Wires extract -> structure -> chunk -> embed for real (Phase 2).… (+27 more)

### Community 5 - "types.ts"
Cohesion: 0.10
Nodes (22): SendMessageCallbacks, CitationRead, DocFormat, DocStatus, DocumentRead, DocumentUploadResponse, JobRead, MessageRead (+14 more)

### Community 6 - "test_structure.py"
Cohesion: 0.23
Nodes (24): build_structure(), _OpenHeading, _assert_contiguous_and_round_trips(), _heading(), _para(), _table(), test_coverage_holds_for_empty_blocks(), test_coverage_holds_for_real_docx_extraction() (+16 more)

### Community 7 - "test_pdf.py"
Cohesion: 0.16
Nodes (21): Exception, Raised when a document has near-zero extractable text — e.g. a scanned PDF with…, ScannedDocumentError, extract(), _guard_not_scanned(), Path, test_anchor_equals_one_indexed_page_number(), test_corrupted_file_raises_clear_exception() (+13 more)

### Community 8 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 9 - "Block"
Cohesion: 0.13
Nodes (21): Block, _blocks_from_font_heuristic(), _blocks_from_outline(), _clean_row(), _page_blocks(), _page_table_items(), _page_text_items(), Any (+13 more)

### Community 10 - "httpx"
Cohesion: 0.20
Nodes (15): GenerationError, AsyncClient, Exception, Streaming client for Ollama's generate endpoint (the `rag-gen` model — qwen3:8b…, Raised when Ollama's generate endpoint fails or returns something unexpected., stream_generate(), _client(), AsyncClient (+7 more)

### Community 11 - "UploadScreen.tsx"
Cohesion: 0.38
Nodes (5): useJob(), useUploadDocument(), STAGES, UploadScreen(), UploadScreenProps

### Community 12 - "test_text.py"
Cohesion: 0.18
Nodes (13): extract(), Path, Extractor for .txt and .md files. No page concept, so `anchor` is just a…, Shared Block IR contract checks, run against every extractor's output., test_anchor_is_sequential_block_index(), test_empty_file_returns_no_blocks(), test_markdown_headings_map_to_levels(), test_markdown_list_becomes_list_block() (+5 more)

### Community 13 - "assert_valid_blocks"
Cohesion: 0.15
Nodes (20): extract(), _iter_block_items(), Path, Extractor for .docx files (python-docx). Heading N styles map to heading…, _table_to_markdown(), assert_valid_blocks(), test_anchor_is_sequential_block_index(), test_blank_paragraphs_are_skipped() (+12 more)

### Community 14 - "test_conversations.py"
Cohesion: 0.28
Nodes (16): _create_project(), _ollama_is_running(), _parse_sse_events(), AsyncClient, AsyncSession, _seed_embedded_chunk(), test_chat_never_cites_another_projects_chunks(), test_create_conversation() (+8 more)

### Community 15 - "App.tsx"
Cohesion: 0.11
Nodes (20): useSections(), useUpdateSectionTitle(), SectionRead, App(), queryClient, View, Shell(), ShellProps (+12 more)

### Community 16 - "compilerOptions"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 17 - "client"
Cohesion: 0.25
Nodes (7): client(), db_session(), _fresh_test_database(), AsyncClient, AsyncSession, A session bound to a connection whose outer transaction is rolled back after…, fixture

### Community 18 - "extract"
Cohesion: 0.19
Nodes (13): extract(), Path, Extractor for .pptx files (python-pptx). Slide titles become heading blocks…, _table_to_markdown(), test_anchor_is_sequential_block_index(), test_blank_slide_produces_no_blocks(), test_reading_order_is_slide_order_title_then_body(), test_slide_body_becomes_paragraphs() (+5 more)

### Community 19 - "embed.py"
Cohesion: 0.14
Nodes (22): embed_batch(), EmbeddingError, get_or_create_embedding_run(), AsyncClient, AsyncSession, Exception, Async client for Ollama's embed endpoint. Calls Ollama over HTTP rather than…, Raised when Ollama's embed endpoint fails or returns something unexpected. (+14 more)

### Community 20 - "Block IR (heading/paragraph/list/table)"
Cohesion: 0.14
Nodes (19): Corrupted PDF fixture (not a real PDF; expects extraction error), Empty text fixture (no content; expects []), PDF with repeated header/footer ('My Book Title'/'Confidential Draft') to strip, Markdown headings fixture (H1/H2/H3 hierarchy), Markdown list fixture (heading + bullet list), Mostly-text PDF with one scanned page (should pass char-count check), PDF without outline or font-size heading signal (single root section), PDF without outline but with large-font headings (heuristic detection) (+11 more)

### Community 21 - "live-browser.js"
Cohesion: 0.04
Nodes (95): applyGlobalBarLabelState(), applyParamValue(), applyPlaceholderSizingStyles(), bindEditBadgeProxy(), clampVariantIndex(), clearHandled(), clearSteerFocusRecoverTimer(), computeInsertPosition() (+87 more)

### Community 22 - "Phase 3 Baseline Evals (vector-only)"
Cohesion: 0.20
Nodes (15): Invariant: page numbers never appear in output, Invariant: every retrieval query filters by project_id, Invariant: survey answers cite labelled summaries, Phase 3 — needle chat, Chat screen (scope bar, toggle, collapsed sources), Citations (claim-level markers, breadcrumb sources), conversations and messages tables, sections.display_path breadcrumb (+7 more)

### Community 23 - "Backend API"
Cohesion: 0.20
Nodes (15): Local RAG Pipeline System Architecture Diagram, Backend API, Browser, Embedder (text to vector, ingest only), Frontend (SPA), Generator (writes answers, query only), Extraction -> Structuring -> Chunking -> Embedding, Ingest Worker (+7 more)

### Community 24 - "chunk_section"
Cohesion: 0.30
Nodes (13): chunk_section(), ChunkDraft, Slide a 700-token/100-overlap window over one section's text.…, _tokenizer(), Builds text with exactly `target_tokens` tokens, verified against the real…, test_chunk_offsets_are_relative_to_the_document(), test_chunks_never_exceed_their_sections_char_range(), test_embed_text_starts_with_breadcrumb_text_does_not() (+5 more)

### Community 25 - "test_project_documents.py"
Cohesion: 0.45
Nodes (12): _create_document(), _create_project(), AsyncClient, test_attach_404s_for_unknown_document(), test_attach_404s_for_unknown_project(), test_attach_document_is_idempotent(), test_attach_document_to_project(), test_detach_404s_when_link_does_not_exist() (+4 more)

### Community 26 - "Ingest pipeline (store → extract → tree → review → chunk → embed → summarise)"
Cohesion: 0.21
Nodes (13): Block IR (TypedDict), Invariant: section tree covers full document, Invariant: every parser emits Block, No OCR / scanned PDFs out of scope, Phase 1 — extraction, Architecture (UI / API / Ingest worker / Query engine / Postgres), Format extractors (PyMuPDF, python-docx, python-pptx, stdlib), Header/footer stripping (+5 more)

### Community 27 - "env.py"
Cohesion: 0.20
Nodes (11): asyncio, do_run_migrations(), Run migrations in 'offline' mode. This configures the context with just a URL…, In this scenario we need to create an Engine and associate a connection with…, Run migrations in 'online' mode., run_async_migrations(), run_migrations_offline(), run_migrations_online() (+3 more)

### Community 28 - "conftest.py"
Cohesion: 0.11
Nodes (16): alembic_config, asyncpg, Settings, get_db(), AsyncSession, The Block IR — the only thing that may cross out of app/extract/. Every format-…, Test fixtures. Runs against a real Postgres (the docker-compose `db` service) —…, BaseSettings (+8 more)

### Community 29 - "applyEditing"
Cohesion: 0.08
Nodes (34): addManualContextText(), applyEditing(), buildLocatorForLeaf(), canRestoreManualEditElement(), collectEditableTextRows(), visit(), collectManualContextPieces(), walk() (+26 more)

### Community 30 - "Needle path (vector + keyword + RRF + rerank + generate)"
Cohesion: 0.24
Nodes (11): Phase 4 — retrieval quality, Phase 6 — polish, bge-reranker-base cross-encoder (in-process), Chunking 700 tokens / 100 overlap, Model configuration (embedder, reranker, generator), Needle path (vector + keyword + RRF + rerank + generate), Query rewriting for follow-ups, Qwen 3 8B generator via Ollama (+3 more)

### Community 31 - "hooks.ts"
Cohesion: 0.14
Nodes (29): attachDocumentToProject(), createConversation(), createProject(), detachDocumentFromProject(), getJob(), getProject(), getSections(), listAllDocuments() (+21 more)

### Community 32 - "ChatScreen.tsx"
Cohesion: 0.17
Nodes (17): sendMessage(), useMessages(), ConversationRead, ChapterRow(), ChapterRowProps, ChatScreen(), handleNewConversation(), handleSend() (+9 more)

### Community 33 - "db service (pgvector/pgvector:pg16)"
Cohesion: 0.20
Nodes (10): just commands (dev, test, db-up, migrate, check-models), Tests use real Postgres, no DB mocks, No Redis/Celery/message queue; plain asyncio worker, db service (pgvector/pgvector:pg16), init-extensions.sql initdb mount, pgdata volume, Phase 0 — skeleton, documents table (+2 more)

### Community 34 - "handleGo"
Cohesion: 0.13
Nodes (22): buildInsertPlaceholderSnapshotFromDom(), buildPickedAnchorSnapshot(), captureAndEmit(), compileShader(), extractContext(), finishVoiceSession(), handleGo(), handleInsertCreate() (+14 more)

### Community 35 - "build_prompt"
Cohesion: 0.43
Nodes (6): build_prompt(), Assembles the prompt sent to the generator: system instructions, numbered…, test_history_appears_in_order(), test_no_history_does_not_crash_or_leave_stray_markers(), test_question_is_the_final_user_turn_followed_by_assistant_cue(), test_sources_appear_verbatim_and_numbered_from_one()

### Community 36 - "test_documents.py"
Cohesion: 0.48
Nodes (6): AsyncClient, test_get_document_not_found(), test_list_all_documents(), test_upload_rejects_unsupported_format(), test_upload_returns_job_and_creates_document(), test_uploading_same_content_twice_dedupes()

### Community 37 - "sections table (ltree section tree)"
Cohesion: 0.38
Nodes (7): Phase 5 — survey path, Multi-document survey: single pass, no reduce step, Lookup/Survey routing toggle, section_summaries table, sections table (ltree section tree), Summary threshold 1500 tokens, ~200-token target, Survey path (search section summaries)

### Community 38 - "test_projects.py"
Cohesion: 0.53
Nodes (5): AsyncClient, test_create_and_get_project(), test_delete_project(), test_get_project_not_found(), test_list_projects_includes_created()

### Community 39 - "chunks table"
Cohesion: 0.40
Nodes (6): Invariant: chunks never cross a section boundary, Invariant: embed_text embedded, text displayed/keyword-searched, Vector(1024) columns; embedder change = migration + re-index, Phase 2 — index, chunks table, embedding_runs (embedding provenance)

### Community 40 - ".oxlintrc.json"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 41 - "test_jobs.py"
Cohesion: 0.67
Nodes (3): AsyncClient, test_get_job_after_upload(), test_get_job_not_found()

### Community 42 - "CLAUDE.md Project Memory"
Cohesion: 1.00
Nodes (3): CLAUDE.md Project Memory, Build Phases, Local RAG Pipeline Design Plan

### Community 43 - "Frontend stack (React+TS+Vite, shadcn/ui, TanStack Query, SSE)"
Cohesion: 0.67
Nodes (3): Frontend stack (React+TS+Vite, shadcn/ui, TanStack Query, SSE), frontend index.html entry (mounts #root, loads src/main.tsx), Frontend README (Vite React TS template)

### Community 44 - "Social Media and Documentation Icon Sprite"
Cohesion: 0.67
Nodes (3): Documentation Icon, Social Media Icons Collection, Social Media and Documentation Icon Sprite

### Community 63 - "resumeSession"
Cohesion: 0.09
Nodes (64): applyParamDefaults(), applyPlaceholderDimensions(), applySavedSessionMeta(), checkpointPayload(), clearSession(), closedClipPath(), commitAcceptedVariantToDom(), completeParameterGenerationIfReady() (+56 more)

### Community 64 - "setLiveState"
Cohesion: 0.13
Nodes (48): abortSvelteComponentInjection(), beginNewLiveConfiguration(), cancelEditing(), cancelEditingToPicking(), cancelInsertConfigure(), cleanup(), cleanupAcceptedSession(), clearAnnotations() (+40 more)

### Community 65 - "modern-screenshot.umd.js"
Cohesion: 0.09
Nodes (55): ae(), be(), bt(), Ce(), s(), Ct(), de(), dt() (+47 more)

### Community 66 - "el"
Cohesion: 0.07
Nodes (55): actionLabel(), applyConfigureBarChrome(), bindConfigureCountPillTooltip(), bindConfigureInlineControlHover(), bindConfigureModifierPillHover(), buildConfigureActionControl(), buildConfigureCountControl(), buildConfigureRow() (+47 more)

### Community 67 - "renderDesignVisual"
Cohesion: 0.08
Nodes (39): buildCollapsible(), buildColorModels(), buildDesignHeader(), buildListHtml(), buildRadiiModels(), buildTypographyModels(), cssSafe(), designEmptyMessage() (+31 more)

### Community 68 - "captureElementToBlob"
Cohesion: 0.14
Nodes (19): averageRgb01(), bufferToBase64(), captureChromeNodes(), captureElementFromRenderedAncestor(), captureElementToBlob(), collectFontCssText(), cssColorToRgb01(), dominantRgb01() (+11 more)

### Community 69 - "initPageChat"
Cohesion: 0.15
Nodes (30): armPageChatForTyping(), attachSteerFocusDebug(), attachSteerFocusGuard(), clearSteerAwaitTimer(), collapsePageChat(), expandPageChat(), focusConfigureInput(), focusPageChatInput() (+22 more)

### Community 70 - "initGlobalBar"
Cohesion: 0.10
Nodes (32): agentHasWorkInFlight(), agentStatusText(), barPaletteForTheme(), brandMarkSvg(), buildParamsPanel(), buildSteerProcessingDots(), buildSteerQueueHint(), designPanelCss() (+24 more)

### Community 71 - "Section"
Cohesion: 0.10
Nodes (36): list_sections(), DbSession, get, _to_read_model(), update_section(), LtreeType, Any, Maps to Postgres LTREE. Stored and returned as plain str paths. (+28 more)

### Community 72 - "Responsive Design"
Cohesion: 0.08
Nodes (25): Assess Adaptation Challenge, Breakpoints: Content-Driven, Content Adaptation, Desktop Adaptation (Mobile → Desktop), Detect Input Method, Not Just Screen Size, Email Adaptation (Web → Email), Implement Adaptations, Layout Adaptation Patterns (+17 more)

### Community 73 - "scheduleAcceptCleanup"
Cohesion: 0.31
Nodes (11): acceptedDomAlreadyClean(), clearHandledWrapperReloadStamp(), deferredRecoverySuperseded(), ensureAcceptedDomClean(), findAcceptedRuntimeWrappers(), handledWrapperReloadKey(), reloadAfterMissingAcceptedDom(), restoreAcceptedDomFromSnapshot() (+3 more)

### Community 74 - "onboard.md"
Cohesion: 0.09
Nodes (22): Assess Onboarding Needs, Context Over Ceremony, Contextual Help, Design Onboarding Experiences, Documentation & Help, Empty State Design, Feature Discovery & Adoption, Guided Tours & Walkthroughs (+14 more)

### Community 75 - "handleManualEditActivity"
Cohesion: 0.18
Nodes (25): clearStoredManualApplyState(), fetchPendingCount(), handleManualEditActivity(), hidePendingApplyDock(), manualApplyLoadingText(), manualApplyStateKey(), manualEditEventForCurrentPage(), numberOrNull() (+17 more)

### Community 76 - "new-work.md"
Cohesion: 0.13
Nodes (14): Recommended Actions, Craft (deprecated alias), Apply, Live-mode signature params, Set the spatial thesis, Two isolated assessments, Verify, Visitor mode (+6 more)

### Community 77 - "SKILL.md"
Cohesion: 0.10
Nodes (15): Before you finish, Scope is sovereign, The amplification, The skeleton test, Why it reads flat, Craft floor, Refuse, Verify (+7 more)

### Community 78 - "The Toolkit"
Cohesion: 0.10
Nodes (20): Animate complex properties, Assess What "Extraordinary" Means Here, For data-heavy interfaces, For functional UI, For performance-critical UI, For visual/marketing surfaces, Implement with Discipline, Interact with the device (+12 more)

### Community 79 - "showToast"
Cohesion: 0.08
Nodes (35): abandonForeignSession(), applyOriginalAttrsToSvelteAnchor(), clearMountErrorCard(), commitAcceptedSvelteComponentToDom(), componentModuleCandidates(), copyToClipboard(), describeMountFailure(), detectDevServerBase() (+27 more)

### Community 80 - "jobs.py"
Cohesion: 0.29
Nodes (6): get_job(), DbSession, get, JobRead, BaseModel, pydantic

### Community 81 - "resolveLiveInjectionAnchor"
Cohesion: 0.16
Nodes (19): buildSvelteExpressionTextMap(), buildSveltePropValuesFromLiveElement(), buildSveltePropValuesV2(), cloneWithoutElements(), collectTextNodes(), collectVisibleTexts(), cssEscapeIdent(), elementMatchesOriginalMarkup() (+11 more)

### Community 82 - "createLiveBrowserSessionState"
Cohesion: 0.21
Nodes (15): createLiveBrowserSessionState(), clearHandled(), clearScrollY(), clearSession(), isHandled(), loadSession(), markHandled(), nextCheckpointRevision() (+7 more)

### Community 83 - "Chunk"
Cohesion: 0.39
Nodes (13): Chunk, AsyncSession, Vector-only retrieval (Phase 3's deliberate baseline — no hybrid, no reranking;…, vector_search(), _make_chunk(), _make_project_with_document(), AsyncSession, test_vector_search_ignores_chunks_with_no_embedding_yet() (+5 more)

### Community 84 - "animate.md"
Cohesion: 0.12
Nodes (14): Accessibility and control, Choose material by meaning, Find the job, Implement to the runtime, Set the motion thesis, Timing and easing, Verify, Visitor mode (+6 more)

### Community 85 - "live.md"
Cohesion: 0.12
Nodes (15): Cleanup, Exit, First-time setup, Handle `accept`, Handle `discard`, Handle fallback, Handle `manual_edit_apply`, Handle `prefetch` (+7 more)

### Community 86 - "Handle `generate`"
Cohesion: 0.12
Nodes (16): 1. Read the screenshot (if present), 2. Wrap the element, 3. Load the action's reference, 4. Plan three variants: identity first, then mode, then axes, 5. Apply the freeform prompt (if present), 6. Deliver variants, 7. Parameters (composition-sized, 0-4 per variant), 8. Signal done (+8 more)

### Community 87 - "createLiveBrowserDomHelpers"
Cohesion: 0.17
Nodes (10): createLiveBrowserDomHelpers(), cssId(), liveUiRoot(), makeFrozenAnchor(), own(), pickable(), rectIsUsableAnchor(), uiAppend() (+2 more)

### Community 88 - "Generate Report"
Cohesion: 0.13
Nodes (14): 1. Accessibility (A11y), 2. Performance, 3. Theming, 4. Responsive Design, 5. Implementation Integrity (CRITICAL), Audit Health Score, Detailed Findings by Severity, Diagnostic Scan (+6 more)

### Community 89 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, jsdom, oxlint, tailwindcss, @tailwindcss/typography, @tailwindcss/vite, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 90 - "onAnnotDown"
Cohesion: 0.20
Nodes (17): beginEditPin(), buildAnnotationsForCapture(), buildPinElement(), cancelEditingPin(), clampPlaceholderSize(), finalizeEditingPin(), initAnnotOverlay(), localCoords() (+9 more)

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

### Community 106 - "showAnnotOverlay"
Cohesion: 0.50
Nodes (5): buildPlaceholderResizeHandles(), cursorForPlaceholderEdge(), positionAnnotOverlay(), showAnnotOverlay(), syncPlaceholderResizeHandles()

### Community 107 - "Product"
Cohesion: 0.20
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

### Community 127 - "live-browser-ignores.js"
Cohesion: 0.52
Nodes (6): globToRegex(), matchesScope(), normalizeIgnoreRule(), normalizeIgnoreValue(), pageCandidates(), resolveDetectIgnores()

### Community 129 - "Diagnostic Scan"
Cohesion: 0.33
Nodes (6): 1. Accessibility (VoiceOver / TalkBack), 2. Performance, 3. Appearance & Theming, 4. Platform Conformance (CRITICAL), 5. Adaptivity, Diagnostic Scan

### Community 130 - "/impeccable hooks"
Cohesion: 0.33
Nodes (6): Constraints, Failure modes, Flow, /impeccable hooks, Routing, Triage findings

### Community 131 - "Visualize: Direction Comps & Asset Production"
Cohesion: 0.33
Nodes (5): After approval: the comp becomes a spec, Generate three compositional options, One approval point, Plates and provenance, Visualize: Direction Comps & Asset Production

### Community 132 - "impeccable"
Cohesion: 0.60
Nodes (5): impeccable script, check_download(), fetch_url(), probe_ok(), setup_help()

### Community 133 - "Impeccable Documenter"
Cohesion: 0.40
Nodes (4): Impeccable Documenter, Input Contract, Output Contract, Workflow

### Community 134 - "Impeccable Documenter"
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
- **531 isolated node(s):** `rag-backend`, `$schema`, `plugins`, `react/rules-of-hooks`, `react/only-export-components` (+526 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 698 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Ollama local model server` and `Reranker (in-process)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Phase 6 — polish` and `Query rewriting for follow-ups`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `init()` connect `initGlobalBar` to `setLiveState`, `initPageChat`, `Init flow`, `handleManualEditActivity`, `SKILL.md`, `doctor.md`, `live-browser.js`, `onAnnotDown`, `resumeSession`?**
  _High betweenness centrality (0.159) - this node is a cross-community bridge._
- **Why does `Commands` connect `SKILL.md` to `initGlobalBar`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._
- **Why does `Init flow` connect `Init flow` to `new-work.md`, `initGlobalBar`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `Document` (e.g. with `list_messages()` and `get_document()`) actually correct?**
  _`Document` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `Section` (e.g. with `list_messages()` and `list_sections()`) actually correct?**
  _`Section` has 12 INFERRED edges - model-reasoned connections that need verification._