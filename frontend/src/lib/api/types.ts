export interface Channel {
  id: string
  telegram_id: string | null
  username: string
  title: string
  description: string | null
  detected_language?: string | null
  subscriber_count: number
  tags?: string[] | null
  created_at: string
  last_fetched_at: string | null
  fetch_job?: FetchJobStatus | null
}

export interface FetchJobStatus {
  id: string
  channel_id: string
  days: number
  status: string
  stage?: string | null
  total_messages?: number | null
  new_messages?: number | null
  processed_messages?: number | null
  error_message?: string | null
  created_at: string
  started_at?: string | null
  finished_at?: string | null
}

export interface Message {
  id: string
  channel_id: string
  channel_title?: string | null
  channel_username?: string | null
  telegram_message_id: number
  original_text: string
  translated_text: string | null
  source_language: string | null
  target_language?: string | null
  media_type: string | null
  media_urls: string[] | null
  published_at: string
  fetched_at: string
  is_duplicate: boolean
  originality_score?: number | null
  duplicate_group_id: string | null
  entities?: {
    persons?: string[]
    locations?: string[]
    organizations?: string[]
  } | null
  needs_translation?: boolean
  translation_priority?: string | null
}

export interface TranslationUpdate {
  message_id: string
  channel_id: string
  translated_text: string
  source_language: string | null
  target_language: string | null
}

export interface MessageListResponse {
  messages: Message[]
  total: number
  page: number
  page_size: number
}

export interface Collection {
  id: string
  user_id: string
  name: string
  description?: string | null
  color?: string | null
  icon?: string | null
  is_default?: boolean
  is_global?: boolean
  parent_id?: string | null
  auto_assign_languages?: string[] | null
  auto_assign_keywords?: string[] | null
  auto_assign_tags?: string[] | null
  channel_ids: string[]
  created_at: string
  updated_at?: string | null
}

export interface CollectionStats {
  message_count: number
  message_count_24h: number
  message_count_7d: number
  channel_count: number
  top_channels: { channel_id: string; channel_title: string; count: number }[]
  activity_trend: { date: string; count: number }[]
  duplicate_rate: number
  languages: Record<string, number>
}

export interface TrustStats {
  primary_sources_rate: number
  propaganda_rate: number
  verified_channels: number
  total_messages_24h: number
}

export interface Alert {
  id: string
  collection_id: string
  user_id: string
  name: string
  keywords?: string[] | null
  entities?: string[] | null
  min_threshold: number
  frequency: string
  notification_channels?: string[] | null
  is_active: boolean
  last_triggered_at?: string | null
  created_at: string
  updated_at?: string | null
}

export interface AlertTrigger {
  id: string
  alert_id: string
  triggered_at: string
  message_ids: string[]
  summary?: string | null
}

export interface StatsOverview {
  total_messages: number
  active_channels: number
  messages_last_24h: number
  duplicates_last_24h: number
  summaries_total: number
}

export interface MessagesByDay {
  date: string
  count: number
}

export interface MessagesByChannel {
  channel_id: string
  channel_title: string
  count: number
}

export interface ChannelInfoUpdate {
  channel_id: string
  subscriber_count: number
  title: string
  success: boolean
  error?: string
}

export interface BulkChannelFailure {
  username: string
  error: string
}

export interface BulkAddResponse {
  succeeded: Channel[]
  failed: BulkChannelFailure[]
  total: number
  success_count: number
  failure_count: number
}
