from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import RoleName
from app.models.deal_action import DealAction
from app.models.deal_health_audit_event import DealHealthAuditEvent
from app.models.role import Role
from app.models.user import User
from app.repositories.deal_action import DealActionRepository
from app.repositories.deal_alert import DealAlertRepository
from app.repositories.quotation import QuotationRepository
from app.services.exceptions import ResourceNotFoundError
from app.services.notification import NotificationService


class DealActionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.action_repo = DealActionRepository()
        self.alert_repo = DealAlertRepository()
        self.quote_repo = QuotationRepository()
        self.notif_service = NotificationService(db)

    async def _resolve_target_user(self, action_type: str, quote_id: int) -> Optional[int]:
        quote = await self.quote_repo.get_by_id(self.db, quote_id)
        if not quote:
            return None

        if action_type == "NUDGE_SALES_REP":
            return quote.sales_rep_id

        if action_type == "ESCALATE_MANAGER":
            stmt = (
                select(User.id)
                .join(Role, User.role_id == Role.id)
                .where(Role.name == RoleName.SALES_MANAGER, User.is_active == True)
                .limit(1)
            )
            res = await self.db.execute(stmt)
            return res.scalar_one_or_none()

        if action_type == "ESCALATE_FINANCE":
            stmt = (
                select(User.id)
                .join(Role, User.role_id == Role.id)
                .where(Role.name == RoleName.FINANCE_OPERATIONS, User.is_active == True)
                .limit(1)
            )
            res = await self.db.execute(stmt)
            return res.scalar_one_or_none()

        return quote.sales_rep_id

    async def trigger_nudge(
        self, alert_id: int, action_type: str, message_text: Optional[str], actor_user: User
    ) -> DealAction:
        alert = await self.alert_repo.get_by_id(self.db, alert_id)
        if not alert:
            raise ResourceNotFoundError(f"DealAlert with ID {alert_id} not found.")

        target_user_id = await self._resolve_target_user(action_type, alert.quotation_id)
        final_msg = message_text or f"Nudge triggered regarding deal alert '{alert.title}'."

        try:
            now = datetime.now(timezone.utc)
            action = DealAction(
                deal_alert_id=alert.id,
                quotation_id=alert.quotation_id,
                action_type=action_type,
                status="COMPLETED",
                target_user_id=target_user_id,
                created_by_user_id=actor_user.id,
                message=final_msg,
                completed_at=now,
            )
            await self.action_repo.create_action(self.db, action)

            self.db.add(
                DealHealthAuditEvent(
                    quotation_id=alert.quotation_id,
                    sales_order_id=alert.sales_order_id,
                    actor_user_id=actor_user.id,
                    event_type="NUDGE_CREATED",
                    event_metadata={"alert_id": alert.id, "action_type": action_type, "target_user_id": target_user_id},
                )
            )

            await self.db.commit()

            if target_user_id:
                await self.notif_service.create_and_dispatch_notification(
                    user_ids=[target_user_id],
                    notification_type="DEAL_NUDGE",
                    title=f"Nudge: {alert.title}",
                    message=final_msg,
                    quotation_id=alert.quotation_id,
                    payload={"alert_id": alert.id, "action_type": action_type},
                )

            await self.notif_service.dispatch_post_commit_events(
                target_user_ids=[target_user_id] if target_user_id else [alert.quotation.sales_rep_id],
                event_name="deal_action.created",
                quotation_id=alert.quotation_id,
                payload={"action_id": action.id, "action_type": action_type, "message": final_msg},
                title=f"Nudge Sent: {action_type}",
                message_text=final_msg,
            )

            return await self.action_repo.get_by_id(self.db, action.id)
        except Exception:
            await self.db.rollback()
            raise

    async def escalate(self, alert_id: int, message_text: Optional[str], actor_user: User) -> DealAction:
        return await self.trigger_nudge(alert_id, "ESCALATE_MANAGER", message_text, actor_user)
