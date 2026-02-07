import { api } from './axios-instance'

// === Escalation Types ===

export interface EscalationTrendPoint {
  date: string
  high_count: number
  medium_count: number
  low_count: number
  avg_score: number
}

export interface EscalationTrendResponse {
  period: string
  trend: EscalationTrendPoint[]
  total_high: number
  total_medium: number
  total_low: number
}

// === Correlation Types ===

export interface CorrelationResponse {
  id: string
  duplicate_group_id: string
  analysis_text: string | null
  consistent_facts: string[]
  unique_details: string[]
  contradictions: string[]
  source_count: number
  created_at: string
}

export interface CorrelationListResponse {
  correlations: CorrelationResponse[]
  total: number
}

// === Pattern Types ===

export interface DetectedPatternResponse {
  id: string
  pattern_type: string
  title: string
  description: string | null
  evidence_message_ids: string[]
  confidence: number
  detected_at: string
  expires_at: string | null
}

export interface PatternListResponse {
  patterns: DetectedPatternResponse[]
  total: number
}

// === Timeline Types ===

export interface TimelineEvent {
  date: string
  description: string
  sources: string[]
  significance: number
}

export interface TimelineResponse {
  id: string
  user_id: string
  title: string
  topic: string | null
  collection_id: string | null
  events: TimelineEvent[]
  date_range_start: string | null
  date_range_end: string | null
  message_count: number
  created_at: string
}

export interface TimelineListResponse {
  timelines: TimelineResponse[]
  total: number
}

export interface TimelineGenerateRequest {
  topic?: string
  collection_id?: string
  start_date?: string
  end_date?: string
}

// === API Client ===

export const analysisApi = {
  // Escalation
  getEscalationTrend: (params?: { collection_id?: string; period?: string }) =>
    api.get<EscalationTrendResponse>('/api/analysis/escalation', { params }),

  // Correlations
  listCorrelations: (limit = 10) =>
    api.get<CorrelationListResponse>('/api/analysis/correlations', { params: { limit } }),

  getCorrelation: (duplicateGroupId: string) =>
    api.get<CorrelationResponse>(`/api/analysis/correlations/${duplicateGroupId}`),

  // Patterns
  listPatterns: (params?: { period?: string; limit?: number }) =>
    api.get<PatternListResponse>('/api/analysis/patterns', { params }),

  getPattern: (patternId: string) =>
    api.get<DetectedPatternResponse>(`/api/analysis/patterns/${patternId}`),

  // Timelines
  generateTimeline: (request: TimelineGenerateRequest) =>
    api.post<TimelineResponse>('/api/analysis/timeline/generate', request),

  listTimelines: (limit = 20) =>
    api.get<TimelineListResponse>('/api/analysis/timelines', { params: { limit } }),

  getTimeline: (timelineId: string) =>
    api.get<TimelineResponse>(`/api/analysis/timelines/${timelineId}`),

  deleteTimeline: (timelineId: string) =>
    api.delete(`/api/analysis/timelines/${timelineId}`),
}
