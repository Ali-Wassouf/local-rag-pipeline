import { useState } from 'react'

import { useCreateProject, useProjects } from '../api/hooks'

interface ProjectsListScreenProps {
  onSelectProject: (projectId: number) => void
  onUploadStandalone: () => void
}

export function ProjectsListScreen({
  onSelectProject,
  onUploadStandalone,
}: ProjectsListScreenProps) {
  const projects = useProjects()
  const createProject = useCreateProject()
  const [name, setName] = useState('')

  function handleCreate() {
    const trimmed = name.trim()
    if (!trimmed) return
    createProject.mutate(trimmed, {
      onSuccess: () => setName(''),
    })
  }

  return (
    <div className="mx-auto max-w-xl p-8">
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Projects</h1>

      <div className="mt-4 flex gap-2">
        <input
          type="text"
          placeholder="New project name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') handleCreate()
          }}
          className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm"
        />
        <button
          type="button"
          onClick={handleCreate}
          disabled={createProject.isPending}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          Create
        </button>
      </div>

      {projects.isLoading && <p className="mt-4 text-sm text-gray-500">Loading…</p>}

      <ul className="mt-6 space-y-1">
        {(projects.data ?? []).map((project) => (
          <li key={project.id}>
            <button
              type="button"
              onClick={() => onSelectProject(project.id)}
              className="w-full rounded px-3 py-2 text-left text-sm text-gray-900 hover:bg-gray-100 dark:text-gray-100 dark:hover:bg-gray-800"
            >
              {project.name}
            </button>
          </li>
        ))}
      </ul>

      <button
        type="button"
        onClick={onUploadStandalone}
        className="mt-6 text-sm text-blue-600 hover:underline"
      >
        Upload a document without a project
      </button>
    </div>
  )
}
