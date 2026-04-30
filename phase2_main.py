#!/usr/bin/env python3
"""
Phase 2: Sentiment Analysis & Feature Engineering.
Analyzes news sentiment, community discussion, and creates ML-ready features.
"""

import json
from pathlib import Path
from datetime import datetime
from data_collection import (
    NewsFetcher,
    StockDataFetcher,
    EventDetector,
)
from data_collection.sentiment_analyzer import SentimentAnalyzer
from data_collection.reddit_fetcher import RedditFetcher
from data_collection.stocktwits_fetcher import StockTwitsFetcher
from data_collection.feature_engineer import FeatureEngineer
from utils.logger import setup_logger

logger = setup_logger(__name__)


def load_phase1_results(results_file: str = None) -> dict:
    """Load Phase 1 results from JSON file."""
    if results_file:
        if not Path(results_file).exists():
            logger.error(f"Results file not found: {results_file}")
            return None
    else:
        # Find latest phase1 results file
        phase1_files = sorted(Path(".").glob("phase1_results_*.json"))
        if not phase1_files:
            logger.error("No Phase 1 results file found. Please run Phase 1 first.")
            return None
        results_file = str(phase1_files[-1])

    logger.info(f"Loading Phase 1 results from: {results_file}")

    with open(results_file, "r") as f:
        return json.load(f)


def main(phase1_file: str = None):
    """Main execution for Phase 2 - Sentiment analysis and feature engineering."""

    logger.info("=" * 60)
    logger.info("PHASE 2: Sentiment Analysis & Feature Engineering")
    logger.info("=" * 60)

    try:
        # Load Phase 1 results
        logger.info("\n[Step 1] Loading Phase 1 results...")
        phase1_results = load_phase1_results(phase1_file)

        if not phase1_results:
            logger.error("Failed to load Phase 1 results")
            return

        detected_events = phase1_results.get("detected_events", [])
        stocks_by_event = phase1_results.get("stocks_by_event_type", {})
        stock_data = phase1_results.get("stock_data", {})

        logger.info(f"Loaded {len(detected_events)} events and {len(stock_data)} stocks")

        # Initialize analyzers and fetchers
        logger.info("\n[Step 2] Initializing sentiment analysis...")
        sentiment_analyzer = SentimentAnalyzer(use_transformer=True)
        reddit_fetcher = RedditFetcher()
        stocktwits_fetcher = StockTwitsFetcher()
        feature_engineer = FeatureEngineer()
        stock_fetcher = StockDataFetcher()

        # Analyze sentiment for detected events
        logger.info("\n[Step 3] Analyzing news sentiment...")
        articles_with_sentiment = sentiment_analyzer.analyze_articles(
            phase1_results.get("detected_events", [])
        )

        # Get sentiment summary
        news_sentiment_summary = sentiment_analyzer.get_sentiment_summary(
            articles_with_sentiment
        )
        logger.info(f"News sentiment: {news_sentiment_summary.get('average_sentiment_score', 0):.2f}")

        # Collect community data and create features for each stock
        logger.info("\n[Step 4] Collecting community sentiment data...")
        all_features = []
        community_data_summary = {}

        for ticker in stock_data.keys():
            logger.info(f"\nProcessing {ticker}...")

            # Get relevant events for this ticker
            ticker_events = [
                e for e in detected_events if ticker in e.get("tickers", [])
            ]

            # Get Reddit data
            logger.info(f"  Fetching Reddit data...")
            reddit_data = reddit_fetcher.get_reddit_sentiment_data(ticker, days_back=1)

            # Get StockTwits data
            logger.info(f"  Fetching StockTwits data...")
            stocktwits_data = stocktwits_fetcher.get_comprehensive_sentiment(ticker)

            # Get updated technical indicators
            logger.info(f"  Fetching technical indicators...")
            hist = stock_fetcher.get_stock_data(ticker, period="1mo")
            indicators = stock_fetcher.calculate_technical_indicators(hist)
            indicators["current_price"] = stock_fetcher.get_current_price(ticker)

            # Get news sentiment for this stock's articles
            ticker_articles = [
                a for a in articles_with_sentiment if ticker in a.get("tickers", [])
            ]
            ticker_news_sentiment = sentiment_analyzer.get_sentiment_summary(
                ticker_articles
            )

            # Create comprehensive feature set
            logger.info(f"  Creating features...")
            features = feature_engineer.create_features(
                ticker=ticker,
                events=ticker_events,
                news_sentiment=ticker_news_sentiment,
                reddit_data=reddit_data,
                stocktwits_data=stocktwits_data,
                stock_indicators=indicators,
            )

            all_features.append(features)

            # Store community data
            community_data_summary[ticker] = {
                "reddit_metrics": reddit_data.get("metrics", {}),
                "stocktwits_sentiment": stocktwits_data.get("sentiment", {}),
            }

            logger.info(
                f"  ✓ {ticker}: Combined sentiment={features.get('combined_sentiment_score', 0):.2f}, "
                f"Momentum={features.get('momentum_score', 0):.2f}"
            )

        # Summary and output
        logger.info("\n[Step 5] Summary")
        logger.info("-" * 60)
        logger.info(f"Total stocks analyzed: {len(all_features)}")
        logger.info(f"Overall news sentiment: {news_sentiment_summary.get('average_sentiment_score', 0):.2f}")

        # Display top positive and negative stocks
        sorted_features = sorted(
            all_features,
            key=lambda x: x.get("combined_sentiment_score", 0),
            reverse=True,
        )

        logger.info("\nTop 5 Bullish stocks:")
        for i, feature in enumerate(sorted_features[:5], 1):
            sentiment = feature.get("combined_sentiment_score", 0)
            momentum = feature.get("momentum_score", 0)
            logger.info(
                f"  {i}. {feature['ticker']}: Sentiment={sentiment:.3f}, Momentum={momentum:.3f}"
            )

        logger.info("\nTop 5 Bearish stocks:")
        for i, feature in enumerate(sorted_features[-5:], 1):
            sentiment = feature.get("combined_sentiment_score", 0)
            momentum = feature.get("momentum_score", 0)
            logger.info(
                f"  {i}. {feature['ticker']}: Sentiment={sentiment:.3f}, Momentum={momentum:.3f}"
            )

        # Save comprehensive results
        results = {
            "timestamp": datetime.now().isoformat(),
            "phase1_summary": {
                "total_events": len(detected_events),
                "total_stocks": len(stock_data),
            },
            "news_sentiment_summary": news_sentiment_summary,
            "stock_features": all_features,
            "community_data_summary": community_data_summary,
        }

        output_file = f"phase2_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"\nResults saved to: {output_file}")

        # Also save as CSV for easier analysis
        import pandas as pd
        df = pd.DataFrame(all_features)
        csv_file = output_file.replace(".json", ".csv")
        df.to_csv(csv_file, index=False)
        logger.info(f"Features CSV saved to: {csv_file}")

        logger.info("=" * 60)
        logger.info("Phase 2 Complete!")
        logger.info("=" * 60)
        logger.info("Next: Phase 3 - Machine Learning Model Training")

    except Exception as e:
        logger.error(f"Error in Phase 2 execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import sys
    phase1_file = sys.argv[1] if len(sys.argv) > 1 else None
    main(phase1_file)
