import { api, buildParams } from './axios-instance'
import type { StatsOverview, MessagesByDay, MessagesByChannel, TrustStats } from './types'

export const statsApi = {
  overview: () => api.get<StatsOverview>('/api/stats/overview'),
  messagesByDay: (days: number = 7) =>
    api.get<MessagesByDay[]>('/api/stats/messages-by-day', { params: { days } }),
  messagesByChannel: (limit: number = 10) =>
    api.get<MessagesByChannel[]>('/api/stats/messages-by-channel', {
      params: { limit },
    }),
  trust: (params?: { channel_ids?: string[] }) =>
    api.get<TrustStats>('/api/stats/trust', { params: params ? buildParams(params) : undefined }),
  exportCsv: (days: number = 7) =>
    api.get('/api/stats/export/csv', { params: { days }, responseType: 'blob' }),
  exportJson: (days: number = 7) =>
    api.get('/api/stats/export/json', { params: { days }, responseType: 'blob' }),
}
