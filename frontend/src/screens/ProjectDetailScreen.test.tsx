import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import type { ReactElement } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as client from '../api/client'
import type { DocumentRead, ProjectRead } from '../api/types'
import { ProjectDetailScreen } from './ProjectDetailScreen'

const project: ProjectRead = {
  id: 1,
  name: 'Physics',
  description: null,
  created_at: '2026-01-01T00:00:00Z',
}

const attachedDoc: DocumentRead = {
  id: 10,
  sha256: 'a'.repeat(64),
  title: 'Mechanics 101',
  author: null,
  format: 'pdf',
  original_name: 'mechanics.pdf',
  status: 'ready',
  generate_summary: true,
  section_count: 0,
  summary_count: 0,
  created_at: '2026-01-01T00:00:00Z',
}

const unattachedDoc: DocumentRead = {
  id: 11,
  sha256: 'b'.repeat(64),
  title: 'Thermodynamics',
  author: null,
  format: 'pdf',
  original_name: 'thermo.pdf',
  status: 'ready',
  generate_summary: true,
  section_count: 0,
  summary_count: 0,
  created_at: '2026-01-01T00:00:00Z',
}

function renderWithClient(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

describe('ProjectDetailScreen', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('shows attached documents with their status', async () => {
    vi.spyOn(client, 'getProject').mockResolvedValue(project);
    vi.spyOn(client, 'listProjectDocuments').mockResolvedValue([attachedDoc]);
    vi.spyOn(client, 'listAllDocuments').mockResolvedValue([attachedDoc, unattachedDoc]);

    renderWithClient(
      <ProjectDetailScreen
        projectId={1}
        onReviewDocument={vi.fn()}
        onUploadHere={vi.fn()}
        onOpenChat={vi.fn()}
        onBack={vi.fn()}
      />,
    )

    expect(await screen.findByText('Mechanics 101')).toBeInTheDocument()
    expect(await screen.findByText('ready')).toBeInTheDocument()
    // Thermodynamics is unattached — it may appear in the attach picker's
    // options, but must not appear as its own document row/button.
    expect(screen.queryByRole('button', { name: 'Thermodynamics' })).not.toBeInTheDocument()
  })

  it('attaching an existing document calls the attach mutation', async () => {
    vi.spyOn(client, 'getProject').mockResolvedValue(project)
    vi.spyOn(client, 'listProjectDocuments').mockResolvedValue([])
    vi.spyOn(client, 'listAllDocuments').mockResolvedValue([unattachedDoc])
    const attachSpy = vi.spyOn(client, 'attachDocumentToProject').mockResolvedValue(undefined)

    renderWithClient(
      <ProjectDetailScreen
        projectId={1}
        onReviewDocument={vi.fn()}
        onUploadHere={vi.fn()}
        onOpenChat={vi.fn()}
        onBack={vi.fn()}
      />,
    )

    const select = await screen.findByLabelText('Attach an existing document')
    await screen.findByRole('option', { name: 'Thermodynamics' })
    fireEvent.change(select, { target: { value: '11' } })
    fireEvent.click(screen.getByRole('button', { name: 'Attach' }))

    await waitFor(() => expect(attachSpy).toHaveBeenCalledWith(1, 11))
  })

  it('removing a document calls the detach mutation', async () => {
    vi.spyOn(client, 'getProject').mockResolvedValue(project)
    vi.spyOn(client, 'listProjectDocuments').mockResolvedValue([attachedDoc])
    vi.spyOn(client, 'listAllDocuments').mockResolvedValue([attachedDoc])
    const detachSpy = vi.spyOn(client, 'detachDocumentFromProject').mockResolvedValue(undefined)

    renderWithClient(
      <ProjectDetailScreen
        projectId={1}
        onReviewDocument={vi.fn()}
        onUploadHere={vi.fn()}
        onOpenChat={vi.fn()}
        onBack={vi.fn()}
      />,
    )

    const removeButton = await screen.findByRole('button', { name: 'Remove' })
    fireEvent.click(removeButton)

    await waitFor(() => expect(detachSpy).toHaveBeenCalledWith(1, 10))
  })

  it('offers to generate a summary later for a document that opted out', async () => {
    const optedOutDoc: DocumentRead = { ...attachedDoc, generate_summary: false }
    vi.spyOn(client, 'getProject').mockResolvedValue(project)
    vi.spyOn(client, 'listProjectDocuments').mockResolvedValue([optedOutDoc])
    vi.spyOn(client, 'listAllDocuments').mockResolvedValue([optedOutDoc])
    const summarizeSpy = vi
      .spyOn(client, 'summarizeDocument')
      .mockResolvedValue({ ...optedOutDoc, generate_summary: true })

    renderWithClient(
      <ProjectDetailScreen
        projectId={1}
        onReviewDocument={vi.fn()}
        onUploadHere={vi.fn()}
        onOpenChat={vi.fn()}
        onBack={vi.fn()}
      />,
    )

    const generateButton = await screen.findByRole('button', { name: 'Generate summary' })
    fireEvent.click(generateButton)

    await waitFor(() => expect(summarizeSpy).toHaveBeenCalledWith(10))
  })

  it('does not offer to generate a summary for a document that already has one', async () => {
    vi.spyOn(client, 'getProject').mockResolvedValue(project)
    vi.spyOn(client, 'listProjectDocuments').mockResolvedValue([attachedDoc])
    vi.spyOn(client, 'listAllDocuments').mockResolvedValue([attachedDoc])

    renderWithClient(
      <ProjectDetailScreen
        projectId={1}
        onReviewDocument={vi.fn()}
        onUploadHere={vi.fn()}
        onOpenChat={vi.fn()}
        onBack={vi.fn()}
      />,
    )

    await screen.findByText('Mechanics 101')
    expect(screen.queryByRole('button', { name: 'Generate summary' })).not.toBeInTheDocument()
  })

  it('does not offer to generate a summary while the document is still indexing', async () => {
    const stillIndexing: DocumentRead = {
      ...attachedDoc,
      generate_summary: false,
      status: 'indexing',
    }
    vi.spyOn(client, 'getProject').mockResolvedValue(project)
    vi.spyOn(client, 'listProjectDocuments').mockResolvedValue([stillIndexing])
    vi.spyOn(client, 'listAllDocuments').mockResolvedValue([stillIndexing])

    renderWithClient(
      <ProjectDetailScreen
        projectId={1}
        onReviewDocument={vi.fn()}
        onUploadHere={vi.fn()}
        onOpenChat={vi.fn()}
        onBack={vi.fn()}
      />,
    )

    await screen.findByText('Mechanics 101')
    expect(screen.queryByRole('button', { name: 'Generate summary' })).not.toBeInTheDocument()
  })

  it('shows the real summary count for a document with real summaries', async () => {
    const summarized: DocumentRead = { ...attachedDoc, section_count: 5, summary_count: 2 }
    vi.spyOn(client, 'getProject').mockResolvedValue(project)
    vi.spyOn(client, 'listProjectDocuments').mockResolvedValue([summarized])
    vi.spyOn(client, 'listAllDocuments').mockResolvedValue([summarized])

    renderWithClient(
      <ProjectDetailScreen
        projectId={1}
        onReviewDocument={vi.fn()}
        onUploadHere={vi.fn()}
        onOpenChat={vi.fn()}
        onBack={vi.fn()}
      />,
    )

    expect(await screen.findByText('2 of 5 sections summarized')).toBeInTheDocument()
  })

  it('distinguishes "opted in but nothing qualified" from having real summaries', async () => {
    // generate_summary=true alone doesn't mean anything was produced — a
    // deck whose sections are all too short to meet the threshold ends up
    // with zero real summaries despite being opted in.
    const nothingQualified: DocumentRead = {
      ...attachedDoc,
      generate_summary: true,
      section_count: 56,
      summary_count: 0,
    }
    vi.spyOn(client, 'getProject').mockResolvedValue(project)
    vi.spyOn(client, 'listProjectDocuments').mockResolvedValue([nothingQualified])
    vi.spyOn(client, 'listAllDocuments').mockResolvedValue([nothingQualified])

    renderWithClient(
      <ProjectDetailScreen
        projectId={1}
        onReviewDocument={vi.fn()}
        onUploadHere={vi.fn()}
        onOpenChat={vi.fn()}
        onBack={vi.fn()}
      />,
    )

    expect(
      await screen.findByText('0 of 56 sections summarized — none were long enough to qualify'),
    ).toBeInTheDocument()
    // Re-running summarization wouldn't change this outcome, so no button.
    expect(screen.queryByRole('button', { name: 'Generate summary' })).not.toBeInTheDocument()
  })

  it('shows "Not summarized" for an opted-out document that has sections', async () => {
    const optedOutWithSections: DocumentRead = {
      ...attachedDoc,
      generate_summary: false,
      section_count: 10,
      summary_count: 0,
    }
    vi.spyOn(client, 'getProject').mockResolvedValue(project)
    vi.spyOn(client, 'listProjectDocuments').mockResolvedValue([optedOutWithSections])
    vi.spyOn(client, 'listAllDocuments').mockResolvedValue([optedOutWithSections])

    renderWithClient(
      <ProjectDetailScreen
        projectId={1}
        onReviewDocument={vi.fn()}
        onUploadHere={vi.fn()}
        onOpenChat={vi.fn()}
        onBack={vi.fn()}
      />,
    )

    expect(await screen.findByText('Not summarized')).toBeInTheDocument()
    expect(await screen.findByRole('button', { name: 'Generate summary' })).toBeInTheDocument()
  })

  it('renames a project', async () => {
    vi.spyOn(client, 'getProject').mockResolvedValue(project)
    vi.spyOn(client, 'listProjectDocuments').mockResolvedValue([])
    vi.spyOn(client, 'listAllDocuments').mockResolvedValue([])
    const renameSpy = vi
      .spyOn(client, 'renameProject')
      .mockResolvedValue({ ...project, name: 'Quantum Physics' })

    renderWithClient(
      <ProjectDetailScreen
        projectId={1}
        onReviewDocument={vi.fn()}
        onUploadHere={vi.fn()}
        onOpenChat={vi.fn()}
        onBack={vi.fn()}
      />,
    )

    await screen.findByText('Physics')
    fireEvent.click(screen.getByRole('button', { name: 'Rename' }))

    const input = screen.getByLabelText('Project name')
    fireEvent.change(input, { target: { value: 'Quantum Physics' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(renameSpy).toHaveBeenCalledWith(1, 'Quantum Physics'))
  })

  it('reindexes a document', async () => {
    vi.spyOn(client, 'getProject').mockResolvedValue(project)
    vi.spyOn(client, 'listProjectDocuments').mockResolvedValue([attachedDoc])
    vi.spyOn(client, 'listAllDocuments').mockResolvedValue([attachedDoc])
    const reindexSpy = vi
      .spyOn(client, 'reindexDocument')
      .mockResolvedValue({ ...attachedDoc, status: 'uploaded' })

    renderWithClient(
      <ProjectDetailScreen
        projectId={1}
        onReviewDocument={vi.fn()}
        onUploadHere={vi.fn()}
        onOpenChat={vi.fn()}
        onBack={vi.fn()}
      />,
    )

    const reindexButton = await screen.findByRole('button', { name: 'Re-index' })
    fireEvent.click(reindexButton)

    await waitFor(() => expect(reindexSpy).toHaveBeenCalledWith(10))
  })

  it('does not allow reindexing a document that is already mid-pipeline', async () => {
    const stillIndexing: DocumentRead = { ...attachedDoc, status: 'indexing' }
    vi.spyOn(client, 'getProject').mockResolvedValue(project)
    vi.spyOn(client, 'listProjectDocuments').mockResolvedValue([stillIndexing])
    vi.spyOn(client, 'listAllDocuments').mockResolvedValue([stillIndexing])

    renderWithClient(
      <ProjectDetailScreen
        projectId={1}
        onReviewDocument={vi.fn()}
        onUploadHere={vi.fn()}
        onOpenChat={vi.fn()}
        onBack={vi.fn()}
      />,
    )

    const reindexButton = await screen.findByRole('button', { name: 'Re-index' })
    expect(reindexButton).toBeDisabled()
  })

  it('requires typing the exact title before permanently deleting a document', async () => {
    vi.spyOn(client, 'getProject').mockResolvedValue(project)
    vi.spyOn(client, 'listProjectDocuments').mockResolvedValue([attachedDoc])
    vi.spyOn(client, 'listAllDocuments').mockResolvedValue([attachedDoc])
    const deleteSpy = vi.spyOn(client, 'deleteDocument').mockResolvedValue(undefined)

    renderWithClient(
      <ProjectDetailScreen
        projectId={1}
        onReviewDocument={vi.fn()}
        onUploadHere={vi.fn()}
        onOpenChat={vi.fn()}
        onBack={vi.fn()}
      />,
    )

    fireEvent.click(await screen.findByRole('button', { name: 'Delete…' }))

    const confirmButton = screen.getByRole('button', { name: 'Delete permanently' })
    const input = screen.getByLabelText('Type the document title to confirm deletion')

    // Wrong text — stays disabled, nothing is called.
    fireEvent.change(input, { target: { value: 'wrong title' } })
    expect(confirmButton).toBeDisabled()
    fireEvent.click(confirmButton)
    expect(deleteSpy).not.toHaveBeenCalled()

    // Exact title — enables the button.
    fireEvent.change(input, { target: { value: 'Mechanics 101' } })
    expect(confirmButton).not.toBeDisabled()
    fireEvent.click(confirmButton)

    await waitFor(() => expect(deleteSpy).toHaveBeenCalledWith(10))
  })

  it('cancels a delete confirmation without deleting', async () => {
    vi.spyOn(client, 'getProject').mockResolvedValue(project)
    vi.spyOn(client, 'listProjectDocuments').mockResolvedValue([attachedDoc])
    vi.spyOn(client, 'listAllDocuments').mockResolvedValue([attachedDoc])
    const deleteSpy = vi.spyOn(client, 'deleteDocument')

    renderWithClient(
      <ProjectDetailScreen
        projectId={1}
        onReviewDocument={vi.fn()}
        onUploadHere={vi.fn()}
        onOpenChat={vi.fn()}
        onBack={vi.fn()}
      />,
    )

    fireEvent.click(await screen.findByRole('button', { name: 'Delete…' }))
    expect(screen.getByRole('button', { name: 'Delete permanently' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(screen.queryByRole('button', { name: 'Delete permanently' })).not.toBeInTheDocument()
    expect(deleteSpy).not.toHaveBeenCalled()
  })

  it('cancels a rename without saving', async () => {
    vi.spyOn(client, 'getProject').mockResolvedValue(project)
    vi.spyOn(client, 'listProjectDocuments').mockResolvedValue([])
    vi.spyOn(client, 'listAllDocuments').mockResolvedValue([])
    const renameSpy = vi.spyOn(client, 'renameProject')

    renderWithClient(
      <ProjectDetailScreen
        projectId={1}
        onReviewDocument={vi.fn()}
        onUploadHere={vi.fn()}
        onOpenChat={vi.fn()}
        onBack={vi.fn()}
      />,
    )

    await screen.findByText('Physics')
    fireEvent.click(screen.getByRole('button', { name: 'Rename' }))
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(screen.getByText('Physics')).toBeInTheDocument()
    expect(renameSpy).not.toHaveBeenCalled()
  })

  it('shows an error if the project fails to load', async () => {
    vi.spyOn(client, 'getProject').mockRejectedValue(new Error('Project not found'))
    vi.spyOn(client, 'listProjectDocuments').mockResolvedValue([])
    vi.spyOn(client, 'listAllDocuments').mockResolvedValue([])

    renderWithClient(
      <ProjectDetailScreen
        projectId={1}
        onReviewDocument={vi.fn()}
        onUploadHere={vi.fn()}
        onOpenChat={vi.fn()}
        onBack={vi.fn()}
      />,
    )

    expect(await screen.findByText('Project not found')).toBeInTheDocument()
  })

  it('shows an error if the document list fails to load', async () => {
    vi.spyOn(client, 'getProject').mockResolvedValue(project)
    vi.spyOn(client, 'listProjectDocuments').mockRejectedValue(new Error('Database unreachable'))
    vi.spyOn(client, 'listAllDocuments').mockResolvedValue([])

    renderWithClient(
      <ProjectDetailScreen
        projectId={1}
        onReviewDocument={vi.fn()}
        onUploadHere={vi.fn()}
        onOpenChat={vi.fn()}
        onBack={vi.fn()}
      />,
    )

    expect(await screen.findByText('Database unreachable')).toBeInTheDocument()
  })

  it('shows an error if attaching a document fails', async () => {
    vi.spyOn(client, 'getProject').mockResolvedValue(project)
    vi.spyOn(client, 'listProjectDocuments').mockResolvedValue([])
    vi.spyOn(client, 'listAllDocuments').mockResolvedValue([unattachedDoc])
    vi.spyOn(client, 'attachDocumentToProject').mockRejectedValue(new Error('Already attached'))

    renderWithClient(
      <ProjectDetailScreen
        projectId={1}
        onReviewDocument={vi.fn()}
        onUploadHere={vi.fn()}
        onOpenChat={vi.fn()}
        onBack={vi.fn()}
      />,
    )

    const select = await screen.findByLabelText('Attach an existing document')
    await screen.findByRole('option', { name: 'Thermodynamics' })
    fireEvent.change(select, { target: { value: '11' } })
    fireEvent.click(screen.getByRole('button', { name: 'Attach' }))

    expect(await screen.findByText('Already attached')).toBeInTheDocument()
  })

  it('shows an error if removing a document fails', async () => {
    vi.spyOn(client, 'getProject').mockResolvedValue(project)
    vi.spyOn(client, 'listProjectDocuments').mockResolvedValue([attachedDoc])
    vi.spyOn(client, 'listAllDocuments').mockResolvedValue([attachedDoc])
    vi.spyOn(client, 'detachDocumentFromProject').mockRejectedValue(new Error('Still in use'))

    renderWithClient(
      <ProjectDetailScreen
        projectId={1}
        onReviewDocument={vi.fn()}
        onUploadHere={vi.fn()}
        onOpenChat={vi.fn()}
        onBack={vi.fn()}
      />,
    )

    fireEvent.click(await screen.findByRole('button', { name: 'Remove' }))

    expect(await screen.findByText('Still in use')).toBeInTheDocument()
  })
})
