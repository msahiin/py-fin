"""
WebSocket Connection Manager
"""
from typing import Dict, List
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        # Store active connections: {client_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}

        # Store subscriptions: {topic: [client_ids]}
        self.subscriptions: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and store new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            # Remove from all subscriptions
            for topic in self.subscriptions:
                if client_id in self.subscriptions[topic]:
                    self.subscriptions[topic].remove(client_id)
            logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_text(message)

    async def send_json(self, data: dict, client_id: str):
        """Send JSON data to specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_json(data)

    async def broadcast(self, message: str):
        """Broadcast message to all connected clients"""
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")

    async def broadcast_json(self, data: dict):
        """Broadcast JSON data to all connected clients"""
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(data)
            except Exception as e:
                logger.error(f"Error broadcasting JSON to {client_id}: {e}")

    def subscribe(self, client_id: str, topic: str):
        """Subscribe client to a topic"""
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        if client_id not in self.subscriptions[topic]:
            self.subscriptions[topic].append(client_id)
            logger.info(f"Client {client_id} subscribed to {topic}")

    def unsubscribe(self, client_id: str, topic: str):
        """Unsubscribe client from a topic"""
        if topic in self.subscriptions and client_id in self.subscriptions[topic]:
            self.subscriptions[topic].remove(client_id)
            logger.info(f"Client {client_id} unsubscribed from {topic}")

    async def publish_to_topic(self, topic: str, data: dict):
        """Publish data to all subscribers of a topic"""
        if topic in self.subscriptions:
            for client_id in self.subscriptions[topic]:
                if client_id in self.active_connections:
                    try:
                        await self.send_json(data, client_id)
                    except Exception as e:
                        logger.error(f"Error publishing to {client_id} on topic {topic}: {e}")
