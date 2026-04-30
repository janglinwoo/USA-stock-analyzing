from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PredictionRequest(BaseModel):
    """Request model for making a prediction."""

    ticker: str
    days_back: Optional[int] = 1


class PredictionResponse(BaseModel):
    """Response model for a prediction."""

    ticker: str
    prediction_date: datetime
    direction_prediction: int  # 1 = up, 0 = down
    direction_confidence: float  # 0-1
    predicted_price_change: float  # percentage
    predicted_price_range_low: float
    predicted_price_range_high: float
    current_price: float
    combined_sentiment: float
    momentum_score: float
    model_version: str


class PredictionHistoryResponse(BaseModel):
    """Response for prediction history."""

    ticker: str
    predictions: List[PredictionResponse]
    total_count: int


class StatusResponse(BaseModel):
    """Response for system status."""

    status: str  # "running", "idle", "error"
    timestamp: datetime
    uptime_seconds: float
    scheduled_jobs: int
    recent_predictions_count: int
    database_connected: bool


class JobStatus(BaseModel):
    """Status of a scheduled job."""

    job_id: str
    job_name: str
    is_active: bool
    next_run_time: Optional[datetime]


class PerformanceMetricsResponse(BaseModel):
    """Response for model performance metrics."""

    metric_date: datetime
    accuracy: Optional[float]
    precision: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]
    rmse: Optional[float]
    r2_score: Optional[float]
    win_rate: Optional[float]
    total_return: Optional[float]


class EventResponse(BaseModel):
    """Response for detected market event."""

    ticker: str
    event_type: str
    event_title: str
    event_date: datetime
    source: str
    url: str


class SentimentSummaryResponse(BaseModel):
    """Response for sentiment summary."""

    ticker: str
    average_sentiment: float
    news_sentiment: float
    reddit_sentiment: float
    stocktwits_sentiment: float
    recent_events: List[EventResponse]


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str
    message: str
    timestamp: datetime
    components: dict  # Status of each component
