"""
Data Collection from Multiple Sources
Binance, Coinbase, MT5, Yahoo Finance
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List
import logging
from binance.client import Client
import ccxt
import yfinance as yf
import asyncio
import aiohttp

logger = logging.getLogger(__name__)


class BinanceCollector:
    """Collect data from Binance exchange"""

    def __init__(self, api_key: str = "", api_secret: str = ""):
        """
        Initialize Binance client

        Args:
            api_key: Binance API key (optional for public data)
            api_secret: Binance API secret (optional for public data)
        """
        self.client = Client(api_key, api_secret) if api_key else Client()

    def get_historical_klines(
        self,
        symbol: str,
        interval: str = "1h",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Get historical candlestick data

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            interval: Timeframe ('1m', '5m', '15m', '1h', '4h', '1d', '1w')
            start_date: Start date string (e.g., '2023-01-01')
            end_date: End date string (e.g., '2024-01-01')
            limit: Number of candles to fetch

        Returns:
            DataFrame with OHLCV data
        """
        try:
            klines = self.client.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=start_date,
                end_str=end_date,
                limit=limit
            )

            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

            # Convert data types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')

            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)

            df.set_index('timestamp', inplace=True)

            logger.info(f"Fetched {len(df)} candles for {symbol} from Binance")
            return df[['open', 'high', 'low', 'close', 'volume']]

        except Exception as e:
            logger.error(f"Error fetching Binance data for {symbol}: {e}")
            return pd.DataFrame()

    async def get_realtime_price(self, symbol: str) -> dict:
        """
        Get real-time price data

        Returns:
            dict with current price info
        """
        try:
            ticker = self.client.get_ticker(symbol=symbol)
            return {
                'symbol': symbol,
                'price': float(ticker['lastPrice']),
                'change_24h': float(ticker['priceChangePercent']),
                'volume': float(ticker['volume']),
                'high_24h': float(ticker['highPrice']),
                'low_24h': float(ticker['lowPrice']),
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error fetching real-time price for {symbol}: {e}")
            return {}

    def get_orderbook(self, symbol: str, limit: int = 100) -> dict:
        """Get order book depth"""
        try:
            orderbook = self.client.get_order_book(symbol=symbol, limit=limit)
            return {
                'bids': [(float(price), float(qty)) for price, qty in orderbook['bids']],
                'asks': [(float(price), float(qty)) for price, qty in orderbook['asks']],
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error fetching orderbook for {symbol}: {e}")
            return {}


class CCXTCollector:
    """Collect data from multiple exchanges using CCXT"""

    def __init__(self, exchange_name: str = 'binance'):
        """
        Initialize CCXT exchange

        Args:
            exchange_name: Exchange name (binance, coinbase, kraken, etc.)
        """
        exchange_class = getattr(ccxt, exchange_name)
        self.exchange = exchange_class({
            'enableRateLimit': True,
        })

    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1h',
        since: Optional[int] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Get OHLCV data

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
            since: Timestamp in milliseconds
            limit: Number of candles

        Returns:
            DataFrame with OHLCV data
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since, limit)

            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )

            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            logger.info(f"Fetched {len(df)} candles for {symbol} from {self.exchange.name}")
            return df

        except Exception as e:
            logger.error(f"Error fetching CCXT data for {symbol}: {e}")
            return pd.DataFrame()

    def get_ticker(self, symbol: str) -> dict:
        """Get current ticker data"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'price': ticker['last'],
                'change_24h': ticker['percentage'],
                'volume': ticker['quoteVolume'],
                'high_24h': ticker['high'],
                'low_24h': ticker['low'],
                'timestamp': datetime.fromtimestamp(ticker['timestamp'] / 1000)
            }
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return {}


class YahooFinanceCollector:
    """Collect data from Yahoo Finance (for forex and stocks)"""

    @staticmethod
    def get_historical_data(
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = '1h'
    ) -> pd.DataFrame:
        """
        Get historical data from Yahoo Finance

        Args:
            symbol: Ticker symbol (e.g., 'EURUSD=X' for forex)
            start_date: Start date string
            end_date: End date string
            interval: Interval ('1m', '5m', '15m', '1h', '1d')

        Returns:
            DataFrame with OHLCV data
        """
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval=interval)

            if df.empty:
                logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()

            # Rename columns to match our format
            df.columns = [col.lower() for col in df.columns]
            df = df[['open', 'high', 'low', 'close', 'volume']]

            logger.info(f"Fetched {len(df)} records for {symbol} from Yahoo Finance")
            return df

        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance data for {symbol}: {e}")
            return pd.DataFrame()


class MT5Collector:
    """Collect data from MetaTrader 5 (Forex)"""

    def __init__(self):
        """Initialize MT5 connection"""
        try:
            import MetaTrader5 as mt5
            self.mt5 = mt5

            if not mt5.initialize():
                logger.error("MT5 initialization failed")
                self.mt5 = None
        except ImportError:
            logger.warning("MetaTrader5 package not installed")
            self.mt5 = None

    def get_historical_data(
        self,
        symbol: str,
        timeframe: int,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        Get historical forex data from MT5

        Args:
            symbol: Forex pair (e.g., 'EURUSD')
            timeframe: MT5 timeframe constant (mt5.TIMEFRAME_H1)
            start_date: Start datetime
            end_date: End datetime

        Returns:
            DataFrame with OHLCV data
        """
        if not self.mt5:
            logger.error("MT5 not initialized")
            return pd.DataFrame()

        try:
            rates = self.mt5.copy_rates_range(symbol, timeframe, start_date, end_date)

            if rates is None:
                logger.warning(f"No data for {symbol}")
                return pd.DataFrame()

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)

            # Rename columns
            df = df.rename(columns={'tick_volume': 'volume'})
            df = df[['open', 'high', 'low', 'close', 'volume']]

            logger.info(f"Fetched {len(df)} records for {symbol} from MT5")
            return df

        except Exception as e:
            logger.error(f"Error fetching MT5 data for {symbol}: {e}")
            return pd.DataFrame()

    def close(self):
        """Close MT5 connection"""
        if self.mt5:
            self.mt5.shutdown()


