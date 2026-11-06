import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Opportunity, StudentProfile, TeamRequest, User
from app.schemas.team_request import (
    TeamRequestCreate,
    TeamRequestResponse,
    TeamRequestUpdate,
    TeamUserSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/team-requests", tags=["Team Requests"])

MAX_REQUESTS_PER_24H = 10


def _build_user_summary(user: User, is_contact_revealed: bool) -> TeamUserSummary:
    """Builds a sanitized or full summary for a user based on acceptance state."""
    profile = user.profile
    skills: List[str] = []
    if profile and profile.student_skills:
        skills = [ss.skill.name for ss in profile.student_skills if ss.skill]

    return TeamUserSummary(
        user_id=user.id,
        full_name=user.full_name,
        college_name=profile.college_name if profile else None,
        degree=profile.degree if profile else None,
        branch=profile.branch if profile else None,
        year=profile.year if profile else None,
        skills=skills,
        # Contact info strictly None unless accepted
        email=user.email if is_contact_revealed else None,
        phone=profile.phone if (is_contact_revealed and profile) else None,
        github_url=profile.github_url if (is_contact_revealed and profile) else None,
        linkedin_url=profile.linkedin_url if (is_contact_revealed and profile) else None,
        portfolio_url=profile.portfolio_url if (is_contact_revealed and profile) else None,
    )


def _format_team_request_response(req: TeamRequest, current_user_id: int) -> TeamRequestResponse:
    """Formats a TeamRequest ORM object into a privacy-guarded TeamRequestResponse."""
    is_accepted = (req.status == "accepted")
    is_sender = (req.from_user_id == current_user_id)

    from_summary = _build_user_summary(req.from_user, is_contact_revealed=is_accepted)
    to_summary = _build_user_summary(req.to_user, is_contact_revealed=is_accepted)

    opp_title = req.opportunity.title if req.opportunity else f"Opportunity #{req.opportunity_id}"

    return TeamRequestResponse(
        id=req.id,
        from_user_id=req.from_user_id,
        to_user_id=req.to_user_id,
        opportunity_id=req.opportunity_id,
        team_post_id=req.team_post_id,
        opportunity_title=opp_title,
        status=req.status,
        message=req.message,
        created_at=req.created_at,
        updated_at=req.updated_at,
        from_user=from_summary,
        to_user=to_summary,
        is_sender=is_sender,
    )


@router.post("", response_model=TeamRequestResponse, status_code=status.HTTP_201_CREATED)
def send_team_request(
    payload: TeamRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a team collaboration request to a potential teammate for a hackathon.
    Enforces rate limits (max 10 requests per 24 hours), duplicate prevention,
    and opt-in verification.
    """
    # 1. Prevent self-requests
    if payload.to_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send a team request to yourself."
        )

    # 2. Check daily spam limit (max 10 in 24h)
    now_utc = datetime.now(timezone.utc)
    day_ago = now_utc - timedelta(hours=24)
    recent_count = (
        db.query(TeamRequest)
        .filter(
            TeamRequest.from_user_id == current_user.id,
            TeamRequest.created_at >= day_ago
        )
        .count()
    )
    if recent_count >= MAX_REQUESTS_PER_24H:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily limit reached. You can send at most {MAX_REQUESTS_PER_24H} team requests in 24 hours."
        )

    # 3. Verify recipient exists and is actively looking for a team
    recipient = db.query(User).filter(User.id == payload.to_user_id, User.is_active == True).first()
    if not recipient or not recipient.profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target student was not found."
        )

    if not recipient.profile.looking_for_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This student is not currently open to receiving team requests."
        )

    # 4. Verify opportunity exists
    opportunity = db.query(Opportunity).filter(Opportunity.id == payload.opportunity_id).first()
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specified opportunity was not found."
        )

    # 5. Check duplicate requests
    existing_req = (
        db.query(TeamRequest)
        .filter(
            TeamRequest.from_user_id == current_user.id,
            TeamRequest.to_user_id == payload.to_user_id,
            TeamRequest.opportunity_id == payload.opportunity_id
        )
        .first()
    )
    if existing_req:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You have already sent a request to this student for this event (Status: {existing_req.status})."
        )

    # Also check if recipient already sent us a request
    reverse_req = (
        db.query(TeamRequest)
        .filter(
            TeamRequest.from_user_id == payload.to_user_id,
            TeamRequest.to_user_id == current_user.id,
            TeamRequest.opportunity_id == payload.opportunity_id
        )
        .first()
    )
    if reverse_req:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This student has already sent you a request for this event (Status: {reverse_req.status}). Please respond to their request."
        )

    # 6. Create request
    new_req = TeamRequest(
        from_user_id=current_user.id,
        to_user_id=payload.to_user_id,
        opportunity_id=payload.opportunity_id,
        team_post_id=payload.team_post_id,
        status="pending",
        message=payload.message.strip() if payload.message else None,
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)

    return _format_team_request_response(new_req, current_user.id)


@router.get("", response_model=List[TeamRequestResponse])
def get_my_team_requests(
    filter_type: Optional[str] = Query(None, description="'sent' | 'received' | None (both)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve all team collaboration requests sent or received by the current student.
    Enforces privacy: contact details are hidden unless the request is accepted.
    """
    query = db.query(TeamRequest)

    if filter_type == "sent":
        query = query.filter(TeamRequest.from_user_id == current_user.id)
    elif filter_type == "received":
        query = query.filter(TeamRequest.to_user_id == current_user.id)
    else:
        query = query.filter(
            or_(
                TeamRequest.from_user_id == current_user.id,
                TeamRequest.to_user_id == current_user.id,
            )
        )

    requests = query.order_by(TeamRequest.created_at.desc()).all()
    return [_format_team_request_response(req, current_user.id) for req in requests]


@router.patch("/{id}", response_model=TeamRequestResponse)
def update_team_request_status(
    id: int,
    payload: TeamRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Accept or decline a team collaboration request.
    Only the recipient (to_user_id) of the request is authorized to respond.
    """
    team_req = db.query(TeamRequest).filter(TeamRequest.id == id).first()
    if not team_req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team request was not found."
        )

    # Authorization check: only the recipient can accept or decline
    if team_req.to_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to respond to this team request."
        )

    team_req.status = payload.status
    db.commit()
    db.refresh(team_req)

    return _format_team_request_response(team_req, current_user.id)
