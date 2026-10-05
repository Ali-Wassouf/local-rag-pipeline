export type DocFormat = 'pdf' | 'docx' | 'pptx' | 'txt' | 'md' | 'epub'

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
  generate_summary: boolean
  section_count: number
  summary_count: number
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

export type StructureSource = 'detected' | 'manual'

export interface SectionRead {
  id: number
  document_id: number
  path: string
  title: string
  display_path: string
  depth: number
  ordinal: number
  char_start: number
  char_end: number
  source: StructureSource
  preview: string
  estimated_chunks: number
}

export interface ProjectRead {
  id: number
  name: string
  description: string | null
  created_at: string
}

export interface ConversationRead {
  id: number
  project_id: number
  title: string | null
  created_at: string
}

export interface CitationRead {
  chunk_id: number | null
  rank: number
  document_title: string
  display_path: string
  is_summary: boolean
  text: string
}

export type ChatMode = 'lookup' | 'survey'

export type MessageRole = 'user' | 'assistant'

export interface MessageRead {
  id: number
  conversation_id: number
  role: MessageRole
  content: string
  created_at: string
  citations: CitationRead[]
}
