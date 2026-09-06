import secrets
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AuditEventType, QuotationStatus, RoleName
from app.engines.recommendation import RecommendationCandidate, RecommendationEngine
from app.engines.what_if import WhatIfSimulationResult, WhatIfSimulatorEngine
from app.models.product_recommendation_rule import ProductRecommendationRule
from app.models.quote_approval_step import QuoteApprovalStep
from app.models.quote_audit_event import QuoteAuditEvent
from app.models.quote_recommendation_dismissal import QuoteRecommendationDismissal
from app.models.quotation import Quotation
from app.models.quotation_line import QuoteLine
from app.models.user import User
from app.repositories.approval_policy import ApprovalPolicyRepository
from app.repositories.billing_plan import BillingPlanRepository
from app.repositories.customer import CustomerRepository
from app.repositories.product import ProductRepository
from app.repositories.product_recommendation_rule import ProductRecommendationRuleRepository
from app.repositories.quotation import QuotationRepository
from app.repositories.quotation_line import QuoteLineRepository
from app.repositories.quote_audit_event import QuoteAuditEventRepository
from app.repositories.quote_recommendation_dismissal import QuoteRecommendationDismissalRepository
from app.schemas.quotation import QuotationCreate, QuotationUpdate
from app.schemas.quotation_line import QuoteLineCreate, QuoteLineUpdate
from app.schemas.what_if import WhatIfRequest
from app.services.discount_policy import DiscountPolicyService
from app.services.exceptions import (
    CommercialPolicyValidationError,
    CurrencyMismatchError,
    InactiveReferenceError,
    InvalidReferenceError,
    QuoteAccessDeniedError,
    QuoteLineNotFoundError,
    QuoteNotEditableError,
    QuoteNotFoundError,
    ResourceNotFoundError,
)
from app.services.quotation_evaluation import QuotationEvaluationService


