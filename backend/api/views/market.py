"""
Market Data API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd

from database import get_db
from models import User
from api.schemas import MarketDataRequest, PriceUpdate
from auth import get_current_user
from data.collectors import DataAggregator, BinanceCollector
from data.processors import DataProcessor

router = APIRouter()


@router.get("/data/{symbol}")
async def get_market_data(
    symbol: str,
    interval: str = "1h",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 1000,
    current_user: User = Depends(get_current_user)
):
    """
    Get historical market data for a symbol
    """
    aggregator = DataAggregator()

    df = aggregator.get_data(
        symbol=symbol,
        source='binance',
        interval=interval,
        start_date=start_date,
        end_date=end_date
    )

    if df.empty:
        raise HTTPException(status_code=404, detail="No data found for symbol")

    # Limit results
    df = df.tail(limit)

    # Convert to JSON-friendly format
    data = df.reset_index().to_dict(orient='records')

    return {
        "symbol": symbol,
        "interval": interval,
        "count": len(data),
        "data": data
    }


@router.get("/price/{symbol}")
async def get_current_price(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get current price for a symbol
    """
    collector = BinanceCollector()
    price_data = await collector.get_realtime_price(symbol)

    if not price_data:
        raise HTTPException(status_code=404, detail="Price data not available")

    return price_data


@router.get("/indicators/{symbol}")
def get_indicators(
    symbol: str,
    interval: str = "1h",
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """
    Get technical indicators for a symbol
    """
    # Get data
    aggregator = DataAggregator()
    df = aggregator.get_data(
        symbol=symbol,
        source='binance',
        interval=interval
    )

    if df.empty:
        raise HTTPException(status_code=404, detail="No data found")

    # Calculate indicators
    processor = DataProcessor()
    df = processor.clean_data(df)
    df = processor.add_technical_indicators(df)

    # Get latest values
    df = df.tail(limit)
    latest = df.iloc[-1]

    indicators = {
        'symbol': symbol,
        'timestamp': latest.name.isoformat() if hasattr(latest.name, 'isoformat') else str(latest.name),
        'price': float(latest['close']),
        'rsi': float(latest['rsi']) if 'rsi' in latest and pd.notna(latest['rsi']) else None,
        'macd': float(latest['macd']) if 'macd' in latest and pd.notna(latest['macd']) else None,
        'macd_signal': float(latest['macd_signal']) if 'macd_signal' in latest and pd.notna(latest['macd_signal']) else None,
        'bb_upper': float(latest['bb_upper']) if 'bb_upper' in latest and pd.notna(latest['bb_upper']) else None,
        'bb_lower': float(latest['bb_lower']) if 'bb_lower' in latest and pd.notna(latest['bb_lower']) else None,
        'sma_20': float(latest['sma_20']) if 'sma_20' in latest and pd.notna(latest['sma_20']) else None,
        'sma_50': float(latest['sma_50']) if 'sma_50' in latest and pd.notna(latest['sma_50']) else None,
        'ema_20': float(latest['ema_20']) if 'ema_20' in latest and pd.notna(latest['ema_20']) else None,
        'atr': float(latest['atr']) if 'atr' in latest and pd.notna(latest['atr']) else None,
        'volume': float(latest['volume'])
    }

    return indicators


@router.get("/symbols")
def get_supported_symbols(
    current_user: User = Depends(get_current_user)
):
    """
    Get list of supported trading symbols
    """
    from config import settings

    return {
        "symbols": settings.SUPPORTED_SYMBOLS,
        "count": len(settings.SUPPORTED_SYMBOLS)
    }


@router.get("/orderbook/{symbol}")
def get_orderbook(
    symbol: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """
    Get order book for a symbol
    """
    collector = BinanceCollector()
    orderbook = collector.get_orderbook(symbol, limit)

    if not orderbook:
        raise HTTPException(status_code=404, detail="Orderbook not available")

    return orderbook
