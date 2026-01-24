import axios from 'axios'

import { useUserStore } from '@/stores/user-store'

const API_URL = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth interceptor to include JWT token
api.interceptors.request.use((config) => {
  const tokens = useUserStore.getState().tokens
  if (tokens?.accessToken) {
    config.headers.Authorization = `Bearer ${tokens.accessToken}`
  }
  return config
})

// Add response interceptor to handle 401 errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Skip auth refresh for login/register endpoints
    const isAuthEndpoint = originalRequest?.url?.includes('/api/auth/login') ||
      originalRequest?.url?.includes('/api/auth/register')

    // If 401 and we haven't already tried to refresh
    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true

      const { tokens, setTokens, logout } = useUserStore.getState()

      if (tokens?.refreshToken) {
        try {
          const response = await axios.post(`${API_URL}/api/auth/refresh`, {
            refresh_token: tokens.refreshToken,
          })

          const newTokens = {
            accessToken: response.data.access_token,
            refreshToken: response.data.refresh_token,
            refreshExpiresAt: response.data.refresh_expires_at,
          }

          setTokens(newTokens)
          originalRequest.headers.Authorization = `Bearer ${newTokens.accessToken}`
          return api(originalRequest)
        } catch {
          // Refresh failed, logout user - AuthGuard will redirect
          logout()
        }
      } else {
        // No refresh token, logout - AuthGuard will redirect
        logout()
      }
    }

    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/api/auth/login', new URLSearchParams({ username: email, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),
  register: (email: string, password: string) =>
    api.post('/api/auth/register', { email, password }),
  me: () => api.get('/api/auth/me'),
  logout: () => api.post('/api/auth/logout'),
}

const buildParams = (params: Record<string, unknown>) => {
  const searchParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null) return
    if (Array.isArray(value)) {
      value.forEach((item) => searchParams.append(key, String(item)))
      return
    }
    searchParams.append(key, String(value))
  })
  return searchParams
}

// Types
export interface Channel {
  id: string
  telegram_id: string | null
  username: string
  title: string
  description: string | null
  detected_language?: string | null
  subscriber_count: number
  tags?: string[] | null
  created_at: string
  last_fetched_at: string | null
  fetch_job?: FetchJobStatus | null
}

export interface FetchJobStatus {
  id: string
  channel_id: string
  days: number
  status: string
  stage?: string | null
  total_messages?: number | null
  new_messages?: number | null
  processed_messages?: number | null
  error_message?: string | null
  created_at: string
  started_at?: string | null
  finished_at?: string | null
}

export interface Message {
  id: string
  channel_id: string
  channel_title?: string | null
  channel_username?: string | null
  telegram_message_id: number
  original_text: string
  translated_text: string | null
  source_language: string | null
  target_language?: string | null
  media_type: string | null
  media_urls: string[] | null
  published_at: string
  fetched_at: string
  is_duplicate: boolean
  originality_score?: number | null
  duplicate_group_id: string | null
  embedding_id?: string | null
  entities?: {
    persons?: string[]
    locations?: string[]
    organizations?: string[]
  } | null
  similarity_score?: number | null
  needs_translation?: boolean
  translation_priority?: string | null
}

export interface TranslationUpdate {
  message_id: string
  channel_id: string
  translated_text: string
  source_language: string | null
  target_language: string | null
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
  collection_id?: string | null
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

export interface SummaryListResponse {
  summaries: Summary[]
  total: number
  page: number
  page_size: number
}

export interface Collection {
  id: string
  user_id: string
  name: string
  description?: string | null
  color?: string | null
  icon?: string | null
  is_default?: boolean
  is_global?: boolean
  parent_id?: string | null
  auto_assign_languages?: string[] | null
  auto_assign_keywords?: string[] | null
  auto_assign_tags?: string[] | null
  channel_ids: string[]
  created_at: string
  updated_at?: string | null
}

export interface CollectionStats {
  message_count: number
  message_count_24h: number
  message_count_7d: number
  channel_count: number
  top_channels: { channel_id: string; channel_title: string; count: number }[]
  activity_trend: { date: string; count: number }[]
  duplicate_rate: number
  languages: Record<string, number>
}

export interface TrustStats {
  primary_sources_rate: number
  propaganda_rate: number
  verified_channels: number
  total_messages_24h: number
}

export interface Alert {
  id: string
  collection_id: string
  user_id: string
  name: string
  keywords?: string[] | null
  entities?: string[] | null
  min_threshold: number
  frequency: string
  notification_channels?: string[] | null
  is_active: boolean
  last_triggered_at?: string | null
  created_at: string
  updated_at?: string | null
}

export interface AlertTrigger {
  id: string
  alert_id: string
  triggered_at: string
  message_ids: string[]
  summary?: string | null
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
  get: (id: string) => api.get<Channel>(`/api/channels/${id}`),
  add: (username: string) => api.post<Channel>('/api/channels', { username }),
  delete: (id: string) => api.delete(`/api/channels/${id}`),
  refresh: (channelIds?: string[]) =>
    api.post<{ job_ids: string[] }>('/api/channels/refresh', {
      channel_ids: channelIds,
    }),
  getJobsStatus: (jobIds: string[]) =>
    api.post<{ jobs: FetchJobStatus[] }>('/api/channels/fetch-jobs/status', {
      job_ids: jobIds,
    }),
}

export const messagesApi = {
  list: (params?: {
    channel_id?: string
    channel_ids?: string[]
    limit?: number
    offset?: number
    start_date?: string
    end_date?: string
  }) =>
    api.get<MessageListResponse>('/api/messages', {
      params: params ? buildParams(params) : undefined,
    }),
  get: (id: string) => api.get<Message>(`/api/messages/${id}`),
  search: (params: {
    q: string
    channel_ids?: string[]
    limit?: number
    offset?: number
    start_date?: string
    end_date?: string
  }) =>
    api.get<MessageListResponse>('/api/messages/search', {
      params: buildParams(params),
    }),
  searchSemantic: (params: {
    q: string
    channel_ids?: string[]
    top_k?: number
    start_date?: string
    end_date?: string
  }) =>
    api.get<MessageListResponse>('/api/messages/search/semantic', {
      params: buildParams(params),
    }),
  similar: (id: string, params?: { top_k?: number }) =>
    api.get<MessageListResponse>(`/api/messages/${id}/similar`, { params }),
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
  }) =>
    api.get('/api/messages/export/pdf', {
      params: params ? buildParams(params) : undefined,
      responseType: 'blob',
    }),
}

