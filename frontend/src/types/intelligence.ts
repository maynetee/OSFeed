export interface EntityRef {
  id: string;
  name: string;
  type: "ORG" | "LOC" | "PER" | "MISC";
  frequency: number;
}

export interface ClusterBase {
  id: string;
  title?: string;
  summary?: string;
  message_count: number;
  sentiment_score?: number;
  urgency_score?: number;
  updated_at: string;
  first_message_at?: string;
  primary_source_channel_id?: string;
  velocity?: number;
  emergence_score?: number;
  structured_summary?: {
    headline: string;
    bullets: string[];
    context: string;
  };
}

export interface ClusterList extends ClusterBase {}

export interface ClusterDetail extends ClusterBase {
  messages_preview: Array<{
    id: string;
    text: string;
  }>;
  entities: EntityRef[];
  timeline: Array<{
    time: string;
    count: number;
  }>;
}

export interface IntelligenceDashboard {
  hot_topics: ClusterList[];
  top_entities: Record<string, EntityRef[]>;
  global_tension: number;
}
