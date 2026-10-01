import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import type { ReactElement } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as client from '../api/client'
import type { DocumentRead, DocumentUploadResponse } from '../api/types'
import { UploadScreen } from './UploadScreen'

const uploadedDocument: DocumentRead = {
  id: 1,
  sha256: 'a'.repeat(64),
  title: 'report',
  author: null,
  format: 'txt',
  original_name: 'report.txt',
  status: 'uploaded',
  generate_summary: true,
  section_count: 0,
  summary_count: 0,
  created_at: '2026-01-01T00:00:00Z',
}

const uploadResponse: DocumentUploadResponse = {
  document: uploadedDocument,
  job_id: 5,
  deduped: false,
}

function renderWithClient(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

// The real file input is visually hidden (triggered via a styled "Choose
// file" button) and has no accessible label of its own, so it's queried
// directly rather than by role/label.
function selectAFile(container: HTMLElement) {
  const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement
  const file = new File(['hello'], 'report.txt', { type: 'text/plain' })
  fireEvent.change(fileInput, { target: { files: [file] } })
}

describe('UploadScreen', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('defaults to generating a summary and passes that choice through on upload', async () => {
    const uploadSpy = vi.spyOn(client, 'uploadDocument').mockResolvedValue(uploadResponse)
    vi.spyOn(client, 'getJob').mockResolvedValue({
      id: 5,
      document_id: 1,
      stage: 'extract',
      progress: 0,
      error: null,
      started_at: null,
      finished_at: null,
    })

    const { container } = renderWithClient(<UploadScreen onReviewDocument={vi.fn()} />)

    expect(screen.getByLabelText('Generate a summary for this document')).toBeChecked()

    selectAFile(container)

    await waitFor(() => expect(uploadSpy).toHaveBeenCalledWith(expect.any(File), undefined, true))
  })

  it('passes false through when the user opts out of generating a summary', async () => {
    const uploadSpy = vi.spyOn(client, 'uploadDocument').mockResolvedValue(uploadResponse)
    vi.spyOn(client, 'getJob').mockResolvedValue({
      id: 5,
      document_id: 1,
      stage: 'extract',
      progress: 0,
      error: null,
      started_at: null,
      finished_at: null,
    })

    const { container } = renderWithClient(<UploadScreen onReviewDocument={vi.fn()} />)

    fireEvent.click(screen.getByLabelText('Generate a summary for this document'))
    selectAFile(container)

    await waitFor(() => expect(uploadSpy).toHaveBeenCalledWith(expect.any(File), undefined, false))
  })

  it('explains the time/resource cost of generating a summary', async () => {
    renderWithClient(<UploadScreen onReviewDocument={vi.fn()} />)

    expect(await screen.findByText(/extra time and compute/i)).toBeInTheDocument()
  })

  it('shows an error if checking on job progress fails', async () => {
    vi.spyOn(client, 'uploadDocument').mockResolvedValue(uploadResponse)
    vi.spyOn(client, 'getJob').mockRejectedValue(new Error('Job not found'))

    const { container } = renderWithClient(<UploadScreen onReviewDocument={vi.fn()} />)
    selectAFile(container)

    expect(await screen.findByText(/Job not found/)).toBeInTheDocument()
  })
})
