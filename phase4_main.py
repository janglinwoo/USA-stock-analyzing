#!/usr/bin/env python3
"""
Phase 4: Real-time Pipeline & Automation.
Run the integrated pipeline with FastAPI server and scheduled updates.
"""

import argparse
import uvicorn
from api.app import app
from pipeline import RealtimePipeline
from pipeline.scheduler import PredictionScheduler
from database import Database
from utils.logger import setup_logger

logger = setup_logger(__name__)


def run_api_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the FastAPI server."""
    logger.info(f"Starting API server on {host}:{port}")
    logger.info("Available endpoints:")
    logger.info("  - GET  /health                  (Health check)")
    logger.info("  - GET  /status                  (System status)")
    logger.info("  - POST /predict                 (Make prediction for single stock)")
    logger.info("  - GET  /predictions/{ticker}    (Get prediction history)")
    logger.info("  - POST /pipeline/run            (Run full pipeline)")
    logger.info("  - POST /scheduler/start         (Start scheduler)")
    logger.info("  - POST /scheduler/stop          (Stop scheduler)")
    logger.info("  - GET  /scheduler/jobs          (List scheduled jobs)")
    logger.info("  - GET  /performance             (Get model metrics)")
    logger.info("  - GET  /accuracy/{days_back}    (Get prediction accuracy)")
    logger.info("\nAPI Documentation: http://localhost:8000/docs")

    uvicorn.run(app, host=host, port=port)


def run_pipeline_once(days_back: int = 1):
    """Run the pipeline once and exit."""
    logger.info("Running pipeline once...")

    try:
        db = Database()
        pipeline = RealtimePipeline(db)

        predictions = pipeline.run_full_pipeline(days_back=days_back)

        logger.info(f"\n✓ Completed: {len(predictions)} predictions made")

        # Print results
        if predictions:
            logger.info("\nPredictions:")
            logger.info("-" * 80)
            for pred in predictions[:5]:  # Show first 5
                logger.info(f"  {pred['ticker']}")
                logger.info(f"    Direction: {'UP' if pred['direction_prediction'] == 1 else 'DOWN'} "
                           f"({pred['direction_confidence']:.1%})")
                logger.info(f"    Price Change: {pred['predicted_price_change']:.2f}%")
                logger.info(f"    Sentiment: {pred['combined_sentiment']:.2f}")
                logger.info("")

        db.close()

    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)


def run_with_scheduler(update_interval: int = 60):
    """Run the pipeline with scheduled updates (no API server)."""
    logger.info(f"Starting pipeline with {update_interval}-minute updates...")

    try:
        db = Database()
        pipeline = RealtimePipeline(db)
        scheduler = PredictionScheduler()

        # Add periodic job
        scheduler.add_interval_job(
            lambda: pipeline.run_full_pipeline(days_back=1),
            minutes=update_interval,
            job_id="periodic_prediction",
        )

        # Print scheduled jobs
        scheduler.print_jobs()

        # Start scheduler
        scheduler.start()

        logger.info("Scheduler is running. Press Ctrl+C to stop.")

        # Keep the program running
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.stop()
            db.close()

    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 4: Real-time Stock Prediction Pipeline"
    )

    parser.add_argument(
        "--mode",
        choices=["api", "run-once", "scheduler"],
        default="api",
        help="Execution mode: api (FastAPI server), run-once (single run), "
        "scheduler (background with interval updates)",
    )

    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="API server host (default: 0.0.0.0)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="API server port (default: 8000)",
    )

    parser.add_argument(
        "--days-back",
        type=int,
        default=1,
        help="Days back to look for news (default: 1)",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Update interval in minutes for scheduler mode (default: 60)",
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("PHASE 4: Real-time Pipeline & Automation")
    logger.info("=" * 60)

    if args.mode == "api":
        run_api_server(host=args.host, port=args.port)

    elif args.mode == "run-once":
        run_pipeline_once(days_back=args.days_back)

    elif args.mode == "scheduler":
        run_with_scheduler(update_interval=args.interval)


if __name__ == "__main__":
    main()