class DataAggregator:
    """Aggregate data from multiple sources"""

    def __init__(self):
        self.binance = BinanceCollector()
        self.ccxt = CCXTCollector()
        self.yahoo = YahooFinanceCollector()
        self.mt5 = MT5Collector()

    def get_data(
        self,
        symbol: str,
        source: str = 'binance',
        interval: str = '1h',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get data from specified source

        Args:
            symbol: Trading pair
            source: Data source ('binance', 'ccxt', 'yahoo', 'mt5')
            interval: Timeframe
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with OHLCV data
        """
        if source == 'binance':
            return self.binance.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_date=start_date,
                end_date=end_date
            )
        elif source == 'ccxt':
            return self.ccxt.get_ohlcv(
                symbol=symbol,
                timeframe=interval
            )
        elif source == 'yahoo':
            return self.yahoo.get_historical_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval=interval
            )
        elif source == 'mt5':
            # Convert interval to MT5 timeframe
            # This is a simplified version
            return self.mt5.get_historical_data(
                symbol=symbol,
                timeframe=1,  # MT5 constant
                start_date=datetime.strptime(start_date, '%Y-%m-%d'),
                end_date=datetime.strptime(end_date, '%Y-%m-%d')
            )
        else:
            logger.error(f"Unknown data source: {source}")
            return pd.DataFrame()

    async def get_multiple_symbols(
        self,
        symbols: List[str],
        source: str = 'binance',
        interval: str = '1h'
    ) -> dict:
        """
        Get data for multiple symbols concurrently

        Returns:
            dict: {symbol: DataFrame}
        """
        results = {}

        for symbol in symbols:
            try:
                df = self.get_data(symbol, source, interval)
                results[symbol] = df
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
                results[symbol] = pd.DataFrame()

        return results
