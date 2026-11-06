from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, nullslast
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Opportunity, SavedOpportunity, User
from app.schemas.opportunity import (
    OpportunityResponse,
    OpportunityDetailResponse,
)

router = APIRouter(prefix="/opportunities", tags=["Opportunities"])


@router.get("", response_model=List[OpportunityResponse])
def list_opportunities(
    category: Optional[str] = None,
    mode: Optional[str] = None,
    min_deadline: Optional[datetime] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = True,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Retrieve paginated opportunities with comprehensive multi-criteria filtering."""
    now = datetime.now(timezone.utc)
    query = db.query(Opportunity)

    if isinstance(is_active, bool):
        query = query.filter(Opportunity.is_active == is_active)
        # By default for active opportunities, only return upcoming or open/ongoing (deadline NULL)
        if is_active and min_deadline is None:
            query = query.filter(or_(Opportunity.deadline == None, Opportunity.deadline >= now))

    if min_deadline and isinstance(min_deadline, datetime):
        # Handle offset-aware / naive conversion
        min_dl = min_deadline if min_deadline.tzinfo else min_deadline.replace(tzinfo=timezone.utc)
        query = query.filter(or_(Opportunity.deadline == None, Opportunity.deadline >= min_dl))

    if category and isinstance(category, str):
        query = query.filter(Opportunity.category.ilike(f"%{category}%"))

    if mode and isinstance(mode, str):
        query = query.filter(Opportunity.mode.ilike(f"%{mode}%"))

    if search and isinstance(search, str):
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Opportunity.title.ilike(search_filter),
                Opportunity.organizer.ilike(search_filter),
                Opportunity.description.ilike(search_filter),
            )
        )

    opportunities = query.order_by(nullslast(Opportunity.deadline.asc())).offset(skip).limit(limit).all()
    return opportunities


@router.get("/{id}", response_model=OpportunityDetailResponse)
def get_opportunity_detail(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve detailed opportunity info including whether it is saved by the current student."""
    opportunity = db.query(Opportunity).filter(Opportunity.id == id).first()
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunity with ID {id} not found."
        )

    # Check if student saved this opportunity
    saved_record = (
        db.query(SavedOpportunity)
        .filter(
            SavedOpportunity.user_id == current_user.id,
            SavedOpportunity.opportunity_id == opportunity.id
        )
        .first()
    )

    return OpportunityDetailResponse(
        id=opportunity.id,
        title=opportunity.title,
        organizer=opportunity.organizer,
        category=opportunity.category,
        description=opportunity.description,
        required_skills=opportunity.required_skills,
        eligibility_criteria=opportunity.eligibility_criteria,
        deadline=opportunity.deadline,
        mode=opportunity.mode,
        location=opportunity.location,
        official_url=opportunity.official_url,
        source=opportunity.source,
        prize_pool=opportunity.prize_pool,
        is_active=opportunity.is_active,
        created_at=opportunity.created_at,
        updated_at=opportunity.updated_at,
        is_saved=bool(saved_record is not None),
        saved_status=saved_record.status if saved_record else None,
        saved_notes=saved_record.notes if saved_record else None
    )
