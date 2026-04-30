from typing import Dict, List
from textblob import TextBlob
from transformers import pipeline
import warnings
from utils.logger import setup_logger

logger = setup_logger(__name__)

warnings.filterwarnings("ignore")


class SentimentAnalyzer:
    """Analyze sentiment from news articles and community posts."""

    def __init__(self, use_transformer: bool = True):
        """
        Initialize sentiment analyzer.

        Args:
            use_transformer: Use transformer models for advanced analysis
        """
        self.use_transformer = use_transformer
        self.transformer_pipeline = None

        if use_transformer:
            try:
                # Financial sentiment model
                self.transformer_pipeline = pipeline(
                    "sentiment-analysis",
                    model="ProsusAI/finbert",
                    device=-1  # CPU, use 0 for GPU
                )
                logger.info("Loaded FinBERT transformer model")
            except Exception as e:
                logger.warning(f"Could not load FinBERT: {e}. Falling back to VADER.")
                self.use_transformer = False

    def analyze_text(self, text: str) -> Dict:
        """
        Analyze sentiment of text using multiple methods.

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
        transformer_result = (
            self._analyze_transformer(text)
            if self.use_transformer
            else None
        )

        # Combine scores
        combined_score = self._combine_scores(vader_result, transformer_result)

        return {
            "vader_sentiment": vader_result["sentiment"],
            "vader_score": vader_result["score"],
            "transformer_sentiment": (
                transformer_result["sentiment"] if transformer_result else None
            ),
            "transformer_score": (
                transformer_result["score"] if transformer_result else None
            ),
            "combined_score": combined_score,
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

    def _analyze_transformer(self, text: str) -> Dict:
        """Transformer-based sentiment analysis."""
        try:
            if len(text) > 512:
                text = text[:512]

            result = self.transformer_pipeline(text)[0]

            # Convert transformer output to standard format
            label = result["label"].lower()
            score = result["score"]

            # Normalize score to -1 to 1 range
            if label == "negative":
                normalized_score = -score
            else:  # positive
                normalized_score = score

            return {"sentiment": label, "score": normalized_score}

        except Exception as e:
            logger.error(f"Error in transformer analysis: {e}")
            return {"sentiment": "unknown", "score": 0.0}

    @staticmethod
    def _combine_scores(
        vader_result: Dict, transformer_result: Dict = None
    ) -> float:
        """Combine VADER and transformer scores."""
        if transformer_result is None:
            return vader_result["score"]

        # Weight: 40% VADER, 60% Transformer (financial sentiment)
        vader_score = vader_result["score"]
        transformer_score = transformer_result["score"]

        combined = (vader_score * 0.4) + (transformer_score * 0.6)
        return min(1.0, max(-1.0, combined))  # Clamp to [-1, 1]

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
