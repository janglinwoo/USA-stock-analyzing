import numpy as np
import pandas as pd
from typing import Dict, Tuple, List
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)
import xgboost as xgb
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DirectionClassifier:
    """Classify stock price direction (up/down) using ensemble methods."""

    def __init__(self, test_size: float = 0.2, random_state: int = 42):
        """
        Initialize direction classifier.

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
        target_column: str = "price_direction",
        exclude_columns: List[str] = None,
    ) -> None:
        """
        Prepare data for training.

        Args:
            df: Feature DataFrame from Phase 2
            target_column: Column name for target variable (up=1, down=0)
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
        Train multiple classification models and compare.

        Returns:
            Dictionary with training results for each model
        """
        if self.X_train is None:
            logger.error("Data not prepared. Call prepare_data() first.")
            raise ValueError("Data not prepared")

        results = {}

        # 1. Logistic Regression
        logger.info("Training Logistic Regression...")
        lr_model = LogisticRegression(max_iter=1000, random_state=self.random_state)
        lr_model.fit(self.X_train, self.y_train)
        lr_pred = lr_model.predict(self.X_test)
        lr_pred_proba = lr_model.predict_proba(self.X_test)[:, 1]

        results["Logistic Regression"] = {
            "model": lr_model,
            "predictions": lr_pred,
            "probabilities": lr_pred_proba,
            "metrics": self._calculate_metrics(self.y_test, lr_pred, lr_pred_proba),
        }

        # 2. Random Forest
        logger.info("Training Random Forest...")
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=self.random_state,
            n_jobs=-1,
        )
        rf_model.fit(self.X_train, self.y_train)
        rf_pred = rf_model.predict(self.X_test)
        rf_pred_proba = rf_model.predict_proba(self.X_test)[:, 1]

        results["Random Forest"] = {
            "model": rf_model,
            "predictions": rf_pred,
            "probabilities": rf_pred_proba,
            "metrics": self._calculate_metrics(self.y_test, rf_pred, rf_pred_proba),
            "feature_importance": rf_model.feature_importances_,
        }

        # 3. Gradient Boosting
        logger.info("Training Gradient Boosting...")
        gb_model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=self.random_state,
        )
        gb_model.fit(self.X_train, self.y_train)
        gb_pred = gb_model.predict(self.X_test)
        gb_pred_proba = gb_model.predict_proba(self.X_test)[:, 1]

        results["Gradient Boosting"] = {
            "model": gb_model,
            "predictions": gb_pred,
            "probabilities": gb_pred_proba,
            "metrics": self._calculate_metrics(self.y_test, gb_pred, gb_pred_proba),
            "feature_importance": gb_model.feature_importances_,
        }

        # 4. XGBoost
        logger.info("Training XGBoost...")
        xgb_model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=self.random_state,
            use_label_encoder=False,
            eval_metric="logloss",
        )
        xgb_model.fit(self.X_train, self.y_train)
        xgb_pred = xgb_model.predict(self.X_test)
        xgb_pred_proba = xgb_model.predict_proba(self.X_test)[:, 1]

        results["XGBoost"] = {
            "model": xgb_model,
            "predictions": xgb_pred,
            "probabilities": xgb_pred_proba,
            "metrics": self._calculate_metrics(self.y_test, xgb_pred, xgb_pred_proba),
            "feature_importance": xgb_model.feature_importances_,
        }

        self.models = results

        # Find best model
        best_f1 = -1
        for model_name, result in results.items():
            f1 = result["metrics"]["f1_score"]
            logger.info(f"{model_name}: F1={f1:.4f}, Accuracy={result['metrics']['accuracy']:.4f}")

            if f1 > best_f1:
                best_f1 = f1
                self.best_model_name = model_name
                self.best_model = result["model"]

        logger.info(f"\nBest model: {self.best_model_name} (F1={best_f1:.4f})")
        return results

    def _calculate_metrics(
        self, y_true, y_pred, y_pred_proba
    ) -> Dict:
        """Calculate evaluation metrics."""
        return {
            "accuracy": accuracy_score(y_true, y_pred),
            "precision": precision_score(y_true, y_pred, zero_division=0),
            "recall": recall_score(y_true, y_pred, zero_division=0),
            "f1_score": f1_score(y_true, y_pred, zero_division=0),
            "roc_auc": roc_auc_score(y_true, y_pred_proba),
            "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
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

    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Make predictions using best model.

        Args:
            X: Input features (scaled)

        Returns:
            Tuple of (predictions, probabilities)
        """
        if self.best_model is None:
            logger.error("Model not trained. Call train_models() first.")
            raise ValueError("Model not trained")

        predictions = self.best_model.predict(X)
        probabilities = self.best_model.predict_proba(X)[:, 1]

        return predictions, probabilities

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
                model, self.X_train, self.y_train, cv=cv_folds, scoring="f1"
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
