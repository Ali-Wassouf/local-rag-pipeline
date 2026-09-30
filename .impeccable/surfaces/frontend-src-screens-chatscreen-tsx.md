---
version: 1
slug: "frontend-src-screens-chatscreen-tsx"
primary_target: "frontend/src/screens/ChatScreen.tsx"
related_targets: ["frontend/src/App.tsx"]
---

## Scope and visitor mode

Operate. Chat screen (`frontend/src/screens/ChatScreen.tsx`) plus a new persistent
shared shell (`frontend/src/App.tsx` and a new `Shell` wrapper) as seen from
Chat. `ProjectsListScreen`, `ProjectDetailScreen`, `UploadScreen`,
`ReviewScreen` keep their current plain content — only the shell chrome
around them changes for consistency. No DB/API changes; no change to SSE
streaming, project scoping, citation data, or Markdown rendering behavior.

## Audience, job, proof

Solo local researcher asking grounded questions over their own document
corpus, needing to read a long answer and trust/verify its citations without
re-reading source material. Real proof on screen: actual `CitationRead[]`
(chunk_id, rank, document_title, display_path) already returned by the API
— nothing invented. Correction made during build: `CitationRead` carries no
summary/passage flag on this screen (that distinction belongs to a
not-yet-built survey feature per CLAUDE.md invariant 6) — every citation
here is already a real retrieved passage, so the footnote treatment below
does not fabricate a summary/passage split.

## Chosen direction and memorable moment

**The Bibliography** — a scholarly monograph's footnote apparatus, warm
paper world. Memorable moment: the footnote rail fixed at the bottom of the
transcript fills in live, in real time, as the answer streams — the reader
watches the evidence assemble under the claim it supports, in the same
motion as the prose itself.

## Unresolved decisions carried to the build

- Exact accent reuse for destructive/error states elsewhere in the app is
  not decided here (flagged for the documenter).
- Only the shell chrome (running head / chapter list) is restyled on other
  screens; their content stays in the incumbent plain look until a future
  round.

## Direction contract

THESIS: A grounded answer is a claim standing on evidence, and the two
must never separate — this surface refuses the chat product's default of
burying sources behind a collapsed "Sources" toggle nobody opens.

OWN-WORLD: Warm cream paper (`--color-paper` #F7F1E6, dark: #17140F), near-
black warm ink for prose (`--color-ink` #221D16, dark: #EDE6D8), a single
restrained oxblood accent (`--color-accent` #7C2D2D, dark: #D47971) reserved
for citation numerals, active states, and rule weight. Two workhorse type
families only: a text-optimized book serif (Source Serif 4) for prose, a
true tabular mono (IBM Plex Mono) for section paths, dates, and folio
numbers — no display face. Hairline rules (`--color-rule` #DED2B8, dark:
#362E22) throughout; no shadows, no rounded chat bubbles, no card
containers.

STORY: The reader opens a conversation (a "chapter" in a running list, dated
and numbered, with a real first-question preview fetched from that
conversation's own messages, not a bare title); asks a question; watches
the answer set in book prose with superscript citation numerals. Each
answer carries its own footnote block directly beneath it — the page a real
footnote lives on is the one that cites it, not a rail shared across the
whole book — showing rank, document title, and section path for every
retrieved source. While an answer is still streaming its footnote block
shows a dormant "assembling sources…" placeholder (dashed rule) that
resolves to the real entries (solid rule) the instant the stream's `done`
event delivers them, since the SSE protocol only carries citations at
completion, never token-by-token.

FIRST VIEWPORT: A running head across the top of the app names the app
("Local RAG") in small tracked caps mono, thin rule beneath (built as the
shared `Shell`). Below it, this screen's own running head names the open
project. Left: the chapter list (conversations), each row showing a folio
number (its position in the list), a date, and a one-line first-question
preview. Right, filling the remaining width: the transcript in serif prose,
comfortable measure (65-75ch), each answer's footnote block attached
directly beneath it, composer fixed at the bottom of the column.

FORM: The Bibliography. Rank 1 of 7 on my own ordered list (own top pick;
the roll's dealt assignment was a different direction, "The Ledger",
declined by the user in favor of this pick). Seed key: 6ae98cb0.

FINISH: unreviewed and undocumented is unfinished; this build ends with the
finish review, the verdict, DESIGN.md, and every shipping raster carrying
its provenance.
