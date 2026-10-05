import { useState } from 'react'

import { useCreateProject, useDeleteProject, useProjects } from '../api/hooks'

interface ProjectsListScreenProps {
  onSelectProject: (projectId: number) => void
  onOpenChat: (projectId: number) => void
  onUploadStandalone: () => void
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
}

export function ProjectsListScreen({
  onSelectProject,
  onOpenChat,
  onUploadStandalone,
}: ProjectsListScreenProps) {
  const projects = useProjects()
  const createProject = useCreateProject()
  const deleteProject = useDeleteProject()
  const [name, setName] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [deletingProjectId, setDeletingProjectId] = useState<number | null>(null)

  function handleCreate() {
    const trimmed = name.trim()
    if (!trimmed) return
    createProject.mutate(trimmed, {
      onSuccess: () => setName(''),
    })
  }

  function confirmDelete(projectId: number) {
    deleteProject.mutate(projectId, {
      onSuccess: () => setDeletingProjectId(null),
    })
  }

  const allProjects = projects.data ?? []
  const filteredProjects = allProjects.filter((project) =>
    project.name.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  return (
    <div className="mx-auto max-w-[1140px] px-6 py-10 md:py-12">
      <div className="flex flex-col gap-6 border-b border-rule pb-8 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="font-serif text-3xl font-normal tracking-tight text-ink md:text-4xl">
            Projects &amp; Reading Rooms
          </h1>
          <p className="mt-2 text-sm text-ink-secondary">
            Organize local PDF, DOCX, PPTX, TXT, and EPUB corpora into dedicated RAG workspaces.
          </p>
        </div>

        <div className="relative w-full md:w-72">
          <input
            type="text"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Filter projects…"
            className="w-full rounded-md border border-rule-strong bg-parchment px-4 py-2 text-sm text-ink placeholder-ink-muted transition-colors focus:border-accent focus:outline-none"
          />
        </div>
      </div>

      <section
        aria-label="Create new project"
        className="my-8 rounded-md border border-rule bg-parchment p-5 md:p-6"
      >
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-sans text-base font-semibold text-ink">
            Initialize a New Reading Project
          </h2>
          <span className="font-mono text-xs tabular-nums text-ink-muted">
            {allProjects.length} Active {allProjects.length === 1 ? 'Project' : 'Projects'}
          </span>
        </div>

        <div className="flex flex-col gap-3 md:flex-row">
          <label htmlFor="project-name-input" className="sr-only">
            New project name
          </label>
          <input
            id="project-name-input"
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') handleCreate()
            }}
            placeholder="New project name (e.g., Distributed Consensus Papers)…"
            className="flex-1 rounded-md border border-rule-strong bg-paper px-3.5 py-2.5 text-sm text-ink placeholder-ink-muted focus:border-accent focus:outline-none"
          />
          <button
            type="button"
            onClick={handleCreate}
            disabled={createProject.isPending || !name.trim()}
            className="shrink-0 cursor-pointer rounded-md bg-accent px-5 py-2.5 text-xs font-semibold whitespace-nowrap text-paper transition-colors hover:bg-accent-hover disabled:pointer-events-none disabled:opacity-45"
          >
            Create
          </button>
        </div>

        {createProject.isError && (
          <p className="mt-2 text-sm text-danger">{(createProject.error as Error).message}</p>
        )}
      </section>

      {projects.isLoading && <p className="text-sm text-ink-muted">Loading…</p>}
      {projects.isError && (
        <p className="text-sm text-danger">{(projects.error as Error).message}</p>
      )}

      <section aria-label="Project list" className="mb-14">
        {filteredProjects.length === 0 && !projects.isLoading ? (
          <div className="border-t border-b border-rule py-12 text-center">
            <p className="font-serif text-lg text-ink-secondary">
              {allProjects.length === 0
                ? 'No projects yet — create one above to get started.'
                : `No projects match "${searchQuery}".`}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-rule border-t border-b border-rule">
            {filteredProjects.map((project) => (
              <article key={project.id} className="py-6">
                <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2 font-mono text-xs tabular-nums text-ink-muted">
                      <span>Created {formatDate(project.created_at)}</span>
                    </div>
                    <h3 className="font-serif text-2xl font-normal text-ink">
                      <button
                        type="button"
                        onClick={() => onSelectProject(project.id)}
                        className="cursor-pointer text-left hover:text-accent focus:outline-none"
                      >
                        {project.name}
                      </button>
                    </h3>
                  </div>

                  <div className="flex shrink-0 items-center gap-2.5">
                    <button
                      type="button"
                      onClick={() => onSelectProject(project.id)}
                      className="cursor-pointer rounded-md border border-rule-strong bg-parchment px-3.5 py-2 text-xs font-medium whitespace-nowrap text-ink transition-colors hover:bg-stone"
                    >
                      Manage Corpus
                    </button>
                    <button
                      type="button"
                      onClick={() => onOpenChat(project.id)}
                      className="cursor-pointer rounded-md bg-accent px-4 py-2 text-xs font-semibold whitespace-nowrap text-paper transition-colors hover:bg-accent-hover"
                    >
                      Open Reading Room
                    </button>
                    <button
                      type="button"
                      onClick={() => setDeletingProjectId(project.id)}
                      className="cursor-pointer rounded-md px-3 py-2 text-xs font-medium whitespace-nowrap text-danger transition-colors hover:bg-danger/10"
                    >
                      Delete…
                    </button>
                  </div>
                </div>

                {deletingProjectId === project.id && (
                  <div className="mt-4 rounded-md border border-danger/30 bg-danger/5 p-3.5">
                    <p className="text-xs text-ink-secondary">
                      Delete &ldquo;{project.name}&rdquo;? Its chapters and chat history will be
                      lost. Its documents are not affected — they stay in your library and in
                      any other project they&rsquo;re attached to. This cannot be undone.
                    </p>
                    <div className="mt-2 flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => confirmDelete(project.id)}
                        disabled={deleteProject.isPending}
                        className="cursor-pointer rounded-md bg-danger px-3 py-1.5 text-xs font-medium text-paper disabled:opacity-50"
                      >
                        {deleteProject.isPending ? 'Deleting…' : 'Delete project'}
                      </button>
                      <button
                        type="button"
                        onClick={() => setDeletingProjectId(null)}
                        className="cursor-pointer text-xs text-ink-secondary hover:text-ink"
                      >
                        Cancel
                      </button>
                    </div>
                    {deleteProject.isError && deleteProject.variables === project.id && (
                      <p className="mt-2 text-xs text-danger">
                        {(deleteProject.error as Error).message}
                      </p>
                    )}
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </section>

      <section
        aria-label="Standalone document upload"
        className="rounded-md border border-rule bg-parchment p-6 md:p-8"
      >
        <div className="flex flex-col items-start justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h2 className="font-serif text-xl font-normal text-ink">
              Upload a Document Without a Project
            </h2>
            <p className="mt-1 text-xs text-ink-secondary">
              Pre-index standalone PDF, DOCX, PPTX, TXT, or EPUB files and attach them to a project
              later.
            </p>
          </div>
          <button
            type="button"
            onClick={onUploadStandalone}
            className="shrink-0 cursor-pointer rounded-md border border-rule-strong bg-paper px-4 py-2 text-xs font-semibold whitespace-nowrap text-ink transition-colors hover:bg-stone"
          >
            Upload Local Files…
          </button>
        </div>
      </section>
    </div>
  )
}
