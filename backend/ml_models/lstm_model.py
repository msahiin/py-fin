"""
LSTM Model for Time Series Prediction
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional
import logging
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau

logger = logging.getLogger(__name__)


class LSTMPredictor:
    """LSTM model for price prediction"""

    def __init__(
        self,
        sequence_length: int = 60,
        n_features: int = 1,
        lstm_units: List[int] = [128, 64, 32],
        dropout_rate: float = 0.2,
        bidirectional: bool = False
    ):
        """
        Initialize LSTM model

        Args:
            sequence_length: Length of input sequences
            n_features: Number of features
            lstm_units: List of LSTM layer sizes
            dropout_rate: Dropout rate for regularization
            bidirectional: Use bidirectional LSTM
        """
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.bidirectional = bidirectional

        self.model = None
        self.scaler = MinMaxScaler()
        self.history = None

    def build_model(self) -> Sequential:
        """
        Build LSTM model architecture

        Returns:
            Compiled Keras model
        """
        model = Sequential()

        # First LSTM layer
        if self.bidirectional:
            model.add(Bidirectional(
                LSTM(self.lstm_units[0], return_sequences=len(self.lstm_units) > 1),
                input_shape=(self.sequence_length, self.n_features)
            ))
        else:
            model.add(LSTM(
                self.lstm_units[0],
                return_sequences=len(self.lstm_units) > 1,
                input_shape=(self.sequence_length, self.n_features)
            ))

        model.add(Dropout(self.dropout_rate))

        # Additional LSTM layers
        for i, units in enumerate(self.lstm_units[1:], 1):
            return_sequences = i < len(self.lstm_units) - 1

            if self.bidirectional:
                model.add(Bidirectional(LSTM(units, return_sequences=return_sequences)))
            else:
                model.add(LSTM(units, return_sequences=return_sequences))

            model.add(Dropout(self.dropout_rate))

        # Output layer
        model.add(Dense(1))

        # Compile model
        model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae', 'mape']
        )

        self.model = model
        logger.info(f"LSTM model built with {model.count_params()} parameters")

        return model

    def prepare_data(
        self,
        data: np.ndarray,
        test_size: float = 0.2,
        validation_size: float = 0.1
    ) -> Tuple:
        """
        Prepare data for training

        Args:
            data: Input data array
            test_size: Test set size
            validation_size: Validation set size

        Returns:
            (X_train, X_val, X_test, y_train, y_val, y_test)
        """
        # Normalize data
        data_scaled = self.scaler.fit_transform(data.reshape(-1, 1))

        # Create sequences
        X, y = [], []
        for i in range(self.sequence_length, len(data_scaled)):
            X.append(data_scaled[i - self.sequence_length:i, 0])
            y.append(data_scaled[i, 0])

        X = np.array(X)
        y = np.array(y)

        # Reshape for LSTM [samples, timesteps, features]
        X = X.reshape((X.shape[0], X.shape[1], 1))

        # Split data
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=test_size, shuffle=False
        )

        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=validation_size, shuffle=False
        )

        logger.info(f"Training samples: {len(X_train)}, Validation: {len(X_val)}, Test: {len(X_test)}")

        return X_train, X_val, X_test, y_train, y_val, y_test

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        epochs: int = 100,
        batch_size: int = 32,
        patience: int = 15,
        save_path: Optional[str] = None
    ):
        """
        Train LSTM model

        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features
            y_val: Validation targets
            epochs: Number of epochs
            batch_size: Batch size
            patience: Early stopping patience
            save_path: Path to save best model
        """
        if self.model is None:
            self.build_model()

        # Callbacks
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=patience,
                restore_best_weights=True,
                verbose=1
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7,
                verbose=1
            )
        ]

        if save_path:
            callbacks.append(
                ModelCheckpoint(
                    save_path,
                    monitor='val_loss',
                    save_best_only=True,
                    verbose=1
                )
            )

        # Train model
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )

        logger.info("LSTM model training completed")

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions

        Args:
            X: Input sequences

        Returns:
            Predictions (inverse transformed)
        """
        if self.model is None:
            raise ValueError("Model not trained yet")

        predictions = self.model.predict(X)
        predictions = self.scaler.inverse_transform(predictions)

        return predictions

    def predict_next(self, last_sequence: np.ndarray, n_steps: int = 1) -> np.ndarray:
        """
        Predict next n steps

        Args:
            last_sequence: Last sequence of data
            n_steps: Number of steps to predict

        Returns:
            Array of predictions
        """
        predictions = []
        current_sequence = last_sequence.copy()

        for _ in range(n_steps):
            # Reshape for prediction
            current_input = current_sequence.reshape((1, self.sequence_length, 1))

            # Predict
            pred = self.model.predict(current_input, verbose=0)
            predictions.append(pred[0, 0])

            # Update sequence
            current_sequence = np.append(current_sequence[1:], pred)

        # Inverse transform
        predictions = self.scaler.inverse_transform(np.array(predictions).reshape(-1, 1))

        return predictions.flatten()

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        """
        Evaluate model performance

        Args:
            X_test: Test features
            y_test: Test targets

        Returns:
            Dictionary of metrics
        """
        if self.model is None:
            raise ValueError("Model not trained yet")

        # Get predictions
        predictions = self.predict(X_test)
        y_test_inv = self.scaler.inverse_transform(y_test.reshape(-1, 1))

        # Calculate metrics
        mse = np.mean((predictions - y_test_inv) ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(predictions - y_test_inv))
        mape = np.mean(np.abs((y_test_inv - predictions) / y_test_inv)) * 100

        metrics = {
            'mse': float(mse),
            'rmse': float(rmse),
            'mae': float(mae),
            'mape': float(mape)
        }

        logger.info(f"LSTM Evaluation - RMSE: {rmse:.4f}, MAE: {mae:.4f}, MAPE: {mape:.2f}%")

        return metrics

    def save(self, path: str):
        """Save model"""
        if self.model:
            self.model.save(path)
            logger.info(f"Model saved to {path}")

    def load(self, path: str):
        """Load model"""
        self.model = keras.models.load_model(path)
        logger.info(f"Model loaded from {path}")


