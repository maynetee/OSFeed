import { api, buildParams } from './axios-instance'
import type { Message, MessageListResponse } from './types'

export const messagesApi = {
  /**
   * Retrieve a paginated list of messages with optional filtering.
   * Supports filtering by channel, date range, media type, and pagination.
   *
   * @param params - Optional query parameters
   * @param params.channel_id - Filter by single channel ID
   * @param params.channel_ids - Filter by multiple channel IDs
   * @param params.limit - Maximum number of messages to return per page
   * @param params.offset - Number of messages to skip (for pagination)
   * @param params.start_date - ISO 8601 date string for earliest message date
   * @param params.end_date - ISO 8601 date string for latest message date
   * @param params.media_types - Filter by media types (e.g., ['photo', 'video'])
   * @returns Promise resolving to a MessageListResponse with paginated results
   */
  list: (params?: {
    channel_id?: string
    channel_ids?: string[]
    limit?: number
    offset?: number
    start_date?: string
    end_date?: string
    media_types?: string[]
    sort?: 'latest' | 'relevance'
    region?: string
    topics?: string[]
    unique_only?: boolean
    min_escalation?: number
  }) =>
    api.get<MessageListResponse>('/api/messages', {
      params: params ? buildParams(params) : undefined,
    }),

  /**
   * Retrieve a single message by its unique identifier.
   * Includes full message content, metadata, and named entities.
   *
   * @param id - Unique identifier of the message
   * @returns Promise resolving to a Message object with complete details
   */
  get: (id: string) => api.get<Message>(`/api/messages/${id}`),

  /**
   * Find messages that are similar or related to a given message.
   * Uses content similarity algorithms to identify duplicates or near-duplicates.
   *
   * @param messageId - ID of the message to find similar messages for
   * @returns Promise resolving to a MessageListResponse containing similar messages
   */
  getSimilar: (messageId: string) =>
    api.get<MessageListResponse>(`/api/messages/${messageId}/similar`),

  /**
   * Search messages by text query with optional filtering.
   * Performs full-text search on both original and translated message content.
   *
   * @param params - Search parameters
   * @param params.q - Search query string
   * @param params.channel_ids - Optional filter by channel IDs
   * @param params.limit - Maximum number of results to return
   * @param params.offset - Number of results to skip (for pagination)
   * @param params.start_date - ISO 8601 date string for earliest message date
   * @param params.end_date - ISO 8601 date string for latest message date
   * @param params.media_types - Filter by media types (e.g., ['photo', 'video'])
   * @returns Promise resolving to a MessageListResponse with search results
   */
  search: (params: {
    q: string
    channel_ids?: string[]
    limit?: number
    offset?: number
    start_date?: string
    end_date?: string
    media_types?: string[]
  }) =>
    api.get<MessageListResponse>('/api/messages/search', {
      params: buildParams(params),
    }),

  /**
   * Fetch historical messages from a channel going back a specified number of days.
   * Creates a background job to retrieve messages from Telegram's history.
   *
   * @param channelId - ID of the channel to fetch messages from
   * @param days - Number of days of history to fetch (defaults to 7)
   * @returns Promise resolving when the fetch job is created
   */
  fetchHistorical: (channelId: string, days: number = 7) =>
    api.post(`/api/messages/fetch-historical/${channelId}?days=${days}`),

  /**
   * Translate messages to a target language.
   * Optionally filter by channel to translate only messages from specific sources.
   *
   * @param targetLanguage - ISO 639-1 language code to translate to (e.g., 'en', 'es')
   * @param channelId - Optional channel ID to limit translation to messages from a specific channel
   * @returns Promise resolving when the translation job is initiated
   */
  translate: (targetLanguage: string, channelId?: string) =>
    api.post('/api/messages/translate', null, {
      params: { target_language: targetLanguage, channel_id: channelId },
    }),

  /**
   * Translate a single message by its ID.
   * Immediately translates the message and returns the updated message object.
   *
   * @param messageId - ID of the message to translate
   * @returns Promise resolving to the Message object with translation applied
   */
  translateById: (messageId: string) =>
    api.post<Message>(`/api/messages/${messageId}/translate`),

  /**
   * Export messages to an HTML file with optional filtering.
   * Generates a formatted HTML document containing the selected messages.
   *
   * @param params - Optional export parameters
   * @param params.channel_id - Filter by single channel ID
   * @param params.channel_ids - Filter by multiple channel IDs
   * @param params.start_date - ISO 8601 date string for earliest message date
   * @param params.end_date - ISO 8601 date string for latest message date
   * @param params.limit - Maximum number of messages to include
   * @param params.media_types - Filter by media types (e.g., ['photo', 'video'])
   * @returns Promise resolving to the HTML file content as a string
   */
  exportHtml: (params?: {
    channel_id?: string
    channel_ids?: string[]
    start_date?: string
    end_date?: string
    limit?: number
    media_types?: string[]
  }) =>
    api.get('/api/messages/export/html', {
      params: params ? buildParams(params) : undefined,
      responseType: 'text',
    }),

  /**
   * Export messages to a PDF file with optional filtering.
   * Generates a formatted PDF document containing the selected messages.
   *
   * @param params - Optional export parameters
   * @param params.channel_id - Filter by single channel ID
   * @param params.channel_ids - Filter by multiple channel IDs
   * @param params.start_date - ISO 8601 date string for earliest message date
   * @param params.end_date - ISO 8601 date string for latest message date
   * @param params.limit - Maximum number of messages to include
   * @param params.media_types - Filter by media types (e.g., ['photo', 'video'])
   * @returns Promise resolving to a Blob containing the PDF file data
   */
  exportPdf: (params?: {
    channel_id?: string
    channel_ids?: string[]
    start_date?: string
    end_date?: string
    limit?: number
    media_types?: string[]
  }) =>
    api.get('/api/messages/export/pdf', {
      params: params ? buildParams(params) : undefined,
      responseType: 'blob',
    }),
}
