import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.firebase import firebase_push_service
from app.models.notification import Notification
from app.models.user_device import UserDevice
from app.repositories.notification import NotificationRepository, UserDeviceRepository
from app.schemas.notification import UserDeviceCreate
from app.services.exceptions import ResourceNotFoundError
from app.websocket.manager import manager as ws_manager

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.notif_repo = NotificationRepository()
        self.device_repo = UserDeviceRepository()

    async def create_notification_record(
        self,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        quotation_id: Optional[int] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """Persists notification record inside current DB transaction."""
        notif = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            quotation_id=quotation_id,
            payload=payload,
            is_read=False,
        )
        return await self.notif_repo.create_notification(self.db, notif)

    async def create_and_dispatch_notification(
        self,
        user_id: int = 0,
        notification_type: str = "NOTIFICATION",
        title: str = "Notification",
        message: str = "",
        quotation_id: Optional[int] = None,
        payload: Optional[Dict[str, Any]] = None,
        recipient_user_ids: Optional[List[int]] = None,
        **kwargs: Any,
    ) -> Optional[Notification]:
        recipients = recipient_user_ids or ([user_id] if user_id else [])
        notif = None
        for uid in recipients:
            notif = await self.create_notification_record(
                user_id=uid,
                notification_type=notification_type,
                title=title,
                message=message,
                quotation_id=quotation_id,
                payload=payload,
            )
        await self.dispatch_post_commit_events(
            target_user_ids=recipients,
            event_name=notification_type,
            quotation_id=quotation_id,
            payload=payload or {},
            title=title,
            message_text=message,
        )
        return notif


    async def dispatch_post_commit_events(
        self,
        target_user_ids: Optional[List[int]] = None,
        event_name: str = "notification.created",
        quotation_id: Optional[int] = None,
        payload: Optional[Dict[str, Any]] = None,
        title: str = "Notification",
        message_text: str = "",
        db: Optional[AsyncSession] = None,
        recipient_user_ids: Optional[List[int]] = None,
        notification_type: Optional[str] = None,
        content: Optional[str] = None,
    ) -> None:
        """
        Delivers real-time WebSockets and FCM push notifications STRICTLY post-commit.
        Accepts flexible arguments for both event naming styles.
        """
        user_ids = target_user_ids or recipient_user_ids or []
        msg = message_text or content or title
        event = event_name or notification_type or "notification.created"
        p_load = payload or {}

        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            # 1. Real-time WebSocket delivery
            await ws_manager.broadcast_to_users(
                target_user_ids=user_ids,
                event_name=event,
                quotation_id=quotation_id,
                data=p_load,
                timestamp=now_iso,
            )
        except Exception as e:
            logger.error(f"Post-commit WebSocket dispatch error: {e}")

        # 2. Firebase Push delivery
        try:
            device_repo = UserDeviceRepository()
            active_db = db or getattr(self, "db", None)
            if active_db:
                for uid in set(user_ids):
                    tokens = await device_repo.get_active_tokens_by_user_id(active_db, uid)
                    if tokens:
                        await firebase_push_service.send_push_notification(
                            device_tokens=tokens,
                            title=title,
                            body=msg,
                            data={"event": event, "quotation_id": quotation_id},
                        )
        except Exception as e:
            logger.error(f"Post-commit FCM push delivery error: {e}")

    async def list_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        is_read: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Notification]:
        read_filter = is_read
        if unread_only:
            read_filter = False
        return await self.notif_repo.list_user_notifications(
            self.db, user_id=user_id, is_read=read_filter, limit=limit, offset=offset
        )

    async def list_user_notifications(
        self,
        user_id: int,
        is_read: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Notification]:
        return await self.list_notifications(user_id=user_id, is_read=is_read, limit=limit, offset=offset)

    async def mark_as_read(self, notification_id: int, user_id: int) -> Notification:
        notif = await self.notif_repo.mark_as_read(self.db, notification_id, user_id)
        if not notif:
            raise ResourceNotFoundError(f"Notification with ID {notification_id} not found.")
        try:
            await self.db.commit()
            return notif
        except Exception:
            await self.db.rollback()
            raise

    async def mark_all_as_read(self, user_id: int) -> int:
        try:
            count = await self.notif_repo.mark_all_as_read(self.db, user_id)
            await self.db.commit()
            return count
        except Exception:
            await self.db.rollback()
            raise

    async def register_device_token(
        self, user_id: int, device_token: str, platform: Optional[str] = None
    ) -> UserDevice:
        try:
            device = UserDevice(
                user_id=user_id,
                device_token=device_token,
                platform=platform,
                is_active=True,
            )
            created = await self.device_repo.register_device(self.db, device)
            await self.db.commit()
            return created
        except Exception:
            await self.db.rollback()
            raise

    async def register_device(self, user_id: int, obj_in: UserDeviceCreate) -> UserDevice:
        return await self.register_device_token(
            user_id=user_id, device_token=obj_in.device_token, platform=obj_in.platform
        )
