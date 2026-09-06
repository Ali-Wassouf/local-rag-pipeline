import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { getJob, uploadDocument } from './client'

export function useUploadDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: uploadDocument,
    onSuccess: (data) => {
      if (data.job_id !== null) {
        queryClient.invalidateQueries({ queryKey: ['job', data.job_id] })
      }
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
