import { api } from './axios-instance'

export interface SummaryResponse {
  id: string
  user_id: string
  collection_id: string | null
  channel_ids: string[]
  date_range_start: string
  date_range_end: string
  summary_text: string
  key_themes: string[]
  notable_events: string[]
  message_count: number
  model_used: string | null
  generation_time_seconds: number | null
  created_at: string
}

export interface SummaryListResponse {
  summaries: SummaryResponse[]
  total: number
}

export interface SummaryGenerateRequest {
  collection_id?: string
  channel_ids?: string[]
  date_range?: string
  max_messages?: number
}

export const summariesApi = {
  generate: (payload: SummaryGenerateRequest) =>
    api.post<SummaryResponse>('/api/summaries/generate', payload),

  list: (params?: { limit?: number; offset?: number }) =>
    api.get<SummaryListResponse>('/api/summaries', { params }),

  get: (id: string) => api.get<SummaryResponse>(`/api/summaries/${id}`),

  delete: (id: string) => api.delete(`/api/summaries/${id}`),
}
