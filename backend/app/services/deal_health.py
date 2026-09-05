from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import QuotationStatus, RoleName
from app.engines.deal_health import (
    DealHealthConfigData,
    DealHealthContext,
    DealHealthEngine,
    DealHealthEvaluation,
)
from app.models.backorder import Backorder
from app.models.customer import Customer
from app.models.deal_alert import DealAlert
from app.models.deal_health_audit_event import DealHealthAuditEvent
from app.models.deal_health_config import DealHealthConfig
from app.models.deal_health_signal import DealHealthSignal
from app.models.deal_health_snapshot import DealHealthSnapshot
from app.models.invoice import Invoice
from app.models.quotation import Quotation
from app.models.quote_approval_step import QuoteApprovalStep
from app.models.quote_audit_event import QuoteAuditEvent
from app.models.quote_negotiation_message import QuoteNegotiationMessage
from app.models.role import Role
from app.models.sales_order import SalesOrder
from app.models.shipment import Shipment
from app.models.user import User
from app.repositories.customer import CustomerRepository
from app.repositories.deal_alert import DealAlertRepository
from app.repositories.deal_health_config import DealHealthConfigRepository
from app.repositories.deal_health_snapshot import DealHealthSnapshotRepository
from app.repositories.quotation import QuotationRepository
from app.repositories.sales_order import SalesOrderRepository
from app.repositories.user import UserRepository
from app.schemas.deal_health import DealHealthConfigCreate, DealHealthConfigUpdate, DealHealthListItem, DealHealthScanResult
from app.services.exceptions import ResourceNotFoundError
from app.services.notification import NotificationService


class DealHealthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.config_repo = DealHealthConfigRepository()
        self.snapshot_repo = DealHealthSnapshotRepository()
        self.alert_repo = DealAlertRepository()
        self.quote_repo = QuotationRepository()
        self.order_repo = SalesOrderRepository()
        self.cust_repo = CustomerRepository()
        self.user_repo = UserRepository()
        self.notif_service = NotificationService(db)

    async def get_or_create_default_config(self) -> DealHealthConfig:
        config = await self.config_repo.get_active_config(self.db)
        if not config:
            config = DealHealthConfig(
                name="Default Deal Health Policy",
                is_active=True,
                healthy_min_score=Decimal("80.00"),
                watch_min_score=Decimal("60.00"),
                at_risk_min_score=Decimal("30.00"),
                stalled_quote_days=5,
                approval_delay_hours=24,
                negotiation_stall_days=3,
                discount_anomaly_threshold_pct=Decimal("10.00"),
                delivery_slippage_days=2,
                backorder_age_days=3,
                invoice_overdue_days=1,
                weight_stalled_quote=Decimal("20.00"),
                weight_discount_anomaly=Decimal("15.00"),
                weight_approval_delay=Decimal("10.00"),
                weight_negotiation_stall=Decimal("15.00"),
                weight_delivery_slippage=Decimal("20.00"),
                weight_backorder=Decimal("10.00"),
                weight_invoice_overdue=Decimal("10.00"),
            )
            await self.config_repo.create_config(self.db, config)
            await self.db.commit()
            config = await self.config_repo.get_active_config(self.db)
        return config

    async def update_config(self, payload: DealHealthConfigUpdate, actor_user_id: int) -> DealHealthConfig:
        await self.config_repo.deactivate_all_configs(self.db)
        curr = await self.get_or_create_default_config()

        new_config = DealHealthConfig(
            name=payload.name if payload.name is not None else curr.name,
            is_active=payload.is_active if payload.is_active is not None else True,
            healthy_min_score=payload.healthy_min_score if payload.healthy_min_score is not None else curr.healthy_min_score,
            watch_min_score=payload.watch_min_score if payload.watch_min_score is not None else curr.watch_min_score,
            at_risk_min_score=payload.at_risk_min_score if payload.at_risk_min_score is not None else curr.at_risk_min_score,
            stalled_quote_days=payload.stalled_quote_days if payload.stalled_quote_days is not None else curr.stalled_quote_days,
            approval_delay_hours=payload.approval_delay_hours if payload.approval_delay_hours is not None else curr.approval_delay_hours,
            negotiation_stall_days=payload.negotiation_stall_days if payload.negotiation_stall_days is not None else curr.negotiation_stall_days,
            discount_anomaly_threshold_pct=payload.discount_anomaly_threshold_pct if payload.discount_anomaly_threshold_pct is not None else curr.discount_anomaly_threshold_pct,
            delivery_slippage_days=payload.delivery_slippage_days if payload.delivery_slippage_days is not None else curr.delivery_slippage_days,
            backorder_age_days=payload.backorder_age_days if payload.backorder_age_days is not None else curr.backorder_age_days,
            invoice_overdue_days=payload.invoice_overdue_days if payload.invoice_overdue_days is not None else curr.invoice_overdue_days,
            weight_stalled_quote=payload.weight_stalled_quote if payload.weight_stalled_quote is not None else curr.weight_stalled_quote,
            weight_discount_anomaly=payload.weight_discount_anomaly if payload.weight_discount_anomaly is not None else curr.weight_discount_anomaly,
            weight_approval_delay=payload.weight_approval_delay if payload.weight_approval_delay is not None else curr.weight_approval_delay,
            weight_negotiation_stall=payload.weight_negotiation_stall if payload.weight_negotiation_stall is not None else curr.weight_negotiation_stall,
            weight_delivery_slippage=payload.weight_delivery_slippage if payload.weight_delivery_slippage is not None else curr.weight_delivery_slippage,
            weight_backorder=payload.weight_backorder if payload.weight_backorder is not None else curr.weight_backorder,
            weight_invoice_overdue=payload.weight_invoice_overdue if payload.weight_invoice_overdue is not None else curr.weight_invoice_overdue,
            created_by_user_id=curr.created_by_user_id,
            updated_by_user_id=actor_user_id,
        )
        await self.config_repo.create_config(self.db, new_config)
        self.db.add(
            DealHealthAuditEvent(
                quotation_id=0,
                actor_user_id=actor_user_id,
                event_type="CONFIG_UPDATED",
                event_metadata={"config_id": new_config.id, "name": new_config.name},
            )
        )
        await self.db.commit()
        return await self.config_repo.get_active_config(self.db)

    async def _get_sales_rep_historical_discounts(
        self, sales_rep_id: int, current_quote_id: int, as_of: datetime
    ) -> List[Decimal]:
        window_start = as_of - timedelta(days=90)
        eligible_statuses = [
            QuotationStatus.APPROVED.value,
            QuotationStatus.SENT_TO_CUSTOMER.value,
            QuotationStatus.CUSTOMER_CONFIRMED.value,
            QuotationStatus.CUSTOMER_ACCEPTED.value,
        ]

        stmt = (
            select(Quotation.weighted_effective_discount_pct)
            .where(
                Quotation.sales_rep_id == sales_rep_id,
                Quotation.id != current_quote_id,
                Quotation.status.in_(eligible_statuses),
                Quotation.created_at >= window_start,
            )
            .order_by(Quotation.created_at.desc())
            .limit(50)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def _resolve_alert_recipients(self, alert_type: str, quote: Quotation) -> List[int]:
        user_ids = {quote.sales_rep_id}

        if alert_type in {"APPROVAL_DELAY", "DISCOUNT_ANOMALY", "NEGATIVE_MARGIN"}:
            mgr_stmt = (
                select(User.id)
                .join(Role, User.role_id == Role.id)
                .where(Role.name.in_([RoleName.SALES_MANAGER, RoleName.ADMIN]), User.is_active == True)
            )
            res = await self.db.execute(mgr_stmt)
            user_ids.update(res.scalars().all())

        if alert_type in {"DELIVERY_SLIPPAGE", "BACKORDER_DELAY", "INVOICE_OVERDUE"}:
            fin_stmt = (
                select(User.id)
                .join(Role, User.role_id == Role.id)
                .where(Role.name.in_([RoleName.FINANCE_OPERATIONS, RoleName.ADMIN]), User.is_active == True)
            )
            res = await self.db.execute(fin_stmt)
            user_ids.update(res.scalars().all())

        return list(user_ids)

    async def evaluate_quotation_health(
        self, quotation_id: int, actor_user_id: Optional[int] = None, as_of: Optional[datetime] = None
    ) -> DealHealthSnapshot:
        now = as_of or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        quote = await self.quote_repo.get_by_id(self.db, quotation_id)
        if not quote:
            raise ResourceNotFoundError(f"Quotation with ID {quotation_id} not found.")

        config_model = await self.get_or_create_default_config()
        config_data = DealHealthConfigData(
            healthy_min_score=config_model.healthy_min_score,
            watch_min_score=config_model.watch_min_score,
            at_risk_min_score=config_model.at_risk_min_score,
            stalled_quote_days=config_model.stalled_quote_days,
            approval_delay_hours=config_model.approval_delay_hours,
            negotiation_stall_days=config_model.negotiation_stall_days,
            discount_anomaly_threshold_pct=config_model.discount_anomaly_threshold_pct,
            delivery_slippage_days=config_model.delivery_slippage_days,
            backorder_age_days=config_model.backorder_age_days,
            invoice_overdue_days=config_model.invoice_overdue_days,
            weight_stalled_quote=config_model.weight_stalled_quote,
            weight_discount_anomaly=config_model.weight_discount_anomaly,
            weight_approval_delay=config_model.weight_approval_delay,
            weight_negotiation_stall=config_model.weight_negotiation_stall,
            weight_delivery_slippage=config_model.weight_delivery_slippage,
            weight_backorder=config_model.weight_backorder,
            weight_invoice_overdue=config_model.weight_invoice_overdue,
        )

        # 1. Determine last meaningful activity timestamp
        activity_times = [quote.updated_at or quote.created_at]

        audit_stmt = (
            select(QuoteAuditEvent.created_at)
            .where(QuoteAuditEvent.quotation_id == quotation_id)
            .order_by(QuoteAuditEvent.created_at.desc())
            .limit(1)
        )
        aud_res = await self.db.execute(audit_stmt)
        latest_aud = aud_res.scalar_one_or_none()
        if latest_aud:
            activity_times.append(latest_aud)

        msg_stmt = (
            select(QuoteNegotiationMessage.created_at)
            .where(QuoteNegotiationMessage.quotation_id == quotation_id)
            .order_by(QuoteNegotiationMessage.created_at.desc())
            .limit(1)
        )
        msg_res = await self.db.execute(msg_stmt)
        latest_msg = msg_res.scalar_one_or_none()
        if latest_msg:
            activity_times.append(latest_msg)

        last_activity = max(activity_times)

        # 2. Check pending approval step
        step_stmt = (
            select(QuoteApprovalStep)
            .where(QuoteApprovalStep.quotation_id == quotation_id, QuoteApprovalStep.status == "PENDING")
            .order_by(QuoteApprovalStep.step_number.asc())
        )
        step_res = await self.db.execute(step_stmt)
        pending_step_obj = step_res.scalars().first()
        pending_step_dict = None
        if pending_step_obj:
            pending_step_dict = {
                "step_type": pending_step_obj.step_type,
                "required_role": pending_step_obj.required_role,
                "created_at": pending_step_obj.created_at,
                "updated_at": pending_step_obj.updated_at,
            }

        # 3. Query historical discounts for rep
        hist_discounts = await self._get_sales_rep_historical_discounts(quote.sales_rep_id, quote.id, now)

        # 4. Check downstream SalesOrder, Backorders, Invoices, Shipments
        order_stmt = select(SalesOrder).where(SalesOrder.quotation_id == quotation_id)
        order_res = await self.db.execute(order_stmt)
        order_obj = order_res.scalar_one_or_none()

        sales_order_dict = None
        backorders_dict: List[Dict[str, Any]] = []
        invoices_dict: List[Dict[str, Any]] = []
        shipments_dict: List[Dict[str, Any]] = []

        if order_obj:
            sales_order_dict = {
                "id": order_obj.id,
                "order_number": order_obj.order_number,
                "status": order_obj.status,
                "created_at": order_obj.created_at,
            }

            bo_stmt = select(Backorder).where(Backorder.sales_order_id == order_obj.id)
            bo_res = await self.db.execute(bo_stmt)
            for bo in bo_res.scalars().all():
                sku = bo.sales_order_line.product_sku_snapshot if bo.sales_order_line else "SKU"
                backorders_dict.append({
                    "id": bo.id,
                    "status": bo.status,
                    "created_at": bo.created_at,
                    "backordered_qty": float(bo.backordered_qty),
                    "product_sku": sku,
                })

            inv_stmt = select(Invoice).where(Invoice.sales_order_id == order_obj.id)
            inv_res = await self.db.execute(inv_stmt)
            for inv in inv_res.scalars().all():
                invoices_dict.append({
                    "id": inv.id,
                    "invoice_number": inv.invoice_number,
                    "status": inv.status,
                    "total_amount": float(inv.total_amount),
                    "balance_due": float(inv.balance_due),
                    "due_date": inv.due_date,
                })

            shp_stmt = select(Shipment).where(Shipment.sales_order_id == order_obj.id)
            shp_res = await self.db.execute(shp_stmt)
            for shp in shp_res.scalars().all():
                shipments_dict.append({
                    "id": shp.id,
                    "shipment_number": shp.shipment_number,
                    "status": shp.status,
                    "created_at": shp.created_at,
                })

        context = DealHealthContext(
            quotation_id=quote.id,
            quote_number=quote.quote_number,
            status=quote.status,
            sales_rep_id=quote.sales_rep_id,
            customer_id=quote.customer_id,
            net_total=quote.net_total,
            margin_pct=quote.margin_pct,
            risk_level=quote.risk_level,
            blended_risk_score=quote.blended_risk_score,
            weighted_effective_discount_pct=quote.weighted_effective_discount_pct or Decimal("0.00"),
            last_meaningful_activity_at=last_activity,
            pending_approval_step=pending_step_dict,
            last_negotiation_activity_at=latest_msg or quote.updated_at,
            sales_rep_historical_discounts=hist_discounts,
            sales_order=sales_order_dict,
            backorders=backorders_dict,
            invoices=invoices_dict,
            shipments=shipments_dict,
        )

        # 5. Run Engine
        evaluation = DealHealthEngine.evaluate(context, config_data, as_of=now)

        # 6. Create Snapshot & Signals
        snapshot = DealHealthSnapshot(
            quotation_id=quote.id,
            sales_order_id=order_obj.id if order_obj else None,
            config_id=config_model.id,
            health_score=evaluation.health_score,
            health_level=evaluation.health_level,
            signal_count=len(evaluation.signals),
            summary=evaluation.summary,
            calculated_at=now,
        )

        for sig in evaluation.signals:
            sig_obj = DealHealthSignal(
                signal_type=sig.signal_type,
                severity=sig.severity,
                score_penalty=sig.score_penalty,
                title=sig.title,
                explanation=sig.explanation,
                metric_value=sig.metric_value,
                threshold_value=sig.threshold_value,
                signal_metadata=sig.metadata,
            )
            snapshot.signals.append(sig_obj)

        await self.snapshot_repo.create_snapshot(self.db, snapshot)
        await self.db.flush()

        # 7. Deduplicate & Upsert Deal Alerts
        created_alert_count = 0
        updated_alert_count = 0

        for sig in evaluation.signals:
            existing_alert = await self.alert_repo.get_active_alert_by_type(self.db, quote.id, sig.signal_type)
            if existing_alert:
                existing_alert.last_triggered_at = now
                existing_alert.occurrence_count += 1
                existing_alert.severity = sig.severity
                existing_alert.title = sig.title
                existing_alert.message = sig.explanation
                existing_alert.snapshot_id = snapshot.id
                updated_alert_count += 1
            else:
                new_alert = DealAlert(
                    quotation_id=quote.id,
                    sales_order_id=order_obj.id if order_obj else None,
                    snapshot_id=snapshot.id,
                    alert_type=sig.signal_type,
                    severity=sig.severity,
                    status="OPEN",
                    title=sig.title,
                    message=sig.explanation,
                    assigned_user_id=quote.sales_rep_id,
                    last_triggered_at=now,
                    occurrence_count=1,
                )
                await self.alert_repo.create_alert(self.db, new_alert)
                created_alert_count += 1

                # Notify relevant roles
                recipients = await self._resolve_alert_recipients(sig.signal_type, quote)
                await self.notif_service.create_and_dispatch_notification(
                    user_ids=recipients,
                    notification_type=f"DEAL_{evaluation.health_level}",
                    title=f"Deal Health Alert: {sig.title}",
                    message=sig.explanation,
                    quotation_id=quote.id,
                    payload={"alert_type": sig.signal_type, "severity": sig.severity, "health_level": evaluation.health_level},
                )

        # Audit Event
        self.db.add(
            DealHealthAuditEvent(
                quotation_id=quote.id,
                sales_order_id=order_obj.id if order_obj else None,
                actor_user_id=actor_user_id,
                event_type="HEALTH_EVALUATED",
                event_metadata={
                    "score": float(evaluation.health_score),
                    "level": evaluation.health_level,
                    "signal_count": len(evaluation.signals),
                    "alerts_created": created_alert_count,
                    "alerts_updated": updated_alert_count,
                },
            )
        )

        await self.db.commit()

        # Real-time WebSocket dispatch
        await self.notif_service.dispatch_post_commit_events(
            target_user_ids=[quote.sales_rep_id],
            event_name="deal_health.updated",
            quotation_id=quote.id,
            payload={
                "health_score": float(evaluation.health_score),
                "health_level": evaluation.health_level,
                "summary": evaluation.summary,
                "signal_count": len(evaluation.signals),
            },
            title=f"Deal Health Updated: {evaluation.health_level}",
            message_text=evaluation.summary,
        )

        return await self.snapshot_repo.get_by_id(self.db, snapshot.id)

    async def get_latest_health(self, quotation_id: int) -> DealHealthSnapshot:
        snap = await self.snapshot_repo.get_latest_by_quotation(self.db, quotation_id)
        if not snap:
            return await self.evaluate_quotation_health(quotation_id)
        return snap

    async def list_deal_health(
        self,
        health_level: Optional[str] = None,
        sales_rep_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        quotation_status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[DealHealthListItem]:
        stmt = (
            select(Quotation, Customer, User)
            .join(Customer, Quotation.customer_id == Customer.id)
            .join(User, Quotation.sales_rep_id == User.id)
        )

        if sales_rep_id:
            stmt = stmt.where(Quotation.sales_rep_id == sales_rep_id)
        if customer_id:
            stmt = stmt.where(Quotation.customer_id == customer_id)
        if quotation_status:
            stmt = stmt.where(Quotation.status == quotation_status)
        if search:
            stmt = stmt.where(
                Quotation.quote_number.ilike(f"%{search}%") | Customer.name.ilike(f"%{search}%")
            )

        stmt = stmt.order_by(Quotation.updated_at.desc()).offset(offset).limit(limit)
        res = await self.db.execute(stmt)
        rows = res.all()

        results = []
        for quote, cust, rep in rows:
            snap = await self.snapshot_repo.get_latest_by_quotation(self.db, quote.id)
            if not snap:
                snap = await self.evaluate_quotation_health(quote.id)

            if health_level and snap.health_level != health_level:
                continue

            open_alerts = await self.alert_repo.list_alerts(self.db, quotation_id=quote.id, status="OPEN")
            top_sig = snap.signals[0].title if snap.signals else None

            results.append(
                DealHealthListItem(
                    quotation_id=quote.id,
                    quote_number=quote.quote_number,
                    customer_id=cust.id,
                    customer_name=cust.name,
                    sales_rep_id=rep.id,
                    sales_rep_name=rep.full_name,
                    quotation_status=quote.status,
                    health_score=snap.health_score,
                    health_level=snap.health_level,
                    top_signal_title=top_sig,
                    open_alert_count=len(open_alerts),
                    last_activity_at=quote.updated_at,
                    calculated_at=snap.calculated_at,
                )
            )

        return results

    async def run_bulk_scan(self, as_of: Optional[datetime] = None) -> DealHealthScanResult:
        now = as_of or datetime.now(timezone.utc)
        stmt = (
            select(Quotation.id)
            .where(Quotation.status.in_(DealHealthEngine.OPEN_QUOTE_STATUSES))
            .order_by(Quotation.id.asc())
        )
        res = await self.db.execute(stmt)
        quote_ids = res.scalars().all()

        evaluated_count = 0
        healthy_count = 0
        watch_count = 0
        at_risk_count = 0
        critical_count = 0
        alerts_created = 0
        alerts_updated = 0

        for q_id in quote_ids:
            snap = await self.evaluate_quotation_health(q_id, as_of=now)
            evaluated_count += 1
            if snap.health_level == "HEALTHY":
                healthy_count += 1
            elif snap.health_level == "WATCH":
                watch_count += 1
            elif snap.health_level == "AT_RISK":
                at_risk_count += 1
            elif snap.health_level == "CRITICAL":
                critical_count += 1

        return DealHealthScanResult(
            evaluated_count=evaluated_count,
            healthy_count=healthy_count,
            watch_count=watch_count,
            at_risk_count=at_risk_count,
            critical_count=critical_count,
            alerts_created=alerts_created,
            alerts_updated=alerts_updated,
        )
