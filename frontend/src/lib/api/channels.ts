import { api } from './axios-instance'
import type { Channel, FetchJobStatus, BulkAddResponse, ChannelInfoUpdate } from './types'

export const channelsApi = {
  /**
   * Retrieve a list of all channels currently being monitored.
   * Returns an array of channel objects with their metadata and status.
   *
   * @returns Promise resolving to an array of Channel objects
   */
  list: () => api.get<Channel[]>('/api/channels'),

  /**
   * Retrieve detailed information about a specific channel by its ID.
   * Includes channel metadata, subscriber count, and fetch job status.
   *
   * @param id - Unique identifier of the channel
   * @returns Promise resolving to a Channel object with full details
   */
  get: (id: string) => api.get<Channel>(`/api/channels/${id}`),

  /**
   * Add a new Telegram channel to the monitoring system.
   * The channel will be added to the database and become available for message fetching.
   *
   * @param username - Telegram username handle of the channel (e.g., 'channelname' or '@channelname')
   * @returns Promise resolving to the newly created Channel object
   */
  add: (username: string) => api.post<Channel>('/api/channels', { username }),

  /**
   * Add multiple Telegram channels to the monitoring system in a single operation.
   * Returns both successful additions and failures with error messages.
   *
   * @param usernames - Array of Telegram username handles to add
   * @returns Promise resolving to a BulkAddResponse with succeeded and failed channels
   */
  addBulk: (usernames: string[]) => api.post<BulkAddResponse>('/api/channels/bulk', { usernames }),

  /**
   * Remove a channel from the monitoring system.
   * This will delete the channel and all associated messages from the database.
   *
   * @param id - Unique identifier of the channel to delete
   * @returns Promise resolving when the channel is successfully deleted
   */
  delete: (id: string) => api.delete(`/api/channels/${id}`),

  /**
   * Initiate a message fetch operation for one or more channels.
   * Starts background jobs to retrieve historical messages from Telegram.
   *
   * @param channelIds - Optional array of channel IDs to refresh (if omitted, refreshes all channels)
   * @returns Promise resolving to an object containing the IDs of created fetch jobs
   */
  refresh: (channelIds?: string[]) =>
    api.post<{ job_ids: string[] }>('/api/channels/refresh', {
      channel_ids: channelIds,
    }),

  /**
   * Update channel metadata (title, subscriber count) from Telegram.
   * Refreshes channel information without fetching messages.
   *
   * @param channelIds - Optional array of channel IDs to update (if omitted, updates all channels)
   * @returns Promise resolving to an object containing update results for each channel
   */
  refreshInfo: (channelIds?: string[]) =>
    api.post<{ results: ChannelInfoUpdate[] }>('/api/channels/refresh-info', {
      channel_ids: channelIds,
    }),

  /**
   * Check the status of ongoing or completed fetch jobs.
   * Returns detailed progress information for each job including messages processed.
   *
   * @param jobIds - Array of fetch job IDs to check
   * @returns Promise resolving to an object containing an array of FetchJobStatus objects
   */
  getJobsStatus: (jobIds: string[]) =>
    api.post<{ jobs: FetchJobStatus[] }>('/api/channels/fetch-jobs/status', {
      job_ids: jobIds,
    }),
}
