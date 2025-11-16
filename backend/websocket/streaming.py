"""
Real-time WebSocket Streaming Service
Streams market data, signals, and trading updates
"""
import asyncio
import json
from typing import Set, Dict
from datetime import datetime
import logging

from data.collectors import BinanceCollector
from websocket.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


class StreamingService:
    """Real-time data streaming service"""

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.active_streams: Dict[str, asyncio.Task] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # topic -> set of client_ids

    async def start_price_stream(self, symbol: str):
        """Start streaming prices for a symbol"""
        stream_key = f"price_{symbol}"

        if stream_key in self.active_streams:
            logger.info(f"Price stream already active for {symbol}")
            return

        async def price_stream_task():
            """Stream price updates"""
            collector = BinanceCollector()

            while True:
                try:
                    price_data = await collector.get_realtime_price(symbol)

                    if price_data:
                        # Broadcast to subscribers
                        await self.connection_manager.publish_to_topic(
                            f"price_{symbol}",
                            {
                                "type": "price_update",
                                "data": {
                                    "symbol": symbol,
                                    "price": price_data['price'],
                                    "change_24h": price_data['change_24h'],
                                    "volume": price_data['volume'],
                                    "timestamp": datetime.utcnow().isoformat()
                                }
                            }
                        )

                    await asyncio.sleep(1)  # Update every second

                except Exception as e:
                    logger.error(f"Error in price stream for {symbol}: {e}")
                    await asyncio.sleep(5)

        # Start the stream task
        task = asyncio.create_task(price_stream_task())
        self.active_streams[stream_key] = task

        logger.info(f"Started price stream for {symbol}")

    async def stop_price_stream(self, symbol: str):
        """Stop streaming prices for a symbol"""
        stream_key = f"price_{symbol}"

        if stream_key in self.active_streams:
            self.active_streams[stream_key].cancel()
            del self.active_streams[stream_key]
            logger.info(f"Stopped price stream for {symbol}")

    async def broadcast_signal(self, signal_data: dict):
        """Broadcast new trading signal"""
        await self.connection_manager.publish_to_topic(
            "signals",
            {
                "type": "new_signal",
                "data": signal_data
            }
        )

    async def broadcast_trade_update(self, trade_data: dict):
        """Broadcast trade execution update"""
        await self.connection_manager.publish_to_topic(
            "trades",
            {
                "type": "trade_update",
                "data": trade_data
            }
        )

    async def broadcast_account_update(self, account_data: dict):
        """Broadcast account balance/equity update"""
        await self.connection_manager.publish_to_topic(
            "account",
            {
                "type": "account_update",
                "data": account_data
            }
        )

    def cleanup(self):
        """Cancel all active streams"""
        for task in self.active_streams.values():
            task.cancel()

        self.active_streams.clear()
        logger.info("All streams stopped")


# Global streaming service instance
streaming_service: StreamingService = None


def get_streaming_service(connection_manager: ConnectionManager) -> StreamingService:
    """Get or create streaming service instance"""
    global streaming_service

    if streaming_service is None:
        streaming_service = StreamingService(connection_manager)

    return streaming_service
