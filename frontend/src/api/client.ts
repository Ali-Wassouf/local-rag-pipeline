import type { DocumentRead, DocumentUploadResponse, JobRead, ProjectRead, SectionRead } from './types'

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
): Promise<DocumentUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  if (projectId !== undefined) {
    formData.append('project_id', String(projectId))
  }
  const response = await fetch(`${API_BASE_URL}/documents`, {
    method: 'POST',
    body: formData,
  })
  return parseOrThrow<DocumentUploadResponse>(response)
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
