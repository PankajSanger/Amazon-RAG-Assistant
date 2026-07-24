import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import * as api from './client'
import type { CreateScrapeJobParams } from './types'

export function useStats() {
  return useQuery({ queryKey: ['stats'], queryFn: api.getStats })
}

export function useProducts() {
  return useQuery({ queryKey: ['products'], queryFn: api.getProducts })
}

export function useReviews() {
  return useQuery({ queryKey: ['reviews'], queryFn: api.getReviews })
}

export function useAskProducts() {
  return useMutation({ mutationFn: api.askProducts })
}

export function useAskReviews() {
  return useMutation({ mutationFn: api.askReviews })
}

export function useReindexProducts() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: api.reindexProducts,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['stats'] }),
  })
}

export function useReindexReviews() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: api.reindexReviews,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['stats'] }),
  })
}

export function useCreateScrapeJob() {
  return useMutation({
    mutationFn: (params: CreateScrapeJobParams) => api.createScrapeJob(params),
  })
}

export function useScrapeJobStatus(jobId: string | null) {
  return useQuery({
    queryKey: ['scrape-job', jobId],
    queryFn: () => api.getScrapeJob(jobId as string),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'done' || status === 'error' ? false : 1500
    },
  })
}

export function useClearDatabase() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: api.clearDatabase,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stats'] })
      queryClient.invalidateQueries({ queryKey: ['products'] })
      queryClient.invalidateQueries({ queryKey: ['reviews'] })
    },
  })
}
