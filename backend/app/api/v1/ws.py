import json
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt import decode_access_token
from app.db.session import get_db
from app.repositories.user import UserRepository
from app.websocket.manager import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = decode_access_token(token)
        user_id = int(payload.sub)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_repo = UserRepository()
    user = await user_repo.get_by_id(db, user_id, load_role=True)
    if not user or not user.is_active or not user.role:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket)
    manager.register_user(websocket, user_id=user.id, role_name=user.role.name)

    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                msg_data = json.loads(raw_data)
                action = msg_data.get("action")
                if action == "subscribe" and "quotation_id" in msg_data:
                    q_id = int(msg_data["quotation_id"])
                    manager.subscribe_quote(user.id, q_id)
                    await websocket.send_json(
                        {"event": "subscription.success", "quotation_id": q_id, "status": "subscribed"}
                    )
                elif action == "ping":
                    await websocket.send_json({"event": "pong"})
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
