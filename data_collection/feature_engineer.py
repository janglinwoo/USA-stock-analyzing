from typing import Dict, List
import pandas as pd
import numpy as np
from utils.logger import setup_logger

logger = setup_logger(__name__)


class FeatureEngineer:
    """Create features from collected data for ML models."""

    def __init__(self):
        pass

    def create_features(
        self,
        ticker: str,
        events: List[Dict],
        news_sentiment: Dict,
        reddit_data: Dict,
        stocktwits_data: Dict,
        stock_indicators: Dict,
    ) -> Dict:
        """
        Create comprehensive feature set from all collected data.

        Args:
            ticker: Stock ticker
            events: Detected events for the stock
            news_sentiment: Sentiment analysis of news articles
            reddit_data: Reddit engagement metrics
            stocktwits_data: StockTwits sentiment data
            stock_indicators: Technical indicators

        Returns:
            Dictionary with all features
        """
        features = {
            "ticker": ticker,
            "timestamp": pd.Timestamp.now().isoformat(),
        }

        # Event features
        event_features = self._extract_event_features(events)
        features.update(event_features)

        # News sentiment features
        news_features = self._extract_news_features(news_sentiment)
        features.update(news_features)

        # Reddit features
        reddit_features = self._extract_reddit_features(reddit_data)
        features.update(reddit_features)

        # StockTwits features
        stocktwits_features = self._extract_stocktwits_features(stocktwits_data)
        features.update(stocktwits_features)

        # Technical indicator features
        technical_features = self._extract_technical_features(stock_indicators)
        features.update(technical_features)

        # Combined sentiment score
        features["combined_sentiment_score"] = (
            self._calculate_combined_sentiment(
                news_features, reddit_features, stocktwits_features
            )
        )

        # Momentum score
        features["momentum_score"] = self._calculate_momentum_score(
            features
        )

        return features

    def _extract_event_features(self, events: List[Dict]) -> Dict:
        """Extract event-related features."""
        if not events:
            return {
                "has_earnings": 0,
                "has_acquisition": 0,
                "has_contract": 0,
                "has_product_launch": 0,
                "has_regulatory": 0,
                "has_bankruptcy": 0,
                "has_executive_change": 0,
                "total_events": 0,
                "event_recency_hours": None,
            }

        event_types = {
            "earnings": 0,
            "acquisition": 0,
            "contract": 0,
            "product": 0,
            "regulatory": 0,
            "bankruptcy": 0,
            "executive": 0,
        }

        for event in events:
            event_type = event.get("event_type", "").lower()
            if event_type in event_types:
                event_types[event_type] = 1

        # Calculate recency
        if events:
            from datetime import datetime
            latest_event = events[0]
            event_time = pd.to_datetime(latest_event.get("detected_at"))
            time_diff = pd.Timestamp.now() - event_time
            recency_hours = time_diff.total_seconds() / 3600
        else:
            recency_hours = None

        return {
            "has_earnings": event_types["earnings"],
            "has_acquisition": event_types["acquisition"],
            "has_contract": event_types["contract"],
            "has_product_launch": event_types["product"],
            "has_regulatory": event_types["regulatory"],
            "has_bankruptcy": event_types["bankruptcy"],
            "has_executive_change": event_types["executive"],
            "total_events": len(events),
            "event_recency_hours": recency_hours,
        }

    def _extract_news_features(self, news_sentiment: Dict) -> Dict:
        """Extract news sentiment features."""
        if not news_sentiment:
            return {
                "news_avg_sentiment": 0,
                "news_positive_ratio": 0,
                "news_negative_ratio": 0,
                "news_neutral_ratio": 1,
                "news_total_articles": 0,
                "news_sentiment_strength": 0,
            }

        return {
            "news_avg_sentiment": news_sentiment.get("average_sentiment_score", 0),
            "news_positive_ratio": news_sentiment.get("positive_ratio", 0),
            "news_negative_ratio": news_sentiment.get("negative_ratio", 0),
            "news_neutral_ratio": news_sentiment.get("neutral_ratio", 1),
            "news_total_articles": news_sentiment.get("total_articles", 0),
            "news_sentiment_strength": abs(
                news_sentiment.get("average_sentiment_score", 0)
            ),
        }

    def _extract_reddit_features(self, reddit_data: Dict) -> Dict:
        """Extract Reddit engagement features."""
        if not reddit_data or not reddit_data.get("metrics"):
            return {
                "reddit_total_posts": 0,
                "reddit_total_comments": 0,
                "reddit_avg_post_score": 0,
                "reddit_avg_engagement": 0,
                "reddit_total_engagement": 0,
                "reddit_mentions_density": 0,
            }

        metrics = reddit_data.get("metrics", {})

        total_posts = metrics.get("total_posts", 0)
        total_comments = metrics.get("total_comments", 0)
        total_engagement = metrics.get("total_engagement", 0)

        return {
            "reddit_total_posts": total_posts,
            "reddit_total_comments": total_comments,
            "reddit_avg_post_score": metrics.get("avg_post_score", 0),
            "reddit_avg_engagement": metrics.get("avg_post_engagement", 0),
            "reddit_total_engagement": total_engagement,
            "reddit_mentions_density": total_posts / (
                total_posts + total_comments + 1
            ),  # Avoid division by zero
        }

    def _extract_stocktwits_features(self, stocktwits_data: Dict) -> Dict:
        """Extract StockTwits sentiment features."""
        sentiment = stocktwits_data.get("sentiment", {})

        if not sentiment:
            return {
                "stocktwits_total_messages": 0,
                "stocktwits_bullish_ratio": 0,
                "stocktwits_bearish_ratio": 0,
                "stocktwits_sentiment_score": 0,
                "stocktwits_avg_engagement": 0,
                "stocktwits_bullish_momentum": 0,
            }

        bullish_ratio = sentiment.get("bullish_ratio", 0)
        bearish_ratio = sentiment.get("bearish_ratio", 0)
        sentiment_score = sentiment.get("sentiment_score", 0)
        total_messages = sentiment.get("total_messages", 0)

        # Bullish momentum: bullish_ratio - bearish_ratio
        bullish_momentum = bullish_ratio - bearish_ratio

        return {
            "stocktwits_total_messages": total_messages,
            "stocktwits_bullish_ratio": bullish_ratio,
            "stocktwits_bearish_ratio": bearish_ratio,
            "stocktwits_sentiment_score": sentiment_score,
            "stocktwits_avg_engagement": sentiment.get("avg_engagement", 0),
            "stocktwits_bullish_momentum": bullish_momentum,
        }

    def _extract_technical_features(self, indicators: Dict) -> Dict:
        """Extract technical indicator features."""
        if not indicators:
            return {
                "rsi": None,
                "macd": None,
                "macd_signal": None,
                "bollinger_position": None,
                "sma_20": None,
                "sma_50": None,
                "volume_ratio": None,
            }

        close_price = indicators.get("current_price", None)
        bb_low = indicators.get("bollinger_low")
        bb_mid = indicators.get("bollinger_mid")
        bb_high = indicators.get("bollinger_high")

        # Calculate Bollinger Band position (0-1, where 0 is at low, 1 is at high)
        bollinger_position = None
        if bb_low and bb_high and bb_high > bb_low:
            bollinger_position = (close_price - bb_low) / (bb_high - bb_low) if close_price else None
            bollinger_position = max(0, min(1, bollinger_position)) if bollinger_position else None

        volume_current = indicators.get("current_volume", 0)
        volume_avg = indicators.get("volume_avg", 1)
        volume_ratio = volume_current / volume_avg if volume_avg > 0 else 1

        return {
            "rsi": indicators.get("rsi"),
            "macd": indicators.get("macd"),
            "macd_signal": indicators.get("macd_signal"),
            "bollinger_position": bollinger_position,
            "sma_20": indicators.get("sma_20"),
            "sma_50": indicators.get("sma_50"),
            "volume_ratio": volume_ratio,
        }

    def _calculate_combined_sentiment(
        self,
        news_features: Dict,
        reddit_features: Dict,
        stocktwits_features: Dict,
    ) -> float:
        """
        Calculate weighted combined sentiment score.

        Weights:
        - News: 40% (most reliable)
        - StockTwits: 35% (retail sentiment)
        - Reddit: 25% (engagement indicator)
        """
        news_sentiment = news_features.get("news_avg_sentiment", 0)
        stocktwits_sentiment = stocktwits_features.get(
            "stocktwits_sentiment_score", 0
        )
        reddit_engagement = reddit_features.get("reddit_total_engagement", 0)

        # Normalize reddit engagement to sentiment scale (-1 to 1)
        reddit_sentiment = min(1.0, reddit_engagement / 100) if reddit_engagement > 0 else 0

        combined = (
            (news_sentiment * 0.40)
            + (stocktwits_sentiment * 0.35)
            + (reddit_sentiment * 0.25)
        )

        return round(combined, 3)

    def _calculate_momentum_score(self, features: Dict) -> float:
        """
        Calculate momentum score based on multiple indicators.

        Factors:
        - Recent events (strong impact)
        - RSI (overbought/oversold)
        - Combined sentiment
        - Volume ratio
        """
        score = 0

        # Event recency (if event happened recently, strong momentum)
        event_recency = features.get("event_recency_hours")
        if event_recency is not None and event_recency < 24:
            score += 0.3  # Recent event boost

        # RSI indicator
        rsi = features.get("rsi")
        if rsi is not None:
            if rsi > 70:
                score += 0.2  # Overbought
            elif rsi < 30:
                score -= 0.2  # Oversold

        # Combined sentiment
        combined_sentiment = features.get("combined_sentiment_score", 0)
        score += combined_sentiment * 0.25

        # Volume ratio
        volume_ratio = features.get("volume_ratio", 1)
        if volume_ratio > 1.5:
            score += 0.15  # High volume
        elif volume_ratio < 0.7:
            score -= 0.1  # Low volume

        return round(max(-1.0, min(1.0, score)), 3)

    def create_feature_dataframe(self, features_list: List[Dict]) -> pd.DataFrame:
        """Convert list of feature dictionaries to DataFrame."""
        df = pd.DataFrame(features_list)
        return df

    def normalize_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize numerical features for ML models."""
        numerical_cols = df.select_dtypes(include=[np.number]).columns

        df_normalized = df.copy()
        for col in numerical_cols:
            if df[col].std() > 0:
                df_normalized[col] = (df[col] - df[col].mean()) / df[col].std()
            else:
                df_normalized[col] = 0

        return df_normalized
