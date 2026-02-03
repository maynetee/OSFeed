import { api, buildParams } from './axios-instance'
import type { Collection, CollectionStats } from './types'

export const collectionsApi = {
  /**
   * Retrieve a list of all collections owned by the authenticated user.
   * Returns an array of collection objects with their metadata and channel associations.
   *
   * @returns Promise resolving to an array of Collection objects
   */
  list: () => api.get<Collection[]>('/api/collections'),

  /**
   * Retrieve detailed information about a specific collection by its ID.
   * Includes all collection metadata, associated channels, and auto-assignment rules.
   *
   * @param id - Unique identifier of the collection
   * @returns Promise resolving to a Collection object with full details
   */
  get: (id: string) => api.get<Collection>(`/api/collections/${id}`),

  /**
   * Create a new collection for organizing channels.
   * Collections can have auto-assignment rules based on language, keywords, or tags.
   *
   * @param payload - Collection creation parameters
   * @param payload.name - Display name for the collection
   * @param payload.description - Optional description explaining the collection's purpose
   * @param payload.channel_ids - Optional array of channel IDs to initially add to the collection
   * @param payload.color - Optional hex color code for UI representation (e.g., '#3b82f6')
   * @param payload.icon - Optional emoji icon for UI representation (e.g., '📁')
   * @param payload.is_default - Whether this is the default collection for new channels
   * @param payload.is_global - Whether this collection is shared globally across all users
   * @param payload.parent_id - Optional ID of parent collection for nesting
   * @param payload.auto_assign_languages - Languages to auto-assign messages from (ISO 639-1 codes)
   * @param payload.auto_assign_keywords - Keywords to auto-assign messages containing these terms
   * @param payload.auto_assign_tags - Tags to auto-assign messages with these tags
   * @returns Promise resolving to the newly created Collection object
   */
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

  /**
   * Update an existing collection's properties.
   * All fields are optional - only provided fields will be updated.
   *
   * @param id - Unique identifier of the collection to update
   * @param payload - Collection update parameters
   * @param payload.name - Updated display name for the collection
   * @param payload.description - Updated description
   * @param payload.channel_ids - Updated array of channel IDs (replaces existing channels)
   * @param payload.color - Updated hex color code
   * @param payload.icon - Updated emoji icon
   * @param payload.is_default - Updated default collection status
   * @param payload.is_global - Updated global sharing status
   * @param payload.parent_id - Updated parent collection ID
   * @param payload.auto_assign_languages - Updated language auto-assignment rules
   * @param payload.auto_assign_keywords - Updated keyword auto-assignment rules
   * @param payload.auto_assign_tags - Updated tag auto-assignment rules
   * @returns Promise resolving to the updated Collection object
   */
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

  /**
   * Delete a collection from the system.
   * Associated channels will remain but will no longer be grouped in this collection.
   *
   * @param id - Unique identifier of the collection to delete
   * @returns Promise resolving when the collection is successfully deleted
   */
  delete: (id: string) => api.delete(`/api/collections/${id}`),

  /**
   * Retrieve detailed statistics for a specific collection.
   * Includes message counts, channel counts, activity trends, and language distribution.
   *
   * @param id - Unique identifier of the collection
   * @returns Promise resolving to a CollectionStats object with comprehensive metrics
   */
  stats: (id: string) => api.get<CollectionStats>(`/api/collections/${id}/stats`),

  /**
   * Get a high-level overview of all collections with summary statistics.
   * Returns basic metrics for each collection including recent activity.
   *
   * @returns Promise resolving to an object containing an array of collection summaries
   */
  overview: () => api.get<{ collections: { id: string; name: string; message_count_7d: number; channel_count: number; created_at: string }[] }>(
    '/api/collections/overview',
  ),

  /**
   * Compare statistics across multiple collections.
   * Returns comparative metrics to analyze differences in activity and content.
   *
   * @param collection_ids - Array of collection IDs to compare
   * @returns Promise resolving to an object containing comparison data for each collection
   */
  compare: (collection_ids: string[]) =>
    api.get<{ comparisons: { collection_id: string; name: string; message_count_7d: number; channel_count: number; duplicate_rate: number }[] }>(
      '/api/collections/compare',
      { params: buildParams({ collection_ids }) },
    ),

  /**
   * Export messages from a collection in a specified format.
   * Supports filtering by date range and limiting the number of messages.
   *
   * @param id - Unique identifier of the collection to export
   * @param params - Optional export parameters
   * @param params.format - Export format ('html', 'pdf', 'json', defaults to 'json')
   * @param params.start_date - ISO 8601 date string for earliest message date
   * @param params.end_date - ISO 8601 date string for latest message date
   * @param params.limit - Maximum number of messages to include
   * @returns Promise resolving to the exported data (Blob for PDF, text/JSON for other formats)
   */
  exportMessages: (id: string, params?: { format?: string; start_date?: string; end_date?: string; limit?: number }) =>
    api.post(`/api/collections/${id}/export`, null, { params: params ? buildParams(params) : undefined, responseType: params?.format === 'pdf' ? 'blob' : undefined }),

  /**
   * Retrieve the list of users with whom this collection is shared.
   * Returns sharing permissions for each user.
   *
   * @param id - Unique identifier of the collection
   * @returns Promise resolving to an array of share objects with user IDs and permissions
   */
  shares: (id: string) => api.get(`/api/collections/${id}/shares`),

  /**
   * Share a collection with another user.
   * Grants the specified user access to the collection with the given permission level.
   *
   * @param id - Unique identifier of the collection to share
   * @param payload - Share parameters
   * @param payload.user_id - ID of the user to share with
   * @param payload.permission - Permission level ('read', 'write', 'admin')
   * @returns Promise resolving when the share is successfully created
   */
  addShare: (id: string, payload: { user_id: string; permission: string }) =>
    api.post(`/api/collections/${id}/shares`, payload),

  /**
   * Remove a user's access to a shared collection.
   * Revokes all permissions for the specified user.
   *
   * @param id - Unique identifier of the collection
   * @param userId - ID of the user whose access should be removed
   * @returns Promise resolving when the share is successfully removed
   */
  removeShare: (id: string, userId: string) =>
    api.delete(`/api/collections/${id}/shares/${userId}`),
}
