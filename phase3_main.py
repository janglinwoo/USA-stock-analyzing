#!/usr/bin/env python3
"""
Phase 3: Machine Learning Model Training.
Train and evaluate models for price direction prediction and price range estimation.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from models import DirectionClassifier, PricePredictor, ModelEvaluator
from utils.logger import setup_logger

logger = setup_logger(__name__)


def load_phase2_results(results_file: str = None) -> pd.DataFrame:
    """Load Phase 2 features from JSON or CSV file."""
    if results_file:
        if not Path(results_file).exists():
            logger.error(f"Results file not found: {results_file}")
            return None
    else:
        # Look for CSV first (easier to load)
        csv_files = sorted(Path(".").glob("phase2_results_*.csv"))
        if csv_files:
            results_file = str(csv_files[-1])
        else:
            # Fall back to JSON
            json_files = sorted(Path(".").glob("phase2_results_*.json"))
            if not json_files:
                logger.error("No Phase 2 results file found.")
                return None
            results_file = str(json_files[-1])

    logger.info(f"Loading Phase 2 results from: {results_file}")

    if results_file.endswith(".csv"):
        df = pd.read_csv(results_file)
    else:
        with open(results_file, "r") as f:
            data = json.load(f)
            df = pd.DataFrame(data.get("stock_features", []))

    return df


def create_target_variables(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create target variables for training.

    Since we don't have actual future prices in historical data,
    create synthetic targets based on heuristics:
    - price_direction: based on sentiment score and technical indicators
    - price_change_percent: based on momentum score
    """
    # Price direction (1 = up, 0 = down)
    # Positive if: combined sentiment > 0 OR momentum score > 0.1
    df["price_direction"] = (
        (df.get("combined_sentiment_score", 0) > 0) |
        (df.get("momentum_score", 0) > 0.1)
    ).astype(int)

    # Price change percent
    # Estimated from momentum and sentiment scores
    momentum = df.get("momentum_score", 0)
    sentiment = df.get("combined_sentiment_score", 0)

    # Formula: momentum (0-0.5 range) + sentiment (-1 to 1 range)
    df["price_change_percent"] = (momentum * 5) + (sentiment * 2)

    logger.info(f"Created target variables")
    logger.info(f"  Uptrend samples: {(df['price_direction'] == 1).sum()}")
    logger.info(f"  Downtrend samples: {(df['price_direction'] == 0).sum()}")

    return df


