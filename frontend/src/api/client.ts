import type {
  ChatMode,
  CitationRead,
  ConversationRead,
  DocumentRead,
  DocumentUploadResponse,
  JobRead,
  MessageRead,
  ProjectRead,
  SectionRead,
} from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function parseOrThrow<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.text()
    throw new Error(`${response.status} ${response.statusText}: ${body}`)
  }
  return (await response.json()) as T
}

async function okOrThrow(response: Response): Promise<void> {
  if (!response.ok) {
    const body = await response.text()
    throw new Error(`${response.status} ${response.statusText}: ${body}`)
  }
}

export async function uploadDocument(
  file: File,
  projectId?: number,
  generateSummary = true,
): Promise<DocumentUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  if (projectId !== undefined) {
    formData.append('project_id', String(projectId))
  }
  formData.append('generate_summary', String(generateSummary))
  const response = await fetch(`${API_BASE_URL}/documents`, {
    method: 'POST',
    body: formData,
  })
  return parseOrThrow<DocumentUploadResponse>(response)
}

export async function summarizeDocument(documentId: number): Promise<DocumentRead> {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/summarize`, {
    method: 'POST',
  })
  return parseOrThrow<DocumentRead>(response)
}

export async function getJob(jobId: number): Promise<JobRead> {
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`)
  return parseOrThrow<JobRead>(response)
}

export async function getSections(documentId: number): Promise<SectionRead[]> {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/sections`)
  return parseOrThrow<SectionRead[]>(response)
}

export async function updateSectionTitle(sectionId: number, title: string): Promise<SectionRead> {
  const response = await fetch(`${API_BASE_URL}/sections/${sectionId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  })
  return parseOrThrow<SectionRead>(response)
}

export async function listProjects(): Promise<ProjectRead[]> {
  const response = await fetch(`${API_BASE_URL}/projects`)
  return parseOrThrow<ProjectRead[]>(response)
}

export async function createProject(name: string): Promise<ProjectRead> {
  const response = await fetch(`${API_BASE_URL}/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  return parseOrThrow<ProjectRead>(response)
}

export async function getProject(projectId: number): Promise<ProjectRead> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}`)
  return parseOrThrow<ProjectRead>(response)
}

export async function renameProject(projectId: number, name: string): Promise<ProjectRead> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  return parseOrThrow<ProjectRead>(response)
}

export async function listProjectDocuments(projectId: number): Promise<DocumentRead[]> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/documents`)
  return parseOrThrow<DocumentRead[]>(response)
}

export async function listAllDocuments(): Promise<DocumentRead[]> {
  const response = await fetch(`${API_BASE_URL}/documents`)
  return parseOrThrow<DocumentRead[]>(response)
}

export async function attachDocumentToProject(
  projectId: number,
  documentId: number,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/documents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ document_id: documentId }),
  })
  await okOrThrow(response)
}

export async function detachDocumentFromProject(
  projectId: number,
  documentId: number,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/documents/${documentId}`, {
    method: 'DELETE',
  })
  await okOrThrow(response)
}

export async function createConversation(projectId: number): Promise<ConversationRead> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/conversations`, {
    method: 'POST',
  })
  return parseOrThrow<ConversationRead>(response)
}

export async function listConversations(projectId: number): Promise<ConversationRead[]> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/conversations`)
  return parseOrThrow<ConversationRead[]>(response)
}

export async function listMessages(conversationId: number): Promise<MessageRead[]> {
  const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages`)
  return parseOrThrow<MessageRead[]>(response)
}

export async function deleteConversation(conversationId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}`, {
    method: 'DELETE',
  })
  await okOrThrow(response)
}

export async function restoreConversation(conversationId: number): Promise<ConversationRead> {
  const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/restore`, {
    method: 'POST',
  })
  return parseOrThrow<ConversationRead>(response)
}

export async function listDeletedConversations(projectId: number): Promise<ConversationRead[]> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/conversations/deleted`)
  return parseOrThrow<ConversationRead[]>(response)
}

export interface SendMessageCallbacks {
  onToken: (token: string) => void
  onDone: (citations: CitationRead[]) => void
  onError: (message: string) => void
}

// The backend streams Server-Sent Events, but EventSource can't POST a
// body, so this parses the "data: {...}\n\n" wire format by hand over a
// plain fetch() ReadableStream.
export async function sendMessage(
  conversationId: number,
  content: string,
  callbacks: SendMessageCallbacks,
  mode: ChatMode = 'lookup',
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, mode }),
  })

  if (!response.ok || !response.body) {
    callbacks.onError(`${response.status} ${response.statusText}`)
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    let boundary = buffer.indexOf('\n\n')
    while (boundary !== -1) {
      const rawEvent = buffer.slice(0, boundary).trim()
      buffer = buffer.slice(boundary + 2)

      if (rawEvent.startsWith('data: ')) {
        const payload = JSON.parse(rawEvent.slice('data: '.length))
        if (payload.error) {
          callbacks.onError(payload.error)
        } else if (payload.done) {
          callbacks.onDone(payload.citations ?? [])
        } else if (typeof payload.token === 'string') {
          callbacks.onToken(payload.token)
        }
      }
      boundary = buffer.indexOf('\n\n')
    }
  }
}
