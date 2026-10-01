import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import rehypeRaw from 'rehype-raw'
import remarkGfm from 'remark-gfm'

import { sendMessage } from '../api/client'
import {
  useConversations,
  useCreateConversation,
  useDeleteConversation,
  useDeletedConversations,
  useMessages,
  useProject,
  useProjectDocuments,
  useRestoreConversation,
} from '../api/hooks'
import type { ChatMode, CitationRead, ConversationRead, MessageRead } from '../api/types'

interface ChatScreenProps {
  projectId: number
  onBack: () => void
}

interface ActiveCitation {
  messageId: number | string
  rank: number
}

// A plain colored numeral reads as styled text, not a control — this world
// has no blue-link convention to borrow, so the affordance has to come from
// shape: a bordered, tinted badge that inverts to solid fill on hover/focus,
// the same "struck vs. dormant" logic a real stamped reference tab would use.
const CITATION_MARKER_CLASSES =
  'inline-flex min-w-[1.1em] cursor-pointer items-center justify-center rounded-full border border-accent/50 bg-accent/10 px-1 font-mono text-[11px] leading-[1.4] font-semibold text-accent tabular-nums transition-colors hover:border-accent hover:bg-accent hover:text-paper focus-visible:border-accent focus-visible:bg-accent focus-visible:text-paper'

// message_citations persists every retrieved chunk the model was handed,
// not just the ones it chose to cite (docs/plan.md §4.6 — deliberate, so
// citation drift with a local 8B model is visible rather than papered
// over by filtering the list down to match). This recovers which ranks
// the prose actually references, so the ledger and inspector can tell the
// two apart instead of rendering them identically.
function extractCitedRanks(content: string): Set<number> {
  const ranks = new Set<number>()
  for (const match of content.matchAll(/\[(\d+)\]/g)) {
    ranks.add(Number(match[1]))
  }
  return ranks
}

// The model outputs real Markdown (bold, lists, headers) plus our own
// [n] citation markers. Markers become a real <button> (via rehype-raw) so
// clicking one opens that source in the right-hand Marginalia Passage
// Inspector rather than jumping anywhere on the page.
function MarkdownMessage({
  content,
  onSelectCitation,
}: {
  content: string
  onSelectCitation?: (rank: number) => void
}) {
  const withStyledCitations = content.replace(
    /\[(\d+)\]/g,
    (_match, n: string) =>
      `<sup class="mx-0.5"><button type="button" data-citation-rank="${n}" class="${CITATION_MARKER_CLASSES}">${n}</button></sup>`,
  )

  function handleClick(event: React.MouseEvent<HTMLDivElement>) {
    if (!onSelectCitation) return
    const target = (event.target as HTMLElement).closest('[data-citation-rank]')
    if (!target) return
    onSelectCitation(Number(target.getAttribute('data-citation-rank')))
  }

  return (
    <div
      onClick={handleClick}
      className="prose prose-sm max-w-none font-serif text-ink prose-headings:font-serif prose-headings:text-ink"
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
        {withStyledCitations}
      </ReactMarkdown>
    </div>
  )
}