class LSTMClassifier(LSTMPredictor):
    """LSTM model for classification (buy/sell/hold)"""

    def __init__(self, n_classes: int = 3, **kwargs):
        """
        Initialize LSTM classifier

        Args:
            n_classes: Number of classes (3 for buy/sell/hold)
            **kwargs: Arguments for LSTMPredictor
        """
        super().__init__(**kwargs)
        self.n_classes = n_classes

    def build_model(self) -> Sequential:
        """Build classification model"""
        model = Sequential()

        # LSTM layers (same as predictor)
        if self.bidirectional:
            model.add(Bidirectional(
                LSTM(self.lstm_units[0], return_sequences=len(self.lstm_units) > 1),
                input_shape=(self.sequence_length, self.n_features)
            ))
        else:
            model.add(LSTM(
                self.lstm_units[0],
                return_sequences=len(self.lstm_units) > 1,
                input_shape=(self.sequence_length, self.n_features)
            ))

        model.add(Dropout(self.dropout_rate))

        for i, units in enumerate(self.lstm_units[1:], 1):
            return_sequences = i < len(self.lstm_units) - 1

            if self.bidirectional:
                model.add(Bidirectional(LSTM(units, return_sequences=return_sequences)))
            else:
                model.add(LSTM(units, return_sequences=return_sequences))

            model.add(Dropout(self.dropout_rate))

        # Output layer for classification
        model.add(Dense(self.n_classes, activation='softmax'))

        # Compile with categorical crossentropy
        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )

        self.model = model
        logger.info(f"LSTM Classifier built with {model.count_params()} parameters")

        return model

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities

        Args:
            X: Input sequences

        Returns:
            Class probabilities
        """
        if self.model is None:
            raise ValueError("Model not trained yet")

        return self.model.predict(X)

    def predict_class(self, X: np.ndarray) -> np.ndarray:
        """
        Predict classes

        Args:
            X: Input sequences

        Returns:
            Predicted classes
        """
        probabilities = self.predict_proba(X)
        return np.argmax(probabilities, axis=1)
