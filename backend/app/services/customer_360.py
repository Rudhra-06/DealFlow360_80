"""Customer 360 Service for Phase 6 Part 2."""

from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.customer import Customer
from app.models.user import User
from app.repositories.analytics import AnalyticsRepository


class Customer360Service:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AnalyticsRepository(session)

    async def get_customer_360(
        self, customer_id: int, current_user: User
    ) -> Dict[str, Any]:
        user_role = current_user.role.name if (current_user and current_user.role) else ""
        if user_role == "CUSTOMER":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for CUSTOMER role"
            )

        customer = await self.session.get(Customer, customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID {customer_id} not found"
            )

        # Security check: SALES_REP can only access assigned customers
        if user_role == "SALES_REP":
            assigned_rep_id = getattr(customer, "assigned_sales_rep_id", None)
            if assigned_rep_id is not None and assigned_rep_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this customer profile"
                )


        data = await self.repo.get_customer_360(customer_id)
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer 360 data not found for customer {customer_id}"
            )
        return data
