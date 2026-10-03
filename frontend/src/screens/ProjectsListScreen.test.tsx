import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import type { ReactElement } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as client from '../api/client'
import type { ProjectRead } from '../api/types'
import { ProjectsListScreen } from './ProjectsListScreen'

const projects: ProjectRead[] = [
  { id: 1, name: 'Physics', description: null, created_at: '2026-01-01T00:00:00Z' },
]

function renderWithClient(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

describe('ProjectsListScreen', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('lists existing projects', async () => {
    vi.spyOn(client, 'listProjects').mockResolvedValue(projects)
    renderWithClient(
      <ProjectsListScreen onSelectProject={vi.fn()} onUploadStandalone={vi.fn()} onOpenChat={vi.fn()} />,
    )

    expect(await screen.findByText('Physics')).toBeInTheDocument()
  })

  it('selecting a project calls onSelectProject with its id', async () => {
    vi.spyOn(client, 'listProjects').mockResolvedValue(projects)
    const onSelectProject = vi.fn()
    renderWithClient(
      <ProjectsListScreen onSelectProject={onSelectProject} onUploadStandalone={vi.fn()} onOpenChat={vi.fn()} />,
    )

    const row = await screen.findByText('Physics')
    fireEvent.click(row)

    expect(onSelectProject).toHaveBeenCalledWith(1)
  })

  it('opening the reading room from a project row calls onOpenChat with its id', async () => {
    vi.spyOn(client, 'listProjects').mockResolvedValue(projects)
    const onOpenChat = vi.fn()
    renderWithClient(
      <ProjectsListScreen onSelectProject={vi.fn()} onUploadStandalone={vi.fn()} onOpenChat={onOpenChat} />,
    )

    fireEvent.click(await screen.findByRole('button', { name: 'Open Reading Room' }))

    expect(onOpenChat).toHaveBeenCalledWith(1)
  })

  it('creating a project calls the create mutation', async () => {
    vi.spyOn(client, 'listProjects').mockResolvedValue([])
    const createSpy = vi.spyOn(client, 'createProject').mockResolvedValue({
      id: 2,
      name: 'Chemistry',
      description: null,
      created_at: '2026-01-01T00:00:00Z',
    })

    renderWithClient(<ProjectsListScreen onSelectProject={vi.fn()} onUploadStandalone={vi.fn()} onOpenChat={vi.fn()} />)

    const input = await screen.findByPlaceholderText(/New project name/)
    fireEvent.change(input, { target: { value: 'Chemistry' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create' }))

    await waitFor(() => expect(createSpy).toHaveBeenCalledWith('Chemistry'))
  })

  it('shows an error if the project list fails to load', async () => {
    vi.spyOn(client, 'listProjects').mockRejectedValue(new Error('Network error'))

    renderWithClient(<ProjectsListScreen onSelectProject={vi.fn()} onUploadStandalone={vi.fn()} onOpenChat={vi.fn()} />)

    expect(await screen.findByText('Network error')).toBeInTheDocument()
  })

  it('shows an error if creating a project fails', async () => {
    vi.spyOn(client, 'listProjects').mockResolvedValue([])
    vi.spyOn(client, 'createProject').mockRejectedValue(new Error('Name already taken'))

    renderWithClient(<ProjectsListScreen onSelectProject={vi.fn()} onUploadStandalone={vi.fn()} onOpenChat={vi.fn()} />)

    const input = await screen.findByPlaceholderText(/New project name/)
    fireEvent.change(input, { target: { value: 'Chemistry' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create' }))

    expect(await screen.findByText('Name already taken')).toBeInTheDocument()
  })
})
