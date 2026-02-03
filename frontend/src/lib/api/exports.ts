import { api, buildParams } from './axios-instance'

export const exportsApi = {
  /**
   * Export messages as a CSV file with optional filtering.
   * Downloads a CSV file containing message data matching the specified criteria.
   *
   * @param params - Optional query parameters for filtering messages
   * @param params.channel_id - Filter messages by a single channel ID
   * @param params.channel_ids - Filter messages by multiple channel IDs
   * @param params.start_date - Filter messages created on or after this date (ISO format)
   * @param params.end_date - Filter messages created on or before this date (ISO format)
   * @param params.media_types - Filter messages by media types (e.g., ['photo', 'video', 'text'])
   * @returns Promise resolving to a Blob containing the CSV file data
   */
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
