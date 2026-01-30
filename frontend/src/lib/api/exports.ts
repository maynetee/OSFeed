import { api, buildParams } from './axios-instance'

export const exportsApi = {
  messagesCsv: (params?: {
    channel_id?: string
    channel_ids?: string[]
    start_date?: string
    end_date?: string
    media_types?: string[]
  }) =>
    api.get('/api/messages/export/csv', {
      params: params ? buildParams(params) : undefined,
      responseType: 'blob',
    }),
}
