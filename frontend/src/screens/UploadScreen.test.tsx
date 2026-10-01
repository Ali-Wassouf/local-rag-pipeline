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

    expect(screen.getByLabelText('Generate a summary for these documents')).toBeChecked()

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

    fireEvent.click(screen.getByLabelText('Generate a summary for these documents'))
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

  it('uploads multiple selected files independently', async () => {
    const uploadSpy = vi.spyOn(client, 'uploadDocument').mockImplementation(async (file) => ({
      document: { ...uploadedDocument, id: file.name.length, title: file.name },
      job_id: file.name.length,
      deduped: false,
    }))
    vi.spyOn(client, 'getJob').mockImplementation(async (jobId) => ({
      id: jobId,
      document_id: jobId,
      stage: 'extract',
      progress: 0,
      error: null,
      started_at: null,
      finished_at: null,
    }))

    const { container } = renderWithClient(<UploadScreen onReviewDocument={vi.fn()} />)
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement
    const fileA = new File(['a'], 'alpha.txt', { type: 'text/plain' })
    const fileB = new File(['b'], 'beta.txt', { type: 'text/plain' })
    fireEvent.change(fileInput, { target: { files: [fileA, fileB] } })

    await waitFor(() => expect(uploadSpy).toHaveBeenCalledTimes(2))
    expect(uploadSpy).toHaveBeenCalledWith(fileA, undefined, true)
    expect(uploadSpy).toHaveBeenCalledWith(fileB, undefined, true)
    expect(await screen.findByText('alpha.txt')).toBeInTheDocument()
    expect(await screen.findByText('beta.txt')).toBeInTheDocument()
  })

  it('does not let one failed upload affect the others', async () => {
    vi.spyOn(client, 'uploadDocument').mockImplementation(async (file) => {
      if (file.name === 'bad.txt') throw new Error('Unsupported file type')
      return { document: uploadedDocument, job_id: 5, deduped: false }
    })
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
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement
    const goodFile = new File(['ok'], 'good.txt', { type: 'text/plain' })
    const badFile = new File(['bad'], 'bad.txt', { type: 'text/plain' })
    fireEvent.change(fileInput, { target: { files: [goodFile, badFile] } })

    expect(await screen.findByText('Unsupported file type')).toBeInTheDocument()
    expect(await screen.findByText(/Job #5/)).toBeInTheDocument()
  })

  it('shows its own review button for each completed file', async () => {
    vi.spyOn(client, 'uploadDocument').mockImplementation(async (file) => ({
      document: { ...uploadedDocument, id: file.name === 'alpha.txt' ? 1 : 2, title: file.name },
      job_id: file.name === 'alpha.txt' ? 1 : 2,
      deduped: false,
    }))
    vi.spyOn(client, 'getJob').mockImplementation(async (jobId) => ({
      id: jobId,
      document_id: jobId,
      stage: 'done',
      progress: 1,
      error: null,
      started_at: null,
      finished_at: null,
    }))
    const onReviewDocument = vi.fn()

    const { container } = renderWithClient(<UploadScreen onReviewDocument={onReviewDocument} />)
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement
    const fileA = new File(['a'], 'alpha.txt', { type: 'text/plain' })
    const fileB = new File(['b'], 'beta.txt', { type: 'text/plain' })
    fireEvent.change(fileInput, { target: { files: [fileA, fileB] } })

    await waitFor(() =>
      expect(screen.getAllByRole('button', { name: 'Review structure' })).toHaveLength(2),
    )
    const reviewButtons = screen.getAllByRole('button', { name: 'Review structure' })

    fireEvent.click(reviewButtons[1])
    expect(onReviewDocument).toHaveBeenCalledWith(2)
  })

  it('a deduped file shows its own note without affecting the other file', async () => {
    vi.spyOn(client, 'uploadDocument').mockImplementation(async (file) => {
      if (file.name === 'dup.txt') {
        return { document: { ...uploadedDocument, title: 'dup' }, job_id: null, deduped: true }
      }
      return { document: uploadedDocument, job_id: 5, deduped: false }
    })
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
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement
    const dupFile = new File(['d'], 'dup.txt', { type: 'text/plain' })
    const newFile = new File(['n'], 'new.txt', { type: 'text/plain' })
    fireEvent.change(fileInput, { target: { files: [dupFile, newFile] } })

    expect(await screen.findByText(/Already ingested as "dup"/)).toBeInTheDocument()
    expect(await screen.findByText(/Job #5/)).toBeInTheDocument()
  })

  it('appends newly chosen files to an in-progress batch rather than replacing it', async () => {
    vi.spyOn(client, 'uploadDocument').mockResolvedValue(uploadResponse)
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
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement
    const fileA = new File(['a'], 'alpha.txt', { type: 'text/plain' })
    fireEvent.change(fileInput, { target: { files: [fileA] } })
    await screen.findByText('alpha.txt')

    const fileB = new File(['b'], 'beta.txt', { type: 'text/plain' })
    fireEvent.change(fileInput, { target: { files: [fileB] } })

    expect(await screen.findByText('beta.txt')).toBeInTheDocument()
    expect(screen.getByText('alpha.txt')).toBeInTheDocument()
  })
})
