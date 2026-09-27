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
  created_at: '2026-01-01T00:00:00Z',
}

function renderWithClient(ui: ReactElement) {
  const queryClient = new QueryClient()
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
        onBack={vi.fn()}
      />,
    )

    const removeButton = await screen.findByRole('button', { name: 'Remove' })
    fireEvent.click(removeButton)

    await waitFor(() => expect(detachSpy).toHaveBeenCalledWith(1, 10))
  })
})
