from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.rbac import require_roles
from app.core.roles import RoleName
from app.db.session import get_db
from app.models.user import User
from app.schemas.product_recommendation_rule import (
    RecommendationRuleCreate,
    RecommendationRuleRead,
    RecommendationRuleUpdate,
)
from app.services.exceptions import (
    CommercialPolicyValidationError,
    InactiveReferenceError,
    InvalidReferenceError,
    ResourceNotFoundError,
)
from app.services.product_recommendation_rule import ProductRecommendationRuleService

router = APIRouter()

READ_ROLES = (
    RoleName.ADMIN,
    RoleName.SALES_REP,
    RoleName.SALES_MANAGER,
    RoleName.FINANCE_OPERATIONS,
)
WRITE_ROLES = (
    RoleName.ADMIN,
    RoleName.SALES_MANAGER,
)


@router.get(
    "",
    response_model=List[RecommendationRuleRead],
    status_code=status.HTTP_200_OK,
    summary="List Product Recommendation Rules",
)
async def list_recommendation_rules(
    source_product_id: Optional[int] = Query(None, description="Filter by anchor source Product ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_promoted: Optional[bool] = Query(None, description="Filter by promoted flag"),
    effective_only: bool = Query(False, description="Filter to currently effective rules only"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
) -> List[RecommendationRuleRead]:
    service = ProductRecommendationRuleService(db)
    return await service.list_rules(
        source_product_id=source_product_id,
        is_active=is_active,
        is_promoted=is_promoted,
        effective_only=effective_only,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{rule_id}",
    response_model=RecommendationRuleRead,
    status_code=status.HTTP_200_OK,
    summary="Get Recommendation Rule by ID",
)
async def get_recommendation_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
) -> RecommendationRuleRead:
    service = ProductRecommendationRuleService(db)
    try:
        return await service.get_rule_by_id(rule_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "",
    response_model=RecommendationRuleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Recommendation Rule",
)
async def create_recommendation_rule(
    obj_in: RecommendationRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
) -> RecommendationRuleRead:
    service = ProductRecommendationRuleService(db)
    try:
        return await service.create_rule(obj_in)
    except (CommercialPolicyValidationError, InvalidReferenceError, InactiveReferenceError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{rule_id}",
    response_model=RecommendationRuleRead,
    status_code=status.HTTP_200_OK,
    summary="Update Recommendation Rule",
)
async def update_recommendation_rule(
    rule_id: int,
    obj_in: RecommendationRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
) -> RecommendationRuleRead:
    service = ProductRecommendationRuleService(db)
    try:
        return await service.update_rule(rule_id, obj_in)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (CommercialPolicyValidationError, InvalidReferenceError, InactiveReferenceError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
