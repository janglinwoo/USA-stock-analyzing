import requests
from datetime import datetime, timedelta
from typing import List, Dict
from config.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class NewsFetcher:
    """Fetch financial news from NewsAPI."""

    def __init__(self):
        self.api_key = Config.NEWS_API_KEY
        self.base_url = f"{Config.NEWS_API_ENDPOINT}/everything"

        if not self.api_key:
            logger.error("NEWS_API_KEY not configured. Please set it in .env file.")
            raise ValueError("NEWS_API_KEY is required")

    def fetch_news(self, keywords: str, days_back: int = None) -> List[Dict]:
        """
        Fetch news articles based on keywords.

        Args:
            keywords: Search query string
            days_back: Number of days to look back (default from Config)

        Returns:
            List of news articles with metadata
        """
        days_back = days_back or Config.DAYS_BACK
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        params = {
            "q": keywords,
            "from": from_date,
            "sortBy": Config.NEWS_SORT_BY,
            "language": "en",
            "apiKey": self.api_key,
            "pageSize": 100,
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "ok":
                logger.error(f"NewsAPI error: {data.get('message')}")
                return []

            articles = data.get("articles", [])
            logger.info(f"Fetched {len(articles)} articles for '{keywords}'")
            return articles

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching news: {e}")
            return []

    def fetch_stock_news(self, ticker: str, days_back: int = None) -> List[Dict]:
        """Fetch news for a specific stock ticker."""
        keywords = f"{ticker} OR {ticker.lower()}"
        return self.fetch_news(keywords, days_back)

    def fetch_financial_news(self, days_back: int = None) -> List[Dict]:
        """Fetch general financial news and market updates."""
        keywords = "stock market OR earnings OR merger OR acquisition"
        return self.fetch_news(keywords, days_back)
