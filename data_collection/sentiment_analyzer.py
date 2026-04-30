from typing import Dict, List
from utils.logger import setup_logger

logger = setup_logger(__name__)


class SentimentAnalyzer:
    """Analyze sentiment from news articles and community posts using VADER only."""

    def __init__(self, use_transformer: bool = False):
        """
        Initialize sentiment analyzer with VADER only (Windows compatible).

        Args:
            use_transformer: Ignored - VADER only
        """
        self.use_transformer = False
        logger.info("Using VADER sentiment analyzer (transformers disabled for Windows compatibility)")

    def analyze_text(self, text: str) -> Dict:
        """
        Analyze sentiment of text using VADER.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with sentiment scores and labels
        """
        if not text or len(text.strip()) == 0:
            return {
                "vader_sentiment": None,
                "vader_score": None,
                "transformer_sentiment": None,
                "transformer_score": None,
                "combined_score": None,
            }

        vader_result = self._analyze_vader(text)

        return {
            "vader_sentiment": vader_result["sentiment"],
            "vader_score": vader_result["score"],
            "transformer_sentiment": None,
            "transformer_score": None,
            "combined_score": vader_result["score"],
        }

    def analyze_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Analyze sentiment for list of articles.

        Args:
            articles: List of articles with 'title' and 'description'

        Returns:
            Articles with added sentiment analysis
        """
        for article in articles:
            text = f"{article.get('title', '')} {article.get('description', '')}"
            sentiment = self.analyze_text(text)
            article["sentiment"] = sentiment

        return articles

    def analyze_comments(self, comments: List[str]) -> List[Dict]:
        """Analyze sentiment for list of comments."""
        results = []
        for comment in comments:
            results.append(
                {
                    "text": comment,
                    "sentiment": self.analyze_text(comment),
                }
            )
        return results

    def _analyze_vader(self, text: str) -> Dict:
        """VADER sentiment analysis."""
        try:
            from nltk.sentiment import SentimentIntensityAnalyzer
            import nltk

            # Download VADER lexicon if needed
            try:
                nltk.data.find("sentiment/vader_lexicon")
            except LookupError:
                nltk.download("vader_lexicon", quiet=True)

            sia = SentimentIntensityAnalyzer()
            scores = sia.polarity_scores(text)

            # Determine sentiment label
            compound = scores["compound"]
            if compound >= 0.05:
                sentiment = "positive"
            elif compound <= -0.05:
                sentiment = "negative"
            else:
                sentiment = "neutral"

            return {"sentiment": sentiment, "score": compound}

        except Exception as e:
            logger.error(f"Error in VADER analysis: {e}")
            return {"sentiment": "unknown", "score": 0.0}

    def get_sentiment_summary(self, articles: List[Dict]) -> Dict:
        """
        Get overall sentiment summary for a list of articles.

        Returns:
            Summary with average scores and distribution
        """
        if not articles:
            return {}

        scores = [
            a.get("sentiment", {}).get("combined_score", 0)
            for a in articles
            if a.get("sentiment", {}).get("combined_score") is not None
        ]

        if not scores:
            return {}

        avg_score = sum(scores) / len(scores)
        positive_count = sum(1 for s in scores if s > 0.05)
        negative_count = sum(1 for s in scores if s < -0.05)
        neutral_count = len(scores) - positive_count - negative_count

        return {
            "average_sentiment_score": avg_score,
            "total_articles": len(articles),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "positive_ratio": positive_count / len(articles),
            "negative_ratio": negative_count / len(articles),
            "neutral_ratio": neutral_count / len(articles),
        }
