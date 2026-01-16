import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Types
export interface Channel {
  id: string
  telegram_id: string
  username: string
  title: string
  description: string | null
  detected_language?: string | null
  subscriber_count: number
  created_at: string
  last_fetched_at: string | null
}

export interface Message {
  id: string
  channel_id: string
  telegram_message_id: number
  original_text: string
  translated_text: string | null
  source_language: string | null
  media_type: string | null
  media_urls: string | null
  published_at: string
  fetched_at: string
  is_duplicate: boolean
  duplicate_group_id: string | null
}

export interface MessageListResponse {
  messages: Message[]
  total: number
  page: number
  page_size: number
}

export interface Summary {
  id: string
  digest_type: string
  title?: string
  content: string
  content_html?: string | null
  entities?: {
    persons: string[]
    locations: string[]
    organizations: string[]
  } | null
  message_count: number
  channels_covered?: number
  duplicates_filtered?: number
  generated_at: string
  period_start: string
  period_end: string
}

export interface Collection {
  id: string
  user_id: string
  name: string
  description?: string | null
  channel_ids: string[]
  created_at: string
  updated_at?: string | null
}

export interface StatsOverview {
  total_messages: number
  active_channels: number
  messages_last_24h: number
  duplicates_last_24h: number
  summaries_total: number
}

export interface MessagesByDay {
  date: string
  count: number
}

export interface MessagesByChannel {
  channel_id: string
  channel_title: string
  count: number
}

// API functions
export const channelsApi = {
  list: () => api.get<Channel[]>('/api/channels'),
  add: (username: string) => api.post<Channel>('/api/channels', { username }),
  delete: (id: string) => api.delete(`/api/channels/${id}`),
}

export const messagesApi = {
  list: (params?: {
    channel_id?: string
    limit?: number
    offset?: number
    start_date?: string
    end_date?: string
  }) => api.get<MessageListResponse>('/api/messages', { params }),
  get: (id: string) => api.get<Message>(`/api/messages/${id}`),
  fetchHistorical: (channelId: string, days: number = 7) =>
    api.post(`/api/messages/fetch-historical/${channelId}?days=${days}`),
  translate: (targetLanguage: string, channelId?: string) =>
    api.post('/api/messages/translate', null, {
      params: { target_language: targetLanguage, channel_id: channelId },
    }),
}

export const summariesApi = {
  getDaily: () => api.get<Summary>('/api/summaries/daily'),
  generate: (filters?: Record<string, string[]>) =>
    api.post<Summary>('/api/summaries/generate', { digest_type: 'daily', filters }),
  exportHtml: (id: string) => api.get(`/api/summaries/${id}/export/html`),
  exportPdf: (id: string) =>
    api.get(`/api/summaries/${id}/export/pdf`, { responseType: 'blob' }),
}

export const collectionsApi = {
  list: () => api.get<Collection[]>('/api/collections'),
  create: (payload: { name: string; description?: string; channel_ids?: string[] }) =>
    api.post<Collection>('/api/collections', payload),
  update: (
    id: string,
    payload: { name?: string; description?: string; channel_ids?: string[] },
  ) => api.put<Collection>(`/api/collections/${id}`, payload),
  delete: (id: string) => api.delete(`/api/collections/${id}`),
}

export const statsApi = {
  overview: () => api.get<StatsOverview>('/api/stats/overview'),
  messagesByDay: (days: number = 7) =>
    api.get<MessagesByDay[]>('/api/stats/messages-by-day', { params: { days } }),
  messagesByChannel: (limit: number = 10) =>
    api.get<MessagesByChannel[]>('/api/stats/messages-by-channel', {
      params: { limit },
    }),
  exportCsv: (days: number = 7) =>
    api.get('/api/stats/export/csv', { params: { days }, responseType: 'blob' }),
}

export const exportsApi = {
  messagesCsv: () => api.get('/api/messages/export/csv', { responseType: 'blob' }),
}

// Language options
export const LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'fr', name: 'Français' },
  { code: 'es', name: 'Español' },
  { code: 'de', name: 'Deutsch' },
  { code: 'ar', name: 'العربية' },
  { code: 'zh', name: '中文' },
  { code: 'ru', name: 'Русский' },
  { code: 'ja', name: '日本語' },
  { code: 'pt', name: 'Português' },
  { code: 'it', name: 'Italiano' },
]
