import { useState } from 'react'

import {
  useAllDocuments,
  useAttachDocument,
  useDetachDocument,
  useProject,
  useProjectDocuments,
} from '../api/hooks'

interface ProjectDetailScreenProps {
  projectId: number
  onReviewDocument: (documentId: number) => void
  onUploadHere: () => void
  onOpenChat: () => void
  onBack: () => void
}

export function ProjectDetailScreen({
  projectId,
  onReviewDocument,
  onUploadHere,
  onOpenChat,
  onBack,
}: ProjectDetailScreenProps) {
  const project = useProject(projectId)
  const projectDocuments = useProjectDocuments(projectId)
  const allDocuments = useAllDocuments()
  const attachDocument = useAttachDocument(projectId)
  const detachDocument = useDetachDocument(projectId)
  const [selectedDocumentId, setSelectedDocumentId] = useState('')

  const attachedIds = new Set((projectDocuments.data ?? []).map((d) => d.id))
  const attachableDocuments = (allDocuments.data ?? []).filter((d) => !attachedIds.has(d.id))

  function handleAttach() {
    if (!selectedDocumentId) return
    attachDocument.mutate(Number(selectedDocumentId), {
      onSuccess: () => setSelectedDocumentId(''),
    })
  }

  return (
    <div className="mx-auto max-w-2xl p-8">
      <button type="button" onClick={onBack} className="mb-4 text-sm text-blue-600 hover:underline">
        &larr; Back to projects
      </button>

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
          {project.data?.name ?? '…'}
        </h1>
        <button
          type="button"
          onClick={onOpenChat}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Chat
        </button>
      </div>

      <div className="mt-6 flex items-center gap-2">
        <label htmlFor="attach-document-select" className="sr-only">
          Attach an existing document
        </label>
        <select
          id="attach-document-select"
          aria-label="Attach an existing document"
          value={selectedDocumentId}
          onChange={(event) => setSelectedDocumentId(event.target.value)}
          className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">Attach an existing document…</option>
          {attachableDocuments.map((doc) => (
            <option key={doc.id} value={doc.id}>
              {doc.title}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={handleAttach}
          disabled={!selectedDocumentId || attachDocument.isPending}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          Attach
        </button>
      </div>

      <button
        type="button"
        onClick={onUploadHere}
        className="mt-3 text-sm text-blue-600 hover:underline"
      >
        Upload a new document into this project
      </button>

      {projectDocuments.isLoading && <p className="mt-4 text-sm text-gray-500">Loading…</p>}

      <ul className="mt-6 space-y-2">
        {(projectDocuments.data ?? []).map((doc) => (
          <li
            key={doc.id}
            className="flex items-center justify-between rounded border border-gray-200 px-3 py-2 dark:border-gray-700"
          >
            <div>
              <button
                type="button"
                onClick={() => onReviewDocument(doc.id)}
                className="text-sm font-medium text-gray-900 hover:underline dark:text-gray-100"
              >
                {doc.title}
              </button>
              <p className="text-xs text-gray-500">{doc.status}</p>
            </div>
            <button
              type="button"
              onClick={() => detachDocument.mutate(doc.id)}
              className="text-sm text-red-600 hover:underline"
            >
              Remove
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
