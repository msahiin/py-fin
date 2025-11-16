"""
Test suite for technical indicators
"""
import pytest
import pandas as pd
import numpy as np
from indicators.technical import TechnicalIndicators, IndicatorSignals


@pytest.fixture
def sample_data():
    """Generate sample OHLCV data"""
    dates = pd.date_range('2024-01-01', periods=100, freq='1H')
    data = {
        'open': np.random.uniform(40000, 42000, 100),
        'high': np.random.uniform(41000, 43000, 100),
        'low': np.random.uniform(39000, 41000, 100),
        'close': np.random.uniform(40000, 42000, 100),
        'volume': np.random.uniform(1000, 5000, 100)
    }
    df = pd.DataFrame(data, index=dates)
    return df


def test_sma(sample_data):
    """Test Simple Moving Average"""
    indicators = TechnicalIndicators()
    sma = indicators.sma(sample_data['close'], period=20)

    assert len(sma) == len(sample_data)
    assert not sma.isnull().all()


def test_rsi(sample_data):
    """Test RSI"""
    indicators = TechnicalIndicators()
    rsi = indicators.rsi(sample_data['close'], period=14)

    assert len(rsi) == len(sample_data)
    # RSI should be between 0 and 100
    assert rsi[~rsi.isnull()].min() >= 0
    assert rsi[~rsi.isnull()].max() <= 100


def test_macd(sample_data):
    """Test MACD"""
    indicators = TechnicalIndicators()
    macd, signal, hist = indicators.macd(sample_data['close'])

    assert len(macd) == len(sample_data)
    assert len(signal) == len(sample_data)
    assert len(hist) == len(sample_data)


def test_bollinger_bands(sample_data):
    """Test Bollinger Bands"""
    indicators = TechnicalIndicators()
    upper, middle, lower = indicators.bollinger_bands(sample_data['close'])

    assert len(upper) == len(sample_data)
    # Upper band should be above lower band
    valid_idx = ~(upper.isnull() | lower.isnull())
    assert (upper[valid_idx] >= lower[valid_idx]).all()


def test_atr(sample_data):
    """Test ATR"""
    indicators = TechnicalIndicators()
    atr = indicators.atr(sample_data['high'], sample_data['low'], sample_data['close'])

    assert len(atr) == len(sample_data)
    # ATR should be positive
    assert (atr[~atr.isnull()] >= 0).all()


def test_rsi_signal():
    """Test RSI signal generation"""
    signal_gen = IndicatorSignals()

    # Create RSI series
    rsi = pd.Series([25, 30, 35])  # Oversold

    signal = signal_gen.rsi_signal(rsi)
    assert signal in ['buy', 'sell', 'neutral']


def test_combine_signals():
    """Test signal combination"""
    signal_gen = IndicatorSignals()

    signals = ['buy', 'buy', 'sell', 'neutral', 'buy']
    result = signal_gen.combine_signals(signals)

    assert 'direction' in result
    assert 'confidence' in result
    assert result['direction'] in ['buy', 'sell', 'neutral']
    assert 0 <= result['confidence'] <= 100