// The ledger of everything retrieved for this reply — cited and uncited
// alike (docs/plan.md §4.6) — shown as a preface to the synthesis it backs,
// with a quick All/Cited Only filter. Every row opens its source in the
// Marginalia Passage Inspector.
function RetrievedLedger({
  citations,
  citedRanks,
  messageId,
  activeCitation,
  filterMode,
  onChangeFilterMode,
  onSelect,
}: {
  citations: CitationRead[]
  citedRanks: Set<number>
  messageId: number | string
  activeCitation: ActiveCitation | null
  filterMode: 'all' | 'cited'
  onChangeFilterMode: (mode: 'all' | 'cited') => void
  onSelect: (rank: number) => void
}) {
  if (citations.length === 0) return null
  const citedCount = citations.filter((c) => citedRanks.has(c.rank)).length
  const uncitedCount = citations.length - citedCount
  const visible = filterMode === 'cited' ? citations.filter((c) => citedRanks.has(c.rank)) : citations

  return (
    <section
      aria-label="Retrieved document passages"
      className="mb-4 rounded-md border border-rule bg-parchment p-4"
    >
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2 border-b border-rule pb-3">
        <div className="font-mono text-xs tabular-nums text-ink-secondary">
          <span className="font-semibold text-ink">{citations.length} Passages Retrieved</span>
          <span aria-hidden="true"> &middot; </span>
          <span className="font-medium text-accent">{citedCount} Cited</span>
          <span aria-hidden="true"> &middot; </span>
          <span>{uncitedCount} Retrieved, not cited</span>
        </div>
        <div className="flex items-center gap-1 rounded-sm bg-stone p-0.5">
          <button
            type="button"
            onClick={() => onChangeFilterMode('all')}
            className={`cursor-pointer rounded-xs px-2 py-0.5 text-[11px] font-medium transition-colors ${
              filterMode === 'all' ? 'bg-paper text-ink' : 'text-ink-secondary hover:text-ink'
            }`}
          >
            All ({citations.length})
          </button>
          <button
            type="button"
            onClick={() => onChangeFilterMode('cited')}
            className={`cursor-pointer rounded-xs px-2 py-0.5 text-[11px] font-medium transition-colors ${
              filterMode === 'cited' ? 'bg-paper text-accent' : 'text-ink-secondary hover:text-ink'
            }`}
          >
            Cited Only ({citedCount})
          </button>
        </div>
      </div>
      <div className="divide-y divide-rule/60">
        {visible.map((citation) => {
          const isCited = citedRanks.has(citation.rank)
          const isActive =
            activeCitation?.messageId === messageId && activeCitation.rank === citation.rank
          return (
            <button
              key={citation.rank}
              type="button"
              onClick={() => onSelect(citation.rank)}
              className={`-mx-2 flex w-full cursor-pointer items-baseline gap-3 rounded-sm px-2 py-2 text-left font-mono text-xs transition-colors ${
                isActive ? 'bg-accent/10' : 'hover:bg-stone/60'
              }`}
            >
              <span
                className={`w-4 shrink-0 tabular-nums font-semibold ${
                  isCited ? 'text-accent' : 'text-ink-muted italic'
                }`}
              >
                {citation.rank}
              </span>
              <span className={`flex-1 leading-relaxed ${isCited ? 'text-ink' : 'text-ink-muted italic'}`}>
                {citation.is_summary && <span className="text-accent not-italic">(summary) </span>}
                {citation.document_title} &ndash; {citation.display_path}
                {!isCited && <span className="ml-1.5 text-ink-muted">(retrieved, not cited)</span>}
              </span>
            </button>
          )
        })}
      </div>
    </section>
  )
}

