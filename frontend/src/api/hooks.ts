import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  attachDocumentToProject,
  createConversation,
  createProject,
  deleteConversation,
  deleteDocument,
  deleteProject,
  detachDocumentFromProject,
  getJob,
  getProject,
  getSections,
  listAllDocuments,
  listConversations,
  listDeletedConversations,
  listMessages,
  listProjectDocuments,
  listProjects,
  reindexDocument,
  renameProject,
  restoreConversation,
  summarizeDocument,
  updateSectionTitle,
  uploadDocument,
} from './client'

export function useUploadDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      file,
      projectId,
      generateSummary,
    }: {
      file: File
      projectId?: number
      generateSummary?: boolean
    }) => uploadDocument(file, projectId, generateSummary),
    onSuccess: (data, variables) => {
      if (data.job_id !== null) {
        queryClient.invalidateQueries({ queryKey: ['job', data.job_id] })
      }
      if (variables.projectId !== undefined) {
        queryClient.invalidateQueries({ queryKey: ['project-documents', variables.projectId] })
      }
    },
  })
}

export function useSummarizeDocument(projectId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (documentId: number) => summarizeDocument(documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project-documents', projectId] })
    },
  })
}

const TERMINAL_STAGE = 'done'

export function useJob(jobId: number | null) {
  return useQuery({
    queryKey: ['job', jobId],
    queryFn: () => getJob(jobId as number),
    enabled: jobId !== null,
    refetchInterval: (query) => {
      const job = query.state.data
      if (!job || job.error || job.stage === TERMINAL_STAGE) return false
      return 1000
    },
  })
}

export function useSections(documentId: number | null) {
  return useQuery({
    queryKey: ['sections', documentId],
    queryFn: () => getSections(documentId as number),
    enabled: documentId !== null,
  })
}

export function useUpdateSectionTitle(documentId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ sectionId, title }: { sectionId: number; title: string }) =>
      updateSectionTitle(sectionId, title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sections', documentId] })
    },
  })
}

export function useProjects() {
  return useQuery({ queryKey: ['projects'], queryFn: listProjects })
}

export function useCreateProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => createProject(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export function useDeleteProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (projectId: number) => deleteProject(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export function useProject(projectId: number | null) {
  return useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProject(projectId as number),
    enabled: projectId !== null,
  })
}

export function useRenameProject(projectId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => renameProject(projectId, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export function useProjectDocuments(projectId: number | null) {
  return useQuery({
    queryKey: ['project-documents', projectId],
    queryFn: () => listProjectDocuments(projectId as number),
    enabled: projectId !== null,
    // Summarizing runs one section at a time in the background (worker.py
    // — resumable, so the UI can show real "N of M" progress) — poll
    // while any document is mid-summary so that progress is actually
    // visible without the user having to refresh, and stop otherwise.
    refetchInterval: (query) => {
      const docs = query.state.data
      return docs?.some((doc) => doc.summarizing) ? 3000 : false
    },
  })
}

export function useAllDocuments() {
  return useQuery({ queryKey: ['all-documents'], queryFn: listAllDocuments })
}

export function useAttachDocument(projectId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (documentId: number) => attachDocumentToProject(projectId, documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project-documents', projectId] })
    },
  })
}

export function useDetachDocument(projectId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (documentId: number) => detachDocumentFromProject(projectId, documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project-documents', projectId] })
    },
  })
}

export function useDeleteDocument(projectId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (documentId: number) => deleteDocument(documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project-documents', projectId] })
      queryClient.invalidateQueries({ queryKey: ['all-documents'] })
    },
  })
}

export function useReindexDocument(projectId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (documentId: number) => reindexDocument(documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project-documents', projectId] })
      queryClient.invalidateQueries({ queryKey: ['all-documents'] })
    },
  })
}

export function useConversations(projectId: number | null) {
  return useQuery({
    queryKey: ['conversations', projectId],
    queryFn: () => listConversations(projectId as number),
    enabled: projectId !== null,
  })
}

export function useCreateConversation(projectId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => createConversation(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations', projectId] })
    },
  })
}

export function useDeletedConversations(projectId: number | null) {
  return useQuery({
    queryKey: ['deleted-conversations', projectId],
    queryFn: () => listDeletedConversations(projectId as number),
    enabled: projectId !== null,
  })
}

export function useDeleteConversation(projectId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (conversationId: number) => deleteConversation(conversationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations', projectId] })
      queryClient.invalidateQueries({ queryKey: ['deleted-conversations', projectId] })
    },
  })
}

export function useRestoreConversation(projectId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (conversationId: number) => restoreConversation(conversationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations', projectId] })
      queryClient.invalidateQueries({ queryKey: ['deleted-conversations', projectId] })
    },
  })
}

export function useMessages(conversationId: number | null) {
  return useQuery({
    queryKey: ['messages', conversationId],
    queryFn: () => listMessages(conversationId as number),
    enabled: conversationId !== null,
  })
}
