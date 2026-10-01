import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import type { ReactElement } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as client from '../api/client'
import type { SectionRead } from '../api/types'
import { ReviewScreen } from './ReviewScreen'

const baseSection: SectionRead = {
  id: 1,
  document_id: 1,
  path: 'n1',
  title: 'Chapter One',
  display_path: 'Chapter One',
  depth: 1,
  ordinal: 1,
  char_start: 0,
  char_end: 20,
  source: 'detected',
  preview: 'Chapter One body text',
  estimated_chunks: 1,
}

function renderWithClient(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

describe('ReviewScreen', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('shows the preview of a section', async () => {
    vi.spyOn(client, 'getSections').mockResolvedValue([baseSection])
    renderWithClient(<ReviewScreen documentId={1} onBack={vi.fn()} />)

    await screen.findByRole('button', { name: 'Chapter One' })
    expect(await screen.findByText('Chapter One body text')).toBeInTheDocument()
  })

  it('editing a title calls the update mutation', async () => {
    vi.spyOn(client, 'getSections').mockResolvedValue([baseSection])
    const updateSpy = vi
      .spyOn(client, 'updateSectionTitle')
      .mockResolvedValue({ ...baseSection, title: 'Renamed', source: 'manual' })

    renderWithClient(<ReviewScreen documentId={1} onBack={vi.fn()} />)

    const titleButton = await screen.findByRole('button', { name: 'Chapter One' })
    fireEvent.click(titleButton)

    const input = screen.getByDisplayValue('Chapter One')
    fireEvent.change(input, { target: { value: 'Renamed' } })
    fireEvent.blur(input)

    await waitFor(() => expect(updateSpy).toHaveBeenCalledWith(1, 'Renamed'))
  })

  it('does not call the update mutation when the title is unchanged', async () => {
    vi.spyOn(client, 'getSections').mockResolvedValue([baseSection])
    const updateSpy = vi.spyOn(client, 'updateSectionTitle')

    renderWithClient(<ReviewScreen documentId={1} onBack={vi.fn()} />)

    const titleButton = await screen.findByRole('button', { name: 'Chapter One' })
    fireEvent.click(titleButton)

    const input = screen.getByDisplayValue('Chapter One')
    fireEvent.blur(input)

    await screen.findByRole('button', { name: 'Chapter One' })
    expect(updateSpy).not.toHaveBeenCalled()
  })

  it('renders an untitled region row when adjacent sections leave a gap', async () => {
    const withGap: SectionRead[] = [
      baseSection,
      {
        ...baseSection,
        id: 2,
        title: 'Chapter Two',
        path: 'n2',
        ordinal: 2,
        char_start: 30,
        char_end: 40,
      },
    ]
    vi.spyOn(client, 'getSections').mockResolvedValue(withGap)
    renderWithClient(<ReviewScreen documentId={1} onBack={vi.fn()} />)

    expect(await screen.findByText('Untitled region')).toBeInTheDocument()
  })

  it('shows an error if the sections fail to load', async () => {
    vi.spyOn(client, 'getSections').mockRejectedValue(new Error('Document not found'))
    renderWithClient(<ReviewScreen documentId={1} onBack={vi.fn()} />)

    expect(await screen.findByText('Document not found')).toBeInTheDocument()
  })

  it('shows an error under the row if saving a title fails', async () => {
    vi.spyOn(client, 'getSections').mockResolvedValue([baseSection])
    vi.spyOn(client, 'updateSectionTitle').mockRejectedValue(new Error('Title cannot be blank'))

    renderWithClient(<ReviewScreen documentId={1} onBack={vi.fn()} />)

    const titleButton = await screen.findByRole('button', { name: 'Chapter One' })
    fireEvent.click(titleButton)

    const input = screen.getByDisplayValue('Chapter One')
    fireEvent.change(input, { target: { value: 'Renamed' } })
    fireEvent.blur(input)

    expect(await screen.findByText(/Title cannot be blank/)).toBeInTheDocument()
  })
})
