import { api, buildParams } from './axios-instance'
import type { Message, MessageListResponse } from './types'

export const messagesApi = {
  list: (params?: {
    channel_id?: string
    channel_ids?: string[]
    limit?: number
    offset?: number
    start_date?: string
    end_date?: string
    media_types?: string[]
  }) =>
    api.get<MessageListResponse>('/api/messages', {
      params: params ? buildParams(params) : undefined,
    }),
  get: (id: string) => api.get<Message>(`/api/messages/${id}`),
  getSimilar: (messageId: string) =>
    api.get<MessageListResponse>(`/api/messages/${messageId}/similar`),
  search: (params: {
    q: string
    channel_ids?: string[]
    limit?: number
    offset?: number
    start_date?: string
    end_date?: string
    media_types?: string[]
  }) =>
    api.get<MessageListResponse>('/api/messages/search', {
      params: buildParams(params),
    }),
  fetchHistorical: (channelId: string, days: number = 7) =>
    api.post(`/api/messages/fetch-historical/${channelId}?days=${days}`),
  translate: (targetLanguage: string, channelId?: string) =>
    api.post('/api/messages/translate', null, {
      params: { target_language: targetLanguage, channel_id: channelId },
    }),
  translateById: (messageId: string) =>
    api.post<Message>(`/api/messages/${messageId}/translate`),
  exportHtml: (params?: {
    channel_id?: string
    channel_ids?: string[]
    start_date?: string
    end_date?: string
    limit?: number
    media_types?: string[]
  }) =>
    api.get('/api/messages/export/html', {
      params: params ? buildParams(params) : undefined,
      responseType: 'text',
    }),
  exportPdf: (params?: {
    channel_id?: string
    channel_ids?: string[]
    start_date?: string
    end_date?: string
    limit?: number
    media_types?: string[]
  }) =>
    api.get('/api/messages/export/pdf', {
      params: params ? buildParams(params) : undefined,
      responseType: 'blob',
    }),
}