def main(phase2_file: str = None):
    """Main execution for Phase 3 - ML model training."""

    logger.info("=" * 60)
    logger.info("PHASE 3: Machine Learning Model Training")
    logger.info("=" * 60)

    try:
        # Load Phase 2 results
        logger.info("\n[Step 1] Loading Phase 2 features...")
        df = load_phase2_results(phase2_file)

        if df is None or df.empty:
            logger.error("Failed to load features")
            return

        logger.info(f"Loaded {len(df)} samples with {len(df.columns)} features")

        # Create target variables
        logger.info("\n[Step 2] Creating target variables...")
        df = create_target_variables(df)

        # Initialize models and evaluator
        logger.info("\n[Step 3] Initializing models...")
        direction_clf = DirectionClassifier()
        price_pred = PricePredictor()
        evaluator = ModelEvaluator()

        # ===== DIRECTION CLASSIFIER =====
        logger.info("\n" + "=" * 60)
        logger.info("DIRECTION CLASSIFIER (Up/Down Prediction)")
        logger.info("=" * 60)

        # Prepare data for direction classifier
        logger.info("\n[Step 4a] Preparing direction classifier data...")
        direction_clf.prepare_data(df, target_column="price_direction")

        # Train direction models
        logger.info("\n[Step 4b] Training direction classification models...")
        direction_results = direction_clf.train_models()

        # Cross-validate
        logger.info("\n[Step 4c] Cross-validating direction classifier...")
        direction_cv = direction_clf.cross_validate(cv_folds=5)

        for model_name, cv_result in direction_cv.items():
            logger.info(
                f"  {model_name}: {cv_result['mean_score']:.4f} "
                f"(±{cv_result['std_score']:.4f})"
            )

        # Evaluate best model
        best_direction_model = direction_clf.best_model
        best_direction_name = direction_clf.best_model_name
        direction_metrics = evaluator.evaluate_direction_classifier(
            best_direction_model,
            direction_clf.X_test,
            direction_clf.y_test,
            direction_clf.feature_names,
        )

        evaluator.print_evaluation_report(
            best_direction_name, direction_metrics, model_type="classification"
        )

        # Get feature importance
        direction_features = direction_clf.get_feature_importance(top_n=10)
        if direction_features is not None:
            logger.info("\nTop 10 Important Features (Direction Classifier):")
            for idx, row in direction_features.iterrows():
                logger.info(f"  {idx + 1}. {row['feature']}: {row['importance']:.4f}")

        # ===== PRICE PREDICTOR =====
        logger.info("\n" + "=" * 60)
        logger.info("PRICE PREDICTOR (Price Range Estimation)")
        logger.info("=" * 60)

        # Prepare data for price predictor
        logger.info("\n[Step 5a] Preparing price predictor data...")
        price_pred.prepare_data(df, target_column="price_change_percent")

        # Train price models
        logger.info("\n[Step 5b] Training price prediction models...")
        price_results = price_pred.train_models()

        # Cross-validate
        logger.info("\n[Step 5c] Cross-validating price predictor...")
        price_cv = price_pred.cross_validate(cv_folds=5)

        for model_name, cv_result in price_cv.items():
            logger.info(
                f"  {model_name}: {cv_result['mean_score']:.4f} "
                f"(±{cv_result['std_score']:.4f})"
            )

        # Evaluate best model
        best_price_model = price_pred.best_model
        best_price_name = price_pred.best_model_name
        price_metrics = evaluator.evaluate_price_predictor(
            best_price_model,
            price_pred.X_test,
            price_pred.y_test,
            price_pred.feature_names,
        )

        evaluator.print_evaluation_report(
            best_price_name, price_metrics, model_type="regression"
        )

        # Get feature importance
        price_features = price_pred.get_feature_importance(top_n=10)
        if price_features is not None:
            logger.info("\nTop 10 Important Features (Price Predictor):")
            for idx, row in price_features.iterrows():
                logger.info(f"  {idx + 1}. {row['feature']}: {row['importance']:.4f}")

        # ===== BACKTESTING =====
        logger.info("\n" + "=" * 60)
        logger.info("BACKTESTING")
        logger.info("=" * 60)

        # Backtest direction classifier
        logger.info("\n[Step 6] Backtesting direction classifier...")
        direction_predictions = best_direction_model.predict(direction_clf.X_test)
        actual_returns = df.loc[direction_clf.X_test.index, "price_change_percent"]

        direction_backtest = evaluator.backtest_direction_predictions(
            direction_predictions, actual_returns.values
        )

        evaluator.print_backtest_report("Direction Classifier", direction_backtest)

        # ===== SUMMARY AND SAVE =====
        logger.info("\n" + "=" * 60)
        logger.info("SUMMARY")
        logger.info("=" * 60)

        results = {
            "timestamp": datetime.now().isoformat(),
            "direction_classifier": {
                "model_name": best_direction_name,
                "metrics": direction_metrics,
                "cross_validation": direction_cv,
                "all_models": {
                    name: result["metrics"]
                    for name, result in direction_results.items()
                },
            },
            "price_predictor": {
                "model_name": best_price_name,
                "metrics": price_metrics,
                "cross_validation": price_cv,
                "all_models": {
                    name: result["metrics"] for name, result in price_results.items()
                },
            },
            "backtest": {
                "direction_classifier": direction_backtest,
            },
            "summary": {
                "total_samples": len(df),
                "training_samples": len(direction_clf.X_train),
                "test_samples": len(direction_clf.X_test),
                "direction_classifier_best": best_direction_name,
                "price_predictor_best": best_price_name,
            },
        }

        output_file = f"phase3_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"\nResults saved to: {output_file}")
        logger.info("=" * 60)
        logger.info("Phase 3 Complete!")
        logger.info("=" * 60)
        logger.info("Next: Phase 4 - Real-time Pipeline & Automation")

    except Exception as e:
        logger.error(f"Error in Phase 3 execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import sys

    phase2_file = sys.argv[1] if len(sys.argv) > 1 else None
    main(phase2_file)
