import { useEffect, useRef, useState } from 'react'

import { useJob, useUploadDocument } from '../api/hooks'

const STAGES = ['extract', 'structure', 'chunk', 'embed', 'summarise', 'done']

interface UploadScreenProps {
  onReviewDocument: (documentId: number) => void
  projectId?: number
  onBack?: () => void
}

interface FileUploadRowProps {
  file: File
  projectId?: number
  generateSummary: boolean
  onReviewDocument: (documentId: number) => void
}

// Each selected file gets its own upload + job-polling lifecycle, entirely
// independent of its siblings — one failing or deduping never blocks or
// clears the others (mirrors ChapterRow's per-item hook pattern).
function FileUploadRow({ file, projectId, generateSummary, onReviewDocument }: FileUploadRowProps) {
  const upload = useUploadDocument()
  const [jobId, setJobId] = useState<number | null>(null)
  const job = useJob(jobId)
  const hasStarted = useRef(false)

  useEffect(() => {
    if (hasStarted.current) return
    hasStarted.current = true
    upload.mutate(
      { file, projectId, generateSummary },
      { onSuccess: (data) => setJobId(data.job_id) },
    )
    // generateSummary and projectId are captured at the moment this file was
    // selected — the checkbox is locked once a batch starts, so re-running
    // this effect on their account would never actually happen.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const stageIndex = job.data ? STAGES.indexOf(job.data.stage) : -1

  return (
    <div className="mt-4 rounded-md border border-rule bg-parchment p-4">
      <p className="font-serif text-sm text-ink">{file.name}</p>

      {upload.isError && <p className="mt-1 text-sm text-danger">{(upload.error as Error).message}</p>}

      {jobId !== null && job.isError && (
        <p className="mt-1 text-sm text-danger">
          Couldn&rsquo;t check on the job&rsquo;s progress: {(job.error as Error).message}
        </p>
      )}

      {upload.data?.deduped && (
        <p className="mt-1 text-sm text-ink-muted italic">
          Already ingested as &ldquo;{upload.data.document.title}&rdquo; — no new job started.
        </p>
      )}

      {jobId !== null && job.data && (
        <div className="mt-2">
          <p className="font-mono text-xs tabular-nums text-ink-secondary">
            Job #{jobId} &middot; stage: <strong className="text-ink">{job.data.stage}</strong>
          </p>
          <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-stone">
            <div
              className="h-full bg-accent transition-all"
              style={{
                width: `${Math.min(
                  100,
                  ((stageIndex >= 0 ? stageIndex : 0) / (STAGES.length - 1)) * 100 +
                    job.data.progress * (100 / (STAGES.length - 1)),
                )}%`,
              }}
            />
          </div>
          {job.data.error && <p className="mt-2 text-sm text-danger">{job.data.error}</p>}
          {job.data.stage === 'done' && upload.data && (
            <div className="mt-2 flex items-center gap-3">
              <p className="text-sm font-medium text-status-ready">Done.</p>
              <button
                type="button"
                onClick={() => onReviewDocument(upload.data.document.id)}
                className="cursor-pointer text-sm font-medium text-accent underline-offset-4 hover:underline"
              >
                Review structure
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function UploadScreen({ onReviewDocument, projectId, onBack }: UploadScreenProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [generateSummary, setGenerateSummary] = useState(true)
  const fileInputRef = useRef<HTMLInputElement>(null)

  function handleFilesChange(event: React.ChangeEvent<HTMLInputElement>) {
    const chosen = Array.from(event.target.files ?? [])
    if (chosen.length === 0) return
    // Picking more files while an earlier batch is still processing adds to
    // the list rather than replacing it — losing track of in-flight uploads
    // would be worse than a longer list.
    setSelectedFiles((prev) => [...prev, ...chosen])
    event.target.value = ''
  }

  return (
    <div className="mx-auto max-w-xl px-6 py-10">
      {onBack && (
        <button
          type="button"
          onClick={onBack}
          className="mb-4 cursor-pointer text-xs font-medium text-ink-secondary transition-colors hover:text-ink"
        >
          &larr; Back
        </button>
      )}
      <h1 className="font-serif text-3xl font-normal tracking-tight text-ink">
        Upload documents
      </h1>

      <div className="mt-5 flex items-start gap-2">
        <input
          id="generate-summary"
          type="checkbox"
          checked={generateSummary}
          onChange={(event) => setGenerateSummary(event.target.checked)}
          disabled={selectedFiles.length > 0}
          className="mt-0.5 accent-accent"
        />
        <label htmlFor="generate-summary" className="text-sm text-ink-secondary">
          Generate a summary for these documents
        </label>
      </div>
      <p className="mt-2 rounded-md border border-rule bg-parchment p-3 text-xs text-ink-secondary">
        Generating a summary takes extra time and compute — it runs one AI generation call for
        every long section once a document finishes indexing. You can leave this unchecked and
        generate a summary for a document later from its project page.
      </p>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf,.docx,.pptx,.txt,.md,.epub"
        onChange={handleFilesChange}
        className="hidden"
      />
      <div className="mt-4 flex items-center gap-3">
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="cursor-pointer rounded-md bg-accent px-4 py-2 text-xs font-semibold text-paper transition-colors hover:bg-accent-hover"
        >
          Choose Files…
        </button>
        <span className="font-mono text-xs text-ink-muted">PDF &middot; DOCX &middot; PPTX &middot; TXT &middot; EPUB</span>
      </div>

      {selectedFiles.map((file, index) => (
        <FileUploadRow
          key={`${file.name}-${index}`}
          file={file}
          projectId={projectId}
          generateSummary={generateSummary}
          onReviewDocument={onReviewDocument}
        />
      ))}
    </div>
  )
}
