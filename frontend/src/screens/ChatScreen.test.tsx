import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
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
  generate_summary: true,
  section_count: 0,
  summary_count: 0,
  summarizing: false,
  summary_total: null,
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
    citations: [{ chunk_id: 99, rank: 1, document_title: 'Mechanics', display_path: 'Ch. 1', is_summary: false, text: 'Passage text.' }],
  },
]

function renderWithClient(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
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
    expect(await screen.findByText('1 Document')).toBeInTheDocument()
  })

  it('selecting a past conversation loads its messages', async () => {
    vi.spyOn(client, 'listConversations').mockResolvedValue([oldConversation])
    vi.spyOn(client, 'listMessages').mockResolvedValue(oldMessages)

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)

    // The chapter row's own preview is fetched from the conversation's real
    // first question, so it can legitimately duplicate transcript text once
    // selected — the folio number is what's unique, so select by that.
    const conversationButton = await screen.findByRole('button', { name: /No\. 1/ })
    fireEvent.click(conversationButton)

    expect(await screen.findByText(/object in motion stays in motion/)).toBeInTheDocument()
    expect(await screen.findAllByText(/Newton's first law/)).toHaveLength(2)
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

    fireEvent.click(await screen.findByRole('button', { name: 'New chapter' }))

    await waitFor(() => expect(createSpy).toHaveBeenCalledWith(1))
  })

  it("a chapter row previews its own first question, not a bare title", async () => {
    vi.spyOn(client, 'listConversations').mockResolvedValue([oldConversation])
    vi.spyOn(client, 'listMessages').mockResolvedValue(oldMessages)

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)

    const row = await screen.findByRole('button', { name: /No\. 1/ })
    await waitFor(() => expect(row).toHaveTextContent("What is Newton's first law?"))
    expect(row).not.toHaveTextContent('Old chat about forces')
  })

  it('sending a message streams tokens and shows the final answer with sources', async () => {
    vi.spyOn(client, 'listConversations').mockResolvedValue([oldConversation])
    vi.spyOn(client, 'listMessages').mockResolvedValue([])
    vi.spyOn(client, 'sendMessage').mockImplementation(
      async (_conversationId: number, _content: string, callbacks: SendMessageCallbacks) => {
        callbacks.onToken('The answer is ')
        callbacks.onToken('42 [1].')
        callbacks.onDone([
          { chunk_id: 7, rank: 1, document_title: 'Mechanics', display_path: 'Ch. 2', is_summary: false, text: 'Passage text.' },
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
    expect((await screen.findAllByText(/Ch\. 2/)).length).toBeGreaterThan(0)
  })

  it('renders Markdown formatting instead of literal syntax characters', async () => {
    const markdownMessages: MessageRead[] = [
      {
        id: 1,
        conversation_id: 5,
        role: 'assistant',
        content: '**ACID** stands for:\n\n1. Atomicity\n2. Consistency',
        created_at: '2026-01-01T00:00:00Z',
        citations: [],
      },
    ]
    vi.spyOn(client, 'listConversations').mockResolvedValue([oldConversation])
    vi.spyOn(client, 'listMessages').mockResolvedValue(markdownMessages)

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)
    fireEvent.click(await screen.findByText('Old chat about forces'))

    const bold = await screen.findByText('ACID')
    expect(bold.tagName).toBe('STRONG')

    // The raw list markers ("1.", "2.") must not appear as literal text —
    // they should have become an actual <ol>/<li> structure.
    expect(await screen.findByText('Atomicity')).toBeInTheDocument()
    expect(screen.getByText('Atomicity').closest('li')).not.toBeNull()
    expect(screen.queryByText(/^1\.\s*Atomicity/)).not.toBeInTheDocument()
  })

  it('switching conversations resets sending state so the new one is not stuck disabled', async () => {
    const anotherConversation: ConversationRead = {
      id: 6,
      project_id: 1,
      title: 'Another chat',
      created_at: '2026-01-01T00:00:00Z',
    }
    vi.spyOn(client, 'listConversations').mockResolvedValue([oldConversation, anotherConversation])
    vi.spyOn(client, 'listMessages').mockResolvedValue([])

    // Simulate a request that never resolves — the in-flight generation
    // the user was mid-way through when they switched conversations.
    vi.spyOn(client, 'sendMessage').mockImplementation(() => new Promise(() => {}))

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)

    fireEvent.click(await screen.findByText('Old chat about forces'))
    const input = await screen.findByPlaceholderText('Ask a question…')
    fireEvent.change(input, { target: { value: 'A question' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send' }))

    expect(screen.getByPlaceholderText('Ask a question…')).toBeDisabled()

    fireEvent.click(screen.getByText('Another chat'))

    expect(await screen.findByPlaceholderText('Ask a question…')).not.toBeDisabled()
  })

  it('still styles citation markers distinctly inside Markdown output', async () => {
    const markdownMessages: MessageRead[] = [
      {
        id: 1,
        conversation_id: 5,
        role: 'assistant',
        content: 'Answers should be **grounded** in sources [1] and [2].',
        created_at: '2026-01-01T00:00:00Z',
        citations: [
          { chunk_id: 1, rank: 1, document_title: 'Doc A', display_path: 'Ch. 1', is_summary: false, text: 'Passage text.' },
          { chunk_id: 2, rank: 2, document_title: 'Doc B', display_path: 'Ch. 2', is_summary: false, text: 'Passage text.' },
        ],
      },
    ]
    vi.spyOn(client, 'listConversations').mockResolvedValue([oldConversation])
    vi.spyOn(client, 'listMessages').mockResolvedValue(markdownMessages)

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)
    fireEvent.click(await screen.findByText('Old chat about forces'))

    expect((await screen.findByText('grounded')).tagName).toBe('STRONG')

    // The inline markers in the prose are real clickable <button>s inside a
    // <sup>, styled distinctly from plain text.
    const reply = (await screen.findByText(/Answers should be/)).closest('.prose') as HTMLElement
    const inlineMarkers = within(reply).getAllByRole('button')
    expect(inlineMarkers.map((el) => el.textContent)).toEqual(['1', '2'])

    // The inspector defaults to the first cited source; clicking the other
    // marker switches it to the second.
    const inspector = await screen.findByLabelText('Marginalia passage inspector')
    expect(within(inspector).getByText('Doc A')).toBeInTheDocument()

    fireEvent.click(inlineMarkers[1])
    expect(within(inspector).getByText('Doc B')).toBeInTheDocument()
  })

  it('clicking a citation marker opens it in the passage inspector', async () => {
    const markdownMessages: MessageRead[] = [
      {
        id: 42,
        conversation_id: 5,
        role: 'assistant',
        content: 'A transaction groups operations into one unit [1]. See also [2].',
        created_at: '2026-01-01T00:00:00Z',
        citations: [
          { chunk_id: 1, rank: 1, document_title: 'DDIA', display_path: 'Ch. 7', is_summary: false, text: 'First passage text.' },
          { chunk_id: 2, rank: 2, document_title: 'Raft Paper', display_path: 'Sec. 3', is_summary: false, text: 'Second passage text.' },
        ],
      },
    ]
    vi.spyOn(client, 'listConversations').mockResolvedValue([oldConversation])
    vi.spyOn(client, 'listMessages').mockResolvedValue(markdownMessages)

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)
    fireEvent.click(await screen.findByText('Old chat about forces'))

    const inspector = await screen.findByLabelText('Marginalia passage inspector')
    // Defaults to the cited source for the latest reply.
    expect(within(inspector).getByText('DDIA')).toBeInTheDocument()

    const reply = (await screen.findByText(/A transaction groups/)).closest('.prose') as HTMLElement
    fireEvent.click(within(reply).getByRole('button', { name: '2' }))

    expect(within(inspector).getByText('Raft Paper')).toBeInTheDocument()
    expect(within(inspector).getByText(/Second passage text\./)).toBeInTheDocument()
  })

  it('the passage inspector shows the full source text, not just its citation', async () => {
    const passageText = 'Transactions group one or more operations into a single logical unit.'
    const markdownMessages: MessageRead[] = [
      {
        id: 43,
        conversation_id: 5,
        role: 'assistant',
        content: 'A transaction groups operations into one unit [1].',
        created_at: '2026-01-01T00:00:00Z',
        citations: [
          {
            chunk_id: 1,
            rank: 1,
            document_title: 'DDIA',
            display_path: 'Ch. 7',
            is_summary: false,
            text: passageText,
          },
        ],
      },
    ]
    vi.spyOn(client, 'listConversations').mockResolvedValue([oldConversation])
    vi.spyOn(client, 'listMessages').mockResolvedValue(markdownMessages)

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)
    fireEvent.click(await screen.findByText('Old chat about forces'))

    expect(await screen.findByText(new RegExp(passageText.replace('.', '\\.')))).toBeInTheDocument()
  })

  it('visually distinguishes a retrieved source the answer never actually cited', async () => {
    // message_citations persists every retrieved chunk, not just the ones
    // the model referenced inline (docs/plan.md §4.6) — the footnote list
    // must tell those two cases apart rather than rendering them the same.
    const markdownMessages: MessageRead[] = [
      {
        id: 7,
        conversation_id: 5,
        role: 'assistant',
        content: 'RAID 10 is best for high availability [1].',
        created_at: '2026-01-01T00:00:00Z',
        citations: [
          { chunk_id: 1, rank: 1, document_title: 'Storage Deck', display_path: 'Slide 16', is_summary: false, text: 'Passage text.' },
          { chunk_id: 2, rank: 2, document_title: 'Storage Deck', display_path: 'Slide 5', is_summary: false, text: 'Passage text.' },
        ],
      },
    ]
    vi.spyOn(client, 'listConversations').mockResolvedValue([oldConversation])
    vi.spyOn(client, 'listMessages').mockResolvedValue(markdownMessages)

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)
    fireEvent.click(await screen.findByText('Old chat about forces'))

    const inspector = await screen.findByLabelText('Marginalia passage inspector')
    // Defaults to the cited source (rank 1, Slide 16).
    expect(within(inspector).getByText('Slide 16')).toBeInTheDocument()
    expect(within(inspector).getByText(/Directly cited/)).toBeInTheDocument()

    fireEvent.click(within(inspector).getByRole('button', { name: '2' }))

    expect(within(inspector).getByText('Slide 5')).toBeInTheDocument()
    expect(within(inspector).getByText(/not cited in reply/)).toBeInTheDocument()
  })

  it('shows a moving indicator next to Reply while the answer is still generating', async () => {
    vi.spyOn(client, 'listConversations').mockResolvedValue([oldConversation])
    vi.spyOn(client, 'listMessages').mockResolvedValue([])
    vi.spyOn(client, 'sendMessage').mockImplementation(() => new Promise(() => {}))

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)
    fireEvent.click(await screen.findByText('Old chat about forces'))

    const input = await screen.findByPlaceholderText('Ask a question…')
    fireEvent.change(input, { target: { value: 'A question' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send' }))

    expect(await screen.findByRole('status')).toHaveTextContent(/composing/i)
  })

  it('removing a chapter deletes it and drops it from the list', async () => {
    vi.spyOn(client, 'listConversations')
      .mockResolvedValueOnce([oldConversation])
      .mockResolvedValue([])
    vi.spyOn(client, 'listMessages').mockResolvedValue([])
    vi.spyOn(client, 'listDeletedConversations').mockResolvedValue([])
    const deleteSpy = vi.spyOn(client, 'deleteConversation').mockResolvedValue(undefined)

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)

    await screen.findByText('Old chat about forces')
    fireEvent.click(await screen.findByRole('button', { name: 'Remove chapter' }))

    await waitFor(() => expect(deleteSpy).toHaveBeenCalledWith(5))
    await waitFor(() =>
      expect(screen.queryByText('Old chat about forces')).not.toBeInTheDocument(),
    )
  })

  it('removing the currently open chapter clears the view back to empty state', async () => {
    vi.spyOn(client, 'listConversations')
      .mockResolvedValueOnce([oldConversation])
      .mockResolvedValue([])
    vi.spyOn(client, 'listMessages').mockResolvedValue(oldMessages)
    vi.spyOn(client, 'listDeletedConversations').mockResolvedValue([])
    vi.spyOn(client, 'deleteConversation').mockResolvedValue(undefined)

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)

    fireEvent.click(await screen.findByText('Old chat about forces'))
    expect(await screen.findByPlaceholderText('Ask a question…')).toBeInTheDocument()

    fireEvent.click(await screen.findByRole('button', { name: 'Remove chapter' }))

    expect(await screen.findByText('Select a chapter, or begin a new one.')).toBeInTheDocument()
  })

  it('shows deleted chapters and restores one on request', async () => {
    const deletedConversation: ConversationRead = {
      id: 9,
      project_id: 1,
      title: 'An old abandoned chat',
      created_at: '2026-01-01T00:00:00Z',
    }
    vi.spyOn(client, 'listConversations').mockResolvedValue([])
    vi.spyOn(client, 'listMessages').mockResolvedValue([])
    vi.spyOn(client, 'listDeletedConversations').mockResolvedValue([deletedConversation])
    const restoreSpy = vi
      .spyOn(client, 'restoreConversation')
      .mockResolvedValue(deletedConversation)

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)

    const summary = await screen.findByText('Deleted (1)')
    fireEvent.click(summary)

    fireEvent.click(await screen.findByRole('button', { name: 'Restore' }))
    await waitFor(() => expect(restoreSpy).toHaveBeenCalledWith(9))
  })

  it('defaults to lookup mode and switches to survey mode on request', async () => {
    vi.spyOn(client, 'listConversations').mockResolvedValue([oldConversation])
    vi.spyOn(client, 'listMessages').mockResolvedValue([])
    const sendSpy = vi
      .spyOn(client, 'sendMessage')
      .mockImplementation(async (_id, _content, callbacks: SendMessageCallbacks) => {
        callbacks.onDone([])
      })

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)
    fireEvent.click(await screen.findByText('Old chat about forces'))

    const input = await screen.findByPlaceholderText('Ask a question…')
    fireEvent.change(input, { target: { value: 'First question' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send' }))
    await waitFor(() =>
      expect(sendSpy).toHaveBeenCalledWith(5, 'First question', expect.anything(), 'lookup'),
    )

    fireEvent.click(screen.getByRole('radio', { name: 'Survey' }))
    fireEvent.change(input, { target: { value: 'Second question' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send' }))
    await waitFor(() =>
      expect(sendSpy).toHaveBeenCalledWith(5, 'Second question', expect.anything(), 'survey'),
    )
  })

  it('visibly labels a summary citation and never styles it like a passage', async () => {
    const surveyMessages: MessageRead[] = [
      {
        id: 11,
        conversation_id: 5,
        role: 'assistant',
        content: 'Across several chapters, the book covers isolation and replication [1].',
        created_at: '2026-01-01T00:00:00Z',
        citations: [
          {
            chunk_id: null,
            rank: 1,
            document_title: 'DDIA',
            display_path: 'Part II',
            is_summary: true,
            text: 'A summary of isolation and replication across the book.',
          },
        ],
      },
    ]
    vi.spyOn(client, 'listConversations').mockResolvedValue([oldConversation])
    vi.spyOn(client, 'listMessages').mockResolvedValue(surveyMessages)

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)
    fireEvent.click(await screen.findByText('Old chat about forces'))

    const inspector = await screen.findByLabelText('Marginalia passage inspector')
    expect(within(inspector).getByText('DDIA')).toBeInTheDocument()
    expect(within(inspector).getByText('Summary')).toBeInTheDocument()
    expect(within(inspector).queryByText('Verbatim Document Excerpt')).not.toBeInTheDocument()
  })

  it('shows an error if the chapter list fails to load', async () => {
    vi.spyOn(client, 'listConversations').mockRejectedValue(new Error('Database unreachable'))
    vi.spyOn(client, 'listDeletedConversations').mockResolvedValue([])

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)

    expect(await screen.findByText('Database unreachable')).toBeInTheDocument()
  })

  it('shows an error if starting a new chapter fails', async () => {
    vi.spyOn(client, 'listConversations').mockResolvedValue([])
    vi.spyOn(client, 'listDeletedConversations').mockResolvedValue([])
    vi.spyOn(client, 'createConversation').mockRejectedValue(new Error('Project not found'))

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)

    fireEvent.click(await screen.findByRole('button', { name: 'New chapter' }))

    expect(await screen.findByText('Project not found')).toBeInTheDocument()
  })

  it('shows an error if removing a chapter fails', async () => {
    vi.spyOn(client, 'listConversations').mockResolvedValue([oldConversation])
    vi.spyOn(client, 'listMessages').mockResolvedValue([])
    vi.spyOn(client, 'listDeletedConversations').mockResolvedValue([])
    vi.spyOn(client, 'deleteConversation').mockRejectedValue(new Error('Conversation not found'))

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)

    fireEvent.click(await screen.findByRole('button', { name: 'Remove chapter' }))

    expect(await screen.findByText('Conversation not found')).toBeInTheDocument()
  })

  it('shows an error if restoring a deleted chapter fails', async () => {
    const deletedConversation: ConversationRead = {
      id: 9,
      project_id: 1,
      title: 'An old abandoned chat',
      created_at: '2026-01-01T00:00:00Z',
    }
    vi.spyOn(client, 'listConversations').mockResolvedValue([])
    vi.spyOn(client, 'listDeletedConversations').mockResolvedValue([deletedConversation])
    vi.spyOn(client, 'restoreConversation').mockRejectedValue(new Error('Already restored'))

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)

    fireEvent.click(await screen.findByText('Deleted (1)'))
    fireEvent.click(await screen.findByRole('button', { name: 'Restore' }))

    expect(await screen.findByText('Already restored')).toBeInTheDocument()
  })

  it('shows an error if the deleted-chapters list fails to load', async () => {
    vi.spyOn(client, 'listConversations').mockResolvedValue([])
    vi.spyOn(client, 'listDeletedConversations').mockRejectedValue(new Error('Server error'))

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)

    expect(await screen.findByText('Server error')).toBeInTheDocument()
  })

  it('shows an error if a chapter’s messages fail to load', async () => {
    vi.spyOn(client, 'listConversations').mockResolvedValue([oldConversation])
    vi.spyOn(client, 'listDeletedConversations').mockResolvedValue([])
    vi.spyOn(client, 'listMessages').mockRejectedValue(new Error('Conversation not found'))

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)
    fireEvent.click(await screen.findByText('Old chat about forces'))

    expect(await screen.findByText(/Conversation not found/)).toBeInTheDocument()
  })

  it('shows an error if the project or its documents fail to load', async () => {
    vi.restoreAllMocks()
    vi.spyOn(client, 'getProject').mockRejectedValue(new Error('Project not found'))
    vi.spyOn(client, 'listProjectDocuments').mockResolvedValue([])
    vi.spyOn(client, 'listConversations').mockResolvedValue([])
    vi.spyOn(client, 'listDeletedConversations').mockResolvedValue([])

    renderWithClient(<ChatScreen projectId={1} onBack={vi.fn()} />)

    expect(await screen.findByText('Project not found')).toBeInTheDocument()
  })
})