class QuotationService:
    """Service layer orchestrating complete quotation transaction lifecycle."""

    EDITABLE_STATUSES = {QuotationStatus.DRAFT.value, QuotationStatus.RETURNED_FOR_REVISION.value}

    def __init__(self, db: AsyncSession) -> None:
        self.db: AsyncSession = db
        self.quote_repo = QuotationRepository()
        self.line_repo = QuoteLineRepository()
        self.audit_repo = QuoteAuditEventRepository()
        self.customer_repo = CustomerRepository()
        self.product_repo = ProductRepository()
        self.billing_plan_repo = BillingPlanRepository()
        self.rule_repo = ProductRecommendationRuleRepository()
        self.dismissal_repo = QuoteRecommendationDismissalRepository()
        self.approval_policy_repo = ApprovalPolicyRepository()
        self.eval_service = QuotationEvaluationService(db)
        self.policy_service = DiscountPolicyService(db)

    def _verify_editability(self, quotation: Quotation) -> None:
        if quotation.status not in self.EDITABLE_STATUSES:
            raise QuoteNotEditableError(
                f"Quotation {quotation.quote_number} is in '{quotation.status}' status and cannot be modified."
            )

    def _verify_ownership(self, quotation: Quotation, current_user: User) -> None:
        # ADMIN, SALES_MANAGER, and FINANCE_OPERATIONS can edit/manage any quotation;
        # SALES_REP can only edit their own assigned quotation.
        is_privileged = False
        user_role_name = getattr(current_user.role, "name", None) if hasattr(current_user, "role") and current_user.role else None
        if hasattr(user_role_name, "value"):
            user_role_name = user_role_name.value

        privileged_roles = {
            RoleName.ADMIN.value if hasattr(RoleName.ADMIN, "value") else str(RoleName.ADMIN),
            RoleName.SALES_MANAGER.value if hasattr(RoleName.SALES_MANAGER, "value") else str(RoleName.SALES_MANAGER),
            RoleName.FINANCE_OPERATIONS.value if hasattr(RoleName.FINANCE_OPERATIONS, "value") else str(RoleName.FINANCE_OPERATIONS),
            "ADMIN",
            "SALES_MANAGER",
            "FINANCE_OPERATIONS",
        }
        if user_role_name in privileged_roles:
            is_privileged = True
        elif hasattr(current_user, "role_id") and current_user.role_id in (1, 2, 3):
            is_privileged = True

        if not is_privileged and quotation.sales_rep_id != current_user.id:
            raise QuoteAccessDeniedError("You do not have permission to modify this quotation.")

    async def _generate_unique_quote_number(self) -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        for _ in range(10):
            rand_hex = secrets.token_hex(4).upper()
            candidate = f"Q-{date_str}-{rand_hex}"
            existing = await self.quote_repo.get_by_quote_number(self.db, candidate)
            if not existing:
                return candidate
        raise RuntimeError("Failed to generate unique quotation number.")

    async def _create_audit_event(
        self,
        quotation_id: int,
        actor_user_id: Optional[int],
        event_type: str,
        from_status: Optional[str] = None,
        to_status: Optional[str] = None,
        reason: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> QuoteAuditEvent:
        event = QuoteAuditEvent(
            quotation_id=quotation_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
            event_metadata=metadata,
        )
        return await self.audit_repo.create_event(self.db, event)

    async def create_quotation(
        self,
        obj_in: QuotationCreate,
        current_user: User,
    ) -> Quotation:
        # 1. Validate Customer
        customer = await self.customer_repo.get_by_id_with_tier(self.db, obj_in.customer_id)
        if not customer:
            raise InvalidReferenceError(f"Customer with ID {obj_in.customer_id} does not exist.")
        if not customer.is_active:
            raise InactiveReferenceError(f"Customer '{customer.name}' is inactive.")

        quote_number = await self._generate_unique_quote_number()

        quotation = Quotation(
            quote_number=quote_number,
            customer_id=customer.id,
            sales_rep_id=current_user.id,
            status=QuotationStatus.DRAFT.value,
            currency=customer.currency or "USD",
            payment_terms_days=obj_in.payment_terms_days if obj_in.payment_terms_days is not None else 30,
            order_discount_pct=obj_in.order_discount_pct if obj_in.order_discount_pct is not None else Decimal("0.00"),
        )
        quotation.customer = customer
        quotation.lines = []
        quotation.risk_reasons = []
        quotation.audit_events = []

        await self.quote_repo.create_quotation(self.db, quotation)

        # Audit Event
        await self._create_audit_event(
            quotation_id=quotation.id,
            actor_user_id=current_user.id,
            event_type=AuditEventType.QUOTE_CREATED.value,
            to_status=QuotationStatus.DRAFT.value,
            metadata={"quote_number": quote_number, "customer_id": customer.id},
        )

        await self.eval_service.evaluate_and_update(quotation)

        try:
            await self.db.commit()
            return await self.get_quotation_by_id(quotation.id)
        except Exception:
            await self.db.rollback()
            raise

    async def get_quotation_by_id(self, quotation_id: int) -> Quotation:
        quote = await self.quote_repo.get_by_id(self.db, quotation_id)
        if not quote:
            raise QuoteNotFoundError(f"Quotation with ID {quotation_id} not found.")
        return quote

    async def list_quotations(
        self,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        sales_rep_id: Optional[int] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Quotation]:
        return await self.quote_repo.list_quotations(
            self.db,
            status=status,
            customer_id=customer_id,
            sales_rep_id=sales_rep_id,
            search=search,
            limit=limit,
            offset=offset,
        )

    async def update_quotation(
        self,
        quotation_id: int,
        obj_in: QuotationUpdate,
        current_user: User,
    ) -> Quotation:
        quote = await self.get_quotation_by_id(quotation_id)
        self._verify_editability(quote)
        self._verify_ownership(quote, current_user)

        updated_fields = {}
        if obj_in.payment_terms_days is not None:
            quote.payment_terms_days = obj_in.payment_terms_days
            updated_fields["payment_terms_days"] = obj_in.payment_terms_days

        if obj_in.order_discount_pct is not None:
            quote.order_discount_pct = obj_in.order_discount_pct
            updated_fields["order_discount_pct"] = str(obj_in.order_discount_pct)

        await self._create_audit_event(
            quotation_id=quote.id,
            actor_user_id=current_user.id,
            event_type=AuditEventType.QUOTE_UPDATED.value,
            metadata=updated_fields,
        )

        await self.eval_service.evaluate_and_update(quote)

        try:
            await self.db.commit()
            return await self.get_quotation_by_id(quote.id)
        except Exception:
            await self.db.rollback()
            raise

    async def add_quote_line(
        self,
        quotation_id: int,
        obj_in: QuoteLineCreate,
        current_user: User,
    ) -> Quotation:
        quote = await self.get_quotation_by_id(quotation_id)
        self._verify_editability(quote)
        self._verify_ownership(quote, current_user)

        # 1. Validate Product
        product = await self.product_repo.get_by_id(self.db, obj_in.product_id)
        if not product:
            raise InvalidReferenceError(f"Product with ID {obj_in.product_id} does not exist.")
        if not product.is_active:
            raise InactiveReferenceError(f"Product '{product.name}' is inactive.")
        if product.currency != quote.currency:
            raise CurrencyMismatchError(
                f"Product currency '{product.currency}' does not match quotation currency '{quote.currency}'."
            )

        # 2. Validate BillingPlan if provided
        billing_plan = None
        if obj_in.billing_plan_id is not None:
            billing_plan = await self.billing_plan_repo.get_by_id(self.db, obj_in.billing_plan_id)
            if not billing_plan:
                raise InvalidReferenceError(f"BillingPlan with ID {obj_in.billing_plan_id} does not exist.")
            if not billing_plan.is_active:
                raise InactiveReferenceError(f"BillingPlan '{billing_plan.name}' is inactive.")

        # 3. Default line discount if omitted
        customer_tier_id = quote.customer.tier_id if quote.customer else None
        as_of = datetime.now(timezone.utc)

        if obj_in.line_discount_pct is not None:
            line_disc = obj_in.line_discount_pct
        else:
            policy, _ = await self.policy_service.get_applicable_policy(
                customer_tier_id=customer_tier_id,
                product_id=product.id,
                as_of=as_of,
            )
            line_disc = policy.standard_discount_pct if policy else Decimal("0.00")

        line = QuoteLine(
            quotation_id=quote.id,
            product_id=product.id,
            billing_plan_id=billing_plan.id if billing_plan else None,
            quantity=obj_in.quantity,
            unit_list_price=product.list_price,
            unit_cost=product.cost_price,
            line_discount_pct=line_disc,
            source_type="MANUAL",
        )

        quote.lines.append(line)

        await self._create_audit_event(
            quotation_id=quote.id,
            actor_user_id=current_user.id,
            event_type=AuditEventType.LINE_ADDED.value,
            metadata={"product_id": product.id, "quantity": str(obj_in.quantity), "line_discount_pct": str(line_disc)},
        )

        await self.eval_service.evaluate_and_update(quote)

        try:
            await self.db.commit()
            return await self.get_quotation_by_id(quote.id)
        except Exception:
            await self.db.rollback()
            raise

    async def update_quote_line(
        self,
        quotation_id: int,
        line_id: int,
        obj_in: QuoteLineUpdate,
        current_user: User,
    ) -> Quotation:
        quote = await self.get_quotation_by_id(quotation_id)
        self._verify_editability(quote)
        self._verify_ownership(quote, current_user)

        line = await self.line_repo.get_by_id(self.db, line_id)
        if not line or line.quotation_id != quote.id:
            raise QuoteLineNotFoundError(f"QuoteLine with ID {line_id} not found on quotation {quotation_id}.")

        updated_fields = {}
        if obj_in.quantity is not None:
            line.quantity = obj_in.quantity
            updated_fields["quantity"] = str(obj_in.quantity)

        if obj_in.line_discount_pct is not None:
            line.line_discount_pct = obj_in.line_discount_pct
            updated_fields["line_discount_pct"] = str(obj_in.line_discount_pct)

        if obj_in.billing_plan_id is not None:
            billing_plan = await self.billing_plan_repo.get_by_id(self.db, obj_in.billing_plan_id)
            if not billing_plan:
                raise InvalidReferenceError(f"BillingPlan with ID {obj_in.billing_plan_id} does not exist.")
            if not billing_plan.is_active:
                raise InactiveReferenceError(f"BillingPlan '{billing_plan.name}' is inactive.")
            line.billing_plan_id = billing_plan.id
            updated_fields["billing_plan_id"] = billing_plan.id

        await self._create_audit_event(
            quotation_id=quote.id,
            actor_user_id=current_user.id,
            event_type=AuditEventType.LINE_UPDATED.value,
            metadata={"line_id": line_id, "changes": updated_fields},
        )

        await self.eval_service.evaluate_and_update(quote)

        try:
            await self.db.commit()
            return await self.get_quotation_by_id(quote.id)
        except Exception:
            await self.db.rollback()
            raise

    async def remove_quote_line(
        self,
        quotation_id: int,
        line_id: int,
        current_user: User,
    ) -> Quotation:
        quote = await self.get_quotation_by_id(quotation_id)
        self._verify_editability(quote)
        self._verify_ownership(quote, current_user)

        line = await self.line_repo.get_by_id(self.db, line_id)
        if not line or line.quotation_id != quote.id:
            raise QuoteLineNotFoundError(f"QuoteLine with ID {line_id} not found on quotation {quotation_id}.")

        await self.line_repo.delete_line(self.db, line)
        quote.lines = [l for l in quote.lines if l.id != line_id]

        await self._create_audit_event(
            quotation_id=quote.id,
            actor_user_id=current_user.id,
            event_type=AuditEventType.LINE_REMOVED.value,
            metadata={"line_id": line_id, "product_id": line.product_id},
        )

        await self.eval_service.evaluate_and_update(quote)

        try:
            await self.db.commit()
            return await self.get_quotation_by_id(quote.id)
        except Exception:
            await self.db.rollback()
            raise

    async def recalculate_quotation(
        self,
        quotation_id: int,
        current_user: User,
    ) -> Quotation:
        quote = await self.get_quotation_by_id(quotation_id)
        self._verify_editability(quote)
        self._verify_ownership(quote, current_user)

        await self._create_audit_event(
            quotation_id=quote.id,
            actor_user_id=current_user.id,
            event_type=AuditEventType.QUOTE_RECALCULATED.value,
        )

        await self.eval_service.evaluate_and_update(quote)

        try:
            await self.db.commit()
            return await self.get_quotation_by_id(quote.id)
        except Exception:
            await self.db.rollback()
            raise

    async def cancel_quotation(
        self,
        quotation_id: int,
        current_user: User,
    ) -> Quotation:
        quote = await self.get_quotation_by_id(quotation_id)
        self._verify_editability(quote)
        self._verify_ownership(quote, current_user)

        old_status = quote.status
        quote.status = QuotationStatus.CANCELLED.value

        await self._create_audit_event(
            quotation_id=quote.id,
            actor_user_id=current_user.id,
            event_type=AuditEventType.QUOTE_CANCELLED.value,
            from_status=old_status,
            to_status=QuotationStatus.CANCELLED.value,
        )

        try:
            await self.db.commit()
            return await self.get_quotation_by_id(quote.id)
        except Exception:
            await self.db.rollback()
            raise

    async def get_audit_events(self, quotation_id: int) -> List[QuoteAuditEvent]:
        await self.get_quotation_by_id(quotation_id)
        return await self.audit_repo.list_by_quotation(self.db, quotation_id)

    # ----------------------------------------------------
    # PHASE 3 PART 2: RECOMMENDATIONS & UPSELL
    # ----------------------------------------------------
    async def get_recommendations(self, quotation_id: int) -> List[RecommendationCandidate]:
        quote = await self.get_quotation_by_id(quotation_id)
        current_product_ids = {l.product_id for l in quote.lines}
        if not current_product_ids:
            return []

        dismissed_rule_ids = await self.dismissal_repo.get_dismissed_rule_ids(self.db, quote.id)

        active_rules_orm = await self.rule_repo.list_rules(self.db, is_active=True, effective_only=True)
        active_rules = [
            {
                "id": r.id,
                "source_product_id": r.source_product_id,
                "suggested_product_id": r.suggested_product_id,
                "affinity_score": r.affinity_score,
                "recommended_qty": r.recommended_qty,
                "is_promoted": r.is_promoted,
                "promotion_label": r.promotion_label,
                "min_margin_pct": r.min_margin_pct,
                "priority": r.priority,
            }
            for r in active_rules_orm
        ]

        products_by_id = {}
        resolved_policy_discounts = {}
        customer_tier_id = quote.customer.tier_id if quote.customer else None
        as_of = quote.created_at or datetime.now(timezone.utc)

        for r in active_rules_orm:
            if r.suggested_product_id not in products_by_id and r.suggested_product:
                products_by_id[r.suggested_product_id] = {
                    "list_price": r.suggested_product.list_price,
                    "cost_price": r.suggested_product.cost_price,
                    "is_active": r.suggested_product.is_active,
                    "currency": r.suggested_product.currency,
                    "name": r.suggested_product.name,
                }
                pol, _ = await self.policy_service.get_applicable_policy(
                    customer_tier_id=customer_tier_id,
                    product_id=r.suggested_product_id,
                    as_of=as_of,
                )
                resolved_policy_discounts[r.suggested_product_id] = pol.standard_discount_pct if pol else Decimal("0.00")

            if r.source_product_id not in products_by_id and r.source_product:
                products_by_id[r.source_product_id] = {
                    "list_price": r.source_product.list_price,
                    "cost_price": r.source_product.cost_price,
                    "is_active": r.source_product.is_active,
                    "currency": r.source_product.currency,
                    "name": r.source_product.name,
                }

        candidates = RecommendationEngine.evaluate(
            current_product_ids=current_product_ids,
            current_order_discount_pct=quote.order_discount_pct,
            current_quote_net_total=quote.net_total,
            current_quote_total_cost=quote.total_cost,
            dismissed_rule_ids=dismissed_rule_ids,
            active_rules=active_rules,
            products_by_id=products_by_id,
            resolved_policy_discounts=resolved_policy_discounts,
        )

        return candidates

    async def add_recommendation_to_quotation(
        self,
        quotation_id: int,
        rule_id: int,
        current_user: User,
    ) -> Quotation:
        quote = await self.get_quotation_by_id(quotation_id)
        self._verify_editability(quote)
        self._verify_ownership(quote, current_user)

        rule = await self.rule_repo.get_by_id(self.db, rule_id)
        if not rule or not rule.is_active:
            raise ResourceNotFoundError(f"Recommendation rule with ID {rule_id} is not available.")

        suggested_product = await self.product_repo.get_by_id(self.db, rule.suggested_product_id)
        if not suggested_product or not suggested_product.is_active:
            raise InactiveReferenceError(f"Suggested product with ID {rule.suggested_product_id} is inactive.")

        if suggested_product.currency != quote.currency:
            raise CurrencyMismatchError(
                f"Suggested product currency '{suggested_product.currency}' does not match quote currency '{quote.currency}'."
            )

        customer_tier_id = quote.customer.tier_id if quote.customer else None
        as_of = quote.created_at or datetime.now(timezone.utc)
        policy, _ = await self.policy_service.get_applicable_policy(
            customer_tier_id=customer_tier_id,
            product_id=suggested_product.id,
            as_of=as_of,
        )
        std_disc = policy.standard_discount_pct if policy else Decimal("0.00")

        line = QuoteLine(
            quotation_id=quote.id,
            product_id=suggested_product.id,
            quantity=rule.recommended_qty,
            unit_list_price=suggested_product.list_price,
            unit_cost=suggested_product.cost_price,
            line_discount_pct=std_disc,
            source_type="UPSELL",
            recommendation_rule_id=rule.id,
        )
        quote.lines.append(line)

        await self._create_audit_event(
            quotation_id=quote.id,
            actor_user_id=current_user.id,
            event_type="UPSELL_ADDED",
            metadata={"rule_id": rule.id, "suggested_product_id": suggested_product.id},
        )

        await self.eval_service.evaluate_and_update(quote)

        try:
            await self.db.commit()
            return await self.get_quotation_by_id(quote.id)
        except Exception:
            await self.db.rollback()
            raise

    async def dismiss_recommendation(
        self,
        quotation_id: int,
        rule_id: int,
        current_user: User,
    ) -> Quotation:
        quote = await self.get_quotation_by_id(quotation_id)
        self._verify_editability(quote)
        self._verify_ownership(quote, current_user)

        rule = await self.rule_repo.get_by_id(self.db, rule_id)
        if not rule:
            raise ResourceNotFoundError(f"Recommendation rule with ID {rule_id} not found.")

        dismissal = QuoteRecommendationDismissal(
            quotation_id=quote.id,
            recommendation_rule_id=rule.id,
            dismissed_by_user_id=current_user.id,
        )
        try:
            await self.dismissal_repo.add_dismissal(self.db, dismissal)
            await self.db.commit()
            return quote
        except Exception:
            await self.db.rollback()
            raise

    # ----------------------------------------------------
    # PHASE 3 PART 2: WHAT-IF SIMULATOR (NON-PERSISTENT)
    # ----------------------------------------------------
    async def run_what_if_simulation(
        self,
        quotation_id: int,
        req_data: WhatIfRequest,
    ) -> WhatIfSimulationResult:
        quote = await self.get_quotation_by_id(quotation_id)

        active_policies_orm = await self.approval_policy_repo.list_policies(self.db, is_active=True, effective_only=True)
        active_policies = [
            {
                "id": p.id,
                "customer_tier_id": p.customer_tier_id,
                "discount_above_pct": p.discount_above_pct,
                "margin_below_pct": p.margin_below_pct,
                "payment_terms_above_days": p.payment_terms_above_days,
                "blended_risk_above": p.blended_risk_above,
                "approval_role": p.approval_role,
                "priority": p.priority,
            }
            for p in active_policies_orm
        ]

        existing_lines = [
            {
                "id": l.id,
                "product_id": l.product_id,
                "quantity": l.quantity,
                "unit_list_price": l.unit_list_price,
                "unit_cost": l.unit_cost,
                "line_discount_pct": l.line_discount_pct,
                "standard_discount_pct_snapshot": l.standard_discount_pct_snapshot,
                "max_discount_pct_snapshot": l.max_discount_pct_snapshot,
            }
            for l in quote.lines
        ]

        customer_tier_id = quote.customer.tier_id if quote.customer else None

        line_overrides = []
        if req_data.line_overrides:
            for lo in req_data.line_overrides:
                line_overrides.append(lo.model_dump(exclude_unset=True))

        sim_res = WhatIfSimulatorEngine.simulate(
            quotation_id=quote.id,
            current_order_discount_pct=quote.order_discount_pct,
            current_payment_terms_days=quote.payment_terms_days,
            current_customer_tier_id=customer_tier_id,
            existing_lines=existing_lines,
            active_approval_policies=active_policies,
            order_discount_pct_override=req_data.order_discount_pct,
            payment_terms_days_override=req_data.payment_terms_days,
            line_overrides=line_overrides,
        )

        return sim_res

    async def send_to_customer(self, quotation_id: int, current_user: User) -> Quotation:
        quote = await self.quote_repo.get_by_id(self.db, quotation_id)
        if not quote:
            raise QuoteNotFoundError(f"Quotation with ID {quotation_id} not found.")

        self._verify_ownership(quote, current_user)

        if quote.status != QuotationStatus.APPROVED.value:
            raise CommercialPolicyValidationError(
                f"Quotation {quote.quote_number} is in '{quote.status}' status and cannot be sent to customer. Must be APPROVED."
            )

        from app.core.enums import NotificationType, VersionSourceType
        from app.repositories.customer_portal_access import CustomerPortalAccessRepository
        from app.services.notification import NotificationService
        from app.services.quote_version import QuoteVersionService

        quote.status = QuotationStatus.SENT_TO_CUSTOMER.value
        await self.db.flush()

        # Create initial snapshot if current_version_id is not set
        if not quote.current_version_id:
            v_service = QuoteVersionService(self.db)
            version = await v_service.create_version_snapshot(
                quotation_id=quote.id,
                source_type=VersionSourceType.INITIAL_RELEASE.value,
                created_by_user_id=current_user.id,
                approval_status="APPROVED",
            )
            quote.current_version_id = version.id
            quote.latest_approved_version_id = version.id

        await self._create_audit_event(
            quotation_id=quote.id,
            actor_user_id=current_user.id,
            event_type=AuditEventType.QUOTE_SENT_TO_CUSTOMER.value,
            from_status=QuotationStatus.APPROVED.value,
            to_status=QuotationStatus.SENT_TO_CUSTOMER.value,
        )

        try:
            await self.db.commit()
            updated_quote = await self.quote_repo.get_by_id(self.db, quote.id)
        except Exception:
            await self.db.rollback()
            raise

        portal_repo = CustomerPortalAccessRepository()
        portal_accesses = await portal_repo.list_access(self.db, customer_id=updated_quote.customer_id, is_active=True)
        cust_user_ids = [pa.user_id for pa in portal_accesses]

        if cust_user_ids:
            notif_service = NotificationService(self.db)
            await notif_service.dispatch_post_commit_events(
                db=self.db,
                recipient_user_ids=cust_user_ids,
                notification_type=NotificationType.QUOTE_SENT.value,
                title=f"Quotation {updated_quote.quote_number} Received",
                content=f"Your quotation {updated_quote.quote_number} is ready for review.",
                quotation_id=updated_quote.id,
                payload={"quotation_id": updated_quote.id, "quote_number": updated_quote.quote_number},
            )

        return updated_quote


