import re
from typing import List, Dict, Set, Tuple
from datetime import datetime
from config.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class EventDetector:
    """Detect stock market events from news articles."""

    def __init__(self):
        self.event_keywords = Config.EVENT_KEYWORDS
        self.ticker_pattern = re.compile(r"\$?([A-Z]{1,5})\b")

    def detect_events(self, articles: List[Dict]) -> List[Dict]:
        """
        Detect events from articles and extract relevant stocks.

        Args:
            articles: List of news articles from NewsAPI

        Returns:
            List of detected events with associated tickers and metadata
        """
        detected_events = []

        for article in articles:
            title = article.get("title", "")
            description = article.get("description", "")
            url = article.get("url", "")
            published_at = article.get("publishedAt", "")
            source = article.get("source", {}).get("name", "")

            # Combine title and description for analysis
            full_text = f"{title} {description}".lower()

            # Detect event type
            event_type = self._detect_event_type(full_text)

            if event_type:
                # Extract ticker symbols
                tickers = self._extract_tickers(title, description)

                if tickers:
                    event = {
                        "event_type": event_type,
                        "title": title,
                        "description": description,
                        "tickers": list(tickers),
                        "url": url,
                        "published_at": published_at,
                        "source": source,
                        "detected_at": datetime.now().isoformat(),
                    }
                    detected_events.append(event)
                    logger.info(f"Detected {event_type} event: {tickers}")

        return detected_events

    def _detect_event_type(self, text: str) -> str:
        """Determine the type of event from text."""
        text_lower = text.lower()

        for event_type, keywords in self.event_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return event_type

        return None

    def _extract_tickers(self, title: str, description: str = "") -> Set[str]:
        """
        Extract stock ticker symbols from text.

        Strategy:
        1. Look for explicit $TICKER format
        2. Extract uppercase words that could be tickers (2-5 letters)
        3. Filter known stocks using common exchanges
        """
        tickers = set()

        # Combine text
        full_text = f"{title} {description}"

        # Find explicit $TICKER format
        dollar_tickers = re.findall(r"\$([A-Z]{1,5})\b", full_text)
        tickers.update(dollar_tickers)

        # Find potential ticker symbols (consecutive uppercase letters)
        potential_tickers = re.findall(r"\b([A-Z]{1,5})\b", title)

        # Filter - prioritize tickers that appear in title
        # Remove common words that aren't tickers
        exclude_words = {
            "THE", "AND", "FOR", "ARE", "BUT", "NOT", "YOU", "ALL", "CAN",
            "HER", "WAS", "ONE", "OUR", "OUT", "DAY", "GET", "HAS", "HIM",
            "HIS", "HOW", "ITS", "MAY", "NEW", "NOW", "OLD", "SEE", "TWO",
            "WAY", "WHO", "BOY", "DID", "ITS", "LET", "PUT", "SAY", "SHE",
            "TOO", "USE", "WILL", "WOULD", "COULD", "SHOULD", "ABOUT",
            "STOCK", "TRADING", "MARKET", "SEC", "NYSE", "NASDAQ", "TECH"
        }

        for ticker in potential_tickers:
            if len(ticker) >= 1 and ticker not in exclude_words:
                tickers.add(ticker)

        # Remove duplicates and return top candidates
        return tickers

    def filter_events_by_type(self, events: List[Dict], event_types: List[str]) -> List[Dict]:
        """Filter detected events by type."""
        return [e for e in events if e["event_type"] in event_types]

    def get_stocks_by_event_type(self, events: List[Dict]) -> Dict[str, Set[str]]:
        """
        Group stocks by event type.

        Returns:
            Dictionary mapping event type to set of tickers
        """
        grouped = {}

        for event in events:
            event_type = event["event_type"]
            tickers = set(event["tickers"])

            if event_type not in grouped:
                grouped[event_type] = set()

            grouped[event_type].update(tickers)

        return grouped