export const summariesApi = {
  getDaily: () => api.get<Summary>('/api/summaries/daily'),
  get: (id: string) => api.get<Summary>(`/api/summaries/${id}`),
  list: (params?: { digest_type?: string; limit?: number; offset?: number; collection_id?: string }) =>
    api.get<SummaryListResponse>('/api/summaries', { params }),
  generate: (filters?: Record<string, string[]>) =>
    api.post<Summary>('/api/summaries/generate', { digest_type: 'daily', filters }),
  exportHtml: (id: string) => api.get(`/api/summaries/${id}/export/html`),
  exportPdf: (id: string) =>
    api.get(`/api/summaries/${id}/export/pdf`, { responseType: 'blob' }),
}

export const collectionsApi = {
  list: () => api.get<Collection[]>('/api/collections'),
  get: (id: string) => api.get<Collection>(`/api/collections/${id}`),
  create: (payload: {
    name: string
    description?: string
    channel_ids?: string[]
    color?: string
    icon?: string
    is_default?: boolean
    is_global?: boolean
    parent_id?: string | null
    auto_assign_languages?: string[]
    auto_assign_keywords?: string[]
    auto_assign_tags?: string[]
  }) =>
    api.post<Collection>('/api/collections', payload),
  update: (
    id: string,
    payload: {
      name?: string
      description?: string
      channel_ids?: string[]
      color?: string
      icon?: string
      is_default?: boolean
      is_global?: boolean
      parent_id?: string | null
      auto_assign_languages?: string[]
      auto_assign_keywords?: string[]
      auto_assign_tags?: string[]
    },
  ) => api.put<Collection>(`/api/collections/${id}`, payload),
  delete: (id: string) => api.delete(`/api/collections/${id}`),
  stats: (id: string) => api.get<CollectionStats>(`/api/collections/${id}/stats`),
  overview: () => api.get<{ collections: { id: string; name: string; message_count_7d: number; channel_count: number; created_at: string }[] }>(
    '/api/collections/overview',
  ),
  compare: (collection_ids: string[]) =>
    api.get<{ comparisons: { collection_id: string; name: string; message_count_7d: number; channel_count: number; duplicate_rate: number }[] }>(
      '/api/collections/compare',
      { params: buildParams({ collection_ids }) },
    ),
  digests: (id: string, params?: { limit?: number; offset?: number }) =>
    api.get<SummaryListResponse>(`/api/collections/${id}/digests`, { params }),
  generateDigest: (id: string) => api.post<Summary>(`/api/collections/${id}/digest`),
  exportMessages: (id: string, params?: { format?: string; start_date?: string; end_date?: string; limit?: number }) =>
    api.post(`/api/collections/${id}/export`, null, { params: params ? buildParams(params) : undefined, responseType: params?.format === 'pdf' ? 'blob' : undefined }),
  shares: (id: string) => api.get(`/api/collections/${id}/shares`),
  addShare: (id: string, payload: { user_id: string; permission: string }) =>
    api.post(`/api/collections/${id}/shares`, payload),
  removeShare: (id: string, userId: string) =>
    api.delete(`/api/collections/${id}/shares/${userId}`),
}

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
}

export const exportsApi = {
  messagesCsv: (params?: {
    channel_id?: string
    channel_ids?: string[]
    start_date?: string
    end_date?: string
  }) =>
    api.get('/api/messages/export/csv', {
      params: params ? buildParams(params) : undefined,
      responseType: 'blob',
    }),
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
