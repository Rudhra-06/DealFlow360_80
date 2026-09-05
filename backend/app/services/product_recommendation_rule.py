from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_recommendation_rule import ProductRecommendationRule
from app.repositories.product import ProductRepository
from app.repositories.product_recommendation_rule import ProductRecommendationRuleRepository
from app.schemas.product_recommendation_rule import (
    RecommendationRuleCreate,
    RecommendationRuleUpdate,
)
from app.services.exceptions import (
    CommercialPolicyValidationError,
    InactiveReferenceError,
    InvalidReferenceError,
    ResourceNotFoundError,
)


class ProductRecommendationRuleService:
    """Service layer managing product recommendation rule configuration."""

    def __init__(self, db: AsyncSession) -> None:
        self.db: AsyncSession = db
        self.rule_repo = ProductRecommendationRuleRepository()
        self.product_repo = ProductRepository()

    async def _validate_rule(
        self,
        source_product_id: int,
        suggested_product_id: int,
        recommended_qty: Decimal,
        affinity_score: Decimal,
        effective_from: datetime,
        effective_to: Optional[datetime],
    ) -> None:
        if source_product_id == suggested_product_id:
            raise CommercialPolicyValidationError("source_product_id and suggested_product_id cannot be the same product.")

        if recommended_qty <= Decimal("0"):
            raise CommercialPolicyValidationError("recommended_qty must be greater than zero.")

        if affinity_score < Decimal("0"):
            raise CommercialPolicyValidationError("affinity_score must be non-negative (>= 0).")

        if effective_to is not None and effective_to <= effective_from:
            raise CommercialPolicyValidationError("effective_to timestamp must be strictly after effective_from timestamp.")

        source = await self.product_repo.get_by_id(self.db, source_product_id)
        if not source:
            raise InvalidReferenceError(f"Source product ID {source_product_id} does not exist.")
        if not source.is_active:
            raise InactiveReferenceError(f"Source product '{source.name}' is inactive.")

        suggested = await self.product_repo.get_by_id(self.db, suggested_product_id)
        if not suggested:
            raise InvalidReferenceError(f"Suggested product ID {suggested_product_id} does not exist.")
        if not suggested.is_active:
            raise InactiveReferenceError(f"Suggested product '{suggested.name}' is inactive.")

    async def create_rule(self, obj_in: RecommendationRuleCreate) -> ProductRecommendationRule:
        eff_from = obj_in.effective_from or datetime.now(timezone.utc)
        await self._validate_rule(
            source_product_id=obj_in.source_product_id,
            suggested_product_id=obj_in.suggested_product_id,
            recommended_qty=obj_in.recommended_qty,
            affinity_score=obj_in.affinity_score,
            effective_from=eff_from,
            effective_to=obj_in.effective_to,
        )

        create_data = obj_in.model_dump()
        create_data["effective_from"] = eff_from

        rule = ProductRecommendationRule(**create_data)
        try:
            await self.rule_repo.create_rule(self.db, rule)
            await self.db.commit()
            return await self.get_rule_by_id(rule.id)
        except Exception:
            await self.db.rollback()
            raise

    async def get_rule_by_id(self, rule_id: int) -> ProductRecommendationRule:
        rule = await self.rule_repo.get_by_id(self.db, rule_id)
        if not rule:
            raise ResourceNotFoundError(f"Recommendation rule with ID {rule_id} not found.")
        return rule

    async def list_rules(
        self,
        source_product_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        is_promoted: Optional[bool] = None,
        effective_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ProductRecommendationRule]:
        return await self.rule_repo.list_rules(
            self.db,
            source_product_id=source_product_id,
            is_active=is_active,
            is_promoted=is_promoted,
            effective_only=effective_only,
            limit=limit,
            offset=offset,
        )

    async def update_rule(self, rule_id: int, obj_in: RecommendationRuleUpdate) -> ProductRecommendationRule:
        rule = await self.get_rule_by_id(rule_id)
        patch_data = obj_in.model_dump(exclude_unset=True)

        final_source = patch_data.get("source_product_id", rule.source_product_id)
        final_suggested = patch_data.get("suggested_product_id", rule.suggested_product_id)
        final_qty = patch_data.get("recommended_qty", rule.recommended_qty)
        final_affinity = patch_data.get("affinity_score", rule.affinity_score)
        final_eff_from = patch_data.get("effective_from", rule.effective_from)
        final_eff_to = patch_data.get("effective_to", rule.effective_to)

        await self._validate_rule(
            source_product_id=final_source,
            suggested_product_id=final_suggested,
            recommended_qty=final_qty,
            affinity_score=final_affinity,
            effective_from=final_eff_from,
            effective_to=final_eff_to,
        )

        for k, v in patch_data.items():
            setattr(rule, k, v)

        try:
            await self.db.flush()
            await self.db.commit()
            return await self.get_rule_by_id(rule.id)
        except Exception:
            await self.db.rollback()
            raise
