import { useState } from 'react'

import type { DocumentRead } from '../api/types'
import {
  useAllDocuments,
  useAttachDocument,
  useDeleteDocument,
  useDetachDocument,
  useProject,
  useProjectDocuments,
  useReindexDocument,
  useRenameProject,
  useSummarizeDocument,
} from '../api/hooks'

// A document mid-pipeline already has a job running for it — a second
// reindex request would just 409.
const IN_PROGRESS_STATUSES = new Set(['uploaded', 'extracting', 'awaiting_review', 'indexing'])

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
  const reindexDocument = useReindexDocument(projectId)
  const deleteDocument = useDeleteDocument(projectId)
  const renameProject = useRenameProject(projectId)
  const [selectedDocumentId, setSelectedDocumentId] = useState('')
  const [isRenaming, setIsRenaming] = useState(false)
  const [draftName, setDraftName] = useState('')
  const [deletingDocId, setDeletingDocId] = useState<number | null>(null)
  const [deleteConfirmText, setDeleteConfirmText] = useState('')

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

  function startDeleting(doc: DocumentRead) {
    setDeletingDocId(doc.id)
    setDeleteConfirmText('')
  }

  function cancelDeleting() {
    setDeletingDocId(null)
    setDeleteConfirmText('')
  }

  function confirmDelete(doc: DocumentRead) {
    if (deleteConfirmText !== doc.title) return
    deleteDocument.mutate(doc.id, {
      onSuccess: () => setDeletingDocId(null),
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
          const isReindexingThis = reindexDocument.isPending && reindexDocument.variables === doc.id
          const reindexFailedForThis =
            reindexDocument.isError && reindexDocument.variables === doc.id
          const isDeletingThis = deleteDocument.isPending && deleteDocument.variables === doc.id
          const deleteFailedForThis =
            deleteDocument.isError && deleteDocument.variables === doc.id
          const isConfirmingDeleteForThis = deletingDocId === doc.id
          return (
            <li
              key={doc.id}
              className="flex flex-col gap-2 rounded border border-gray-200 px-3 py-2 dark:border-gray-700"
            >
              <div className="flex items-center justify-between">
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
                  {reindexFailedForThis && (
                    <p className="text-xs text-red-600">
                      {(reindexDocument.error as Error).message}
                    </p>
                  )}
                  {deleteFailedForThis && (
                    <p className="text-xs text-red-600">
                      {(deleteDocument.error as Error).message}
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
                    onClick={() => reindexDocument.mutate(doc.id)}
                    disabled={isReindexingThis || IN_PROGRESS_STATUSES.has(doc.status)}
                    className="text-sm text-blue-600 hover:underline disabled:opacity-50"
                  >
                    {isReindexingThis ? 'Starting…' : 'Re-index'}
                  </button>
                  <button
                    type="button"
                    onClick={() => startDeleting(doc)}
                    className="text-sm text-red-600 hover:underline"
                  >
                    Delete…
                  </button>
                  <button
                    type="button"
                    onClick={() => detachDocument.mutate(doc.id)}
                    className="text-sm text-red-600 hover:underline"
                  >
                    Remove
                  </button>
                </div>
              </div>
              {isConfirmingDeleteForThis && (
                <div className="rounded border border-red-200 bg-red-50 p-3 dark:border-red-900 dark:bg-red-950">
                  <p className="text-xs text-red-800 dark:text-red-200">
                    This permanently deletes &ldquo;{doc.title}&rdquo; and all of its data —
                    sections, chunks, summaries — from every project it&rsquo;s in, not just this
                    one. This cannot be undone. Type the document&rsquo;s title to confirm.
                  </p>
                  <div className="mt-2 flex items-center gap-2">
                    <label htmlFor={`delete-confirm-${doc.id}`} className="sr-only">
                      Type the document title to confirm deletion
                    </label>
                    <input
                      id={`delete-confirm-${doc.id}`}
                      type="text"
                      value={deleteConfirmText}
                      onChange={(event) => setDeleteConfirmText(event.target.value)}
                      placeholder={doc.title}
                      autoFocus
                      className="flex-1 rounded-md border border-gray-300 px-2 py-1 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
                    />
                    <button
                      type="button"
                      onClick={() => confirmDelete(doc)}
                      disabled={deleteConfirmText !== doc.title || isDeletingThis}
                      className="shrink-0 rounded-md bg-red-600 px-3 py-1 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
                    >
                      {isDeletingThis ? 'Deleting…' : 'Delete permanently'}
                    </button>
                    <button
                      type="button"
                      onClick={cancelDeleting}
                      className="shrink-0 text-sm text-gray-500 hover:underline"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </li>
          )
        })}
      </ul>
    </div>
  )
}
