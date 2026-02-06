import asyncio
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect
import json


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
        
        message_json = json.dumps(message)
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception:
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections.discard(conn)
    
    async def send_alert_update(self, alert_id: int, action: str, data: dict = None):
        """Send alert update to all connected clients"""
        message = {
            "type": "alert_update",
            "alert_id": alert_id,
            "action": action,  # created, acknowledged, resolved, updated
            "data": data
        }
        await self.broadcast(message)
    
    async def send_stats_update(self, stats: dict):
        """Send stats update to all connected clients"""
        message = {
            "type": "stats_update",
            "data": stats
        }
        await self.broadcast(message)


# Global connection manager
manager = ConnectionManager()
