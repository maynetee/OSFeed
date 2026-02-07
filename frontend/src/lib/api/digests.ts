import { api } from './axios-instance'

export interface DigestPreference {
  id: string
  user_id: string
  enabled: boolean
  frequency: string
  send_hour: number
  collection_ids: string[] | null
  max_messages: number
  last_sent_at: string | null
  created_at: string | null
  updated_at: string | null
}

export const digestsApi = {
  getPreferences: () => api.get<DigestPreference>('/api/digests/preferences'),

  updatePreferences: (payload: {
    enabled?: boolean
    frequency?: string
    send_hour?: number
    collection_ids?: string[]
    max_messages?: number
  }) => api.post<DigestPreference>('/api/digests/preferences', payload),

  sendPreview: (payload?: { collection_ids?: string[]; max_messages?: number }) =>
    api.post<{ message: string }>('/api/digests/preview', payload || {}),
}
