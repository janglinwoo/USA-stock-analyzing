import numpy as np
import pandas as pd
from typing import Dict, Tuple, List
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score,
)
import xgboost as xgb
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PricePredictor:
    """Predict stock price range (±%) using regression models."""

    def __init__(self, test_size: float = 0.2, random_state: int = 42):
        """
        Initialize price predictor.

        Args:
            test_size: Proportion of data for testing
            random_state: Random seed for reproducibility
        """
        self.test_size = test_size
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.models = {}
        self.best_model = None
        self.best_model_name = None
        self.feature_names = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None

    def prepare_data(
        self,
        df: pd.DataFrame,
        target_column: str = "price_change_percent",
        exclude_columns: List[str] = None,
    ) -> None:
        """
        Prepare data for training.

        Args:
            df: Feature DataFrame from Phase 2
            target_column: Column name for target variable (price change %)
            exclude_columns: Columns to exclude from features
        """
        if target_column not in df.columns:
            logger.error(f"Target column '{target_column}' not found in dataframe")
            raise ValueError(f"Column {target_column} not found")

        # Select features
        exclude = exclude_columns or [
            "ticker",
            "timestamp",
            "price_direction",
            "future_price",
            "price_change_percent",
        ]
        feature_cols = [col for col in df.columns if col not in exclude]

        # Remove non-numeric columns
        feature_cols = [
            col
            for col in feature_cols
            if df[col].dtype in [np.float64, np.float32, np.int64, np.int32]
        ]

        self.feature_names = feature_cols

        # Handle missing values
        X = df[feature_cols].fillna(0)
        y = df[target_column]

        # Split data
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=self.test_size, random_state=self.random_state
        )

        # Scale features
        self.X_train = self.scaler.fit_transform(self.X_train)
        self.X_test = self.scaler.transform(self.X_test)

        logger.info(f"Data prepared: {len(self.X_train)} train, {len(self.X_test)} test")
        logger.info(f"Features: {len(feature_cols)}")

    def train_models(self) -> Dict[str, Dict]:
        """
        Train multiple regression models and compare.

        Returns:
            Dictionary with training results for each model
        """
        if self.X_train is None:
            logger.error("Data not prepared. Call prepare_data() first.")
            raise ValueError("Data not prepared")

        results = {}

        # 1. Linear Regression
        logger.info("Training Linear Regression...")
        lr_model = LinearRegression()
        lr_model.fit(self.X_train, self.y_train)
        lr_pred = lr_model.predict(self.X_test)

        results["Linear Regression"] = {
            "model": lr_model,
            "predictions": lr_pred,
            "metrics": self._calculate_metrics(self.y_test, lr_pred),
        }

        # 2. Ridge Regression
        logger.info("Training Ridge Regression...")
        ridge_model = Ridge(alpha=1.0)
        ridge_model.fit(self.X_train, self.y_train)
        ridge_pred = ridge_model.predict(self.X_test)

        results["Ridge Regression"] = {
            "model": ridge_model,
            "predictions": ridge_pred,
            "metrics": self._calculate_metrics(self.y_test, ridge_pred),
        }

        # 3. Lasso Regression
        logger.info("Training Lasso Regression...")
        lasso_model = Lasso(alpha=0.1, max_iter=10000)
        lasso_model.fit(self.X_train, self.y_train)
        lasso_pred = lasso_model.predict(self.X_test)

        results["Lasso Regression"] = {
            "model": lasso_model,
            "predictions": lasso_pred,
            "metrics": self._calculate_metrics(self.y_test, lasso_pred),
        }

        # 4. Random Forest Regression
        logger.info("Training Random Forest Regression...")
        rf_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=self.random_state,
            n_jobs=-1,
        )
        rf_model.fit(self.X_train, self.y_train)
        rf_pred = rf_model.predict(self.X_test)

        results["Random Forest"] = {
            "model": rf_model,
            "predictions": rf_pred,
            "metrics": self._calculate_metrics(self.y_test, rf_pred),
            "feature_importance": rf_model.feature_importances_,
        }

        # 5. Gradient Boosting Regression
        logger.info("Training Gradient Boosting...")
        gb_model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=self.random_state,
        )
        gb_model.fit(self.X_train, self.y_train)
        gb_pred = gb_model.predict(self.X_test)

        results["Gradient Boosting"] = {
            "model": gb_model,
            "predictions": gb_pred,
            "metrics": self._calculate_metrics(self.y_test, gb_pred),
            "feature_importance": gb_model.feature_importances_,
        }

        # 6. XGBoost Regression
        logger.info("Training XGBoost...")
        xgb_model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=self.random_state,
            eval_metric="rmse",
        )
        xgb_model.fit(self.X_train, self.y_train)
        xgb_pred = xgb_model.predict(self.X_test)

        results["XGBoost"] = {
            "model": xgb_model,
            "predictions": xgb_pred,
            "metrics": self._calculate_metrics(self.y_test, xgb_pred),
            "feature_importance": xgb_model.feature_importances_,
        }

        self.models = results

        # Find best model (lowest RMSE)
        best_rmse = float("inf")
        for model_name, result in results.items():
            rmse = result["metrics"]["rmse"]
            r2 = result["metrics"]["r2_score"]
            logger.info(f"{model_name}: RMSE={rmse:.4f}, R²={r2:.4f}")

            if rmse < best_rmse:
                best_rmse = rmse
                self.best_model_name = model_name
                self.best_model = result["model"]

        logger.info(f"\nBest model: {self.best_model_name} (RMSE={best_rmse:.4f})")
        return results

    def _calculate_metrics(self, y_true, y_pred) -> Dict:
        """Calculate evaluation metrics."""
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)

        return {
            "mse": mse,
            "rmse": rmse,
            "mae": mae,
            "r2_score": r2,
        }

    def get_feature_importance(self, top_n: int = 10) -> pd.DataFrame:
        """Get top important features from tree-based models."""
        if not self.best_model_name or "feature_importance" not in self.models.get(
            self.best_model_name, {}
        ):
            logger.warning("Feature importance not available for this model")
            return None

        importance = self.models[self.best_model_name]["feature_importance"]
        feature_importance_df = pd.DataFrame(
            {
                "feature": self.feature_names,
                "importance": importance,
            }
        ).sort_values("importance", ascending=False)

        return feature_importance_df.head(top_n)

    def get_model_summary(self) -> Dict:
        """Get summary of all trained models."""
        summary = {}
        for model_name, result in self.models.items():
            summary[model_name] = result["metrics"]

        return summary

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions using best model.

        Args:
            X: Input features (scaled)

        Returns:
            Price change percentage predictions
        """
        if self.best_model is None:
            logger.error("Model not trained. Call train_models() first.")
            raise ValueError("Model not trained")

        return self.best_model.predict(X)

    def predict_price_range(self, X: np.ndarray, current_price: float) -> np.ndarray:
        """
        Predict price range (actual prices) from percentage change.

        Args:
            X: Input features (scaled)
            current_price: Current stock price

        Returns:
            Array of predicted prices
        """
        predicted_change_pct = self.predict(X)
        predicted_prices = current_price * (1 + predicted_change_pct / 100)
        return predicted_prices

    def cross_validate(self, cv_folds: int = 5) -> Dict:
        """Perform cross-validation on training data."""
        if self.X_train is None:
            logger.error("Data not prepared. Call prepare_data() first.")
            raise ValueError("Data not prepared")

        logger.info(f"Performing {cv_folds}-fold cross-validation...")
        cv_results = {}

        for model_name, result in self.models.items():
            model = result["model"]
            scores = cross_val_score(
                model, self.X_train, self.y_train, cv=cv_folds, scoring="r2"
            )

            cv_results[model_name] = {
                "mean_score": scores.mean(),
                "std_score": scores.std(),
                "scores": scores.tolist(),
            }

            logger.info(
                f"{model_name}: {scores.mean():.4f} (+/- {scores.std():.4f})"
            )

        return cv_results
