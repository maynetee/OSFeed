import { api } from './axios-instance'
import type { Alert, AlertTrigger } from './types'

export const alertsApi = {
  /**
   * Retrieve a list of alerts for the authenticated user.
   * Optionally filter by collection ID.
   *
   * @param params - Optional query parameters
   * @param params.collection_id - Filter alerts by collection ID
   * @returns Promise resolving to an array of Alert objects
   */
  list: (params?: { collection_id?: string }) => api.get<Alert[]>('/api/alerts', { params }),

  /**
   * Create a new alert with specified keywords, entities, and notification settings.
   * Alerts monitor collections for matching content and trigger notifications.
   *
   * @param payload - Alert configuration
   * @param payload.name - Display name for the alert
   * @param payload.collection_id - ID of the collection to monitor
   * @param payload.keywords - Optional array of keywords to match
   * @param payload.entities - Optional array of named entities to match
   * @param payload.min_threshold - Optional minimum relevance threshold (0-1)
   * @param payload.frequency - Optional notification frequency (e.g., 'realtime', 'daily')
   * @param payload.notification_channels - Optional array of notification channels (e.g., 'email', 'webhook')
   * @param payload.is_active - Optional flag to enable/disable the alert (defaults to true)
   * @returns Promise resolving to the created Alert object
   */
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

  /**
   * Update an existing alert's configuration.
   * Only provided fields will be updated; omitted fields remain unchanged.
   *
   * @param id - The alert ID to update
   * @param payload - Partial alert configuration with fields to update
   * @returns Promise resolving to the updated Alert object
   */
  update: (id: string, payload: Partial<Omit<Alert, 'id' | 'user_id' | 'created_at' | 'updated_at'>>) =>
    api.put<Alert>(`/api/alerts/${id}`, payload),

  /**
   * Delete an alert by ID.
   * This permanently removes the alert and its trigger history.
   *
   * @param id - The alert ID to delete
   * @returns Promise resolving when the alert is deleted
   */
  delete: (id: string) => api.delete(`/api/alerts/${id}`),

  /**
   * Retrieve trigger history for a specific alert.
   * Returns all times this alert has been triggered, with matched messages.
   *
   * @param id - The alert ID to get triggers for
   * @param params - Optional query parameters
   * @param params.limit - Maximum number of triggers to return
   * @returns Promise resolving to an array of AlertTrigger objects
   */
  triggers: (id: string, params?: { limit?: number }) =>
    api.get<AlertTrigger[]>(`/api/alerts/${id}/triggers`, { params }),

  /**
   * Retrieve recent alert triggers across all alerts for the authenticated user.
   * Useful for displaying a unified notification feed.
   *
   * @param params - Optional query parameters
   * @param params.limit - Maximum number of triggers to return
   * @returns Promise resolving to an array of AlertTrigger objects
   */
  recentTriggers: (params?: { limit?: number }) =>
    api.get<AlertTrigger[]>('/api/alerts/triggers/recent', { params }),
}
