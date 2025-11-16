"""
Data Processing and Feature Engineering
"""
import pandas as pd
import numpy as np
from typing import List, Optional
from indicators.technical import TechnicalIndicators


class DataProcessor:
    """Process and prepare data for ML models"""

    @staticmethod
    def clean_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean data - handle missing values, duplicates

        Args:
            df: Raw OHLCV DataFrame

        Returns:
            Cleaned DataFrame
        """
        # Remove duplicates
        df = df[~df.index.duplicated(keep='first')]

        # Sort by timestamp
        df = df.sort_index()

        # Forward fill missing values
        df = df.fillna(method='ffill')

        # Drop remaining NaN
        df = df.dropna()

        return df

    @staticmethod
    def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add all technical indicators to DataFrame

        Args:
            df: OHLCV DataFrame

        Returns:
            DataFrame with indicators
        """
        indicators = TechnicalIndicators()

        # Moving Averages
        df['sma_9'] = indicators.sma(df['close'], 9)
        df['sma_20'] = indicators.sma(df['close'], 20)
        df['sma_50'] = indicators.sma(df['close'], 50)
        df['sma_100'] = indicators.sma(df['close'], 100)
        df['sma_200'] = indicators.sma(df['close'], 200)

        df['ema_9'] = indicators.ema(df['close'], 9)
        df['ema_20'] = indicators.ema(df['close'], 20)
        df['ema_50'] = indicators.ema(df['close'], 50)

        # Momentum Indicators
        df['rsi'] = indicators.rsi(df['close'], 14)
        df['rsi_6'] = indicators.rsi(df['close'], 6)
        df['rsi_24'] = indicators.rsi(df['close'], 24)

        # MACD
        macd, signal, hist = indicators.macd(df['close'])
        df['macd'] = macd
        df['macd_signal'] = signal
        df['macd_hist'] = hist

        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = indicators.bollinger_bands(df['close'])
        df['bb_upper'] = bb_upper
        df['bb_middle'] = bb_middle
        df['bb_lower'] = bb_lower
        df['bb_width'] = (bb_upper - bb_lower) / bb_middle

        # Stochastic
        stoch_k, stoch_d = indicators.stochastic(df['high'], df['low'], df['close'])
        df['stoch_k'] = stoch_k
        df['stoch_d'] = stoch_d

        # Volatility Indicators
        df['atr'] = indicators.atr(df['high'], df['low'], df['close'])
        df['atr_percent'] = (df['atr'] / df['close']) * 100

        # Trend Indicators
        df['adx'] = indicators.adx(df['high'], df['low'], df['close'])
        df['cci'] = indicators.cci(df['high'], df['low'], df['close'])
        df['williams_r'] = indicators.williams_r(df['high'], df['low'], df['close'])

        # Volume Indicators
        df['obv'] = indicators.obv(df['close'], df['volume'])
        df['mfi'] = indicators.mfi(df['high'], df['low'], df['close'], df['volume'])
        df['vwap'] = indicators.vwap(df['high'], df['low'], df['close'], df['volume'])

        # Parabolic SAR
        df['sar'] = indicators.parabolic_sar(df['high'], df['low'])

        # Rate of Change
        df['roc'] = indicators.roc(df['close'], 12)

        # Chaikin Money Flow
        df['cmf'] = indicators.cmf(df['high'], df['low'], df['close'], df['volume'], 20)

        return df

    @staticmethod
    def add_price_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add price-based features

        Args:
            df: DataFrame with OHLCV

        Returns:
            DataFrame with price features
        """
        # Price changes
        df['price_change'] = df['close'].pct_change()
        df['price_change_1h'] = df['close'].pct_change(periods=1)
        df['price_change_4h'] = df['close'].pct_change(periods=4)
        df['price_change_24h'] = df['close'].pct_change(periods=24)

        # High-Low spread
        df['hl_spread'] = (df['high'] - df['low']) / df['close']

        # Close position in daily range
        df['close_position'] = (df['close'] - df['low']) / (df['high'] - df['low'])

        # Gap
        df['gap'] = df['open'] - df['close'].shift(1)
        df['gap_percent'] = (df['gap'] / df['close'].shift(1)) * 100

        # Volume changes
        df['volume_change'] = df['volume'].pct_change()
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']

        return df

    @staticmethod
    def add_lag_features(df: pd.DataFrame, columns: List[str], lags: List[int]) -> pd.DataFrame:
        """
        Add lagged features for time series

        Args:
            df: DataFrame
            columns: Columns to create lags for
            lags: List of lag periods

        Returns:
            DataFrame with lag features
        """
        for col in columns:
            for lag in lags:
                df[f'{col}_lag_{lag}'] = df[col].shift(lag)

        return df

    @staticmethod
    def add_rolling_features(df: pd.DataFrame, column: str, windows: List[int]) -> pd.DataFrame:
        """
        Add rolling statistics

        Args:
            df: DataFrame
            column: Column to calculate rolling stats
            windows: List of window sizes

        Returns:
            DataFrame with rolling features
        """
        for window in windows:
            df[f'{column}_rolling_mean_{window}'] = df[column].rolling(window=window).mean()
            df[f'{column}_rolling_std_{window}'] = df[column].rolling(window=window).std()
            df[f'{column}_rolling_min_{window}'] = df[column].rolling(window=window).min()
            df[f'{column}_rolling_max_{window}'] = df[column].rolling(window=window).max()

        return df

    @staticmethod
    def create_target(df: pd.DataFrame, horizon: int = 1, threshold: float = 0.0) -> pd.DataFrame:
        """
        Create target variable for classification

        Args:
            df: DataFrame with close price
            horizon: Prediction horizon (periods ahead)
            threshold: Threshold for classification (percentage)

        Returns:
            DataFrame with target variable
        """
        # Future price
        df['future_price'] = df['close'].shift(-horizon)

        # Price change
        df['future_return'] = (df['future_price'] - df['close']) / df['close'] * 100

        # Classification target (0=down, 1=neutral, 2=up)
        df['target'] = 1  # neutral
        df.loc[df['future_return'] > threshold, 'target'] = 2  # up
        df.loc[df['future_return'] < -threshold, 'target'] = 0  # down

        # Binary target (0=down, 1=up)
        df['target_binary'] = (df['future_return'] > 0).astype(int)

        # Regression target
        df['target_price'] = df['future_price']

        return df

    @staticmethod
    def normalize_features(df: pd.DataFrame, method: str = 'minmax') -> pd.DataFrame:
        """
        Normalize features

        Args:
            df: DataFrame
            method: 'minmax' or 'standard'

        Returns:
            Normalized DataFrame
        """
        if method == 'minmax':
            return (df - df.min()) / (df.max() - df.min())
        elif method == 'standard':
            return (df - df.mean()) / df.std()
        else:
            return df

    @staticmethod
    def prepare_ml_data(
        df: pd.DataFrame,
        target_col: str = 'target',
        drop_cols: Optional[List[str]] = None
    ) -> tuple:
        """
        Prepare data for ML models

        Args:
            df: DataFrame with features and target
            target_col: Target column name
            drop_cols: Columns to drop

        Returns:
            (X, y) - Features and target
        """
        # Drop NaN
        df = df.dropna()

        # Default columns to drop
        if drop_cols is None:
            drop_cols = ['future_price', 'future_return', 'target', 'target_binary', 'target_price']

        # Separate features and target
        y = df[target_col].values
        X = df.drop(columns=[col for col in drop_cols if col in df.columns])

        return X, y

    @staticmethod
    def create_sequences(data: np.ndarray, sequence_length: int) -> np.ndarray:
        """
        Create sequences for LSTM

        Args:
            data: Input data array
            sequence_length: Length of sequences

        Returns:
            3D array of sequences (samples, timesteps, features)
        """
        sequences = []

        for i in range(len(data) - sequence_length):
            sequences.append(data[i:i + sequence_length])

        return np.array(sequences)
