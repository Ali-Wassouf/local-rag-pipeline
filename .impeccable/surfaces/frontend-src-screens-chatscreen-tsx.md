---
version: 1
slug: "frontend-src-screens-chatscreen-tsx"
primary_target: "frontend/src/screens/ChatScreen.tsx"
related_targets: ["frontend/src/App.tsx","frontend/src/components/Shell.tsx","frontend/src/screens/ProjectsListScreen.tsx","frontend/src/screens/ProjectDetailScreen.tsx","frontend/src/screens/UploadScreen.tsx","frontend/src/screens/ReviewScreen.tsx"]
---

## Scope and visitor mode

Operate. Full visual world replacement across every screen: `ChatScreen.tsx`
(the Reading Room), `ProjectsListScreen.tsx`, `ProjectDetailScreen.tsx`,
`UploadScreen.tsx`, `ReviewScreen.tsx`, the shared `Shell.tsx` and `App.tsx`.
No DB/API changes beyond what was already shipped (source-passage view,
document removal/re-index, multi-file upload); no change to SSE streaming,
project scoping, citation data, or retrieval behavior. Dark mode dropped by
explicit user decision — the world is light-only, deliberately.

## Audience, job, proof

Solo local researcher asking grounded questions over their own document
corpus, managing projects and a document corpus, needing to read a long
answer and verify its citations without re-reading source material. Real
proof on screen: actual `CitationRead[]` (rank, document_title,
display_path, is_summary, text) and `DocumentRead` (section_count,
summary_count, status) already returned by the API — nothing invented. No
document-scope retrieval filter and no per-document "unassigned vault" were
added (explicit user decision to keep this a pure visual/layout port, not a
feature expansion) — the chat screen omits the reference's document-scope
dropdown, and the Projects list omits its unassigned-documents section.

## Chosen direction and memorable moment

**Marginalia** — an archival paper reading room, adopted wholesale from a
complete, finished reference implementation the user supplied
(`~/Downloads/docuchat-local`, itself already named "Marginalia"). This is
not a generated direction: the user pinned the exact visual world, so no
concept-seed roll or direction tournament ran — the brief IS the comp.
Memorable moment: the Reading Room's right-hand Marginalia Passage
Inspector — clicking any citation marker, in the prose or in a reply's
retrieved-passages ledger, opens that source's full verbatim text (or,
visibly labelled, its summary — CLAUDE.md invariant 6) in a dedicated
column that persists across the whole chapter, replacing the prior
build's inline expand-per-footnote pattern.

## Unresolved decisions carried to the build

- The detector flags the Passage Inspector's quote blockquote
  (`border-l-2 border-l-accent`) as the "side-tab accent border" slop
  pattern. Kept deliberately: it is a named, literal element of the pinned
  reference (`.verbatim-quote { border-left: 2px solid var(--accent-oxblood) }`)
  central to the signature interaction, not an unconsidered default.
- Project `description`, per-project document/chapter counts on the
  Projects list, and project deletion all exist in the reference's mock
  data/UI but have no backend counterpart here and were not added — the
  Projects list shows only what `ProjectRead` actually carries
  (name, created_at).

## Direction contract

THESIS: A grounded answer is a claim standing on evidence, and the two
must never separate — this world refuses the chat product's default of
burying sources behind a collapsed toggle, going further than the prior
build by giving evidence its own permanent column rather than an
inline expand.

OWN-WORLD: Archival paper palette, light only — `--color-paper` #FBF9F5,
`--color-parchment` #F3EFE6, `--color-stone` #EBE5D8, hairline rules
`--color-rule` #E2D9C8 / `--color-rule-strong` #C8BCA6, ink hierarchy
`--color-ink` #1C1917 / `--color-ink-secondary` #57534E / `--color-ink-muted`
#78716C, a single oxblood accent `--color-accent` #9A3412 (hover #7C2D12),
status green #15803D, danger red #DC2626. Three type families: Newsreader
(serif, prose and headings), Plus Jakarta Sans (sans, UI chrome), JetBrains
Mono (tabular data — dates, folio numbers, section paths, counts). No
shadows, no rounded chat bubbles; flat parchment panels and hairline rules
throughout.

STORY: A persistent top bar (brand — project-scoped tabs — nothing else)
replaces full-screen navigation jumps. The Reading Room is a 3-column
workbench: a numbered chapter rail (soft-delete/restore preserved) on the
left, the inquiry stream in the center (each reply prefaced by a retrieved-
passages ledger distinguishing cited from retrieved-but-uncited sources,
with an All/Cited Only filter), and the Marginalia Passage Inspector fixed
on the right, always showing the currently-selected source's full text.
Project Corpus (`ProjectDetailScreen`) keeps every existing action —
attach, upload, rename, generate-summary, re-index, type-to-confirm
delete — restyled into dual ingestion panels and a document ledger with
real summarization progress bars.

FIRST VIEWPORT: Reading Room, chapter selected: top bar (brand + "Project
Corpus (N)" / "Reading Room (Chat)" tabs) across the full width; below it,
three columns — chapter rail (fixed width), reading stream (flexible,
68ch measure), Marginalia Passage Inspector (fixed width) — each
independently scrollable, composer fixed at the stream's bottom.

FORM: Marginalia (adopted from a user-supplied finished reference, not
rolled). No seed key — direction pinned by brief, not generated.

FINISH: unreviewed and undocumented is unfinished; this build ends with
the finish review, the verdict, DESIGN.md, and every shipping raster
carrying its provenance.
