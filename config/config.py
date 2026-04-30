import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration settings for the stock analysis application."""

    NEWS_API_KEY = os.getenv("NEWS_API_KEY")
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///stock_analysis.db")

    UPDATE_INTERVAL_MINUTES = int(os.getenv("UPDATE_INTERVAL_MINUTES", 60))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Event detection keywords
    EVENT_KEYWORDS = {
        "earnings": ["earnings", "quarterly report", "Q1", "Q2", "Q3", "Q4", "financial results"],
        "acquisition": ["acquisition", "acquired", "acquired by", "merger", "merged with"],
        "contract": ["contract", "agreement", "deal", "partnership", "collaboration"],
        "product": ["product launch", "new product", "launched", "release"],
        "regulatory": ["fda approval", "regulatory", "approval", "certification"],
        "bankruptcy": ["bankruptcy", "bankrupt", "filing", "chapter 11"],
        "executive": ["ceo", "cfo", "resignation", "appointed", "executive change"],
    }

    # Stock market hours (EST)
    MARKET_OPEN_HOUR = 9
    MARKET_OPEN_MINUTE = 30
    MARKET_CLOSE_HOUR = 16
    MARKET_CLOSE_MINUTE = 0

    # Data collection parameters
    NEWS_FETCH_COUNTRY = "us"
    NEWS_SORT_BY = "publishedAt"
    DAYS_BACK = 3

    # API endpoints
    NEWS_API_ENDPOINT = "https://newsapi.org/v2"
    ALPHA_VANTAGE_ENDPOINT = "https://www.alphavantage.co/query"
