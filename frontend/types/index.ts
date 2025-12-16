export interface AIAnalysis {
  summary: string;
  category: string;
  score: number;
  reasoning: string;
  tags: string[];
}

export interface SourceRef {
  source: string;
  source_id: string;
}

export interface DeepSeekEvaluation {
  version: number;
  model: string;
  overall_score: number;
  product_view: string;
  investor_view: string;
  market_view: string;
  recommendation: string;
  created_at: string;
}

export interface MetricPoint {
  recorded_at: string;
  value: number;
  rank?: number;
}

export interface Article {
  id: number;
  title: string;
  url: string;
  source: string;
  source_id: string;
  publish_date: string;
  first_seen_at?: string;
  last_seen_at?: string;
  seen_count?: number;
  sources?: SourceRef[];
  platforms_count?: number;
  analysis?: AIAnalysis;
  metrics_history?: MetricPoint[];
  evaluations?: DeepSeekEvaluation[];
}
