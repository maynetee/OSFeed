export interface Channel {
  /** Unique identifier for the channel */
  id: string
  /** Telegram's internal numeric channel ID (null if not available) */
  telegram_id: string | null
  /** Telegram username handle for the channel (e.g., @channelname) */
  username: string
  /** Display title of the channel */
  title: string
  /** Optional description or bio of the channel */
  description: string | null
  /** Detected primary language code for the channel's content (ISO 639-1, e.g., 'en', 'ru') */
  detected_language?: string | null
  /** Number of subscribers following this channel */
  subscriber_count: number
  /** Optional array of user-defined tags for categorization */
  tags?: string[] | null
  /** Region taxonomy tag (e.g., 'Europe', 'Middle East') */
  region?: string | null
  /** Topic taxonomy tags (e.g., ['Conflict', 'Intelligence']) */
  topics?: string[] | null
  /** ISO 8601 timestamp when the channel was first added to the system */
  created_at: string
  /** ISO 8601 timestamp of the most recent message fetch operation (null if never fetched) */
  last_fetched_at: string | null
  /** Current status of the ongoing or most recent message fetch job (null if no job exists) */
  fetch_job?: FetchJobStatus | null
}

export interface FetchJobStatus {
  /** Unique identifier for the fetch job */
  id: string
  /** ID of the channel being fetched */
  channel_id: string
  /** Number of days of message history to fetch */
  days: number
  /** Current status of the job (e.g., 'pending', 'running', 'completed', 'failed') */
  status: string
  /** Current processing stage of the job (e.g., 'fetching', 'translating', 'analyzing') */
  stage?: string | null
  /** Total number of messages found in the channel for the specified time period */
  total_messages?: number | null
  /** Number of messages newly added to the system (not previously stored) */
  new_messages?: number | null
  /** Number of messages that have been processed so far */
  processed_messages?: number | null
  /** Error message if the job failed (null if successful or still running) */
  error_message?: string | null
  /** ISO 8601 timestamp when the job was created */
  created_at: string
  /** ISO 8601 timestamp when the job started execution (null if not started) */
  started_at?: string | null
  /** ISO 8601 timestamp when the job completed or failed (null if still running) */
  finished_at?: string | null
}

export interface Message {
  /** Unique identifier for the message in our system */
  id: string
  /** ID of the channel this message belongs to */
  channel_id: string
  /** Display title of the channel (denormalized for convenience) */
  channel_title?: string | null
  /** Username handle of the channel (denormalized for convenience) */
  channel_username?: string | null
  /** Telegram's internal numeric message ID */
  telegram_message_id: number
  /** Original message text in its source language */
  original_text: string
  /** Translated text in the target language (null if not yet translated) */
  translated_text: string | null
  /** Detected or specified source language code (ISO 639-1, e.g., 'ru', 'uk') */
  source_language: string | null
  /** Target language for translation (ISO 639-1, e.g., 'en', defaults to user preference) */
  target_language?: string | null
  /** Type of media attached to the message (e.g., 'photo', 'video', 'document', null if text-only) */
  media_type: string | null
  /** Array of URLs for attached media files (null if no media) */
  media_urls: string[] | null
  /** ISO 8601 timestamp when the message was originally published on Telegram */
  published_at: string
  /** ISO 8601 timestamp when the message was fetched into our system */
  fetched_at: string
  /** Whether this message is a duplicate or near-duplicate of another message */
  is_duplicate: boolean
  /** Originality score from 0.0 to 1.0 (higher = more original, null if not calculated) */
  originality_score?: number | null
  /** ID of the duplicate group this message belongs to (null if not a duplicate) */
  duplicate_group_id: string | null
  /** Named entities extracted from the message text (persons, locations, organizations) */
  entities?: {
    /** Array of person names mentioned in the message */
    persons?: string[]
    /** Array of location names mentioned in the message */
    locations?: string[]
    /** Array of organization names mentioned in the message */
    organizations?: string[]
  } | null
  /** Whether this message requires translation (based on language settings) */
  needs_translation?: boolean
  /** Translation priority level (e.g., 'high', 'normal', 'low', null if not prioritized) */
  translation_priority?: string | null
  /** Relevance score from 0.0 to 1.0 (higher = more relevant, null if not calculated) */
  relevance_score?: number | null
}

