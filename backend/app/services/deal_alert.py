from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deal_alert import DealAlert
from app.models.deal_health_audit_event import DealHealthAuditEvent
from app.models.user import User
from app.repositories.deal_alert import DealAlertRepository
from app.repositories.quotation import QuotationRepository
from app.schemas.deal_health import DealAlertListItem
from app.services.exceptions import CommercialPolicyValidationError, ResourceNotFoundError
from app.services.notification import NotificationService


class DealAlertService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.alert_repo = DealAlertRepository()
        self.quote_repo = QuotationRepository()
        self.notif_service = NotificationService(db)

    async def get_alert(self, alert_id: int) -> DealAlert:
        alert = await self.alert_repo.get_by_id(self.db, alert_id)
        if not alert:
            raise ResourceNotFoundError(f"DealAlert with ID {alert_id} not found.")
        return alert

    async def list_alerts(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        alert_type: Optional[str] = None,
        quotation_id: Optional[int] = None,
        assigned_user_id: Optional[int] = None,
        sales_rep_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[DealAlertListItem]:
        alerts = await self.alert_repo.list_alerts(
            self.db,
            status=status,
            severity=severity,
            alert_type=alert_type,
            quotation_id=quotation_id,
            assigned_user_id=assigned_user_id,
            sales_rep_id=sales_rep_id,
            customer_id=customer_id,
            limit=limit,
            offset=offset,
        )

        results = []
        for a in alerts:
            quote = a.quotation
            cust_name = quote.customer.name if quote and quote.customer else "Unknown Customer"
            rep_name = quote.sales_rep.full_name if quote and quote.sales_rep else "Unknown Rep"
            quote_num = quote.quote_number if quote else "Q-UNK"

            results.append(
                DealAlertListItem(
                    id=a.id,
                    quotation_id=a.quotation_id,
                    quote_number=quote_num,
                    customer_name=cust_name,
                    sales_rep_name=rep_name,
                    alert_type=a.alert_type,
                    severity=a.severity,
                    status=a.status,
                    title=a.title,
                    message=a.message,
                    created_at=a.created_at,
                    last_triggered_at=a.last_triggered_at,
                    occurrence_count=a.occurrence_count,
                )
            )

        return results

    async def acknowledge_alert(self, alert_id: int, current_user: User) -> DealAlert:
        alert = await self.get_alert(alert_id)
        if alert.status in {"RESOLVED", "DISMISSED"}:
            raise CommercialPolicyValidationError(f"Cannot acknowledge alert in '{alert.status}' status.")

        try:
            now = datetime.now(timezone.utc)
            alert.status = "ACKNOWLEDGED"
            alert.acknowledged_at = now
            alert.acknowledged_by_user_id = current_user.id

            self.db.add(
                DealHealthAuditEvent(
                    quotation_id=alert.quotation_id,
                    sales_order_id=alert.sales_order_id,
                    actor_user_id=current_user.id,
                    event_type="ALERT_ACKNOWLEDGED",
                    event_metadata={"alert_id": alert.id, "alert_type": alert.alert_type},
                )
            )

            await self.db.commit()

            # Realtime post-commit dispatch
            await self.notif_service.dispatch_post_commit_events(
                target_user_ids=[alert.quotation.sales_rep_id],
                event_name="deal_alert.acknowledged",
                quotation_id=alert.quotation_id,
                payload={"alert_id": alert.id, "status": alert.status},
                title=f"Alert Acknowledged: {alert.title}",
                message_text=f"Alert {alert.title} acknowledged by {current_user.full_name}.",
            )

            return await self.get_alert(alert.id)
        except Exception:
            await self.db.rollback()
            raise

    async def resolve_alert(self, alert_id: int, resolution_note: str, current_user: User) -> DealAlert:
        alert = await self.get_alert(alert_id)

        try:
            now = datetime.now(timezone.utc)
            alert.status = "RESOLVED"
            alert.resolved_at = now
            alert.resolved_by_user_id = current_user.id
            alert.resolution_note = resolution_note

            self.db.add(
                DealHealthAuditEvent(
                    quotation_id=alert.quotation_id,
                    sales_order_id=alert.sales_order_id,
                    actor_user_id=current_user.id,
                    event_type="ALERT_RESOLVED",
                    event_metadata={"alert_id": alert.id, "resolution_note": resolution_note},
                )
            )

            await self.db.commit()

            await self.notif_service.dispatch_post_commit_events(
                target_user_ids=[alert.quotation.sales_rep_id],
                event_name="deal_alert.resolved",
                quotation_id=alert.quotation_id,
                payload={"alert_id": alert.id, "status": alert.status, "note": resolution_note},
                title=f"Alert Resolved: {alert.title}",
                message_text=f"Alert resolved by {current_user.full_name}: {resolution_note}",
            )

            return await self.get_alert(alert.id)
        except Exception:
            await self.db.rollback()
            raise

    async def dismiss_alert(self, alert_id: int, reason: Optional[str], current_user: User) -> DealAlert:
        alert = await self.get_alert(alert_id)

        try:
            now = datetime.now(timezone.utc)
            alert.status = "DISMISSED"
            alert.resolved_at = now
            alert.resolved_by_user_id = current_user.id
            alert.resolution_note = f"DISMISSED: {reason}" if reason else "DISMISSED"

            self.db.add(
                DealHealthAuditEvent(
                    quotation_id=alert.quotation_id,
                    sales_order_id=alert.sales_order_id,
                    actor_user_id=current_user.id,
                    event_type="ALERT_DISMISSED",
                    event_metadata={"alert_id": alert.id, "reason": reason},
                )
            )

            await self.db.commit()
            return await self.get_alert(alert.id)
        except Exception:
            await self.db.rollback()
            raise
