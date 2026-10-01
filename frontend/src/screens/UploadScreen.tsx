import { useRef, useState } from 'react'

import { useJob, useUploadDocument } from '../api/hooks'

const STAGES = ['extract', 'structure', 'chunk', 'embed', 'summarise', 'done']

interface UploadScreenProps {
  onReviewDocument: (documentId: number) => void
  projectId?: number
  onBack?: () => void
}

export function UploadScreen({ onReviewDocument, projectId, onBack }: UploadScreenProps) {
  const [jobId, setJobId] = useState<number | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)
  const [generateSummary, setGenerateSummary] = useState(true)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const upload = useUploadDocument()
  const job = useJob(jobId)

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return
    setFileName(file.name)
    upload.mutate(
      { file, projectId, generateSummary },
      {
        onSuccess: (data) => setJobId(data.job_id),
      },
    )
  }

  const stageIndex = job.data ? STAGES.indexOf(job.data.stage) : -1

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
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Upload a document</h1>

      <div className="mt-4 flex items-start gap-2">
        <input
          id="generate-summary"
          type="checkbox"
          checked={generateSummary}
          onChange={(event) => setGenerateSummary(event.target.checked)}
          disabled={upload.isPending}
          className="mt-0.5"
        />
        <label htmlFor="generate-summary" className="text-sm text-gray-700 dark:text-gray-300">
          Generate a summary for this document
        </label>
      </div>
      <p className="mt-2 rounded-md bg-blue-50 p-3 text-xs text-blue-800 dark:bg-blue-950 dark:text-blue-200">
        Generating a summary takes extra time and compute — it runs one AI generation call for
        every long section once the document finishes indexing. You can leave this unchecked and
        generate a summary for the document later from its project page.
      </p>

      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,.pptx,.txt,.md"
        onChange={handleFileChange}
        disabled={upload.isPending}
        className="hidden"
      />
      <div className="mt-4 flex items-center gap-3">
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={upload.isPending}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {upload.isPending ? 'Uploading…' : 'Choose file'}
        </button>
        {fileName && <span className="text-sm text-gray-500">{fileName}</span>}
      </div>

      {upload.isError && (
        <p className="mt-4 text-sm text-red-600">{(upload.error as Error).message}</p>
      )}

      {upload.data?.deduped && (
        <p className="mt-4 text-sm text-gray-500">
          Already ingested as "{upload.data.document.title}" — no new job started.
        </p>
      )}

      {jobId !== null && job.data && (
        <div className="mt-6">
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
