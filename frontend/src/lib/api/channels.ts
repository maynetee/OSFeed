import { api } from './axios-instance'
import type {
  Channel,
  FetchJobStatus,
  BulkAddResponse,
  ChannelInfoUpdate,
} from './types'

export const channelsApi = {
  list: () => api.get<Channel[]>('/api/channels'),
  get: (id: string) => api.get<Channel>(`/api/channels/${id}`),
  add: (username: string) => api.post<Channel>('/api/channels', { username }),
  addBulk: (usernames: string[]) =>
    api.post<BulkAddResponse>('/api/channels/bulk', { usernames }),
  delete: (id: string) => api.delete(`/api/channels/${id}`),
  refresh: (channelIds?: string[]) =>
    api.post<{ job_ids: string[] }>('/api/channels/refresh', {
      channel_ids: channelIds,
    }),
  refreshInfo: (channelIds?: string[]) =>
    api.post<{ results: ChannelInfoUpdate[] }>('/api/channels/refresh-info', {
      channel_ids: channelIds,
    }),
  getJobsStatus: (jobIds: string[]) =>
    api.post<{ jobs: FetchJobStatus[] }>('/api/channels/fetch-jobs/status', {
      job_ids: jobIds,
    }),
}
