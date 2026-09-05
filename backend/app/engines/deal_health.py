from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional


@dataclass
class DealHealthSignalItem:
    signal_type: str
    severity: str  # INFO, WARNING, HIGH, CRITICAL
    score_penalty: Decimal
    title: str
    explanation: str
    metric_value: Optional[Decimal] = None
    threshold_value: Optional[Decimal] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class DealHealthEvaluation:
    health_score: Decimal
    health_level: str  # HEALTHY, WATCH, AT_RISK, CRITICAL
    signals: List[DealHealthSignalItem] = field(default_factory=list)
    summary: str = ""


@dataclass
class DealHealthConfigData:
    healthy_min_score: Decimal = Decimal("80.00")
    watch_min_score: Decimal = Decimal("60.00")
    at_risk_min_score: Decimal = Decimal("30.00")

    stalled_quote_days: int = 5
    approval_delay_hours: int = 24
    negotiation_stall_days: int = 3
    discount_anomaly_threshold_pct: Decimal = Decimal("10.00")
    delivery_slippage_days: int = 2
    backorder_age_days: int = 3
    invoice_overdue_days: int = 1

    weight_stalled_quote: Decimal = Decimal("20.00")
    weight_discount_anomaly: Decimal = Decimal("15.00")
    weight_approval_delay: Decimal = Decimal("10.00")
    weight_negotiation_stall: Decimal = Decimal("15.00")
    weight_delivery_slippage: Decimal = Decimal("20.00")
    weight_backorder: Decimal = Decimal("10.00")
    weight_invoice_overdue: Decimal = Decimal("10.00")


@dataclass
class DealHealthContext:
    quotation_id: int
    quote_number: str
    status: str
    sales_rep_id: int
    customer_id: int
    net_total: Decimal
    margin_pct: Decimal
    risk_level: Optional[str] = None
    blended_risk_score: Optional[Decimal] = None
    weighted_effective_discount_pct: Decimal = Decimal("0.00")

    last_meaningful_activity_at: Optional[datetime] = None
    pending_approval_step: Optional[Dict[str, Any]] = None
    last_negotiation_activity_at: Optional[datetime] = None

    sales_rep_historical_discounts: List[Decimal] = field(default_factory=list)

    sales_order: Optional[Dict[str, Any]] = None
    backorders: List[Dict[str, Any]] = field(default_factory=list)
    invoices: List[Dict[str, Any]] = field(default_factory=list)
    shipments: List[Dict[str, Any]] = field(default_factory=list)


