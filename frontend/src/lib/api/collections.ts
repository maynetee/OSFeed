import { api, buildParams } from './axios-instance'
import type { Collection, CollectionStats } from './types'

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
  exportMessages: (id: string, params?: { format?: string; start_date?: string; end_date?: string; limit?: number }) =>
    api.post(`/api/collections/${id}/export`, null, { params: params ? buildParams(params) : undefined, responseType: params?.format === 'pdf' ? 'blob' : undefined }),
  shares: (id: string) => api.get(`/api/collections/${id}/shares`),
  addShare: (id: string, payload: { user_id: string; permission: string }) =>
    api.post(`/api/collections/${id}/shares`, payload),
  removeShare: (id: string, userId: string) =>
    api.delete(`/api/collections/${id}/shares/${userId}`),
}
