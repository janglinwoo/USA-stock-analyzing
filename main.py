#!/usr/bin/env python3
"""
Phase 1: Main script for data collection and event detection.
Fetches financial news, detects events, and identifies affected stocks.
"""

from data_collection import NewsFetcher, StockDataFetcher, EventDetector
from utils.logger import setup_logger
import json
from datetime import datetime

logger = setup_logger(__name__)


def main():
    """Main execution for Phase 1 - Data collection and event detection."""

    logger.info("=" * 60)
    logger.info("PHASE 1: Data Collection & Event Detection")
    logger.info("=" * 60)

    try:
        # Initialize fetchers and detector
        news_fetcher = NewsFetcher()
        stock_fetcher = StockDataFetcher()
        event_detector = EventDetector()

        # 1. Fetch general financial news
        logger.info("\n[Step 1] Fetching financial news...")
        financial_news = news_fetcher.fetch_financial_news(days_back=1)

        if not financial_news:
            logger.warning("No financial news found. Check API key or network.")
            return

        # 2. Detect events and extract tickers
        logger.info("\n[Step 2] Detecting events and extracting stock tickers...")
        detected_events = event_detector.detect_events(financial_news)

        if not detected_events:
            logger.info("No market events detected in recent news.")
            return

        logger.info(f"Detected {len(detected_events)} events")

        # 3. Group by event type
        logger.info("\n[Step 3] Grouping stocks by event type...")
        stocks_by_event = event_detector.get_stocks_by_event_type(detected_events)

        for event_type, tickers in stocks_by_event.items():
            logger.info(f"  {event_type.upper()}: {', '.join(sorted(tickers))}")

        # 4. Fetch stock data for detected stocks
        logger.info("\n[Step 4] Fetching current stock data...")
        all_tickers = set()
        for tickers in stocks_by_event.values():
            all_tickers.update(tickers)

        stock_data_summary = {}
        for ticker in sorted(all_tickers):
            price = stock_fetcher.get_current_price(ticker)
            info = stock_fetcher.get_stock_info(ticker)
            hist = stock_fetcher.get_stock_data(ticker, period="1mo")
            indicators = stock_fetcher.calculate_technical_indicators(hist)

            stock_data_summary[ticker] = {
                "current_price": price,
                "company_name": info.get("company_name", "N/A"),
                "sector": info.get("sector", "N/A"),
                "technical_indicators": indicators,
            }

            logger.info(
                f"  {ticker}: ${price:.2f if price else 'N/A'} "
                f"({info.get('company_name', 'Unknown')})"
            )

        # 5. Summary and output
        logger.info("\n[Step 5] Summary")
        logger.info("-" * 60)
        logger.info(f"Total events detected: {len(detected_events)}")
        logger.info(f"Total unique stocks: {len(all_tickers)}")
        logger.info(f"Event types found: {', '.join(stocks_by_event.keys())}")

        # Save results to JSON for Phase 2
        results = {
            "timestamp": datetime.now().isoformat(),
            "detected_events": detected_events,
            "stocks_by_event_type": {k: list(v) for k, v in stocks_by_event.items()},
            "stock_data": stock_data_summary,
        }

        output_file = f"phase1_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"\nResults saved to: {output_file}")
        logger.info("=" * 60)
        logger.info("Phase 1 Complete!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error in main execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
