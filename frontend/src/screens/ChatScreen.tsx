import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import rehypeRaw from 'rehype-raw'
import remarkGfm from 'remark-gfm'

import { sendMessage } from '../api/client'
import {
  useConversations,
  useCreateConversation,
  useMessages,
  useProject,
  useProjectDocuments,
} from '../api/hooks'
import type { CitationRead, ConversationRead, MessageRead } from '../api/types'

interface ChatScreenProps {
  projectId: number
  onBack: () => void
}

// A plain colored numeral reads as styled text, not a control — this world
// has no blue-link convention to borrow, so the affordance has to come from
// shape: a bordered, tinted badge that inverts to solid fill on hover/focus,
// the same "struck vs. dormant" logic a real stamped reference tab would use.
const CITATION_MARKER_CLASSES =
  'inline-flex min-w-[1.1em] items-center justify-center rounded-full border border-accent/50 bg-accent/10 px-1 font-mono text-[10px] leading-[1.4] font-semibold text-accent no-underline tabular-nums transition-colors hover:border-accent hover:bg-accent hover:text-paper focus-visible:border-accent focus-visible:bg-accent focus-visible:text-paper dark:border-accent-dark/50 dark:bg-accent-dark/10 dark:text-accent-dark dark:hover:border-accent-dark dark:hover:bg-accent-dark dark:hover:text-paper-dark dark:focus-visible:border-accent-dark dark:focus-visible:bg-accent-dark dark:focus-visible:text-paper-dark'

function footnoteAnchorId(messageId: number | string, rank: string | number) {
  return `fn-${messageId}-${rank}`
}

// message_citations persists every retrieved chunk the model was handed,
// not just the ones it chose to cite (docs/plan.md §4.6 — deliberate, so
// citation drift with a local 8B model is visible rather than papered
// over by filtering the list down to match). This recovers which ranks
// the prose actually references, so the footnote list can tell the two
// apart instead of rendering them identically.
function extractCitedRanks(content: string): Set<number> {
  const ranks = new Set<number>()
  for (const match of content.matchAll(/\[(\d+)\]/g)) {
    ranks.add(Number(match[1]))
  }
  return ranks
}

// The model outputs real Markdown (bold, lists, headers) plus our own
// [n] citation markers. Markers get turned into a <sup><a> before handing
// off to ReactMarkdown (via rehype-raw) so both render properly together;
// the <a href="#fn-…"> is a real same-page link to that citation's own
// footnote line — clicking or tabbing to it jumps there and, via :target
// in index.css, keeps it highlighted for exactly as long as it's the one
// being read.
function MarkdownMessage({ content, messageId }: { content: string; messageId: number | string }) {
  const withStyledCitations = content.replace(
    /\[(\d+)\]/g,
    (_match, n: string) =>
      `<sup class="mx-0.5"><a href="#${footnoteAnchorId(messageId, n)}" class="${CITATION_MARKER_CLASSES}">${n}</a></sup>`,
  )
  return (
    <div className="prose prose-sm max-w-none font-serif text-ink prose-headings:font-serif prose-headings:text-ink dark:text-ink-dark dark:prose-invert dark:prose-headings:text-ink-dark">
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
        {withStyledCitations}
      </ReactMarkdown>
    </div>
  )
}

