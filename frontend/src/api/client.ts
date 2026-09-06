import type { DocumentUploadResponse, JobRead } from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function parseOrThrow<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.text()
    throw new Error(`${response.status} ${response.statusText}: ${body}`)
  }
  return (await response.json()) as T
}

export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
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
