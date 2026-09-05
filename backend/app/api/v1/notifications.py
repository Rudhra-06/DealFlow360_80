from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.notification import NotificationRead, UserDeviceCreate, UserDeviceRead
from app.services.exceptions import ResourceNotFoundError
from app.services.notification import NotificationService

router = APIRouter()


@router.get(
    "",
    response_model=List[NotificationRead],
    summary="List notifications for current user",
)
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NotificationService(db)
    notifs = await service.list_notifications(
        user_id=current_user.id, unread_only=unread_only, limit=limit, offset=offset
    )
    return [NotificationRead.model_validate(n) for n in notifs]


@router.put(
    "/{notification_id}/read",
    response_model=NotificationRead,
    summary="Mark specific notification as read",
)
async def mark_notification_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NotificationService(db)
    try:
        notif = await service.mark_as_read(notification_id=notification_id, user_id=current_user.id)
        return NotificationRead.model_validate(notif)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/read-all",
    summary="Mark all notifications for current user as read",
)
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NotificationService(db)
    count = await service.mark_all_as_read(user_id=current_user.id)
    return {"message": "All notifications marked as read", "updated_count": count}


@router.post(
    "/devices",
    response_model=UserDeviceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register FCM push notification device token",
)
async def register_device_token(
    obj_in: UserDeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NotificationService(db)
    device = await service.register_device_token(
        user_id=current_user.id, device_token=obj_in.device_token, platform=obj_in.platform
    )
    return UserDeviceRead.model_validate(device)
