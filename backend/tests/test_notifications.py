import pytest
from sqlalchemy import select

from app.core.roles import RoleName
from app.models.role import Role
from app.models.user import User
from app.services.notification import NotificationService


async def get_or_create_role(db_session, role_name: str):
    res = await db_session.execute(select(Role).where(Role.name == role_name))
    role = res.scalar_one_or_none()
    if not role:
        role = Role(name=role_name, description=role_name)
        db_session.add(role)
        await db_session.flush()
    return role


@pytest.mark.asyncio
async def test_notifications_and_device_registration(db_session):
    role = await get_or_create_role(db_session, RoleName.SALES_REP)

    user = User(email="notif_user@example.com", hashed_password="pw", full_name="Notif User", role_id=role.id)
    db_session.add(user)
    await db_session.flush()

    notif_service = NotificationService(db_session)

    # 1. Create notifications
    n1 = await notif_service.create_notification_record(
        user_id=user.id,
        notification_type="QUOTE_SENT",
        title="Quote Sent",
        message="Your quote Q-001 has been sent.",
    )
    n2 = await notif_service.create_notification_record(
        user_id=user.id,
        notification_type="CUSTOMER_COMMENT",
        title="New Comment",
        message="Customer posted a comment.",
    )

    # List unread notifications
    unread = await notif_service.list_notifications(user_id=user.id, unread_only=True)
    assert len(unread) == 2

    # Mark n1 read
    read_n1 = await notif_service.mark_as_read(n1.id, user.id)
    assert read_n1.is_read is True
    assert read_n1.read_at is not None

    unread_after = await notif_service.list_notifications(user_id=user.id, unread_only=True)
    assert len(unread_after) == 1

    # Mark all read
    updated_count = await notif_service.mark_all_as_read(user.id)
    assert updated_count == 1

    # Register device token
    dev = await notif_service.register_device_token(user_id=user.id, device_token="fcm_token_12345", platform="android")
    assert dev.device_token == "fcm_token_12345"
    assert dev.platform == "android"
    assert dev.is_active is True
