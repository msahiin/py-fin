"""
LightGBM Model for Trading Predictions
"""
import numpy as np
import pandas as pd
from typing import Optional
import logging
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import lightgbm as lgb
import pickle

logger = logging.getLogger(__name__)


class LightGBMClassifier:
    """LightGBM for price direction classification"""

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 7,
        learning_rate: float = 0.1,
        num_leaves: int = 31,
        random_state: int = 42
    ):
        """
        Initialize LightGBM classifier

        Args:
            n_estimators: Number of boosting iterations
            max_depth: Maximum tree depth
            learning_rate: Learning rate
            num_leaves: Maximum number of leaves
            random_state: Random seed
        """
        self.params = {
            'n_estimators': n_estimators,
            'max_depth': max_depth,
            'learning_rate': learning_rate,
            'num_leaves': num_leaves,
            'random_state': random_state,
            'objective': 'multiclass',
            'num_class': 3,
            'metric': 'multi_logloss',
            'verbosity': -1
        }

        self.model = lgb.LGBMClassifier(**self.params)
        self.feature_importance = None

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: np.ndarray,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[np.ndarray] = None,
        early_stopping_rounds: int = 50
    ):
        """
        Train LightGBM classifier

        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features
            y_val: Validation labels
            early_stopping_rounds: Early stopping rounds
        """
        if X_val is not None and y_val is not None:
            self.model.fit(
                X_train, y_train,
                eval_set=[(X_train, y_train), (X_val, y_val)],
                eval_names=['train', 'valid'],
                callbacks=[
                    lgb.early_stopping(stopping_rounds=early_stopping_rounds, verbose=True),
                    lgb.log_evaluation(period=10)
                ]
            )
        else:
            self.model.fit(X_train, y_train)

        # Get feature importance
        self.feature_importance = pd.DataFrame({
            'feature': X_train.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        logger.info("LightGBM classifier training completed")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict classes"""
        return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict class probabilities"""
        return self.model.predict_proba(X)

    def evaluate(self, X_test: pd.DataFrame, y_test: np.ndarray) -> dict:
        """Evaluate model performance"""
        y_pred = self.predict(X_test)
        y_proba = self.predict_proba(X_test)

        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted'),
            'recall': recall_score(y_test, y_pred, average='weighted'),
            'f1_score': f1_score(y_test, y_pred, average='weighted')
        }

        logger.info(f"LightGBM Evaluation - Accuracy: {metrics['accuracy']:.4f}, F1: {metrics['f1_score']:.4f}")

        return metrics

    def get_feature_importance(self, top_n: int = 20) -> pd.DataFrame:
        """Get top N important features"""
        if self.feature_importance is None:
            raise ValueError("Model not trained yet")

        return self.feature_importance.head(top_n)

    def save(self, path: str):
        """Save model"""
        with open(path, 'wb') as f:
            pickle.dump(self.model, f)
        logger.info(f"Model saved to {path}")

    def load(self, path: str):
        """Load model"""
        with open(path, 'rb') as f:
            self.model = pickle.load(f)
        logger.info(f"Model loaded from {path}")


class EnsembleModel:
    """Ensemble of multiple ML models"""

    def __init__(self):
        """Initialize ensemble model"""
        self.models = {}
        self.weights = {}

    def add_model(self, name: str, model, weight: float = 1.0):
        """
        Add model to ensemble

        Args:
            name: Model name
            model: Model instance
            weight: Model weight for voting
        """
        self.models[name] = model
        self.weights[name] = weight

        logger.info(f"Added model '{name}' to ensemble with weight {weight}")

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict using weighted voting

        Args:
            X: Features

        Returns:
            Weighted average probabilities
        """
        if not self.models:
            raise ValueError("No models in ensemble")

        # Get predictions from all models
        predictions = []
        weights = []

        for name, model in self.models.items():
            try:
                proba = model.predict_proba(X)
                predictions.append(proba)
                weights.append(self.weights[name])
            except Exception as e:
                logger.error(f"Error getting prediction from {name}: {e}")

        if not predictions:
            raise ValueError("All models failed to predict")

        # Weighted average
        predictions = np.array(predictions)
        weights = np.array(weights)
        weights = weights / weights.sum()  # Normalize

        weighted_proba = np.average(predictions, axis=0, weights=weights)

        return weighted_proba

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict classes"""
        proba = self.predict_proba(X)
        return np.argmax(proba, axis=1)

    def evaluate(self, X_test: pd.DataFrame, y_test: np.ndarray) -> dict:
        """Evaluate ensemble performance"""
        y_pred = self.predict(X_test)

        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted'),
            'recall': recall_score(y_test, y_pred, average='weighted'),
            'f1_score': f1_score(y_test, y_pred, average='weighted')
        }

        logger.info(f"Ensemble Evaluation - Accuracy: {metrics['accuracy']:.4f}, F1: {metrics['f1_score']:.4f}")

        return metrics

    def get_model_contributions(self, X: pd.DataFrame) -> dict:
        """
        Get individual model predictions and their contributions

        Args:
            X: Features

        Returns:
            Dictionary with model predictions
        """
        contributions = {}

        for name, model in self.models.items():
            try:
                proba = model.predict_proba(X)
                prediction = np.argmax(proba, axis=1)
                confidence = np.max(proba, axis=1)

                contributions[name] = {
                    'prediction': prediction.tolist(),
                    'confidence': confidence.tolist(),
                    'weight': self.weights[name]
                }
            except Exception as e:
                logger.error(f"Error getting contribution from {name}: {e}")

        return contributions