// A real footnote sits on the page that cites it, not on a rail shared
// across the whole book — so every answer carries its own block, directly
// beneath it. While the answer is still streaming, citations don't exist
// yet (the SSE "done" event is the only place the server sends them), so
// this shows a dormant placeholder rather than pretending otherwise.
function Footnotes({
  citations,
  pending,
  messageId,
  citedRanks,
}: {
  citations: CitationRead[]
  pending: boolean
  messageId: number | string
  citedRanks?: Set<number>
}) {
  if (!pending && citations.length === 0) return null

  return (
    <div
      className={
        pending
          ? 'mt-3 border-t border-dashed border-rule pt-2 dark:border-rule-dark'
          : 'mt-3 border-t border-rule pt-2 dark:border-rule-dark'
      }
    >
      {pending ? (
        <p className="font-mono text-[11px] tracking-wide text-ink-muted italic dark:text-ink-muted-dark">
          assembling sources…
        </p>
      ) : (
        <ol className="space-y-1">
          {citations.map((citation) => {
            const wasCited = citedRanks?.has(citation.rank) ?? true
            return (
              <li
                key={citation.chunk_id}
                id={footnoteAnchorId(messageId, citation.rank)}
                className={`footnote-entry flex scroll-mt-6 gap-2 px-1 font-mono text-[11px] ${
                  wasCited
                    ? 'text-ink-muted dark:text-ink-muted-dark'
                    : 'text-ink-muted/55 italic dark:text-ink-muted-dark/55'
                }`}
              >
                <span
                  className={
                    wasCited
                      ? 'tabular-nums text-accent dark:text-accent-dark'
                      : 'tabular-nums text-ink-muted/55 dark:text-ink-muted-dark/55'
                  }
                >
                  {citation.rank}
                </span>
                <span>
                  {citation.document_title} &mdash; {citation.display_path}
                  {!wasCited && ' (retrieved, not cited)'}
                </span>
              </li>
            )
          })}
        </ol>
      )}
    </div>
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
}

function ChapterRow({ conversation, folio, isActive, onSelect }: ChapterRowProps) {
  const messages = useMessages(conversation.id)
  const firstQuestion = messages.data?.find((message) => message.role === 'user')?.content
  const preview = firstQuestion ?? conversation.title ?? 'New chapter'

  return (
    <li>
      <button
        type="button"
        onClick={onSelect}
        aria-current={isActive ? 'true' : undefined}
        className={`w-full border-l-2 px-3 py-2 text-left transition-colors ${
          isActive
            ? 'border-accent bg-rail dark:border-accent-dark dark:bg-rail-dark'
            : 'border-transparent hover:bg-rail/60 dark:hover:bg-rail-dark/60'
        }`}
      >
        <div className="flex items-baseline justify-between gap-2 font-mono text-[11px] text-ink-muted tabular-nums dark:text-ink-muted-dark">
          <span>No. {folio}</span>
          <span>{formatFolioDate(conversation.created_at)}</span>
        </div>
        <p className="mt-0.5 truncate font-serif text-sm text-ink dark:text-ink-dark">{preview}</p>
      </button>
    </li>
  )
}

export function ChatScreen({ projectId, onBack }: ChatScreenProps) {
  const project = useProject(projectId)
  const projectDocuments = useProjectDocuments(projectId)
  const conversations = useConversations(projectId)
  const createConversation = useCreateConversation(projectId)

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

  useEffect(() => {
    setMessages(history.data ?? [])
  }, [history.data])

  function switchConversation(id: number) {
    currentConversationIdRef.current = id
    setConversationId(id)
    setIsSending(false)
    setStreamingText('')
    setSendError(null)
  }

  function handleNewConversation() {
    createConversation.mutate(undefined, {
      onSuccess: (conversation) => {
        switchConversation(conversation.id)
        setMessages([])
      },
    })
  }

  function handleSend() {
    const content = draft.trim()
    if (!content || conversationId === null) return

    const activeConversationId = conversationId
    setDraft('')
    setSendError(null)
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
    void sendMessage(activeConversationId, content, {
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
    })
  }

  const documentCount = projectDocuments.data?.length ?? 0
  const chapters = conversations.data ?? []

  return (
    <div className="mx-auto flex max-w-6xl">
      <aside className="w-64 shrink-0 border-r border-rule dark:border-rule-dark">
        <div className="flex items-center justify-between gap-2 border-b border-rule px-4 py-3 dark:border-rule-dark">
          <button
            type="button"
            onClick={onBack}
            className="font-mono text-[11px] tracking-wide text-ink-muted uppercase hover:text-accent dark:text-ink-muted-dark dark:hover:text-accent-dark"
          >
            &larr; Back
          </button>
          <button
            type="button"
            onClick={handleNewConversation}
            className="border border-rule px-2 py-1 font-mono text-[11px] tracking-wide text-ink uppercase hover:border-accent hover:text-accent dark:border-rule-dark dark:text-ink-dark dark:hover:border-accent-dark dark:hover:text-accent-dark"
          >
            New chapter
          </button>
        </div>
        <ul>
          {chapters.map((conversation, index) => (
            <ChapterRow
              key={conversation.id}
              conversation={conversation}
              folio={index + 1}
              isActive={conversationId === conversation.id}
              onSelect={() => switchConversation(conversation.id)}
            />
          ))}
        </ul>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="border-b border-rule px-6 py-3 dark:border-rule-dark">
          <h1 className="font-serif text-lg text-ink italic dark:text-ink-dark">
            {project.data?.name ?? '…'}
          </h1>
          <p className="font-mono text-[11px] tracking-wide text-ink-muted uppercase dark:text-ink-muted-dark">
            {documentCount} document{documentCount === 1 ? '' : 's'}
          </p>
        </div>

        {conversationId === null ? (
          <p className="px-6 py-6 font-serif text-sm text-ink-muted dark:text-ink-muted-dark">
            Select a chapter, or begin a new one.
          </p>
        ) : (
          <>
            <div className="max-w-[75ch] flex-1 space-y-6 overflow-y-auto px-6 py-6">
              {messages.map((message) => (
                <div key={message.id}>
                  <p className="font-mono text-[11px] tracking-wide text-ink-muted uppercase dark:text-ink-muted-dark">
                    {message.role === 'user' ? 'You asked' : 'Reply'}
                  </p>
                  {message.role === 'user' ? (
                    <p className="mt-1 font-serif text-sm text-ink dark:text-ink-dark">
                      {message.content}
                    </p>
                  ) : (
                    <>
                      <MarkdownMessage content={message.content} messageId={message.id} />
                      <Footnotes
                        citations={message.citations}
                        pending={false}
                        messageId={message.id}
                        citedRanks={extractCitedRanks(message.content)}
                      />
                    </>
                  )}
                </div>
              ))}

              {isSending && (
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-mono text-[11px] tracking-wide text-ink-muted uppercase dark:text-ink-muted-dark">
                      Reply
                    </p>
                    <span
                      aria-hidden="true"
                      className="relative h-px w-[7.5rem] shrink-0 overflow-hidden bg-rule dark:bg-rule-dark"
                    >
                      <span className="absolute inset-y-0 left-0 h-full w-10 bg-accent motion-safe:animate-[ink-scan_1.1s_linear_infinite] dark:bg-accent-dark" />
                    </span>
                    <span className="sr-only" role="status">
                      Composing a reply&hellip;
                    </span>
                  </div>
                  <MarkdownMessage content={streamingText} messageId="streaming" />
                  <Footnotes citations={[]} pending={true} messageId="streaming" />
                </div>
              )}
            </div>

            {sendError && (
              <p className="px-6 text-sm text-red-700 dark:text-red-400">{sendError}</p>
            )}

            <div className="flex gap-2 border-t border-rule px-6 py-4 dark:border-rule-dark">
              <input
                type="text"
                placeholder="Ask a question…"
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') handleSend()
                }}
                disabled={isSending}
                className="flex-1 border border-rule bg-transparent px-3 py-2 font-serif text-sm text-ink placeholder:text-ink-muted disabled:opacity-50 dark:border-rule-dark dark:text-ink-dark dark:placeholder:text-ink-muted-dark"
              />
              <button
                type="button"
                onClick={handleSend}
                disabled={isSending || !draft.trim()}
                className="border border-ink px-4 py-2 font-mono text-[11px] tracking-wide text-ink uppercase hover:border-accent hover:text-accent disabled:opacity-40 dark:border-ink-dark dark:text-ink-dark dark:hover:border-accent-dark dark:hover:text-accent-dark"
              >
                Send
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
