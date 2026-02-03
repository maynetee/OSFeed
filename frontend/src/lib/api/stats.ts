import { api, buildParams } from './axios-instance'
import type { StatsOverview, MessagesByDay, MessagesByChannel, TrustStats } from './types'

export const statsApi = {
  /**
   * Retrieve overall statistics summary for the authenticated user.
   * Includes total messages, channels, collections, and other aggregate metrics.
   *
   * @returns Promise resolving to a StatsOverview object with aggregate statistics
   */
  overview: () => api.get<StatsOverview>('/api/stats/overview'),

  /**
   * Retrieve message count statistics grouped by day.
   * Returns daily message counts for the specified time period.
   *
   * @param days - Number of days to include in the statistics (defaults to 7)
   * @returns Promise resolving to an array of MessagesByDay objects with daily counts
   */
  messagesByDay: (days: number = 7) =>
    api.get<MessagesByDay[]>('/api/stats/messages-by-day', { params: { days } }),

  /**
   * Retrieve message count statistics grouped by channel.
   * Returns top channels by message count, limited to the specified number.
   *
   * @param limit - Maximum number of channels to return (defaults to 10)
   * @returns Promise resolving to an array of MessagesByChannel objects with message counts
   */
  messagesByChannel: (limit: number = 10) =>
    api.get<MessagesByChannel[]>('/api/stats/messages-by-channel', {
      params: { limit },
    }),

  /**
   * Retrieve trust and credibility statistics for channels.
   * Optionally filter by specific channel IDs.
   *
   * @param params - Optional query parameters
   * @param params.channel_ids - Filter trust stats by specific channel IDs
   * @returns Promise resolving to a TrustStats object with credibility metrics
   */
  trust: (params?: { channel_ids?: string[] }) =>
    api.get<TrustStats>('/api/stats/trust', { params: params ? buildParams(params) : undefined }),

  /**
   * Export statistics data as a CSV file.
   * Downloads aggregate statistics for the specified time period.
   *
   * @param days - Number of days to include in the export (defaults to 7)
   * @returns Promise resolving to a Blob containing the CSV file data
   */
  exportCsv: (days: number = 7) =>
    api.get('/api/stats/export/csv', { params: { days }, responseType: 'blob' }),

  /**
   * Export statistics data as a JSON file.
   * Downloads aggregate statistics for the specified time period.
   *
   * @param days - Number of days to include in the export (defaults to 7)
   * @returns Promise resolving to a Blob containing the JSON file data
   */
  exportJson: (days: number = 7) =>
    api.get('/api/stats/export/json', { params: { days }, responseType: 'blob' }),
}
