import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import type { ReactElement } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as client from '../api/client'
import type { SendMessageCallbacks } from '../api/client'
import type { ConversationRead, DocumentRead, MessageRead, ProjectRead } from '../api/types'
import { ChatScreen } from './ChatScreen'

const project: ProjectRead = {
  id: 1,
  name: 'Physics',
  description: null,
  created_at: '2026-01-01T00:00:00Z',
}

const doc: DocumentRead = {
  id: 10,
  sha256: 'a'.repeat(64),
  title: 'Mechanics',
  author: null,
  format: 'pdf',
  original_name: 'mechanics.pdf',
  status: 'ready',
  created_at: '2026-01-01T00:00:00Z',
}

const oldConversation: ConversationRead = {
  id: 5,
  project_id: 1,
  title: 'Old chat about forces',
  created_at: '2026-01-01T00:00:00Z',
}

const oldMessages: MessageRead[] = [
  {
    id: 1,
    conversation_id: 5,
    role: 'user',
    content: 'What is Newton\'s first law?',
    created_at: '2026-01-01T00:00:00Z',
    citations: [],
  },
  {
    id: 2,
    conversation_id: 5,
    role: 'assistant',
    content: 'An object in motion stays in motion [1].',
    created_at: '2026-01-01T00:00:01Z',
    citations: [{ chunk_id: 99, rank: 1, document_title: 'Mechanics', display_path: 'Ch. 1' }],
  },
]

function renderWithClient(ui: ReactElement) {
  const queryClient = new QueryClient()
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

describe('ChatScreen', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.spyOn(client, 'getProject').mockResolvedValue(project)
    vi.spyOn(client, 'listProjectDocuments').mockResolvedValue([doc])
  })

  it('shows the scope bar with project name and document count', async () => {
    vi.spyOn(client, 'listConversations').mockResolvedValue([])
    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)

    expect(await screen.findByText('Physics')).toBeInTheDocument()
    expect(await screen.findByText('1 document')).toBeInTheDocument()
  })

  it('selecting a past conversation loads its messages', async () => {
    vi.spyOn(client, 'listConversations').mockResolvedValue([oldConversation])
    vi.spyOn(client, 'listMessages').mockResolvedValue(oldMessages)

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)

    const conversationButton = await screen.findByText('Old chat about forces')
    fireEvent.click(conversationButton)

    expect(await screen.findByText(/Newton's first law/)).toBeInTheDocument()
    expect(await screen.findByText(/object in motion stays in motion/)).toBeInTheDocument()
  })

  it('starting a new conversation calls the create mutation', async () => {
    vi.spyOn(client, 'listConversations').mockResolvedValue([])
    const createSpy = vi.spyOn(client, 'createConversation').mockResolvedValue({
      id: 6,
      project_id: 1,
      title: null,
      created_at: '2026-01-01T00:00:00Z',
    })

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)

    fireEvent.click(await screen.findByRole('button', { name: 'New conversation' }))

    await waitFor(() => expect(createSpy).toHaveBeenCalledWith(1))
  })

  it('sending a message streams tokens and shows the final answer with sources', async () => {
    vi.spyOn(client, 'listConversations').mockResolvedValue([oldConversation])
    vi.spyOn(client, 'listMessages').mockResolvedValue([])
    vi.spyOn(client, 'sendMessage').mockImplementation(
      async (_conversationId: number, _content: string, callbacks: SendMessageCallbacks) => {
        callbacks.onToken('The answer is ')
        callbacks.onToken('42 [1].')
        callbacks.onDone([
          { chunk_id: 7, rank: 1, document_title: 'Mechanics', display_path: 'Ch. 2' },
        ])
      },
    )

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)

    fireEvent.click(await screen.findByText('Old chat about forces'))

    const input = await screen.findByPlaceholderText('Ask a question…')
    fireEvent.change(input, { target: { value: 'What is the answer?' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send' }))

    // The [1] marker renders as its own styled <sup> showing just the
    // number (brackets dropped — the pill styling itself signals "citation"),
    // so the sentence is split across sibling nodes with no literal
    // brackets in the merged text. Match on the paragraph's combined text.
    expect(
      await screen.findByText(
        (_content, element) => element?.tagName === 'P' && element.textContent === 'The answer is 42 1.',
      ),
    ).toBeInTheDocument()
    expect(await screen.findByText(/Ch\. 2/)).toBeInTheDocument()
  })
})