export interface TranslationUpdate {
  /** ID of the message being updated with translated text */
  message_id: string
  /** ID of the channel the message belongs to */
  channel_id: string
  /** The translated text in the target language */
  translated_text: string
  /** Source language code of the original text (ISO 639-1) */
  source_language: string | null
  /** Target language code for the translation (ISO 639-1) */
  target_language: string | null
}

export interface MessageListResponse {
  /** Array of message objects returned in this page */
  messages: Message[]
  /** Total number of messages matching the query across all pages */
  total: number
  /** Current page number (1-indexed) */
  page: number
  /** Number of messages per page */
  page_size: number
}

export interface Collection {
  /** Unique identifier for the collection */
  id: string
  /** ID of the user who owns this collection */
  user_id: string
  /** Display name of the collection */
  name: string
  /** Optional description explaining the collection's purpose */
  description?: string | null
  /** Optional hex color code for UI representation (e.g., '#3b82f6') */
  color?: string | null
  /** Optional emoji icon for UI representation (e.g., '📁') */
  icon?: string | null
  /** Whether this is the user's default collection for new channels */
  is_default?: boolean
  /** Whether this collection is shared globally across all users */
  is_global?: boolean
  /** Optional ID of the parent collection if this is nested */
  parent_id?: string | null
  /** Languages to auto-assign messages from (ISO 639-1 codes, null if not set) */
  auto_assign_languages?: string[] | null
  /** Keywords to auto-assign messages containing these terms (null if not set) */
  auto_assign_keywords?: string[] | null
  /** Tags to auto-assign messages with these tags (null if not set) */
  auto_assign_tags?: string[] | null
  /** Array of channel IDs included in this collection */
  channel_ids: string[]
  /** ISO 8601 timestamp when the collection was created */
  created_at: string
  /** ISO 8601 timestamp when the collection was last updated (null if never updated) */
  updated_at?: string | null
}

export interface CollectionStats {
  /** Total number of messages in the collection */
  message_count: number
  /** Number of messages received in the last 24 hours */
  message_count_24h: number
  /** Number of messages received in the last 7 days */
  message_count_7d: number
  /** Number of channels in the collection */
  channel_count: number
  /** Array of top channels by message count with channel details */
  top_channels: { channel_id: string; channel_title: string; count: number }[]
  /** Daily message count trend data for charting */
  activity_trend: { date: string; count: number }[]
  /** Duplicate message rate as a decimal from 0.0 to 1.0 */
  duplicate_rate: number
  /** Distribution of messages by language code (ISO 639-1) with counts */
  languages: Record<string, number>
}

export interface TrustStats {
  /** Rate of messages from primary/verified sources as a decimal from 0.0 to 1.0 */
  primary_sources_rate: number
  /** Rate of messages flagged as propaganda as a decimal from 0.0 to 1.0 */
  propaganda_rate: number
  /** Number of verified channels in the dataset */
  verified_channels: number
  /** Total number of messages received in the last 24 hours */
  total_messages_24h: number
}

export interface ApiUsageStats {
  /** Time window in days for the statistics */
  window_days: number
  /** Total tokens consumed */
  total_tokens: number
  /** Estimated cost in USD */
  estimated_cost_usd: number
  /** Detailed breakdown by service/model */
  breakdown: Array<{
    provider: string
    model: string
    purpose: string
    total_tokens: number
    estimated_cost_usd: number
  }>
}

export interface TranslationMetrics {
  /** Total number of translations performed */
  total_translations: number
  /** Number of cache hits */
  cache_hits: number
  /** Number of cache misses */
  cache_misses: number
  /** Cache hit rate as percentage (0-100) */
  cache_hit_rate: number
  /** Tokens saved by caching */
  tokens_saved: number
}

