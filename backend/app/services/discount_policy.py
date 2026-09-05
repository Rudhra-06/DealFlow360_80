from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Sequence, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discount_policy import DiscountPolicy
from app.repositories.customer_tier import CustomerTierRepository
from app.repositories.discount_policy import DiscountPolicyRepository
from app.repositories.product import ProductRepository
from app.repositories.product_category import ProductCategoryRepository
from app.schemas.discount_policy import DiscountPolicyCreate, DiscountPolicyUpdate
from app.services.exceptions import (
    CommercialPolicyValidationError,
    InactiveReferenceError,
    InvalidReferenceError,
    PolicyAmbiguityError,
    ResourceNotFoundError,
)


class DiscountPolicyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.policy_repo = DiscountPolicyRepository()
        self.tier_repo = CustomerTierRepository()
        self.category_repo = ProductCategoryRepository()
        self.product_repo = ProductRepository()

    async def _validate_policy_state(
        self,
        name: str,
        customer_tier_id: Optional[int],
        product_category_id: Optional[int],
        product_id: Optional[int],
        standard_discount_pct: Decimal,
        max_discount_pct: Decimal,
        priority: int,
        effective_from: datetime,
        effective_to: Optional[datetime],
        is_active: bool,
        exclude_policy_id: Optional[int] = None,
    ) -> None:
        # 1. Product vs Category scope check
        if product_id is not None and product_category_id is not None:
            raise CommercialPolicyValidationError(
                "DiscountPolicy cannot be scoped to both product_id and product_category_id simultaneously."
            )

        # 2. Percentage range check
        if standard_discount_pct < Decimal("0.00") or standard_discount_pct > Decimal("100.00"):
            raise CommercialPolicyValidationError("standard_discount_pct must be between 0.00 and 100.00.")

        if max_discount_pct < Decimal("0.00") or max_discount_pct > Decimal("100.00"):
            raise CommercialPolicyValidationError("max_discount_pct must be between 0.00 and 100.00.")

        if standard_discount_pct > max_discount_pct:
            raise CommercialPolicyValidationError(
                f"standard_discount_pct ({standard_discount_pct}) cannot exceed max_discount_pct ({max_discount_pct})."
            )

        # 3. Effective date ordering check
        if effective_to is not None and effective_to <= effective_from:
            raise CommercialPolicyValidationError("effective_to timestamp must be strictly after effective_from timestamp.")

        # 4. Active Foreign Reference Checks
        if customer_tier_id is not None:
            tier = await self.tier_repo.get_by_id(self.db, customer_tier_id)
            if not tier:
                raise InvalidReferenceError(f"CustomerTier with ID {customer_tier_id} does not exist.")
            if not tier.is_active:
                raise InactiveReferenceError(f"CustomerTier '{tier.name}' (ID {customer_tier_id}) is inactive.")

        if product_category_id is not None:
            category = await self.category_repo.get_by_id(self.db, product_category_id)
            if not category:
                raise InvalidReferenceError(f"ProductCategory with ID {product_category_id} does not exist.")
            if not category.is_active:
                raise InactiveReferenceError(f"ProductCategory '{category.name}' (ID {product_category_id}) is inactive.")

        if product_id is not None:
            product = await self.product_repo.get_by_id(self.db, product_id)
            if not product:
                raise InvalidReferenceError(f"Product with ID {product_id} does not exist.")
            if not product.is_active:
                raise InactiveReferenceError(f"Product '{product.name}' (ID {product_id}) is inactive.")

        # 5. Overlap ambiguity check for active policies
        if is_active:
            overlaps = await self.policy_repo.find_scope_overlaps(
                self.db,
                customer_tier_id=customer_tier_id,
                product_category_id=product_category_id,
                product_id=product_id,
                priority=priority,
                effective_from=effective_from,
                effective_to=effective_to,
                exclude_policy_id=exclude_policy_id,
            )
            if overlaps:
                conflicting = overlaps[0]
                raise PolicyAmbiguityError(
                    f"Active DiscountPolicy '{conflicting.name}' (ID {conflicting.id}) already exists with identical scope, priority ({priority}), and overlapping effective dates."
                )

    async def create_policy(self, obj_in: DiscountPolicyCreate) -> DiscountPolicy:
        try:
            eff_from = obj_in.effective_from or datetime.now(timezone.utc)
            await self._validate_policy_state(
                name=obj_in.name,
                customer_tier_id=obj_in.customer_tier_id,
                product_category_id=obj_in.product_category_id,
                product_id=obj_in.product_id,
                standard_discount_pct=obj_in.standard_discount_pct,
                max_discount_pct=obj_in.max_discount_pct,
                priority=obj_in.priority,
                effective_from=eff_from,
                effective_to=obj_in.effective_to,
                is_active=obj_in.is_active,
            )
            create_data = obj_in.model_dump()
            create_data["effective_from"] = eff_from

            policy = DiscountPolicy(**create_data)
            self.db.add(policy)
            await self.db.flush()
            await self.db.commit()
            return await self.get_policy_by_id(policy.id)
        except Exception:
            await self.db.rollback()
            raise

    async def update_policy(self, policy_id: int, obj_in: DiscountPolicyUpdate) -> DiscountPolicy:
        policy = await self.policy_repo.get_by_id(self.db, policy_id)
        if not policy:
            raise ResourceNotFoundError(f"DiscountPolicy with ID {policy_id} not found.")

        patch_data = obj_in.model_dump(exclude_unset=True)

        # Merge prospective final state
        final_name = patch_data.get("name", policy.name)
        final_tier_id = patch_data.get("customer_tier_id", policy.customer_tier_id)
        final_category_id = patch_data.get("product_category_id", policy.product_category_id)
        final_product_id = patch_data.get("product_id", policy.product_id)
        final_std_pct = patch_data.get("standard_discount_pct", policy.standard_discount_pct)
        final_max_pct = patch_data.get("max_discount_pct", policy.max_discount_pct)
        final_priority = patch_data.get("priority", policy.priority)
        final_eff_from = patch_data.get("effective_from", policy.effective_from)
        final_eff_to = patch_data.get("effective_to", policy.effective_to)
        final_is_active = patch_data.get("is_active", policy.is_active)

        try:
            await self._validate_policy_state(
                name=final_name,
                customer_tier_id=final_tier_id,
                product_category_id=final_category_id,
                product_id=final_product_id,
                standard_discount_pct=final_std_pct,
                max_discount_pct=final_max_pct,
                priority=final_priority,
                effective_from=final_eff_from,
                effective_to=final_eff_to,
                is_active=final_is_active,
                exclude_policy_id=policy_id,
            )

            for field, value in patch_data.items():
                setattr(policy, field, value)

            await self.db.flush()
            await self.db.commit()
            return await self.get_policy_by_id(policy_id)
        except Exception:
            await self.db.rollback()
            raise

    async def get_policy_by_id(self, policy_id: int) -> DiscountPolicy:
        policy = await self.policy_repo.get_by_id(self.db, policy_id)
        if not policy:
            raise ResourceNotFoundError(f"DiscountPolicy with ID {policy_id} not found.")
        return policy

    async def list_policies(
        self,
        customer_tier_id: Optional[int] = None,
        product_category_id: Optional[int] = None,
        product_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        effective_only: bool = False,
        as_of: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[DiscountPolicy]:
        return await self.policy_repo.list_policies(
            self.db,
            customer_tier_id=customer_tier_id,
            product_category_id=product_category_id,
            product_id=product_id,
            is_active=is_active,
            effective_only=effective_only,
            as_of=as_of,
            limit=limit,
            offset=offset,
        )

    async def get_applicable_policy(
        self,
        customer_tier_id: Optional[int],
        product_id: Optional[int],
        as_of: Optional[datetime] = None,
    ) -> Tuple[Optional[DiscountPolicy], Optional[str]]:
        """Resolves the single most applicable DiscountPolicy based on scope specificity and priority."""
        ref_time = as_of or datetime.now(timezone.utc)

        category_id = None
        if product_id is not None:
            product = await self.product_repo.get_by_id(self.db, product_id)
            if product:
                category_id = product.category_id

        candidates = await self.policy_repo.find_effective_candidates(
            self.db,
            customer_tier_id=customer_tier_id,
            product_category_id=category_id,
            product_id=product_id,
            as_of=ref_time,
        )

        if not candidates:
            return None, None

        # Classify and rank by specificity score
        # 1: tier + product
        # 2: product
        # 3: tier + category
        # 4: category
        # 5: tier
        # 6: global
        ranked = []
        for p in candidates:
            if p.product_id == product_id and product_id is not None and p.customer_tier_id == customer_tier_id and customer_tier_id is not None:
                spec = (1, "tier+product")
            elif p.product_id == product_id and product_id is not None and p.customer_tier_id is None:
                spec = (2, "product")
            elif p.product_category_id == category_id and category_id is not None and p.customer_tier_id == customer_tier_id and customer_tier_id is not None:
                spec = (3, "tier+category")
            elif p.product_category_id == category_id and category_id is not None and p.customer_tier_id is None:
                spec = (4, "category")
            elif p.customer_tier_id == customer_tier_id and customer_tier_id is not None and p.product_id is None and p.product_category_id is None:
                spec = (5, "tier")
            elif p.customer_tier_id is None and p.product_id is None and p.product_category_id is None:
                spec = (6, "global")
            else:
                continue
            ranked.append((spec[0], p.priority, p.id, spec[1], p))

        if not ranked:
            return None, None

        ranked.sort(key=lambda x: (x[0], x[1], x[2]))
        winner = ranked[0]
        return winner[4], winner[3]