class DealHealthEngine:
    """
    Pure, deterministic business engine for Deal Health scoring, anomaly detection,
    and signal evaluation.
    """

    OPEN_QUOTE_STATUSES = {
        "DRAFT",
        "PENDING_MANAGER_APPROVAL",
        "PENDING_FINANCE_APPROVAL",
        "APPROVED",
        "SENT_TO_CUSTOMER",
        "UNDER_NEGOTIATION",
        "REAPPROVAL_REQUIRED",
        "RETURNED_FOR_REVISION",
    }

    @classmethod
    def evaluate(
        self,
        context: DealHealthContext,
        config: DealHealthConfigData,
        as_of: Optional[datetime] = None,
    ) -> DealHealthEvaluation:
        now = as_of or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        signals: List[DealHealthSignalItem] = []

        # 1. STALLED QUOTE SIGNAL
        if context.status in self.OPEN_QUOTE_STATUSES and context.last_meaningful_activity_at:
            act_time = context.last_meaningful_activity_at
            if act_time.tzinfo is None:
                act_time = act_time.replace(tzinfo=timezone.utc)

            elapsed_days = (now - act_time).total_seconds() / 86400.0
            if elapsed_days > float(config.stalled_quote_days):
                sev = "HIGH" if elapsed_days >= (config.stalled_quote_days * 2) else "WARNING"
                penalty = config.weight_stalled_quote
                signals.append(
                    DealHealthSignalItem(
                        signal_type="STALLED_QUOTE",
                        severity=sev,
                        score_penalty=penalty,
                        title=f"Quotation Stalled ({int(elapsed_days)} days inactive)",
                        explanation=(
                            f"No meaningful activity on quotation {context.quote_number} for {int(elapsed_days)} days "
                            f"(configured threshold: {config.stalled_quote_days} days)."
                        ),
                        metric_value=Decimal(str(round(elapsed_days, 2))),
                        threshold_value=Decimal(str(config.stalled_quote_days)),
                        metadata={"elapsed_days": round(elapsed_days, 2), "status": context.status},
                    )
                )

        # 2. DISCOUNT ANOMALY SIGNAL
        # Minimum sample size: 3 historical quotations for the sales rep
        if len(context.sales_rep_historical_discounts) >= 3:
            hist_avg = sum(context.sales_rep_historical_discounts) / Decimal(str(len(context.sales_rep_historical_discounts)))
            delta_pp = context.weighted_effective_discount_pct - hist_avg
            if delta_pp >= config.discount_anomaly_threshold_pct:
                sev = "HIGH" if delta_pp >= (config.discount_anomaly_threshold_pct * Decimal("1.5")) else "WARNING"
                penalty = config.weight_discount_anomaly
                signals.append(
                    DealHealthSignalItem(
                        signal_type="DISCOUNT_ANOMALY",
                        severity=sev,
                        score_penalty=penalty,
                        title=f"Discount Anomaly (+{delta_pp:.1f} pp above rep average)",
                        explanation=(
                            f"Quotation weighted discount ({context.weighted_effective_discount_pct:.1f}%) is "
                            f"{delta_pp:.1f} percentage points higher than Sales Rep historical average "
                            f"({hist_avg:.1f}%) across {len(context.sales_rep_historical_discounts)} historical deals "
                            f"(threshold: {config.discount_anomaly_threshold_pct:.1f} pp)."
                        ),
                        metric_value=delta_pp.quantize(Decimal("0.01")),
                        threshold_value=config.discount_anomaly_threshold_pct,
                        metadata={
                            "current_discount_pct": float(context.weighted_effective_discount_pct),
                            "rep_historical_avg_pct": float(hist_avg),
                            "delta_pp": float(delta_pp),
                            "sample_count": len(context.sales_rep_historical_discounts),
                        },
                    )
                )

        # 3. APPROVAL DELAY SIGNAL
        if (
            context.status in {"PENDING_MANAGER_APPROVAL", "PENDING_FINANCE_APPROVAL"}
            and context.pending_approval_step
        ):
            step_time = context.pending_approval_step.get("updated_at") or context.pending_approval_step.get("created_at")
            if step_time:
                if step_time.tzinfo is None:
                    step_time = step_time.replace(tzinfo=timezone.utc)
                elapsed_hours = (now - step_time).total_seconds() / 3600.0
                if elapsed_hours > float(config.approval_delay_hours):
                    sev = "HIGH" if elapsed_hours >= (config.approval_delay_hours * 2) else "WARNING"
                    penalty = config.weight_approval_delay
                    req_role = context.pending_approval_step.get("required_role", "APPROVER")
                    signals.append(
                        DealHealthSignalItem(
                            signal_type="APPROVAL_DELAY",
                            severity=sev,
                            score_penalty=penalty,
                            title=f"Approval Delayed ({int(elapsed_hours)} hrs pending)",
                            explanation=(
                                f"{req_role} approval has been pending for {int(elapsed_hours)} hours against "
                                f"a configured threshold of {config.approval_delay_hours} hours."
                            ),
                            metric_value=Decimal(str(round(elapsed_hours, 2))),
                            threshold_value=Decimal(str(config.approval_delay_hours)),
                            metadata={
                                "elapsed_hours": round(elapsed_hours, 2),
                                "required_role": req_role,
                                "step_type": context.pending_approval_step.get("step_type"),
                            },
                        )
                    )

        # 4. NEGOTIATION STALL SIGNAL
        if context.status == "UNDER_NEGOTIATION" and context.last_negotiation_activity_at:
            neg_time = context.last_negotiation_activity_at
            if neg_time.tzinfo is None:
                neg_time = neg_time.replace(tzinfo=timezone.utc)
            elapsed_days = (now - neg_time).total_seconds() / 86400.0
            if elapsed_days > float(config.negotiation_stall_days):
                sev = "HIGH" if elapsed_days >= (config.negotiation_stall_days * 2) else "WARNING"
                penalty = config.weight_negotiation_stall
                signals.append(
                    DealHealthSignalItem(
                        signal_type="NEGOTIATION_STALL",
                        severity=sev,
                        score_penalty=penalty,
                        title=f"Negotiation Stalled ({int(elapsed_days)} days inactive)",
                        explanation=(
                            f"No customer/internal negotiation activity on quotation {context.quote_number} for {int(elapsed_days)} days "
                            f"(threshold: {config.negotiation_stall_days} days)."
                        ),
                        metric_value=Decimal(str(round(elapsed_days, 2))),
                        threshold_value=Decimal(str(config.negotiation_stall_days)),
                        metadata={"elapsed_days": round(elapsed_days, 2)},
                    )
                )

        # 5. HIGH QUOTE RISK / NEGATIVE MARGIN SIGNALS
        if context.risk_level in {"HIGH", "CORAL_RED"} or (context.blended_risk_score and context.blended_risk_score > Decimal("70.00")):
            signals.append(
                DealHealthSignalItem(
                    signal_type="HIGH_DISCOUNT_RISK",
                    severity="HIGH",
                    score_penalty=Decimal("10.00"),
                    title="High Commercial Discount Risk",
                    explanation=f"Quotation has elevated risk score ({context.blended_risk_score or 0}) and level '{context.risk_level}'.",
                    metric_value=context.blended_risk_score,
                    metadata={"risk_level": context.risk_level},
                )
            )

        if context.margin_pct < Decimal("0.00"):
            signals.append(
                DealHealthSignalItem(
                    signal_type="NEGATIVE_MARGIN",
                    severity="CRITICAL",
                    score_penalty=Decimal("25.00"),
                    title="Negative Profit Margin",
                    explanation=f"Quotation has negative profit margin ({context.margin_pct:.2f}%).",
                    metric_value=context.margin_pct,
                )
            )

        # 6. DELIVERY / FULFILLMENT SLIPPAGE SIGNAL
        if context.sales_order and context.sales_order.get("status") in {"FULFILLMENT", "PARTIALLY_FULFILLED"}:
            so_time = context.sales_order.get("created_at")
            if so_time:
                if isinstance(so_time, str):
                    so_time = datetime.fromisoformat(so_time)
                if so_time.tzinfo is None:
                    so_time = so_time.replace(tzinfo=timezone.utc)
                elapsed_days = (now - so_time).total_seconds() / 86400.0
                if elapsed_days > float(config.delivery_slippage_days):
                    sev = "HIGH" if elapsed_days >= (config.delivery_slippage_days * 2) else "WARNING"
                    penalty = config.weight_delivery_slippage
                    signals.append(
                        DealHealthSignalItem(
                            signal_type="DELIVERY_SLIPPAGE",
                            severity=sev,
                            score_penalty=penalty,
                            title=f"Fulfillment Slippage ({int(elapsed_days)} days open)",
                            explanation=(
                                f"Sales Order {context.sales_order.get('order_number')} physical fulfillment has been pending "
                                f"for {int(elapsed_days)} days (threshold: {config.delivery_slippage_days} days)."
                            ),
                            metric_value=Decimal(str(round(elapsed_days, 2))),
                            threshold_value=Decimal(str(config.delivery_slippage_days)),
                            metadata={"order_number": context.sales_order.get("order_number"), "elapsed_days": round(elapsed_days, 2)},
                        )
                    )

        # 7. BACKORDER RISK SIGNAL
        if context.backorders:
            open_bos = [bo for bo in context.backorders if bo.get("status") in {"OPEN", "PARTIALLY_RESOLVED"}]
            if open_bos:
                oldest_bo = min(open_bos, key=lambda b: b.get("created_at") or now)
                bo_time = oldest_bo.get("created_at")
                if isinstance(bo_time, str):
                    bo_time = datetime.fromisoformat(bo_time)
                if bo_time and bo_time.tzinfo is None:
                    bo_time = bo_time.replace(tzinfo=timezone.utc)
                age_days = (now - bo_time).total_seconds() / 86400.0 if bo_time else 0.0
                if age_days > float(config.backorder_age_days):
                    penalty = config.weight_backorder
                    signals.append(
                        DealHealthSignalItem(
                            signal_type="BACKORDER_DELAY",
                            severity="HIGH" if age_days >= (config.backorder_age_days * 2) else "WARNING",
                            score_penalty=penalty,
                            title=f"Backorder Delay ({int(age_days)} days open)",
                            explanation=(
                                f"Open backorder for product '{oldest_bo.get('product_sku', 'SKU')}' has been unresolved "
                                f"for {int(age_days)} days (threshold: {config.backorder_age_days} days)."
                            ),
                            metric_value=Decimal(str(round(age_days, 2))),
                            threshold_value=Decimal(str(config.backorder_age_days)),
                            metadata={"backorder_count": len(open_bos), "oldest_age_days": round(age_days, 2)},
                        )
                    )

        # 8. INVOICE OVERDUE SIGNAL
        if context.invoices:
            overdue_invs = []
            for inv in context.invoices:
                bal = Decimal(str(inv.get("balance_due") or 0))
                due = inv.get("due_date")
                if isinstance(due, str):
                    due = datetime.fromisoformat(due)
                if due and due.tzinfo is None:
                    due = due.replace(tzinfo=timezone.utc)
                if bal > Decimal("0.00") and due and now > due:
                    overdue_days = (now - due).days
                    if overdue_days >= config.invoice_overdue_days:
                        overdue_invs.append((inv, overdue_days))

            if overdue_invs:
                max_inv, max_days = max(overdue_invs, key=lambda x: x[1])
                penalty = config.weight_invoice_overdue
                signals.append(
                    DealHealthSignalItem(
                        signal_type="INVOICE_OVERDUE",
                        severity="CRITICAL" if max_days >= 14 else ("HIGH" if max_days >= 7 else "WARNING"),
                        score_penalty=penalty,
                        title=f"Invoice Overdue ({max_days} days past due)",
                        explanation=(
                            f"Invoice {max_inv.get('invoice_number')} has outstanding balance of "
                            f"{max_inv.get('balance_due')} and is {max_days} days past due date."
                        ),
                        metric_value=Decimal(str(max_days)),
                        threshold_value=Decimal(str(config.invoice_overdue_days)),
                        metadata={"invoice_number": max_inv.get("invoice_number"), "overdue_days": max_days},
                    )
                )

        # 9. SCORE & LEVEL CALCULATION
        total_penalty = sum((s.score_penalty for s in signals), Decimal("0.00"))
        raw_score = Decimal("100.00") - total_penalty
        health_score = max(Decimal("0.00"), min(Decimal("100.00"), raw_score)).quantize(Decimal("0.01"))

        if health_score >= config.healthy_min_score:
            health_level = "HEALTHY"
        elif health_score >= config.watch_min_score:
            health_level = "WATCH"
        elif health_score >= config.at_risk_min_score:
            health_level = "AT_RISK"
        else:
            health_level = "CRITICAL"

        # 10. DETERMINISTIC SUMMARY GENERATION
        if not signals:
            summary = f"Deal {context.quote_number} is HEALTHY with a score of {health_score:.2f}/100 and no active risk signals."
        else:
            top_sigs = sorted(signals, key=lambda s: ({"CRITICAL": 4, "HIGH": 3, "WARNING": 2, "INFO": 1}.get(s.severity, 0), s.score_penalty), reverse=True)
            top_titles = [s.title for s in top_sigs[:2]]
            summary = (
                f"Deal {context.quote_number} is classified as {health_level} (score {health_score:.2f}/100) "
                f"due to {len(signals)} risk signal(s): {'; '.join(top_titles)}."
            )

        return DealHealthEvaluation(
            health_score=health_score,
            health_level=health_level,
            signals=signals,
            summary=summary,
        )
