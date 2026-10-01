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
    <div className="mt-4 rounded-md border border-gray-200 p-3 dark:border-gray-700">
      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{file.name}</p>

      {upload.isError && (
        <p className="mt-1 text-sm text-red-600">{(upload.error as Error).message}</p>
      )}

      {jobId !== null && job.isError && (
        <p className="mt-1 text-sm text-red-600">
          Couldn&rsquo;t check on the job&rsquo;s progress: {(job.error as Error).message}
        </p>
      )}

      {upload.data?.deduped && (
        <p className="mt-1 text-sm text-gray-500">
          Already ingested as "{upload.data.document.title}" — no new job started.
        </p>
      )}

      {jobId !== null && job.data && (
        <div className="mt-2">
          <p className="text-sm text-gray-700 dark:text-gray-300">
            Job #{jobId} — stage: <strong>{job.data.stage}</strong>
          </p>
          <div className="mt-2 h-2 w-full overflow-hidden rounded bg-gray-200 dark:bg-gray-700">
            <div
              className="h-full bg-blue-600 transition-all"
              style={{
                width: `${Math.min(
                  100,
                  ((stageIndex >= 0 ? stageIndex : 0) / (STAGES.length - 1)) * 100 +
                    job.data.progress * (100 / (STAGES.length - 1)),
                )}%`,
              }}
            />
          </div>
          {job.data.error && <p className="mt-2 text-sm text-red-600">{job.data.error}</p>}
          {job.data.stage === 'done' && upload.data && (
            <div className="mt-2 flex items-center gap-3">
              <p className="text-sm text-green-600">Done.</p>
              <button
                type="button"
                onClick={() => onReviewDocument(upload.data.document.id)}
                className="text-sm text-blue-600 hover:underline"
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
    <div className="mx-auto max-w-xl p-8">
      {onBack && (
        <button
          type="button"
          onClick={onBack}
          className="mb-4 text-sm text-blue-600 hover:underline"
        >
          &larr; Back
        </button>
      )}
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
        Upload documents
      </h1>

      <div className="mt-4 flex items-start gap-2">
        <input
          id="generate-summary"
          type="checkbox"
          checked={generateSummary}
          onChange={(event) => setGenerateSummary(event.target.checked)}
          disabled={selectedFiles.length > 0}
          className="mt-0.5"
        />
        <label htmlFor="generate-summary" className="text-sm text-gray-700 dark:text-gray-300">
          Generate a summary for these documents
        </label>
      </div>
      <p className="mt-2 rounded-md bg-blue-50 p-3 text-xs text-blue-800 dark:bg-blue-950 dark:text-blue-200">
        Generating a summary takes extra time and compute — it runs one AI generation call for
        every long section once a document finishes indexing. You can leave this unchecked and
        generate a summary for a document later from its project page.
      </p>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf,.docx,.pptx,.txt,.md"
        onChange={handleFilesChange}
        className="hidden"
      />
      <div className="mt-4 flex items-center gap-3">
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Choose files
        </button>
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
