export interface Prediction {
  ticker: string;
  prediction_date: string;
  direction_prediction: number; // 1 = up, 0 = down
  direction_confidence: number;
  predicted_price_change: number;
  predicted_price_range_low: number;
  predicted_price_range_high: number;
  current_price: number;
  combined_sentiment: number;
  momentum_score: number;
  model_version: string;
}

export interface PredictionHistory {
  ticker: string;
  predictions: Prediction[];
  total_count: number;
}

export interface SystemStatus {
  status: string;
  timestamp: string;
  uptime_seconds: number;
  scheduled_jobs: number;
  recent_predictions_count: number;
  database_connected: boolean;
}

export interface JobStatus {
  job_id: string;
  job_name: string;
  is_active: boolean;
  next_run_time: string | null;
}

export interface PerformanceMetrics {
  metric_date: string;
  accuracy: number | null;
  precision: number | null;
  recall: number | null;
  f1_score: number | null;
  rmse: number | null;
  r2_score: number | null;
  win_rate: number | null;
  total_return: number | null;
}

export interface MarketEvent {
  ticker: string;
  event_type: string;
  event_title: string;
  event_date: string;
  source: string;
  url: string;
}

export interface SentimentSummary {
  ticker: string;
  average_sentiment: number;
  news_sentiment: number;
  reddit_sentiment: number;
  stocktwits_sentiment: number;
  recent_events: MarketEvent[];
}

export interface HealthCheck {
  status: string;
  message: string;
  timestamp: string;
  components: Record<string, string>;
}

export interface PredictionAccuracy {
  total: number;
  correct: number;
  accuracy: number;
  date_range_days: number;
}
