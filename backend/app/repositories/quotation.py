from typing import List, Optional
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.customer import Customer
from app.models.discount_policy import DiscountPolicy
from app.models.product import Product
from app.models.quotation import Quotation
from app.models.quotation_line import QuoteLine
from app.models.user import User
from app.repositories.base import BaseRepository


class QuotationRepository(BaseRepository[Quotation]):
    def __init__(self) -> None:
        super().__init__(Quotation)

    def _default_options(self):
        return [
            selectinload(Quotation.customer).selectinload(Customer.tier),
            selectinload(Quotation.sales_rep).selectinload(User.role),
            selectinload(Quotation.lines).joinedload(QuoteLine.product).joinedload(Product.category),
            selectinload(Quotation.lines).selectinload(QuoteLine.billing_plan),
            selectinload(Quotation.lines).selectinload(QuoteLine.resolved_discount_policy).options(
                joinedload(DiscountPolicy.customer_tier),
                joinedload(DiscountPolicy.product_category),
                joinedload(DiscountPolicy.product).joinedload(Product.category),
            ),
            selectinload(Quotation.risk_reasons),
            selectinload(Quotation.audit_events),
            selectinload(Quotation.current_version),
            selectinload(Quotation.latest_approved_version),
            selectinload(Quotation.confirmed_version),
        ]

    async def create_quotation(self, db: AsyncSession, quotation: Quotation) -> Quotation:
        db.add(quotation)
        await db.flush()
        return quotation

    async def get_by_id(self, db: AsyncSession, quotation_id: int) -> Optional[Quotation]:
        stmt = (
            select(Quotation)
            .options(*self._default_options())
            .execution_options(populate_existing=True)
            .where(Quotation.id == quotation_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_quote_number(self, db: AsyncSession, quote_number: str) -> Optional[Quotation]:
        stmt = (
            select(Quotation)
            .options(*self._default_options())
            .execution_options(populate_existing=True)
            .where(Quotation.quote_number == quote_number)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_quotations(
        self,
        db: AsyncSession,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        sales_rep_id: Optional[int] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Quotation]:
        stmt = select(Quotation).options(*self._default_options()).join(Quotation.customer)

        if status is not None:
            stmt = stmt.where(Quotation.status == status)
        if customer_id is not None:
            stmt = stmt.where(Quotation.customer_id == customer_id)
        if sales_rep_id is not None:
            stmt = stmt.where(Quotation.sales_rep_id == sales_rep_id)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Quotation.quote_number.ilike(pattern),
                    Customer.name.ilike(pattern),
                    Customer.customer_code.ilike(pattern),
                )
            )

        stmt = stmt.order_by(Quotation.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().unique().all())
