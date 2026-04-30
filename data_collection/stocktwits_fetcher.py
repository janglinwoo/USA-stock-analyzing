import requests
from typing import List, Dict, Optional
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger(__name__)


class StockTwitsFetcher:
    """Fetch stock sentiment data from StockTwits."""

    API_BASE = "https://api.stocktwits.com/api/2"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )

    def get_symbol_info(self, ticker: str) -> Optional[Dict]:
        """
        Get symbol information from StockTwits.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with symbol metadata
        """
        url = f"{self.API_BASE}/symbols/lookup"
        params = {"q": ticker}

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("results"):
                symbol = data["results"][0]
                return {
                    "symbol": symbol.get("symbol"),
                    "title": symbol.get("title"),
                    "description": symbol.get("description"),
                    "exchange": symbol.get("exchange"),
                    "type": symbol.get("type"),
                }

            logger.warning(f"Symbol {ticker} not found on StockTwits")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching symbol info: {e}")
            return None

    def get_symbol_messages(self, ticker: str, limit: int = 30) -> List[Dict]:
        """
        Get recent messages (cashtags) for a symbol.

        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of messages to fetch

        Returns:
            List of messages with sentiment and engagement
        """
        url = f"{self.API_BASE}/symbols/{ticker.upper()}/messages"
        params = {"limit": min(limit, 30)}  # API max is 30

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            messages = []
            for msg in data.get("messages", []):
                user_followers = msg.get("user", {}).get("followers_count", 0)
                likes = msg.get("likes", 0)
                replies = msg.get("conversation_replies", 0)
                sentiment = msg.get("sentiment")  # bullish, bearish, neutral

                messages.append(
                    {
                        "id": msg.get("id"),
                        "body": msg.get("body"),
                        "created_at": msg.get("created_at"),
                        "user": msg.get("user", {}).get("username", ""),
                        "user_followers": user_followers,
                        "likes": likes,
                        "replies": replies,
                        "sentiment": sentiment,
                        "engagement_score": likes + replies + (user_followers / 1000),
                    }
                )

            logger.info(f"Fetched {len(messages)} messages for {ticker}")
            return messages

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching messages for {ticker}: {e}")
            return []

    def get_symbol_trending(self) -> List[Dict]:
        """Get trending symbols on StockTwits."""
        url = f"{self.API_BASE}/trending/symbols"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            symbols = []
            for symbol in data.get("symbols", []):
                symbols.append(
                    {
                        "symbol": symbol.get("symbol"),
                        "title": symbol.get("title"),
                        "watchlist_count": symbol.get("watchlist_count", 0),
                    }
                )

            logger.info(f"Fetched {len(symbols)} trending symbols")
            return symbols

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching trending symbols: {e}")
            return []

    def get_sentiment_summary(self, ticker: str) -> Dict:
        """
        Get sentiment summary for a symbol.

        Returns:
            Dictionary with bullish/bearish ratio and other metrics
        """
        messages = self.get_symbol_messages(ticker, limit=100)

        if not messages:
            logger.warning(f"No sentiment data available for {ticker}")
            return {}

        sentiments = [msg.get("sentiment") for msg in messages if msg.get("sentiment")]
        bullish_count = sentiments.count("bullish")
        bearish_count = sentiments.count("bearish")
        neutral_count = sentiments.count("neutral")
        total_sentiment = bullish_count + bearish_count + neutral_count

        avg_engagement = (
            sum(msg.get("engagement_score", 0) for msg in messages) / len(messages)
        )

        bullish_ratio = bullish_count / total_sentiment if total_sentiment > 0 else 0
        bearish_ratio = bearish_count / total_sentiment if total_sentiment > 0 else 0

        return {
            "ticker": ticker,
            "total_messages": len(messages),
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "neutral_count": neutral_count,
            "bullish_ratio": bullish_ratio,
            "bearish_ratio": bearish_ratio,
            "sentiment_score": (bullish_count - bearish_count) / total_sentiment
            if total_sentiment > 0
            else 0,
            "avg_engagement": avg_engagement,
            "top_messages": sorted(messages, key=lambda x: x.get("engagement_score", 0), reverse=True)[:5],
        }

    def get_comprehensive_sentiment(self, ticker: str) -> Dict:
        """
        Get comprehensive sentiment data from StockTwits.

        Returns:
            Dictionary with messages and sentiment summary
        """
        symbol_info = self.get_symbol_info(ticker)
        sentiment = self.get_sentiment_summary(ticker)

        return {
            "ticker": ticker,
            "symbol_info": symbol_info,
            "sentiment": sentiment,
        }
