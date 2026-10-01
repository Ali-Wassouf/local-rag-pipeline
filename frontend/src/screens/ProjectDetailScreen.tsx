import { useState } from 'react'

import type { DocumentRead } from '../api/types'
import {
  useAllDocuments,
  useAttachDocument,
  useDetachDocument,
  useProject,
  useProjectDocuments,
  useRenameProject,
  useSummarizeDocument,
} from '../api/hooks'

// generate_summary=true only means summarization ran, not that it produced
// anything — a document whose sections are all shorter than the threshold
// (docs/plan.md §8) ends up with zero real summaries despite opting in.
// Surfacing the real counts is what lets someone tell that apart from
// "has real summaries", instead of both looking identical in the UI.
function summaryStatusText(doc: DocumentRead): string | null {
  if (doc.section_count === 0) return null
  if (!doc.generate_summary) return 'Not summarized'
  if (doc.summary_count === 0) {
    return `0 of ${doc.section_count} sections summarized — none were long enough to qualify`
  }
  return `${doc.summary_count} of ${doc.section_count} sections summarized`
}

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
  const summarizeDocument = useSummarizeDocument(projectId)
  const renameProject = useRenameProject(projectId)
  const [selectedDocumentId, setSelectedDocumentId] = useState('')
  const [isRenaming, setIsRenaming] = useState(false)
  const [draftName, setDraftName] = useState('')

  const attachedIds = new Set((projectDocuments.data ?? []).map((d) => d.id))
  const attachableDocuments = (allDocuments.data ?? []).filter((d) => !attachedIds.has(d.id))

  function handleAttach() {
    if (!selectedDocumentId) return
    attachDocument.mutate(Number(selectedDocumentId), {
      onSuccess: () => setSelectedDocumentId(''),
    })
  }

  function startRenaming() {
    setDraftName(project.data?.name ?? '')
    setIsRenaming(true)
  }

  function handleRenameSubmit() {
    const trimmed = draftName.trim()
    if (!trimmed) return
    renameProject.mutate(trimmed, {
      onSuccess: () => setIsRenaming(false),
    })
  }

  return (
    <div className="mx-auto max-w-2xl p-8">
      <button type="button" onClick={onBack} className="mb-4 text-sm text-blue-600 hover:underline">
        &larr; Back to projects
      </button>

      <div className="flex items-center justify-between gap-3">
        {isRenaming ? (
          <div className="flex flex-1 items-center gap-2">
            <label htmlFor="rename-project-input" className="sr-only">
              Project name
            </label>
            <input
              id="rename-project-input"
              type="text"
              value={draftName}
              onChange={(event) => setDraftName(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') handleRenameSubmit()
                if (event.key === 'Escape') setIsRenaming(false)
              }}
              autoFocus
              className="flex-1 rounded-md border border-gray-300 px-2 py-1 text-2xl font-semibold text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
            />
            <button
              type="button"
              onClick={handleRenameSubmit}
              disabled={renameProject.isPending || !draftName.trim()}
              className="text-sm text-blue-600 hover:underline disabled:opacity-50"
            >
              Save
            </button>
            <button
              type="button"
              onClick={() => setIsRenaming(false)}
              className="text-sm text-gray-500 hover:underline"
            >
              Cancel
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
              {project.data?.name ?? '…'}
            </h1>
            <button
              type="button"
              onClick={startRenaming}
              className="text-sm text-blue-600 hover:underline"
            >
              Rename
            </button>
          </div>
        )}
        <button
          type="button"
          onClick={onOpenChat}
          className="shrink-0 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Chat
        </button>
      </div>
      {renameProject.isError && (
        <p className="mt-1 text-sm text-red-600">{(renameProject.error as Error).message}</p>
      )}

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
        {(projectDocuments.data ?? []).map((doc) => {
          const isSummarizingThis =
            summarizeDocument.isPending && summarizeDocument.variables === doc.id
          const summarizeFailedForThis =
            summarizeDocument.isError && summarizeDocument.variables === doc.id
          return (
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
                {summaryStatusText(doc) && (
                  <p className="text-xs text-gray-500">{summaryStatusText(doc)}</p>
                )}
                {summarizeFailedForThis && (
                  <p className="text-xs text-red-600">
                    {(summarizeDocument.error as Error).message}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-3">
                {!doc.generate_summary && doc.status === 'ready' && (
                  <button
                    type="button"
                    onClick={() => summarizeDocument.mutate(doc.id)}
                    disabled={isSummarizingThis}
                    className="text-sm text-blue-600 hover:underline disabled:opacity-50"
                  >
                    {isSummarizingThis ? 'Starting…' : 'Generate summary'}
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => detachDocument.mutate(doc.id)}
                  className="text-sm text-red-600 hover:underline"
                >
                  Remove
                </button>
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
