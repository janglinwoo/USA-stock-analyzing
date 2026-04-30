import requests
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from utils.logger import setup_logger

logger = setup_logger(__name__)


class RedditFetcher:
    """Fetch stock discussions from Reddit."""

    # Reddit Pushshift API endpoint (unofficial but widely used)
    PUSHSHIFT_API = "https://api.pushshift.io/reddit"

    # Popular stock subreddits
    STOCK_SUBREDDITS = [
        "stocks",
        "investing",
        "wallstreetbets",
        "stockmarket",
        "dividends",
        "SecurityAnalysis",
    ]

    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 10

    def get_subreddit_posts(
        self,
        subreddit: str,
        ticker: str,
        days_back: int = 1,
        limit: int = 100,
    ) -> List[Dict]:
        """
        Get posts mentioning a ticker from a subreddit.

        Args:
            subreddit: Subreddit name (without r/)
            ticker: Stock ticker to search for
            days_back: Number of days to look back
            limit: Maximum number of posts to return

        Returns:
            List of posts with metadata
        """
        after_timestamp = (datetime.now() - timedelta(days=days_back)).timestamp()

        url = f"{self.PUSHSHIFT_API}/submission/search"
        params = {
            "subreddit": subreddit,
            "q": ticker,
            "after": int(after_timestamp),
            "size": min(limit, 100),
            "sort": "desc",
            "sort_type": "created_utc",
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            posts = []
            for post in data.get("data", []):
                posts.append(
                    {
                        "title": post.get("title", ""),
                        "text": post.get("selftext", ""),
                        "score": post.get("score", 0),
                        "num_comments": post.get("num_comments", 0),
                        "created_utc": post.get("created_utc"),
                        "url": f"https://reddit.com{post.get('permalink', '')}",
                        "subreddit": subreddit,
                        "author": post.get("author", "[deleted]"),
                    }
                )

            logger.info(f"Fetched {len(posts)} posts from r/{subreddit} about {ticker}")
            return posts

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Reddit posts: {e}")
            return []

    def get_ticker_mentions(
        self, ticker: str, days_back: int = 1, limit: int = 500
    ) -> List[Dict]:
        """
        Get all mentions of a ticker across popular subreddits.

        Args:
            ticker: Stock ticker
            days_back: Number of days to look back
            limit: Maximum total posts

        Returns:
            List of posts mentioning the ticker
        """
        all_posts = []
        posts_per_subreddit = limit // len(self.STOCK_SUBREDDITS)

        for subreddit in self.STOCK_SUBREDDITS:
            posts = self.get_subreddit_posts(
                subreddit, ticker, days_back, posts_per_subreddit
            )
            all_posts.extend(posts)

        return all_posts

    def get_subreddit_comments(
        self,
        subreddit: str,
        ticker: str,
        days_back: int = 1,
        limit: int = 100,
    ) -> List[Dict]:
        """
        Get comments mentioning a ticker from a subreddit.

        Args:
            subreddit: Subreddit name (without r/)
            ticker: Stock ticker to search for
            days_back: Number of days to look back
            limit: Maximum number of comments to return

        Returns:
            List of comments with metadata
        """
        after_timestamp = (datetime.now() - timedelta(days=days_back)).timestamp()

        url = f"{self.PUSHSHIFT_API}/comment/search"
        params = {
            "subreddit": subreddit,
            "q": ticker,
            "after": int(after_timestamp),
            "size": min(limit, 100),
            "sort": "desc",
            "sort_type": "created_utc",
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            comments = []
            for comment in data.get("data", []):
                comments.append(
                    {
                        "text": comment.get("body", ""),
                        "score": comment.get("score", 0),
                        "created_utc": comment.get("created_utc"),
                        "url": f"https://reddit.com{comment.get('permalink', '')}",
                        "subreddit": subreddit,
                        "author": comment.get("author", "[deleted]"),
                    }
                )

            logger.info(f"Fetched {len(comments)} comments from r/{subreddit} about {ticker}")
            return comments

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Reddit comments: {e}")
            return []

    def get_reddit_sentiment_data(self, ticker: str, days_back: int = 1) -> Dict:
        """
        Get comprehensive Reddit sentiment data for a ticker.

        Returns:
            Dictionary with posts, comments, and engagement metrics
        """
        posts = self.get_ticker_mentions(ticker, days_back, limit=500)

        # Also get comments (sample from main subreddit)
        comments = self.get_subreddit_comments(
            "stocks", ticker, days_back, limit=100
        )

        if not posts and not comments:
            logger.warning(f"No Reddit data found for {ticker}")
            return {}

        # Calculate engagement metrics
        total_posts = len(posts)
        total_comments = len(comments)
        avg_post_score = (
            sum(p.get("score", 0) for p in posts) / total_posts if posts else 0
        )
        avg_post_engagement = (
            sum(p.get("num_comments", 0) for p in posts) / total_posts if posts else 0
        )
        avg_comment_score = (
            sum(c.get("score", 0) for c in comments) / total_comments
            if comments
            else 0
        )

        return {
            "ticker": ticker,
            "posts": posts,
            "comments": comments,
            "metrics": {
                "total_posts": total_posts,
                "total_comments": total_comments,
                "avg_post_score": avg_post_score,
                "avg_post_engagement": avg_post_engagement,
                "avg_comment_score": avg_comment_score,
                "total_engagement": (
                    sum(p.get("num_comments", 0) for p in posts)
                    + sum(c.get("score", 0) for c in comments)
                ),
            },
        }

    def extract_ticker_symbols(self, text: str) -> List[str]:
        """Extract ticker symbols from text (e.g., $AAPL)."""
        pattern = r"\$([A-Z]{1,5})\b"
        return re.findall(pattern, text)