// The signature moment: a dedicated right-hand column holding the full
// verbatim text (or, labelled as such, the summary — CLAUDE.md invariant
// 6) of whichever source is currently under inspection, rather than an
// inline expand buried in the transcript.
function PassageInspector({
  message,
  citedRanks,
  activeCitation,
  onSelect,
  onManageDocuments,
}: {
  message: MessageRead | undefined
  citedRanks: Set<number>
  activeCitation: ActiveCitation | null
  onSelect: (rank: number) => void
  onManageDocuments: () => void
}) {
  const [copied, setCopied] = useState(false)

  const citations = message?.citations ?? []
  const inspected =
    (activeCitation && citations.find((c) => c.rank === activeCitation.rank)) ||
    citations.find((c) => citedRanks.has(c.rank)) ||
    citations[0]

  function handleCopy() {
    if (!inspected) return
    void navigator.clipboard?.writeText(
      `"${inspected.text}" — ${inspected.document_title} (${inspected.display_path})`,
    )
    setCopied(true)
    setTimeout(() => setCopied(false), 1800)
  }

  return (
    <aside
      aria-label="Marginalia passage inspector"
      className="flex flex-col justify-between overflow-y-auto border-t border-rule bg-parchment p-5 lg:col-span-3 lg:border-t-0 lg:border-l"
    >
      {inspected ? (
        <div className="space-y-5">
          <div className="flex items-center justify-between border-b border-rule pb-3">
            <span className="text-xs font-semibold text-ink">Marginalia Passage Inspector</span>
            <span className="font-mono text-xs font-semibold tabular-nums text-accent">
              Source #{inspected.rank}
            </span>
          </div>

          {citations.length > 1 && (
            <div>
              <div className="mb-1.5 font-mono text-[11px] text-ink-muted">
                Jump to retrieved passage:
              </div>
              <div className="flex flex-wrap gap-1.5">
                {citations.map((c) => {
                  const isCited = citedRanks.has(c.rank)
                  const isActive = c.rank === inspected.rank
                  return (
                    <button
                      key={c.rank}
                      type="button"
                      onClick={() => onSelect(c.rank)}
                      title={isCited ? `Source ${c.rank} (cited)` : `Source ${c.rank} (retrieved, not cited)`}
                      className={`h-7 w-7 cursor-pointer rounded-sm border font-mono text-xs font-semibold tabular-nums transition-colors ${
                        isActive
                          ? 'border-accent bg-accent text-paper'
                          : isCited
                            ? 'border-rule-strong bg-paper text-accent hover:border-accent'
                            : 'border-rule bg-stone/60 text-ink-muted italic'
                      }`}
                    >
                      {c.rank}
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          <div className="space-y-1.5 rounded-md border border-rule bg-paper p-3.5">
            <h2 className="text-sm leading-snug font-semibold text-ink">
              {inspected.document_title}
            </h2>
            <p className="font-mono text-xs leading-relaxed text-ink-secondary">
              {inspected.display_path}
            </p>
            <div className="pt-1 font-mono text-[11px]">
              {citedRanks.has(inspected.rank) ? (
                <span className="font-medium text-status-ready">
                  &#9679; Directly cited in reply synthesis
                </span>
              ) : (
                <span className="text-ink-muted italic">
                  &#9675; Retrieved, not cited in reply
                </span>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-ink">
                {/* CLAUDE.md invariant 6 — a survey citation's source is a
                    summary, never presented as a passage the model read. */}
                {inspected.is_summary ? 'Summary' : 'Verbatim Document Excerpt'}
              </span>
              <button
                type="button"
                onClick={handleCopy}
                className="cursor-pointer text-xs font-medium text-accent hover:underline"
              >
                {copied ? 'Copied' : 'Copy Quote'}
              </button>
            </div>
            <blockquote className="rounded-r-md border-y border-r border-l-2 border-rule border-l-accent bg-paper p-3.5 font-serif text-[15px] leading-[1.75] text-ink">
              &ldquo;{inspected.text}&rdquo;
            </blockquote>
          </div>
        </div>
      ) : (
        <p className="py-12 text-center text-xs text-ink-muted">
          Ask a question to inspect its sources here.
        </p>
      )}

      <div className="mt-6 border-t border-rule pt-6">
        <button
          type="button"
          onClick={onManageDocuments}
          className="w-full cursor-pointer rounded-md border border-rule-strong bg-paper px-3.5 py-2 text-xs font-medium text-ink transition-colors hover:bg-stone"
        >
          Manage Project Documents
        </button>
      </div>
    </aside>
  )
}

function formatFolioDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

interface ChapterRowProps {
  conversation: ConversationRead
  folio: number
  isActive: boolean
  onSelect: () => void
  onRemove: () => void
}

function ChapterRow({ conversation, folio, isActive, onSelect, onRemove }: ChapterRowProps) {
  const messages = useMessages(conversation.id)
  const firstQuestion = messages.data?.find((message) => message.role === 'user')?.content
  const preview = firstQuestion ?? conversation.title ?? 'New chapter'

  return (
    <li className="group relative">
      <button
        type="button"
        onClick={onSelect}
        aria-current={isActive ? 'true' : undefined}
        className={`w-full cursor-pointer border-l-[3px] py-3 pr-14 pl-4 text-left transition-colors ${
          isActive ? 'border-accent bg-paper' : 'border-transparent hover:bg-stone/60'
        }`}
      >
        <div className="mb-1 flex items-center justify-between font-mono text-[11px] tabular-nums text-ink-muted">
          <span className={isActive ? 'font-semibold text-accent' : ''}>No. {folio}</span>
          <span>{formatFolioDate(conversation.created_at)}</span>
        </div>
        <p
          className={`truncate font-serif text-[15px] leading-snug ${
            isActive ? 'font-medium text-ink' : 'text-ink-secondary'
          }`}
        >
          {preview}
        </p>
      </button>
      <button
        type="button"
        onClick={(event) => {
          event.stopPropagation()
          onRemove()
        }}
        aria-label="Remove chapter"
        title="Move chapter to Deleted"
        className="absolute top-3 right-3 cursor-pointer font-mono text-[10px] text-ink-muted opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100 hover:text-danger"
      >
        Remove
      </button>
    </li>
  )
}

export function ChatScreen({ projectId, onBack }: ChatScreenProps) {
  const project = useProject(projectId)
  const projectDocuments = useProjectDocuments(projectId)
  const conversations = useConversations(projectId)
  const createConversation = useCreateConversation(projectId)
  const deletedConversations = useDeletedConversations(projectId)
  const deleteConversation = useDeleteConversation(projectId)
  const restoreConversation = useRestoreConversation(projectId)

  const [conversationId, setConversationId] = useState<number | null>(null)
  // A previous conversation's send can still be in flight (and will still
  // finish and persist correctly server-side) after the user switches to a
  // different one — this tracks which conversation is *currently viewed* so
  // a late callback from an abandoned conversation can't leave this one's
  // UI stuck, and switching itself resets the UI immediately.
  const currentConversationIdRef = useRef<number | null>(null)
  const history = useMessages(conversationId)
  const [messages, setMessages] = useState<MessageRead[]>([])
  const [draft, setDraft] = useState('')
  const [streamingText, setStreamingText] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [sendError, setSendError] = useState<string | null>(null)
  const [mode, setMode] = useState<ChatMode>('lookup')
  const [activeCitation, setActiveCitation] = useState<ActiveCitation | null>(null)
  const [passageFilterMode, setPassageFilterMode] = useState<'all' | 'cited'>('all')
  const [showDeletedDrawer, setShowDeletedDrawer] = useState(false)

  useEffect(() => {
    setMessages(history.data ?? [])
  }, [history.data])

  function switchConversation(id: number) {
    currentConversationIdRef.current = id
    setConversationId(id)
    setIsSending(false)
    setStreamingText('')
    setSendError(null)
    setActiveCitation(null)
  }

  function handleNewConversation() {
    createConversation.mutate(undefined, {
      onSuccess: (conversation) => {
        switchConversation(conversation.id)
        setMessages([])
      },
    })
  }

  function handleRemoveConversation(id: number) {
    deleteConversation.mutate(id, {
      onSuccess: () => {
        if (conversationId === id) {
          // The open chapter was just removed — there's nothing left to
          // show, so fall back to the empty state rather than leaving a
          // now-gone conversation's transcript on screen.
          currentConversationIdRef.current = null
          setConversationId(null)
          setIsSending(false)
          setStreamingText('')
          setSendError(null)
        }
      },
    })
  }

  function handleSend() {
    const content = draft.trim()
    if (!content || conversationId === null) return

    const activeConversationId = conversationId
    setDraft('')
    setSendError(null)
    setActiveCitation(null)
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now(),
        conversation_id: activeConversationId,
        role: 'user',
        content,
        created_at: new Date().toISOString(),
        citations: [],
      },
    ])
    setIsSending(true)
    setStreamingText('')

    let fullText = ''
    void sendMessage(
      activeConversationId,
      content,
      {
        onToken: (token) => {
          if (currentConversationIdRef.current !== activeConversationId) return
          fullText += token
          setStreamingText(fullText)
        },
        onDone: (citations) => {
          if (currentConversationIdRef.current !== activeConversationId) return
          setMessages((prev) => [
            ...prev,
            {
              id: Date.now() + 1,
              conversation_id: activeConversationId,
              role: 'assistant',
              content: fullText,
              created_at: new Date().toISOString(),
              citations,
            },
          ])
          setStreamingText('')
          setIsSending(false)
        },
        onError: (message) => {
          if (currentConversationIdRef.current !== activeConversationId) return
          setSendError(message)
          setIsSending(false)
        },
      },
      mode,
    )
  }

  const documentCount = projectDocuments.data?.length ?? 0
  const chapters = conversations.data ?? []
  const deletedChapters = deletedConversations.data ?? []

  const assistantMessages = messages.filter((m) => m.role === 'assistant')
  const lastAssistantMessage = assistantMessages[assistantMessages.length - 1]
  const inspectorMessage = activeCitation
    ? messages.find((m) => m.id === activeCitation.messageId)
    : lastAssistantMessage
  const inspectorCitedRanks = inspectorMessage ? extractCitedRanks(inspectorMessage.content) : new Set<number>()

  return (
    <div className="grid h-full grid-cols-1 lg:grid-cols-12 lg:overflow-hidden">
      {/* ===================================================================
          COLUMN 1: CHAPTER RAIL
         =================================================================== */}
      <aside
        aria-label="Inquiry chapters"
        className="flex max-h-[50vh] flex-col border-b border-rule bg-parchment lg:col-span-3 lg:max-h-none lg:border-r lg:border-b-0"
      >
        <div className="flex shrink-0 items-center justify-between gap-2 border-b border-rule p-4">
          <button
            type="button"
            onClick={onBack}
            className="inline-flex cursor-pointer items-center gap-1.5 text-xs font-medium text-ink-secondary transition-colors hover:text-ink"
          >
            &larr; Back
          </button>
          <button
            type="button"
            onClick={handleNewConversation}
            className="cursor-pointer rounded-md border border-rule-strong bg-paper px-3 py-1.5 text-xs font-semibold text-ink transition-colors hover:bg-stone"
          >
            New chapter
          </button>
        </div>
        {(conversations.isError || createConversation.isError || deleteConversation.isError) && (
          <p className="shrink-0 border-b border-rule px-4 py-2 font-mono text-[11px] text-danger">
            {(
              (conversations.error ?? createConversation.error ?? deleteConversation.error) as Error
            ).message}
          </p>
        )}
        <ul className="min-h-0 flex-1 overflow-y-auto">
          {chapters.map((conversation, index) => (
            <ChapterRow
              key={conversation.id}
              conversation={conversation}
              folio={index + 1}
              isActive={conversationId === conversation.id}
              onSelect={() => switchConversation(conversation.id)}
              onRemove={() => handleRemoveConversation(conversation.id)}
            />
          ))}
        </ul>

        {deletedConversations.isError && (
          <p className="shrink-0 border-t border-rule px-4 py-2 font-mono text-[11px] text-danger">
            {(deletedConversations.error as Error).message}
          </p>
        )}
        {deletedChapters.length > 0 && (
          <div className="shrink-0 border-t border-rule-strong bg-stone/60">
            <button
              type="button"
              onClick={() => setShowDeletedDrawer((prev) => !prev)}
              className="flex w-full cursor-pointer items-center justify-between px-4 py-2.5 font-mono text-xs text-ink-secondary hover:text-ink"
            >
              <span>Deleted ({deletedChapters.length})</span>
              <span aria-hidden="true">{showDeletedDrawer ? '⌄' : '›'}</span>
            </button>
            {showDeletedDrawer && (
              <div className="max-h-36 space-y-2 overflow-y-auto border-t border-rule px-4 pt-2 pb-3">
                {restoreConversation.isError && (
                  <p className="font-mono text-[11px] text-danger">
                    {(restoreConversation.error as Error).message}
                  </p>
                )}
                {deletedChapters.map((conversation) => (
                  <div key={conversation.id} className="flex items-center justify-between gap-2 py-1 text-xs">
                    <span className="truncate font-serif text-ink-muted italic">
                      {conversation.title ?? 'New chapter'}
                    </span>
                    <button
                      type="button"
                      onClick={() => restoreConversation.mutate(conversation.id)}
                      className="shrink-0 cursor-pointer text-[11px] font-medium text-accent hover:underline"
                    >
                      Restore
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </aside>

      {/* ===================================================================
          COLUMN 2: READING & INQUIRY STREAM
         =================================================================== */}
      <main className="flex min-h-0 min-w-0 flex-col lg:col-span-6">
        <header className="shrink-0 border-b border-rule px-6 py-4">
          <h1 className="font-serif text-2xl font-normal text-ink italic">
            {project.data?.name ?? '…'}
          </h1>
          <p className="mt-0.5 font-mono text-xs tabular-nums text-ink-muted">
            {documentCount} {documentCount === 1 ? 'Document' : 'Documents'}
          </p>
          {(project.isError || projectDocuments.isError) && (
            <p className="mt-1 text-sm text-danger">
              {((project.error ?? projectDocuments.error) as Error).message}
            </p>
          )}
        </header>

        {conversationId === null ? (
          <p className="px-6 py-6 font-serif text-sm text-ink-muted">
            Select a chapter, or begin a new one.
          </p>
        ) : (
          <>
            <div className="min-h-0 flex-1 space-y-8 overflow-y-auto px-6 py-8 md:px-10">
              {history.isError && (
                <p className="font-serif text-sm text-danger">
                  Couldn&rsquo;t load this chapter&rsquo;s messages: {(history.error as Error).message}
                </p>
              )}
              {messages.map((message) => (
                <div key={message.id} className="mx-auto max-w-[68ch] space-y-3">
                  {message.role === 'user' ? (
                    <div className="space-y-1.5 border-l-2 border-rule-strong pl-4">
                      <p className="font-mono text-xs text-ink-muted">You Asked</p>
                      <p className="font-serif text-xl text-ink">{message.content}</p>
                    </div>
                  ) : (
                    <div className="space-y-4 border-t border-rule pt-4">
                      <RetrievedLedger
                        citations={message.citations}
                        citedRanks={extractCitedRanks(message.content)}
                        messageId={message.id}
                        activeCitation={activeCitation}
                        filterMode={passageFilterMode}
                        onChangeFilterMode={setPassageFilterMode}
                        onSelect={(rank) => setActiveCitation({ messageId: message.id, rank })}
                      />
                      <p className="font-mono text-xs text-ink-muted">Reply</p>
                      <MarkdownMessage
                        content={message.content}
                        onSelectCitation={(rank) => setActiveCitation({ messageId: message.id, rank })}
                      />
                    </div>
                  )}
                </div>
              ))}

              {isSending && (
                <div className="mx-auto max-w-[68ch] space-y-4 border-t border-rule pt-4">
                  {streamingText === '' && (
                    <div className="rounded-md border border-dashed border-rule-strong bg-parchment p-4">
                      <p className="font-mono text-xs text-ink-muted italic">assembling sources&hellip;</p>
                    </div>
                  )}
                  <div className="flex items-center gap-2">
                    <p className="font-mono text-xs text-ink-muted">Reply</p>
                    <span
                      aria-hidden="true"
                      className="relative h-px w-[7.5rem] shrink-0 overflow-hidden bg-rule"
                    >
                      <span className="absolute inset-y-0 left-0 h-full w-10 bg-accent motion-safe:animate-[ink-scan_1.1s_linear_infinite]" />
                    </span>
                    <span className="sr-only" role="status">
                      Composing a reply&hellip;
                    </span>
                  </div>
                  <MarkdownMessage content={streamingText} />
                </div>
              )}
            </div>

            {sendError && <p className="shrink-0 px-6 pb-2 text-sm text-danger">{sendError}</p>}

            <footer className="shrink-0 border-t border-rule bg-parchment p-4 md:px-8 md:py-4">
              <div className="mx-auto max-w-[68ch] space-y-3">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <div
                    className="inline-flex items-center gap-1 self-start rounded-md border border-rule-strong bg-stone p-1"
                    role="radiogroup"
                    aria-label="Question mode"
                  >
                    {(['lookup', 'survey'] as const).map((option) => (
                      <button
                        key={option}
                        type="button"
                        role="radio"
                        aria-checked={mode === option}
                        onClick={() => setMode(option)}
                        className={`cursor-pointer rounded-sm px-3 py-1 text-xs font-semibold whitespace-nowrap transition-colors ${
                          mode === option
                            ? 'border border-accent/30 bg-paper text-accent'
                            : 'text-ink-secondary hover:text-ink'
                        }`}
                      >
                        {option === 'lookup' ? 'Lookup' : 'Survey'}
                      </button>
                    ))}
                  </div>
                  <p className="font-serif text-xs text-ink-secondary italic">
                    {mode === 'lookup'
                      ? 'Finds specific passages that answer this question directly.'
                      : 'Synthesizes overarching themes across summarized document sections.'}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    placeholder="Ask a question…"
                    value={draft}
                    onChange={(event) => setDraft(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter') handleSend()
                    }}
                    disabled={isSending}
                    className="flex-1 rounded-md border border-rule-strong bg-paper px-4 py-2.5 font-serif text-sm text-ink placeholder-ink-muted focus:border-accent focus:outline-none disabled:opacity-50"
                  />
                  <button
                    type="button"
                    onClick={handleSend}
                    disabled={isSending || !draft.trim()}
                    className="cursor-pointer rounded-md bg-accent px-5 py-2.5 text-xs font-semibold whitespace-nowrap text-paper transition-colors hover:bg-accent-hover disabled:pointer-events-none disabled:opacity-45"
                  >
                    Send
                  </button>
                </div>
              </div>
            </footer>
          </>
        )}
      </main>

      {/* ===================================================================
          COLUMN 3: MARGINALIA PASSAGE INSPECTOR
         =================================================================== */}
      <PassageInspector
        message={inspectorMessage}
        citedRanks={inspectorCitedRanks}
        activeCitation={activeCitation}
        onSelect={(rank) =>
          inspectorMessage && setActiveCitation({ messageId: inspectorMessage.id, rank })
        }
        onManageDocuments={onBack}
      />
    </div>
  )
}
