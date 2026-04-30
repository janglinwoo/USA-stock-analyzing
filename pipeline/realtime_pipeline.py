import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple
from data_collection import (
    NewsFetcher,
    StockDataFetcher,
    EventDetector,
    SentimentAnalyzer,
    RedditFetcher,
    StockTwitsFetcher,
    FeatureEngineer,
)
from models import DirectionClassifier, PricePredictor
from database import Database, Prediction
from utils.logger import setup_logger

logger = setup_logger(__name__)


class RealtimePipeline:
    """Complete real-time prediction pipeline integrating all phases."""

    def __init__(self, db: Database, direction_model=None, price_model=None):
        """
        Initialize the pipeline.

        Args:
            db: Database instance
            direction_model: Trained direction classifier model
            price_model: Trained price predictor model
        """
        self.db = db
        self.direction_model = direction_model
        self.price_model = price_model

        # Initialize components
        self.news_fetcher = NewsFetcher()
        self.stock_fetcher = StockDataFetcher()
        self.event_detector = EventDetector()
        self.sentiment_analyzer = SentimentAnalyzer(use_transformer=False)  # Faster
        self.reddit_fetcher = RedditFetcher()
        self.stocktwits_fetcher = StockTwitsFetcher()
        self.feature_engineer = FeatureEngineer()

        logger.info("Real-time pipeline initialized")

    def run_full_pipeline(self, days_back: int = 1) -> List[Dict]:
        """
        Run the complete pipeline: Phase 1 → Phase 2 → Phase 3.

        Args:
            days_back: Number of days to look back for news

        Returns:
            List of prediction results for each detected stock
        """
        logger.info("=" * 60)
        logger.info("Starting Real-time Pipeline")
        logger.info("=" * 60)

        try:
            # Phase 1: Data Collection & Event Detection
            logger.info("\n[Phase 1] Detecting events...")
            detected_events, stocks_by_event = self._phase1_detect_events(days_back)

            if not detected_events:
                logger.warning("No events detected")
                return []

            # Get unique tickers
            all_tickers = set()
            for tickers in stocks_by_event.values():
                all_tickers.update(tickers)

            logger.info(f"Found {len(all_tickers)} stocks with events")

            # Phase 2: Sentiment Analysis & Feature Engineering
            logger.info("\n[Phase 2] Analyzing sentiment and creating features...")
            stock_features = self._phase2_create_features(
                detected_events, all_tickers
            )

            # Phase 3: Make Predictions
            logger.info("\n[Phase 3] Making predictions...")
            predictions = self._phase3_predict(stock_features)

            # Save to database
            logger.info("\n[Database] Saving predictions...")
            self._save_predictions_to_db(predictions)

            logger.info("=" * 60)
            logger.info("Pipeline Complete!")
            logger.info(f"Total predictions: {len(predictions)}")
            logger.info("=" * 60)

            return predictions

        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            return []

    def _phase1_detect_events(self, days_back: int) -> Tuple[List[Dict], Dict]:
        """Phase 1: Detect events and extract tickers."""
        try:
            # Fetch financial news
            financial_news = self.news_fetcher.fetch_financial_news(days_back=days_back)

            if not financial_news:
                logger.warning("No financial news found")
                return [], {}

            # Detect events
            detected_events = self.event_detector.detect_events(financial_news)
            stocks_by_event = self.event_detector.get_stocks_by_event_type(
                detected_events
            )

            # Save events to database
            session = self.db.get_session()
            for event in detected_events:
                event_data = {
                    "ticker": event["tickers"][0] if event["tickers"] else "UNKNOWN",
                    "event_type": event["event_type"],
                    "event_title": event["title"][:255],
                    "event_description": event.get("description", "")[:1000],
                    "event_date": datetime.fromisoformat(event["published_at"]),
                    "source": event["source"],
                    "url": event["url"],
                    "detected_at": datetime.now(),
                }
                for ticker in event["tickers"]:
                    event_data["ticker"] = ticker
                    self.db.add_market_event(session, event_data)

            session.close()

            return detected_events, stocks_by_event

        except Exception as e:
            logger.error(f"Error in Phase 1: {e}")
            return [], {}

    def _phase2_create_features(
        self, detected_events: List[Dict], tickers: set
    ) -> Dict[str, Dict]:
        """Phase 2: Sentiment analysis and feature engineering."""
        try:
            stock_features = {}

            for ticker in tickers:
                logger.info(f"Processing {ticker}...")

                # Get relevant events
                ticker_events = [
                    e for e in detected_events if ticker in e.get("tickers", [])
                ]

                # News sentiment
                ticker_articles = [
                    a
                    for a in detected_events
                    if ticker in a.get("tickers", [])
                ]
                news_sentiment = {}
                if ticker_articles:
                    ticker_articles = self.sentiment_analyzer.analyze_articles(
                        ticker_articles
                    )
                    news_sentiment = self.sentiment_analyzer.get_sentiment_summary(
                        ticker_articles
                    )

                # Community data
                reddit_data = self.reddit_fetcher.get_reddit_sentiment_data(
                    ticker, days_back=1
                )
                stocktwits_data = self.stocktwits_fetcher.get_comprehensive_sentiment(
                    ticker
                )

                # Technical indicators
                hist = self.stock_fetcher.get_stock_data(ticker, period="1mo")
                indicators = self.stock_fetcher.calculate_technical_indicators(hist)
                current_price = self.stock_fetcher.get_current_price(ticker)
                indicators["current_price"] = current_price

                # Create features
                features = self.feature_engineer.create_features(
                    ticker=ticker,
                    events=ticker_events,
                    news_sentiment=news_sentiment,
                    reddit_data=reddit_data,
                    stocktwits_data=stocktwits_data,
                    stock_indicators=indicators,
                )

                stock_features[ticker] = features

            return stock_features

        except Exception as e:
            logger.error(f"Error in Phase 2: {e}")
            return {}

    def _phase3_predict(self, stock_features: Dict[str, Dict]) -> List[Dict]:
        """Phase 3: Make predictions using trained models."""
        try:
            if not self.direction_model or not self.price_model:
                logger.error("Models not trained. Load models first.")
                return []

            predictions = []

            for ticker, features in stock_features.items():
                try:
                    # Extract feature values (in order used during training)
                    feature_dict = {
                        k: v
                        for k, v in features.items()
                        if k not in ["ticker", "timestamp"]
                    }

                    # Convert to array format for model
                    # For real implementation, need to load feature order from training
                    feature_values = np.array(
                        [list(feature_dict.values())]
                    ).astype(float)

                    # Handle NaN values
                    feature_values = np.nan_to_num(feature_values, 0)

                    # Get predictions
                    direction_pred, direction_conf = self.direction_model.predict(
                        feature_values
                    )
                    price_pred = self.price_model.predict(feature_values)

                    current_price = features.get("current_price", 0)

                    prediction_result = {
                        "ticker": ticker,
                        "prediction_date": datetime.now(),
                        "direction_prediction": int(direction_pred[0]),
                        "direction_confidence": float(direction_conf[0]),
                        "predicted_price_change": float(price_pred[0]),
                        "predicted_price_range_low": float(
                            current_price * (1 + (price_pred[0] - 2) / 100)
                        ),
                        "predicted_price_range_high": float(
                            current_price * (1 + (price_pred[0] + 2) / 100)
                        ),
                        "current_price": float(current_price),
                        "current_rsi": float(features.get("rsi") or 0),
                        "current_volume": float(
                            features.get("volume_ratio", 1) * 1000000
                        ),
                        "news_sentiment": float(
                            features.get("news_avg_sentiment", 0)
                        ),
                        "reddit_sentiment": float(
                            features.get("reddit_total_engagement", 0)
                        ),
                        "stocktwits_sentiment": float(
                            features.get("stocktwits_sentiment_score", 0)
                        ),
                        "combined_sentiment": float(
                            features.get("combined_sentiment_score", 0)
                        ),
                        "momentum_score": float(
                            features.get("momentum_score", 0)
                        ),
                        "model_version": "phase3_v1",
                    }

                    predictions.append(prediction_result)

                except Exception as e:
                    logger.error(f"Error predicting for {ticker}: {e}")
                    continue

            return predictions

        except Exception as e:
            logger.error(f"Error in Phase 3: {e}")
            return []

    def _save_predictions_to_db(self, predictions: List[Dict]) -> None:
        """Save predictions to database."""
        try:
            session = self.db.get_session()

            for pred in predictions:
                self.db.add_prediction(session, pred)

            session.close()
            logger.info(f"Saved {len(predictions)} predictions to database")

        except Exception as e:
            logger.error(f"Error saving predictions: {e}")

    def predict_single_stock(self, ticker: str) -> Dict:
        """Make prediction for a single stock."""
        logger.info(f"Making prediction for {ticker}...")

        try:
            # Run mini-pipeline for single ticker
            features = self._phase2_create_features([], {ticker})

            if ticker not in features:
                logger.warning(f"Could not create features for {ticker}")
                return {}

            predictions = self._phase3_predict({ticker: features[ticker]})

            if predictions:
                pred = predictions[0]
                self.db.add_prediction(self.db.get_session(), pred)
                return pred

            return {}

        except Exception as e:
            logger.error(f"Error predicting {ticker}: {e}")
            return {}

    def load_trained_models(
        self,
        direction_model_path: str = None,
        price_model_path: str = None,
    ) -> bool:
        """
        Load pre-trained models from pickle files.

        Args:
            direction_model_path: Path to saved direction classifier
            price_model_path: Path to saved price predictor

        Returns:
            True if models loaded successfully
        """
        import pickle

        try:
            if direction_model_path:
                with open(direction_model_path, "rb") as f:
                    self.direction_model = pickle.load(f)
                logger.info(f"Loaded direction model from {direction_model_path}")

            if price_model_path:
                with open(price_model_path, "rb") as f:
                    self.price_model = pickle.load(f)
                logger.info(f"Loaded price model from {price_model_path}")

            return self.direction_model is not None and self.price_model is not None

        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False
