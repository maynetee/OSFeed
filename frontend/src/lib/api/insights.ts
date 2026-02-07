import { api } from './axios-instance'

export interface SignalsProcessed {
  today: number
  this_week: number
  all_time: number
}

export interface IntelligenceTip {
  title: string
  description: string
  severity: 'info' | 'warning' | 'critical'
}

export interface TrendingTopic {
  topic: string
  count: number
}

export interface ActivitySpike {
  channel_id: string
  channel_title: string
  today_count: number
  daily_average: number
  ratio: number
}

export interface InsightsDashboardData {
  signals_processed: SignalsProcessed
  intelligence_tips: IntelligenceTip[]
  trending_topics: TrendingTopic[]
  activity_spikes: ActivitySpike[]
}

export const insightsApi = {
  dashboard: () => api.get<InsightsDashboardData>('/api/insights/dashboard'),
}
