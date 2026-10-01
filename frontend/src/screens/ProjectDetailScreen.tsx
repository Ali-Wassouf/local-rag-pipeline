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

  const documents = projectDocuments.data ?? []
  const attachedIds = new Set(documents.map((d) => d.id))
  const attachableDocuments = (allDocuments.data ?? []).filter((d) => !attachedIds.has(d.id))
  const totalSections = documents.reduce((acc, d) => acc + d.section_count, 0)
  const summarizedSections = documents.reduce((acc, d) => acc + d.summary_count, 0)

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
    <div className="mx-auto max-w-[1040px] px-6 py-10">
      <button
        type="button"
        onClick={onBack}
        className="cursor-pointer text-xs font-medium text-ink-secondary transition-colors hover:text-ink"
      >
        &larr; Back to projects
      </button>

      <header className="flex flex-col justify-between gap-6 border-b border-rule pt-5 pb-8 md:flex-row md:items-start">
        <div className="flex-1 space-y-2">
          {isRenaming ? (
            <div className="flex max-w-xl items-center gap-2">
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
                className="flex-1 rounded-md border border-accent bg-parchment px-3 py-1.5 font-serif text-2xl text-ink focus:outline-none"
              />
              <button
                type="button"
                onClick={handleRenameSubmit}
                disabled={renameProject.isPending || !draftName.trim()}
                className="cursor-pointer rounded-md bg-accent px-3 py-2 text-xs font-semibold text-paper disabled:opacity-50"
              >
                Save
              </button>
              <button
                type="button"
                onClick={() => setIsRenaming(false)}
                className="cursor-pointer p-2 text-xs text-ink-secondary hover:text-ink"
              >
                Cancel
              </button>
            </div>
          ) : (
            <div className="flex flex-wrap items-baseline gap-3">
              <h1 className="text-3xl font-normal tracking-tight text-ink md:text-4xl">
                {project.data?.name ?? '…'}
              </h1>
              <button
                type="button"
                onClick={startRenaming}
                className="cursor-pointer text-xs font-medium text-accent underline-offset-4 hover:underline"
              >
                Rename
              </button>
            </div>
          )}
          {(renameProject.isError || project.isError) && (
            <p className="text-sm text-danger">
              {((renameProject.error ?? project.error) as Error).message}
            </p>
          )}

          <div className="flex flex-wrap items-center gap-2 pt-1 font-mono text-xs tabular-nums text-ink-muted">
            <span>
              {documents.length} {documents.length === 1 ? 'Document' : 'Documents'} Attached
            </span>
            {totalSections > 0 && (
              <>
                <span aria-hidden="true">&middot;</span>
                <span>
                  {summarizedSections} of {totalSections} Total Sections Summarized
                </span>
              </>
            )}
          </div>
        </div>

        <button
          type="button"
          onClick={onOpenChat}
          className="shrink-0 cursor-pointer rounded-md bg-accent px-5 py-2.5 text-sm font-semibold whitespace-nowrap text-paper transition-colors hover:bg-accent-hover"
        >
          Chat with Corpus
        </button>
      </header>

      <section
        aria-label="Document ingestion controls"
        className="my-8 grid grid-cols-1 gap-6 lg:grid-cols-2"
      >
        <div className="flex flex-col justify-between rounded-md border border-rule bg-parchment p-5">
          <div>
            <h2 className="mb-1 font-sans text-sm font-semibold text-ink">
              Attach an Existing Document
            </h2>
            <p className="mb-4 text-xs text-ink-secondary">
              Link a document already indexed elsewhere, without duplicating its embeddings.
            </p>
          </div>
          <div className="flex items-center gap-2.5">
            <label htmlFor="attach-document-select" className="sr-only">
              Attach an existing document
            </label>
            <select
              id="attach-document-select"
              aria-label="Attach an existing document"
              value={selectedDocumentId}
              onChange={(event) => setSelectedDocumentId(event.target.value)}
              className="min-w-0 flex-1 rounded-md border border-rule-strong bg-paper px-3.5 py-2.5 text-sm text-ink focus:border-accent focus:outline-none"
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
              className="shrink-0 cursor-pointer rounded-md border border-rule-strong bg-paper px-4 py-2.5 text-xs font-semibold whitespace-nowrap text-ink transition-colors hover:bg-stone disabled:pointer-events-none disabled:opacity-45"
            >
              Attach
            </button>
          </div>
          {(attachDocument.isError || allDocuments.isError) && (
            <p className="mt-2 text-sm text-danger">
              {((attachDocument.error ?? allDocuments.error) as Error).message}
            </p>
          )}
        </div>

        <div className="flex flex-col justify-between rounded-md border border-dashed border-rule-strong bg-parchment p-5">
          <div className="flex items-center justify-between gap-2">
            <h2 className="font-sans text-sm font-semibold text-ink">
              Upload New Documents Into This Project
            </h2>
            <span className="font-mono text-xs text-ink-muted">PDF &middot; DOCX &middot; PPTX &middot; TXT</span>
          </div>
          <p className="mb-4 text-xs text-ink-secondary">
            Local parsing chunks headings, slides, and paragraphs for Lookup and Survey
            synthesis.
          </p>
          <div>
            <button
              type="button"
              onClick={onUploadHere}
              className="cursor-pointer rounded-md bg-ink px-4 py-2 text-xs font-semibold text-paper transition-colors hover:bg-ink/85"
            >
              Upload Local Files…
            </button>
          </div>
        </div>
      </section>

      <section aria-label="Attached documents">
        <div className="flex items-center justify-between border-b border-rule pb-3">
          <h2 className="text-lg font-normal text-ink">
            Attached Project Documents ({documents.length})
          </h2>
        </div>

        {projectDocuments.isLoading && <p className="py-4 text-sm text-ink-muted">Loading…</p>}
        {(projectDocuments.isError || detachDocument.isError) && (
          <p className="py-2 text-sm text-danger">
            {((projectDocuments.error ?? detachDocument.error) as Error).message}
          </p>
        )}

        {!projectDocuments.isLoading && documents.length === 0 ? (
          <div className="border-b border-rule py-12 text-center">
            <p className="font-serif text-lg text-ink-secondary">
              No documents attached to this project yet.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-rule border-b border-rule">
            {documents.map((doc) => {
              const isSummarizingThis =
                summarizeDocument.isPending && summarizeDocument.variables === doc.id
              const summarizeFailedForThis =
                summarizeDocument.isError && summarizeDocument.variables === doc.id
              const isReindexingThis =
                reindexDocument.isPending && reindexDocument.variables === doc.id
              const reindexFailedForThis =
                reindexDocument.isError && reindexDocument.variables === doc.id
              const isDeletingThis = deleteDocument.isPending && deleteDocument.variables === doc.id
              const deleteFailedForThis =
                deleteDocument.isError && deleteDocument.variables === doc.id
              const isConfirmingDeleteForThis = deletingDocId === doc.id
              const pct =
                doc.section_count > 0
                  ? Math.round((doc.summary_count / doc.section_count) * 100)
                  : 0

              return (
                <article key={doc.id} className="py-5">
                  <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                    <div className="flex-1 space-y-1.5">
                      <button
                        type="button"
                        onClick={() => onReviewDocument(doc.id)}
                        className="cursor-pointer text-left font-serif text-xl text-ink transition-colors hover:text-accent focus:outline-none"
                      >
                        {doc.title}
                      </button>

                      <div className="flex flex-wrap items-center gap-2 font-mono text-xs tabular-nums text-ink-secondary">
                        <span className="font-semibold text-accent">
                          {doc.format.toUpperCase()}
                        </span>
                        <span aria-hidden="true">&middot;</span>
                        <span className="text-status-ready">{doc.status}</span>
                        {summaryStatusText(doc) && (
                          <>
                            <span aria-hidden="true">&middot;</span>
                            <span>{summaryStatusText(doc)}</span>
                          </>
                        )}
                      </div>

                      {(doc.section_count > 0 || !doc.generate_summary) && (
                        <div className="flex items-center gap-3 pt-1">
                          {doc.section_count > 0 && (
                            <div className="h-1.5 w-40 overflow-hidden rounded-full bg-stone">
                              <div
                                className="h-full bg-accent transition-all duration-300"
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                          )}
                          {!doc.generate_summary && doc.status === 'ready' && (
                            <button
                              type="button"
                              onClick={() => summarizeDocument.mutate(doc.id)}
                              disabled={isSummarizingThis}
                              className="cursor-pointer text-xs font-medium text-accent underline-offset-4 hover:underline disabled:opacity-50"
                            >
                              {isSummarizingThis ? 'Starting…' : 'Generate summary'}
                            </button>
                          )}
                        </div>
                      )}

                      {summarizeFailedForThis && (
                        <p className="text-xs text-danger">
                          {(summarizeDocument.error as Error).message}
                        </p>
                      )}
                      {reindexFailedForThis && (
                        <p className="text-xs text-danger">
                          {(reindexDocument.error as Error).message}
                        </p>
                      )}
                      {deleteFailedForThis && (
                        <p className="text-xs text-danger">
                          {(deleteDocument.error as Error).message}
                        </p>
                      )}
                    </div>

                    <div className="flex shrink-0 items-center gap-3">
                      <button
                        type="button"
                        onClick={() => reindexDocument.mutate(doc.id)}
                        disabled={isReindexingThis || IN_PROGRESS_STATUSES.has(doc.status)}
                        className="cursor-pointer rounded-md border border-rule-strong bg-parchment px-3 py-1.5 text-xs font-medium whitespace-nowrap text-ink transition-colors hover:bg-stone disabled:pointer-events-none disabled:opacity-45"
                      >
                        {isReindexingThis ? 'Starting…' : 'Re-index'}
                      </button>
                      <button
                        type="button"
                        onClick={() => startDeleting(doc)}
                        className="cursor-pointer rounded-md px-3 py-1.5 text-xs font-medium whitespace-nowrap text-danger transition-colors hover:bg-danger/10"
                      >
                        Delete…
                      </button>
                      <button
                        type="button"
                        onClick={() => detachDocument.mutate(doc.id)}
                        className="cursor-pointer rounded-md px-3 py-1.5 text-xs font-medium whitespace-nowrap text-danger transition-colors hover:bg-danger/10"
                      >
                        Remove
                      </button>
                    </div>
                  </div>

                  {isConfirmingDeleteForThis && (
                    <div className="mt-4 rounded-md border border-danger/30 bg-danger/5 p-3.5">
                      <p className="text-xs text-ink-secondary">
                        This permanently deletes &ldquo;{doc.title}&rdquo; and all of its data —
                        sections, chunks, summaries — from every project it&rsquo;s in, not just
                        this one. This cannot be undone. Type the document&rsquo;s title to
                        confirm.
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
                          className="flex-1 rounded-md border border-rule-strong bg-paper px-2 py-1 text-sm text-ink focus:border-accent focus:outline-none"
                        />
                        <button
                          type="button"
                          onClick={() => confirmDelete(doc)}
                          disabled={deleteConfirmText !== doc.title || isDeletingThis}
                          className="shrink-0 cursor-pointer rounded-md bg-danger px-3 py-1 text-sm font-medium text-paper disabled:opacity-50"
                        >
                          {isDeletingThis ? 'Deleting…' : 'Delete permanently'}
                        </button>
                        <button
                          type="button"
                          onClick={cancelDeleting}
                          className="shrink-0 cursor-pointer text-sm text-ink-secondary hover:text-ink"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                </article>
              )
            })}
          </div>
        )}
      </section>
    </div>
  )
}
