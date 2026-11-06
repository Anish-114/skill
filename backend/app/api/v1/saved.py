from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Opportunity, SavedOpportunity, User
from app.schemas.saved_opportunity import (
    SavedOpportunityCreate,
    SavedOpportunityUpdate,
    SavedOpportunityResponse,
)
from app.schemas.opportunity import OpportunityResponse

router = APIRouter(prefix="/saved-opportunities", tags=["Saved Opportunities"])

VALID_SAVED_STATUSES = {
    "saved",
    "applied",
    "in_progress",
    "shortlisted",
    "selected",
    "rejected",
    "archived",
}


@router.get("", response_model=List[SavedOpportunityResponse])
def list_saved_opportunities(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all bookmarked/saved opportunities for the current student."""
    query = db.query(SavedOpportunity).filter(SavedOpportunity.user_id == current_user.id)
    if status_filter and isinstance(status_filter, str) and status_filter.strip().lower() != "all":
        query = query.filter(SavedOpportunity.status == status_filter.strip().lower())

    saved_items = query.order_by(SavedOpportunity.saved_at.desc()).all()

    results = []
    for item in saved_items:
        opp_schema = OpportunityResponse.model_validate(item.opportunity)
        results.append(
            SavedOpportunityResponse(
                id=item.id,
                user_id=item.user_id,
                opportunity_id=item.opportunity_id,
                status=item.status,
                notes=item.notes,
                saved_at=item.saved_at,
                opportunity=opp_schema
            )
        )
    return results


@router.post("/{opportunity_id}", response_model=SavedOpportunityResponse, status_code=status.HTTP_201_CREATED)
@router.put("/{opportunity_id}", response_model=SavedOpportunityResponse)
@router.patch("/{opportunity_id}", response_model=SavedOpportunityResponse)
def save_or_update_opportunity(
    opportunity_id: int,
    payload: Optional[SavedOpportunityCreate] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bookmark an opportunity or update its tracking status and notes.
    Enforces user ownership (can only modify own saved records) and validates status.
    Allowed statuses: saved, applied, in_progress, shortlisted, selected, rejected, archived.
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunity with ID {opportunity_id} not found."
        )

    # Validate status if provided
    clean_status: Optional[str] = None
    if payload and payload.status is not None:
        raw_status = payload.status.strip().lower()
        if raw_status not in VALID_SAVED_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status '{payload.status}'. Allowed statuses are: {', '.join(sorted(VALID_SAVED_STATUSES))}"
            )
        clean_status = raw_status

    saved_record = (
        db.query(SavedOpportunity)
        .filter(
            SavedOpportunity.user_id == current_user.id,
            SavedOpportunity.opportunity_id == opportunity_id
        )
        .first()
    )

    if saved_record:
        # Update existing record
        if clean_status is not None:
            saved_record.status = clean_status
        if payload and payload.notes is not None:
            saved_record.notes = payload.notes
    else:
        # Create new record
        saved_record = SavedOpportunity(
            user_id=current_user.id,
            opportunity_id=opportunity_id,
            status=clean_status or "saved",
            notes=payload.notes if payload else None
        )
        db.add(saved_record)

    db.commit()
    db.refresh(saved_record)

    return SavedOpportunityResponse(
        id=saved_record.id,
        user_id=saved_record.user_id,
        opportunity_id=saved_record.opportunity_id,
        status=saved_record.status,
        notes=saved_record.notes,
        saved_at=saved_record.saved_at,
        opportunity=OpportunityResponse.model_validate(opportunity)
    )


@router.delete("/{opportunity_id}", status_code=status.HTTP_200_OK)
def remove_saved_opportunity(
    opportunity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove an opportunity bookmark for the current student."""
    saved_record = (
        db.query(SavedOpportunity)
        .filter(
            SavedOpportunity.user_id == current_user.id,
            SavedOpportunity.opportunity_id == opportunity_id
        )
        .first()
    )

    if not saved_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunity {opportunity_id} is not bookmarked."
        )

    db.delete(saved_record)
    db.commit()
    return {"message": "Opportunity bookmark removed successfully.", "opportunity_id": opportunity_id}
