import { api } from './axios-instance'
import type { Alert, AlertTrigger } from './types'

export const alertsApi = {
  list: (params?: { collection_id?: string }) => api.get<Alert[]>('/api/alerts', { params }),
  create: (payload: {
    name: string
    collection_id: string
    keywords?: string[]
    entities?: string[]
    min_threshold?: number
    frequency?: string
    notification_channels?: string[]
    is_active?: boolean
  }) => api.post<Alert>('/api/alerts', payload),
  update: (id: string, payload: Partial<Omit<Alert, 'id' | 'user_id' | 'created_at' | 'updated_at'>>) =>
    api.put<Alert>(`/api/alerts/${id}`, payload),
  delete: (id: string) => api.delete(`/api/alerts/${id}`),
  triggers: (id: string, params?: { limit?: number }) =>
    api.get<AlertTrigger[]>(`/api/alerts/${id}/triggers`, { params }),
  recentTriggers: (params?: { limit?: number }) =>
    api.get<AlertTrigger[]>('/api/alerts/triggers/recent', { params }),
}
