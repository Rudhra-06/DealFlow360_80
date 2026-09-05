import asyncio
from typing import Any, Dict, List, Optional, Set
from fastapi import WebSocket
from app.core.roles import RoleName


class ConnectionManager:
    """In-process WebSocket Connection Manager for real-time DealFlow360 events."""

    def __init__(self) -> None:
        # user_id -> Set[WebSocket]
        self._user_connections: Dict[int, Set[WebSocket]] = {}
        # websocket -> (user_id, role_name)
        self._socket_info: Dict[WebSocket, Dict[str, Any]] = {}
        # quotation_id -> Set[user_id]
        self._subscriptions: Dict[int, Set[int]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()

    def register_user(self, websocket: WebSocket, user_id: int, role_name: str) -> None:
        if user_id not in self._user_connections:
            self._user_connections[user_id] = set()
        self._user_connections[user_id].add(websocket)
        self._socket_info[websocket] = {"user_id": user_id, "role": role_name}

    def disconnect(self, websocket: WebSocket) -> None:
        info = self._socket_info.pop(websocket, None)
        if info:
            user_id = info["user_id"]
            if user_id in self._user_connections:
                self._user_connections[user_id].discard(websocket)
                if not self._user_connections[user_id]:
                    del self._user_connections[user_id]

    def subscribe_quote(self, user_id: int, quotation_id: int) -> None:
        if quotation_id not in self._subscriptions:
            self._subscriptions[quotation_id] = set()
        self._subscriptions[quotation_id].add(user_id)

    async def send_to_user(self, user_id: int, message: Dict[str, Any]) -> None:
        if user_id in self._user_connections:
            sockets = list(self._user_connections[user_id])
            for ws in sockets:
                try:
                    # Role-safe sanitization for CUSTOMER
                    role = self._socket_info.get(ws, {}).get("role")
                    payload = self._sanitize_payload(message, role)
                    await ws.send_json(payload)
                except Exception:
                    self.disconnect(ws)

    async def broadcast_to_users(
        self,
        target_user_ids: List[int],
        event_name: str,
        quotation_id: Optional[int],
        data: Dict[str, Any],
        timestamp: str,
    ) -> None:
        envelope = {
            "event": event_name,
            "quotation_id": quotation_id,
            "timestamp": timestamp,
            "data": data,
        }
        for uid in set(target_user_ids):
            await self.send_to_user(uid, envelope)

    def _sanitize_payload(self, envelope: Dict[str, Any], role: Optional[str]) -> Dict[str, Any]:
        if role == RoleName.CUSTOMER:
            # Strip sensitive commercial details if present
            sanitized = envelope.copy()
            data = sanitized.get("data", {}).copy()
            for key in ["unit_cost", "total_cost", "margin_amount", "margin_pct", "risk_reasons", "risk_score"]:
                data.pop(key, None)
            sanitized["data"] = data
            return sanitized
        return envelope


manager = ConnectionManager()
