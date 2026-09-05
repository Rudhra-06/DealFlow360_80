from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.quote_negotiation_line_change import QuoteNegotiationLineChange
from app.models.quote_negotiation_message import QuoteNegotiationMessage
from app.models.quote_negotiation_request import QuoteNegotiationRequest
from app.repositories.base import BaseRepository


class QuoteNegotiationMessageRepository(BaseRepository[QuoteNegotiationMessage]):
    def __init__(self) -> None:
        super().__init__(QuoteNegotiationMessage)

    async def create_message(self, db: AsyncSession, msg: QuoteNegotiationMessage) -> QuoteNegotiationMessage:
        db.add(msg)
        await db.flush()
        return msg

    async def list_messages(
        self, db: AsyncSession, quotation_id: int, is_customer_visible_only: bool = False
    ) -> List[QuoteNegotiationMessage]:
        stmt = (
            select(QuoteNegotiationMessage)
            .options(
                selectinload(QuoteNegotiationMessage.author_user),
                selectinload(QuoteNegotiationMessage.line),
            )
            .where(QuoteNegotiationMessage.quotation_id == quotation_id)
        )
        if is_customer_visible_only:
            stmt = stmt.where(QuoteNegotiationMessage.is_customer_visible == True)

        stmt = stmt.order_by(QuoteNegotiationMessage.created_at.asc())
        res = await db.execute(stmt)
        return list(res.scalars().all())


class QuoteNegotiationRequestRepository(BaseRepository[QuoteNegotiationRequest]):
    def __init__(self) -> None:
        super().__init__(QuoteNegotiationRequest)

    def _default_options(self):
        return [
            selectinload(QuoteNegotiationRequest.line_changes).selectinload(QuoteNegotiationLineChange.quotation_line),
            selectinload(QuoteNegotiationRequest.requested_by_user),
            selectinload(QuoteNegotiationRequest.resolved_by_user),
            selectinload(QuoteNegotiationRequest.base_version),
        ]

    async def create_request(self, db: AsyncSession, req: QuoteNegotiationRequest) -> QuoteNegotiationRequest:
        db.add(req)
        await db.flush()
        return req

    async def get_by_id(self, db: AsyncSession, request_id: int) -> Optional[QuoteNegotiationRequest]:
        stmt = select(QuoteNegotiationRequest).options(*self._default_options()).where(QuoteNegotiationRequest.id == request_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_pending_by_quote(self, db: AsyncSession, quotation_id: int) -> List[QuoteNegotiationRequest]:
        stmt = (
            select(QuoteNegotiationRequest)
            .options(*self._default_options())
            .where(QuoteNegotiationRequest.quotation_id == quotation_id, QuoteNegotiationRequest.status == "PENDING")
            .order_by(QuoteNegotiationRequest.created_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def list_requests(self, db: AsyncSession, quotation_id: int) -> List[QuoteNegotiationRequest]:
        stmt = (
            select(QuoteNegotiationRequest)
            .options(*self._default_options())
            .where(QuoteNegotiationRequest.quotation_id == quotation_id)
            .order_by(QuoteNegotiationRequest.created_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def supersede_older_pending_requests(self, db: AsyncSession, quotation_id: int, current_request_id: int) -> None:
        stmt = (
            update(QuoteNegotiationRequest)
            .where(
                QuoteNegotiationRequest.quotation_id == quotation_id,
                QuoteNegotiationRequest.id != current_request_id,
                QuoteNegotiationRequest.status == "PENDING",
            )
            .values(status="SUPERSEDED")
        )
        await db.execute(stmt)
