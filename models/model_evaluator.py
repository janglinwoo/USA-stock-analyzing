import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ModelEvaluator:
    """Evaluate and backtest trained models."""

    def __init__(self):
        self.evaluation_results = {}
        self.backtest_results = {}

    def evaluate_direction_classifier(
        self, model, X_test, y_test, feature_names: List[str] = None
    ) -> Dict:
        """
        Evaluate direction classification model.

        Args:
            model: Trained classifier
            X_test: Test features
            y_test: Test labels
            feature_names: Names of features

        Returns:
            Comprehensive evaluation metrics
        """
        from sklearn.metrics import (
            accuracy_score,
            precision_score,
            recall_score,
            f1_score,
            roc_auc_score,
            confusion_matrix,
            classification_report,
        )

        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]

        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred, zero_division=0),
            "recall": recall_score(y_test, y_pred, zero_division=0),
            "f1_score": f1_score(y_test, y_pred, zero_division=0),
            "roc_auc": roc_auc_score(y_test, y_pred_proba),
        }

        # Confusion matrix
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
        metrics["true_positives"] = int(tp)
        metrics["true_negatives"] = int(tn)
        metrics["false_positives"] = int(fp)
        metrics["false_negatives"] = int(fn)

        # Specificity and sensitivity
        metrics["sensitivity"] = tp / (tp + fn) if (tp + fn) > 0 else 0
        metrics["specificity"] = tn / (tn + fp) if (tn + fp) > 0 else 0

        return metrics

    def evaluate_price_predictor(
        self, model, X_test, y_test, feature_names: List[str] = None
    ) -> Dict:
        """
        Evaluate price prediction (regression) model.

        Args:
            model: Trained regressor
            X_test: Test features
            y_test: Test values
            feature_names: Names of features

        Returns:
            Comprehensive evaluation metrics
        """
        from sklearn.metrics import (
            mean_squared_error,
            mean_absolute_error,
            mean_absolute_percentage_error,
            r2_score,
        )

        y_pred = model.predict(X_test)

        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        mape = mean_absolute_percentage_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        # Within ±2% accuracy
        within_2pct = np.mean(np.abs(y_test - y_pred) <= 2)
        # Within ±5% accuracy
        within_5pct = np.mean(np.abs(y_test - y_pred) <= 5)

        metrics = {
            "mse": mse,
            "rmse": rmse,
            "mae": mae,
            "mape": mape,
            "r2_score": r2,
            "within_2_percent_accuracy": within_2pct,
            "within_5_percent_accuracy": within_5pct,
        }

        return metrics

    def backtest_direction_predictions(
        self,
        predictions: np.ndarray,
        actual_returns: np.ndarray,
        initial_capital: float = 10000,
        position_size: float = 1.0,
    ) -> Dict:
        """
        Backtest direction prediction strategy.

        Args:
            predictions: Model predictions (1 for up, 0 for down)
            actual_returns: Actual price returns (%)
            initial_capital: Starting capital
            position_size: Fraction of capital per trade

        Returns:
            Backtest performance metrics
        """
        if len(predictions) != len(actual_returns):
            logger.error("Predictions and returns must have same length")
            raise ValueError("Length mismatch")

        capital = initial_capital
        trades = 0
        winning_trades = 0
        losing_trades = 0
        returns = []

        for pred, actual_return in zip(predictions, actual_returns):
            # If model predicts up (1)
            if pred == 1:
                # Profit if return is positive
                trade_return = position_size * actual_return
            else:
                # Profit if return is negative
                trade_return = -position_size * actual_return

            capital += capital * (trade_return / 100)
            returns.append(trade_return)
            trades += 1

            if trade_return > 0:
                winning_trades += 1
            else:
                losing_trades += 1

        total_return = (capital - initial_capital) / initial_capital * 100
        win_rate = winning_trades / trades if trades > 0 else 0

        # Sharpe ratio (simplified, assuming risk-free rate = 0)
        returns_array = np.array(returns)
        std_return = np.std(returns_array) if len(returns_array) > 1 else 1
        sharpe_ratio = np.mean(returns_array) / std_return if std_return > 0 else 0

        # Drawdown
        cumulative_returns = np.cumsum(returns_array)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / (np.abs(running_max) + 1e-6)
        max_drawdown = np.min(drawdown)

        return {
            "total_return_percent": total_return,
            "final_capital": capital,
            "num_trades": trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "avg_return_per_trade": np.mean(returns_array),
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "returns": returns,
        }

    def backtest_price_predictions(
        self,
        predicted_prices: np.ndarray,
        actual_prices: np.ndarray,
        current_prices: np.ndarray,
        initial_capital: float = 10000,
    ) -> Dict:
        """
        Backtest price prediction strategy.

        Args:
            predicted_prices: Model predicted prices
            actual_prices: Actual future prices
            current_prices: Current prices at prediction time
            initial_capital: Starting capital

        Returns:
            Backtest performance metrics
        """
        capital = initial_capital
        trades = 0
        profitable_trades = 0
        returns = []

        for predicted, actual, current in zip(
            predicted_prices, actual_prices, current_prices
        ):
            # Buy if prediction is higher than current
            if predicted > current:
                # Price change from predicted to actual
                return_pct = (actual - current) / current * 100
                capital += capital * (return_pct / 100)
                returns.append(return_pct)

                if return_pct > 0:
                    profitable_trades += 1

                trades += 1

        total_return = (capital - initial_capital) / initial_capital * 100

        if len(returns) > 0:
            win_rate = profitable_trades / trades
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = avg_return / std_return if std_return > 0 else 0
        else:
            win_rate = 0
            avg_return = 0
            sharpe_ratio = 0

        return {
            "total_return_percent": total_return,
            "final_capital": capital,
            "num_trades": trades,
            "profitable_trades": profitable_trades,
            "win_rate": win_rate,
            "avg_return_per_trade": avg_return,
            "sharpe_ratio": sharpe_ratio,
            "returns": returns,
        }

    def get_feature_importance_summary(
        self, feature_names: List[str], importances: np.ndarray, top_n: int = 15
    ) -> pd.DataFrame:
        """
        Get top N important features.

        Args:
            feature_names: Names of features
            importances: Importance scores
            top_n: Number of top features to return

        Returns:
            DataFrame with feature importances sorted
        """
        df = pd.DataFrame(
            {
                "feature": feature_names,
                "importance": importances,
            }
        ).sort_values("importance", ascending=False)

        return df.head(top_n)

    def print_evaluation_report(
        self,
        model_name: str,
        metrics: Dict,
        model_type: str = "classification",
    ) -> None:
        """Print formatted evaluation report."""
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Model Evaluation Report: {model_name}")
        logger.info(f"Type: {model_type.upper()}")
        logger.info(f"{'=' * 60}")

        if model_type == "classification":
            logger.info(f"Accuracy:    {metrics.get('accuracy', 0):.4f}")
            logger.info(f"Precision:   {metrics.get('precision', 0):.4f}")
            logger.info(f"Recall:      {metrics.get('recall', 0):.4f}")
            logger.info(f"F1-Score:    {metrics.get('f1_score', 0):.4f}")
            logger.info(f"ROC-AUC:     {metrics.get('roc_auc', 0):.4f}")
            logger.info(f"Sensitivity: {metrics.get('sensitivity', 0):.4f}")
            logger.info(f"Specificity: {metrics.get('specificity', 0):.4f}")

        elif model_type == "regression":
            logger.info(f"RMSE:         {metrics.get('rmse', 0):.4f}")
            logger.info(f"MAE:          {metrics.get('mae', 0):.4f}")
            logger.info(f"MAPE:         {metrics.get('mape', 0):.4f}")
            logger.info(f"R² Score:     {metrics.get('r2_score', 0):.4f}")
            logger.info(f"Within ±2%:   {metrics.get('within_2_percent_accuracy', 0):.4f}")
            logger.info(f"Within ±5%:   {metrics.get('within_5_percent_accuracy', 0):.4f}")

        logger.info(f"{'=' * 60}\n")

    def print_backtest_report(
        self, strategy_name: str, backtest_metrics: Dict
    ) -> None:
        """Print formatted backtest report."""
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Backtest Report: {strategy_name}")
        logger.info(f"{'=' * 60}")
        logger.info(f"Total Return:        {backtest_metrics.get('total_return_percent', 0):.2f}%")
        logger.info(f"Final Capital:       ${backtest_metrics.get('final_capital', 0):.2f}")
        logger.info(f"Number of Trades:    {backtest_metrics.get('num_trades', 0)}")
        logger.info(f"Win Rate:            {backtest_metrics.get('win_rate', 0):.2%}")
        logger.info(f"Avg Return/Trade:    {backtest_metrics.get('avg_return_per_trade', 0):.2f}%")
        logger.info(f"Sharpe Ratio:        {backtest_metrics.get('sharpe_ratio', 0):.4f}")
        logger.info(f"Max Drawdown:        {backtest_metrics.get('max_drawdown', 0):.2%}")
        logger.info(f"{'=' * 60}\n")
