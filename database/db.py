from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

Base = declarative_base()


class Prediction(Base):
    """Prediction record for a stock."""

    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False, index=True)
    prediction_date = Column(DateTime, default=datetime.now, nullable=False, index=True)

    # Direction prediction
    direction_prediction = Column(Integer)  # 1 = up, 0 = down
    direction_confidence = Column(Float)  # Probability

    # Price prediction
    predicted_price_change = Column(Float)  # Percentage change
    predicted_price_range_low = Column(Float)  # Low estimate
    predicted_price_range_high = Column(Float)  # High estimate

    # Current market data
    current_price = Column(Float)
    current_rsi = Column(Float)
    current_volume = Column(Float)

    # Sentiment scores
    news_sentiment = Column(Float)
    reddit_sentiment = Column(Float)
    stocktwits_sentiment = Column(Float)
    combined_sentiment = Column(Float)

    # Events detected
    events_detected = Column(Text)  # JSON string of detected events
    momentum_score = Column(Float)

    # Actual outcome (populated later)
    actual_price_close = Column(Float)
    actual_price_change = Column(Float)
    outcome_date = Column(DateTime)
    is_correct_direction = Column(Boolean)

    # Metadata
    model_version = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Prediction(ticker={self.ticker}, date={self.prediction_date}, direction={self.direction_prediction})>"


class MarketEvent(Base):
    """Detected market events."""

    __tablename__ = "market_events"

    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # earnings, acquisition, etc.
    event_title = Column(String(255))
    event_description = Column(Text)
    event_date = Column(DateTime, nullable=False)
    source = Column(String(100))
    url = Column(Text)
    detected_at = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<MarketEvent(ticker={self.ticker}, type={self.event_type}, date={self.event_date})>"


class PerformanceMetric(Base):
    """Track model performance metrics over time."""

    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True)
    metric_date = Column(DateTime, default=datetime.now, index=True)

    # Classification metrics
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    roc_auc = Column(Float)

    # Regression metrics
    rmse = Column(Float)
    mae = Column(Float)
    r2_score = Column(Float)

    # Backtest metrics
    win_rate = Column(Float)
    total_return = Column(Float)
    sharpe_ratio = Column(Float)

    # Metadata
    predictions_count = Column(Integer)
    model_version = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<PerformanceMetric(date={self.metric_date}, f1={self.f1_score})>"


class Database:
    """Database manager for the stock analysis system."""

    def __init__(self, db_url: str = None):
        """
        Initialize database connection.

        Args:
            db_url: Database URL (defaults to SQLite)
        """
        if db_url is None:
            # Default to SQLite
            db_url = "sqlite:///./stock_analysis.db"

        logger.info(f"Connecting to database: {db_url}")

        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Create tables
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created/verified")

    def get_session(self):
        """Get a new database session."""
        return self.SessionLocal()

    def add_prediction(self, session, prediction_data: dict) -> Prediction:
        """Add a new prediction record."""
        try:
            prediction = Prediction(**prediction_data)
            session.add(prediction)
            session.commit()
            logger.info(f"Added prediction for {prediction_data.get('ticker')}")
            return prediction
        except Exception as e:
            logger.error(f"Error adding prediction: {e}")
            session.rollback()
            return None

    def get_latest_predictions(self, session, ticker: str, limit: int = 10) -> list:
        """Get latest predictions for a ticker."""
        try:
            predictions = (
                session.query(Prediction)
                .filter(Prediction.ticker == ticker.upper())
                .order_by(Prediction.prediction_date.desc())
                .limit(limit)
                .all()
            )
            return predictions
        except Exception as e:
            logger.error(f"Error fetching predictions: {e}")
            return []

    def get_predictions_by_date_range(
        self, session, start_date: datetime, end_date: datetime
    ) -> list:
        """Get predictions within a date range."""
        try:
            predictions = (
                session.query(Prediction)
                .filter(
                    Prediction.prediction_date >= start_date,
                    Prediction.prediction_date <= end_date,
                )
                .order_by(Prediction.prediction_date.desc())
                .all()
            )
            return predictions
        except Exception as e:
            logger.error(f"Error fetching predictions by date: {e}")
            return []

    def add_market_event(self, session, event_data: dict) -> MarketEvent:
        """Add a market event record."""
        try:
            event = MarketEvent(**event_data)
            session.add(event)
            session.commit()
            logger.info(f"Added event for {event_data.get('ticker')}")
            return event
        except Exception as e:
            logger.error(f"Error adding event: {e}")
            session.rollback()
            return None

    def get_recent_events(self, session, ticker: str = None, limit: int = 50) -> list:
        """Get recent market events."""
        try:
            query = session.query(MarketEvent)

            if ticker:
                query = query.filter(MarketEvent.ticker == ticker.upper())

            events = query.order_by(MarketEvent.event_date.desc()).limit(limit).all()
            return events
        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            return []

    def add_performance_metric(self, session, metric_data: dict) -> PerformanceMetric:
        """Add a performance metric record."""
        try:
            metric = PerformanceMetric(**metric_data)
            session.add(metric)
            session.commit()
            logger.info("Added performance metric")
            return metric
        except Exception as e:
            logger.error(f"Error adding metric: {e}")
            session.rollback()
            return None

    def get_latest_metrics(self, session) -> PerformanceMetric:
        """Get latest performance metrics."""
        try:
            metric = (
                session.query(PerformanceMetric)
                .order_by(PerformanceMetric.metric_date.desc())
                .first()
            )
            return metric
        except Exception as e:
            logger.error(f"Error fetching metrics: {e}")
            return None

    def update_prediction_outcome(
        self, session, prediction_id: int, outcome_data: dict
    ) -> bool:
        """Update prediction with actual outcome."""
        try:
            prediction = session.query(Prediction).filter_by(id=prediction_id).first()

            if prediction:
                for key, value in outcome_data.items():
                    setattr(prediction, key, value)

                session.commit()
                logger.info(f"Updated prediction {prediction_id} with outcome")
                return True

            return False
        except Exception as e:
            logger.error(f"Error updating prediction: {e}")
            session.rollback()
            return False

    def get_prediction_accuracy(self, session, days_back: int = 30) -> dict:
        """Calculate prediction accuracy metrics for recent predictions."""
        from datetime import timedelta
        from sqlalchemy import func

        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)

            predictions = (
                session.query(Prediction)
                .filter(
                    Prediction.prediction_date >= cutoff_date,
                    Prediction.is_correct_direction.isnot(None),
                )
                .all()
            )

            if not predictions:
                return {"total": 0, "accuracy": 0}

            correct = sum(1 for p in predictions if p.is_correct_direction)
            accuracy = correct / len(predictions) if predictions else 0

            return {
                "total": len(predictions),
                "correct": correct,
                "accuracy": accuracy,
                "date_range_days": days_back,
            }

        except Exception as e:
            logger.error(f"Error calculating accuracy: {e}")
            return {"total": 0, "accuracy": 0}

    def close(self):
        """Close database connection."""
        self.engine.dispose()
        logger.info("Database connection closed")
