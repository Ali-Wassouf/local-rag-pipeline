export type DocFormat = 'pdf' | 'docx' | 'pptx' | 'txt' | 'md'

export type DocStatus =
  | 'uploaded'
  | 'extracting'
  | 'awaiting_review'
  | 'indexing'
  | 'ready'
  | 'failed'

export interface DocumentRead {
  id: number
  sha256: string
  title: string
  author: string | null
  format: DocFormat
  original_name: string
  status: DocStatus
  created_at: string
}

export interface DocumentUploadResponse {
  document: DocumentRead
  job_id: number | null
  deduped: boolean
}

export interface JobRead {
  id: number
  document_id: number
  stage: string
  progress: number
  error: string | null
  started_at: string | null
  finished_at: string | null
}