export interface Alert {
  /** Unique identifier for the alert */
  id: string
  /** ID of the collection this alert monitors */
  collection_id: string
  /** ID of the user who owns this alert */
  user_id: string
  /** Display name for the alert */
  name: string
  /** Keywords to trigger the alert (null if not using keyword matching) */
  keywords?: string[] | null
  /** Named entities to trigger the alert (null if not using entity matching) */
  entities?: string[] | null
  /** Match mode: "any" (default) or "all" keywords must match */
  match_mode?: string
  /** Minimum threshold for triggering (interpretation depends on alert type) */
  min_threshold: number
  /** How often to check for matches (e.g., 'realtime', 'hourly', 'daily') */
  frequency: string
  /** Where to send notifications (e.g., ['email', 'push'], null for default) */
  notification_channels?: string[] | null
  /** Whether the alert is currently active and checking for matches */
  is_active: boolean
  /** ISO 8601 timestamp when the alert was last triggered (null if never triggered) */
  last_triggered_at?: string | null
  /** ISO 8601 timestamp when the alert was last evaluated */
  last_evaluated_at?: string | null
  /** ISO 8601 timestamp when the alert was created */
  created_at: string
  /** ISO 8601 timestamp when the alert was last updated (null if never updated) */
  updated_at?: string | null
}

export interface AlertTrigger {
  /** Unique identifier for the alert trigger event */
  id: string
  /** ID of the alert that was triggered */
  alert_id: string
  /** ISO 8601 timestamp when the alert was triggered */
  triggered_at: string
  /** Array of message IDs that caused the alert to trigger */
  message_ids: string[]
  /** Optional summary text describing why the alert triggered */
  summary?: string | null
}

export interface StatsOverview {
  /** Total number of messages in the system */
  total_messages: number
  /** Number of channels currently being monitored */
  active_channels: number
  /** Number of messages received in the last 24 hours */
  messages_last_24h: number
  /** Number of duplicate messages detected in the last 24 hours */
  duplicates_last_24h: number
  /** Total number of AI-generated summaries */
  summaries_total: number
}

export interface MessagesByDay {
  /** Date string in ISO 8601 format (YYYY-MM-DD) */
  date: string
  /** Number of messages received on this date */
  count: number
}

export interface MessagesByChannel {
  /** Unique identifier for the channel */
  channel_id: string
  /** Display title of the channel */
  channel_title: string
  /** Number of messages from this channel */
  count: number
}

export interface ChannelInfoUpdate {
  /** ID of the channel that was updated */
  channel_id: string
  /** Updated subscriber count for the channel */
  subscriber_count: number
  /** Updated display title of the channel */
  title: string
  /** Whether the update operation succeeded */
  success: boolean
  /** Error message if the update failed (undefined if successful) */
  error?: string
}

export interface BulkChannelFailure {
  /** Username of the channel that failed to be added */
  username: string
  /** Error message describing why the channel couldn't be added */
  error: string
}

export interface BulkAddResponse {
  /** Array of successfully added channel objects */
  succeeded: Channel[]
  /** Array of failures with usernames and error messages */
  failed: BulkChannelFailure[]
  /** Total number of channels attempted */
  total: number
  /** Number of channels successfully added */
  success_count: number
  /** Number of channels that failed to be added */
  failure_count: number
}

export interface CuratedCollection {
  id: string
  name: string
  description: string | null
  region: string | null
  topic: string | null
  curator: string | null
  channel_count: number
  curated_channel_usernames: string[]
  thumbnail_url: string | null
  last_curated_at: string | null
}

export interface Notification {
  id: string
  user_id: string
  type: string
  title: string
  body?: string | null
  link?: string | null
  is_read: boolean
  metadata?: Record<string, unknown> | null
  created_at: string
}

export interface NotificationListResponse {
  notifications: Notification[]
  unread_count: number
  total: number
}

export interface DashboardData {
  /** Overview statistics for the dashboard */
  overview: StatsOverview
  /** Daily message count trend data for charting */
  messages_by_day: MessagesByDay[]
  /** Top channels by message count with channel details */
  messages_by_channel: MessagesByChannel[]
  /** Trust metrics including primary sources and propaganda rates */
  trust_stats: TrustStats
  /** API usage and cost statistics */
  api_usage: ApiUsageStats
  /** Translation cache performance metrics */
  translation_metrics: TranslationMetrics
  /** Array of all channels in the system */
  channels: Channel[]
  /** Array of all collections for the current user */
  collections: Collection[]
}
