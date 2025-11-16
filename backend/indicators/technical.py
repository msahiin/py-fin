"""
Technical Indicators Library
Comprehensive collection of trading indicators
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional
import talib


class TechnicalIndicators:
    """Calculate various technical indicators"""

    @staticmethod
    def sma(data: pd.Series, period: int = 20) -> pd.Series:
        """Simple Moving Average"""
        return talib.SMA(data, timeperiod=period)

    @staticmethod
    def ema(data: pd.Series, period: int = 20) -> pd.Series:
        """Exponential Moving Average"""
        return talib.EMA(data, timeperiod=period)

    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        return talib.RSI(data, timeperiod=period)

    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        MACD - Moving Average Convergence Divergence
        Returns: (macd_line, signal_line, histogram)
        """
        macd_line, signal_line, histogram = talib.MACD(
            data, fastperiod=fast, slowperiod=slow, signalperiod=signal
        )
        return macd_line, signal_line, histogram

    @staticmethod
    def bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands
        Returns: (upper_band, middle_band, lower_band)
        """
        upper, middle, lower = talib.BBANDS(
            data, timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev
        )
        return upper, middle, lower

    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
                   fastk_period: int = 14, slowk_period: int = 3, slowd_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic Oscillator
        Returns: (slowk, slowd)
        """
        slowk, slowd = talib.STOCH(
            high, low, close,
            fastk_period=fastk_period,
            slowk_period=slowk_period,
            slowd_period=slowd_period
        )
        return slowk, slowd

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average True Range - Volatility indicator"""
        return talib.ATR(high, low, close, timeperiod=period)

    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average Directional Index - Trend strength"""
        return talib.ADX(high, low, close, timeperiod=period)

    @staticmethod
    def cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """Commodity Channel Index"""
        return talib.CCI(high, low, close, timeperiod=period)

    @staticmethod
    def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Williams %R"""
        return talib.WILLR(high, low, close, timeperiod=period)

    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """On-Balance Volume"""
        return talib.OBV(close, volume)

    @staticmethod
    def mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
        """Money Flow Index"""
        return talib.MFI(high, low, close, volume, timeperiod=period)

    @staticmethod
    def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Volume Weighted Average Price"""
        typical_price = (high + low + close) / 3
        return (typical_price * volume).cumsum() / volume.cumsum()

    @staticmethod
    def parabolic_sar(high: pd.Series, low: pd.Series, acceleration: float = 0.02, maximum: float = 0.2) -> pd.Series:
        """Parabolic SAR"""
        return talib.SAR(high, low, acceleration=acceleration, maximum=maximum)

    @staticmethod
    def ichimoku(high: pd.Series, low: pd.Series, close: pd.Series,
                 tenkan_period: int = 9, kijun_period: int = 26, senkou_span_b_period: int = 52) -> dict:
        """
        Ichimoku Cloud
        Returns dict with: tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span
        """
        # Tenkan-sen (Conversion Line)
        tenkan_sen = (high.rolling(window=tenkan_period).max() +
                      low.rolling(window=tenkan_period).min()) / 2

        # Kijun-sen (Base Line)
        kijun_sen = (high.rolling(window=kijun_period).max() +
                     low.rolling(window=kijun_period).min()) / 2

        # Senkou Span A (Leading Span A)
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(kijun_period)

        # Senkou Span B (Leading Span B)
        senkou_span_b = ((high.rolling(window=senkou_span_b_period).max() +
                          low.rolling(window=senkou_span_b_period).min()) / 2).shift(kijun_period)

        # Chikou Span (Lagging Span)
        chikou_span = close.shift(-kijun_period)

        return {
            'tenkan_sen': tenkan_sen,
            'kijun_sen': kijun_sen,
            'senkou_span_a': senkou_span_a,
            'senkou_span_b': senkou_span_b,
            'chikou_span': chikou_span
        }

    @staticmethod
    def fibonacci_retracement(high: float, low: float) -> dict:
        """
        Calculate Fibonacci retracement levels
        """
        diff = high - low
        return {
            '0.0': high,
            '0.236': high - 0.236 * diff,
            '0.382': high - 0.382 * diff,
            '0.500': high - 0.500 * diff,
            '0.618': high - 0.618 * diff,
            '0.786': high - 0.786 * diff,
            '1.0': low
        }

    @staticmethod
    def pivot_points(high: float, low: float, close: float) -> dict:
        """
        Calculate Pivot Points
        """
        pivot = (high + low + close) / 3

        return {
            'pivot': pivot,
            'r1': 2 * pivot - low,
            'r2': pivot + (high - low),
            'r3': high + 2 * (pivot - low),
            's1': 2 * pivot - high,
            's2': pivot - (high - low),
            's3': low - 2 * (high - pivot)
        }

    @staticmethod
    def support_resistance(data: pd.Series, window: int = 20, num_levels: int = 3) -> dict:
        """
        Identify support and resistance levels
        """
        # Find local maxima (resistance)
        resistance = data.rolling(window=window, center=True).max()
        resistance_levels = resistance[resistance == data].drop_duplicates().nlargest(num_levels).tolist()

        # Find local minima (support)
        support = data.rolling(window=window, center=True).min()
        support_levels = support[support == data].drop_duplicates().nsmallest(num_levels).tolist()

        return {
            'resistance': resistance_levels,
            'support': support_levels
        }

    @staticmethod
    def keltner_channels(high: pd.Series, low: pd.Series, close: pd.Series,
                         ema_period: int = 20, atr_period: int = 10, multiplier: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Keltner Channels
        Returns: (upper_channel, middle_line, lower_channel)
        """
        middle = talib.EMA(close, timeperiod=ema_period)
        atr = talib.ATR(high, low, close, timeperiod=atr_period)

        upper = middle + (multiplier * atr)
        lower = middle - (multiplier * atr)

        return upper, middle, lower

    @staticmethod
    def donchian_channels(high: pd.Series, low: pd.Series, period: int = 20) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Donchian Channels
        Returns: (upper_channel, middle_channel, lower_channel)
        """
        upper = high.rolling(window=period).max()
        lower = low.rolling(window=period).min()
        middle = (upper + lower) / 2

        return upper, middle, lower

    @staticmethod
    def roc(data: pd.Series, period: int = 12) -> pd.Series:
        """Rate of Change"""
        return talib.ROC(data, timeperiod=period)

    @staticmethod
    def cmf(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 20) -> pd.Series:
        """
        Chaikin Money Flow
        """
        mfv = ((close - low) - (high - close)) / (high - low) * volume
        return mfv.rolling(window=period).sum() / volume.rolling(window=period).sum()


class IndicatorSignals:
    """Generate trading signals from indicators"""

    @staticmethod
    def rsi_signal(rsi: pd.Series, oversold: int = 30, overbought: int = 70) -> str:
        """
        Generate signal from RSI
        Returns: 'buy', 'sell', or 'neutral'
        """
        current_rsi = rsi.iloc[-1]

        if current_rsi < oversold:
            return 'buy'
        elif current_rsi > overbought:
            return 'sell'
        else:
            return 'neutral'

    @staticmethod
    def macd_signal(macd_line: pd.Series, signal_line: pd.Series) -> str:
        """
        Generate signal from MACD
        Returns: 'buy', 'sell', or 'neutral'
        """
        if macd_line.iloc[-1] > signal_line.iloc[-1] and macd_line.iloc[-2] <= signal_line.iloc[-2]:
            return 'buy'  # Bullish crossover
        elif macd_line.iloc[-1] < signal_line.iloc[-1] and macd_line.iloc[-2] >= signal_line.iloc[-2]:
            return 'sell'  # Bearish crossover
        else:
            return 'neutral'

    @staticmethod
    def moving_average_signal(price: pd.Series, ma_short: pd.Series, ma_long: pd.Series) -> str:
        """
        Generate signal from moving average crossover
        Returns: 'buy', 'sell', or 'neutral'
        """
        if ma_short.iloc[-1] > ma_long.iloc[-1] and ma_short.iloc[-2] <= ma_long.iloc[-2]:
            return 'buy'  # Golden cross
        elif ma_short.iloc[-1] < ma_long.iloc[-1] and ma_short.iloc[-2] >= ma_long.iloc[-2]:
            return 'sell'  # Death cross
        else:
            return 'neutral'

    @staticmethod
    def bollinger_signal(price: pd.Series, upper: pd.Series, lower: pd.Series) -> str:
        """
        Generate signal from Bollinger Bands
        Returns: 'buy', 'sell', or 'neutral'
        """
        current_price = price.iloc[-1]

        if current_price <= lower.iloc[-1]:
            return 'buy'  # Price at lower band - oversold
        elif current_price >= upper.iloc[-1]:
            return 'sell'  # Price at upper band - overbought
        else:
            return 'neutral'

    @staticmethod
    def stochastic_signal(slowk: pd.Series, slowd: pd.Series, oversold: int = 20, overbought: int = 80) -> str:
        """
        Generate signal from Stochastic Oscillator
        Returns: 'buy', 'sell', or 'neutral'
        """
        if slowk.iloc[-1] < oversold and slowk.iloc[-1] > slowd.iloc[-1]:
            return 'buy'  # Oversold and turning up
        elif slowk.iloc[-1] > overbought and slowk.iloc[-1] < slowd.iloc[-1]:
            return 'sell'  # Overbought and turning down
        else:
            return 'neutral'

    @staticmethod
    def combine_signals(signals: list) -> dict:
        """
        Combine multiple signals and calculate confidence

        Args:
            signals: List of signal strings ('buy', 'sell', 'neutral')

        Returns:
            dict with 'direction' and 'confidence'
        """
        buy_count = signals.count('buy')
        sell_count = signals.count('sell')
        total_signals = len(signals)

        if buy_count > sell_count:
            direction = 'buy'
            confidence = (buy_count / total_signals) * 100
        elif sell_count > buy_count:
            direction = 'sell'
            confidence = (sell_count / total_signals) * 100
        else:
            direction = 'neutral'
            confidence = 0

        return {
            'direction': direction,
            'confidence': confidence,
            'buy_signals': buy_count,
            'sell_signals': sell_count,
            'neutral_signals': total_signals - buy_count - sell_count
        }
