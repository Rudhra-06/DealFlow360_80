from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.notification import Notification
from app.models.user_device import UserDevice
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self) -> None:
        super().__init__(Notification)

    async def create_notification(self, db: AsyncSession, notif: Notification) -> Notification:
        db.add(notif)
        await db.flush()
        return notif

    async def get_by_id(self, db: AsyncSession, notification_id: int) -> Optional[Notification]:
        stmt = (
            select(Notification)
            .options(selectinload(Notification.quotation))
            .where(Notification.id == notification_id)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_user_notifications(
        self,
        db: AsyncSession,
        user_id: int,
        is_read: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Notification]:
        stmt = (
            select(Notification)
            .options(selectinload(Notification.quotation))
            .where(Notification.user_id == user_id)
        )
        if is_read is not None:
            stmt = stmt.where(Notification.is_read == is_read)

        stmt = stmt.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def mark_as_read(self, db: AsyncSession, notification_id: int, user_id: int) -> Optional[Notification]:
        notif = await self.get_by_id(db, notification_id)
        if notif and notif.user_id == user_id:
            notif.is_read = True
            notif.read_at = datetime.now(timezone.utc)
            await db.flush()
        return notif

    async def mark_all_as_read(self, db: AsyncSession, user_id: int) -> int:
        now = datetime.now(timezone.utc)
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .values(is_read=True, read_at=now)
        )
        res = await db.execute(stmt)
        return res.rowcount or 0


class UserDeviceRepository(BaseRepository[UserDevice]):
    def __init__(self) -> None:
        super().__init__(UserDevice)

    async def register_device(self, db: AsyncSession, device: UserDevice) -> UserDevice:
        db.add(device)
        await db.flush()
        return device

    async def get_active_tokens_by_user_id(self, db: AsyncSession, user_id: int) -> List[str]:
        stmt = select(UserDevice.device_token).where(UserDevice.user_id == user_id, UserDevice.is_active == True)
        res = await db.execute(stmt)
        return list(res.scalars().all())
