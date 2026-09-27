import { useEffect, useState } from 'react'

import { sendMessage } from '../api/client'
import {
  useConversations,
  useCreateConversation,
  useMessages,
  useProject,
  useProjectDocuments,
} from '../api/hooks'
import type { CitationRead, MessageRead } from '../api/types'

interface ChatScreenProps {
  projectId: number
  onBack: () => void
}

function renderWithMarkers(content: string) {
  const parts = content.split(/(\[\d+\])/g)
  return parts.map((part, index) => {
    const match = /^\[(\d+)\]$/.exec(part)
    if (match) {
      return (
        <sup
          key={index}
          className="mx-0.5 rounded bg-blue-100 px-1 text-xs font-semibold text-blue-700 dark:bg-blue-900 dark:text-blue-300"
        >
          {match[1]}
        </sup>
      )
    }
    return <span key={index}>{part}</span>
  })
}

function SourcesList({ citations }: { citations: CitationRead[] }) {
  if (citations.length === 0) return null
  return (
    <details className="mt-2 text-xs text-gray-500 dark:text-gray-400">
      <summary className="cursor-pointer">Sources ({citations.length})</summary>
      <ul className="mt-1 space-y-1">
        {citations.map((citation) => (
          <li key={citation.chunk_id}>
            [{citation.rank}] {citation.document_title} — {citation.display_path}
          </li>
        ))}
      </ul>
    </details>
  )
}

export function ChatScreen({ projectId, onBack }: ChatScreenProps) {
  const project = useProject(projectId)
  const projectDocuments = useProjectDocuments(projectId)
  const conversations = useConversations(projectId)
  const createConversation = useCreateConversation(projectId)

  const [conversationId, setConversationId] = useState<number | null>(null)
  const history = useMessages(conversationId)
  const [messages, setMessages] = useState<MessageRead[]>([])
  const [draft, setDraft] = useState('')
  const [streamingText, setStreamingText] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [sendError, setSendError] = useState<string | null>(null)

  useEffect(() => {
    setMessages(history.data ?? [])
  }, [history.data])

  function handleNewConversation() {
    createConversation.mutate(undefined, {
      onSuccess: (conversation) => {
        setConversationId(conversation.id)
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
        fullText += token
        setStreamingText(fullText)
      },
      onDone: (citations) => {
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
        setSendError(message)
        setIsSending(false)
      },
    })
  }

  const documentCount = projectDocuments.data?.length ?? 0

  return (
    <div className="mx-auto flex max-w-4xl gap-6 p-8">
      <div className="w-56 shrink-0">
        <button type="button" onClick={onBack} className="mb-4 text-sm text-blue-600 hover:underline">
          &larr; Back
        </button>
        <button
          type="button"
          onClick={handleNewConversation}
          className="w-full rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          New conversation
        </button>
        <ul className="mt-4 space-y-1">
          {(conversations.data ?? []).map((conversation) => (
            <li key={conversation.id}>
              <button
                type="button"
                onClick={() => setConversationId(conversation.id)}
                className={`w-full truncate rounded px-2 py-1 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-800 ${
                  conversationId === conversation.id ? 'bg-blue-50 dark:bg-blue-950' : ''
                }`}
              >
                {conversation.title ?? 'Untitled'}
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="flex-1">
        <div className="border-b border-gray-200 pb-3 dark:border-gray-700">
          <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {project.data?.name ?? '…'}
          </h1>
          <p className="text-xs text-gray-500">
            {documentCount} document{documentCount === 1 ? '' : 's'}
          </p>
        </div>

        {conversationId === null ? (
          <p className="mt-6 text-sm text-gray-500">
            Select a conversation or start a new one.
          </p>
        ) : (
          <>
            <div className="mt-4 space-y-4">
              {messages.map((message) => (
                <div key={message.id}>
                  <p className="text-xs font-medium text-gray-400">
                    {message.role === 'user' ? 'You' : 'Assistant'}
                  </p>
                  <p className="text-sm text-gray-900 dark:text-gray-100">
                    {renderWithMarkers(message.content)}
                  </p>
                  {message.role === 'assistant' && <SourcesList citations={message.citations} />}
                </div>
              ))}

              {isSending && (
                <div>
                  <p className="text-xs font-medium text-gray-400">Assistant</p>
                  <p className="text-sm text-gray-900 dark:text-gray-100">
                    {renderWithMarkers(streamingText)}
                  </p>
                </div>
              )}
            </div>

            {sendError && <p className="mt-2 text-sm text-red-600">{sendError}</p>}

            <div className="mt-6 flex gap-2">
              <input
                type="text"
                placeholder="Ask a question…"
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') handleSend()
                }}
                disabled={isSending}
                className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm"
              />
              <button
                type="button"
                onClick={handleSend}
                disabled={isSending || !draft.trim()}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
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
