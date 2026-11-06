import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Opportunity, Skill, TeamPost, TeamRequest, User
from app.schemas.team_post import (
    TeamPostCreate,
    TeamPostUpdate,
    TeamPostResponse,
    TeamPostJoinRequest,
)
from app.schemas.team_request import TeamRequestResponse
from app.api.v1.team_requests import (
    _build_user_summary,
    _format_team_request_response,
    MAX_REQUESTS_PER_24H,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Team Posts"])

MAX_POSTS_PER_24H = 5


def _auto_close_expired_opportunity_posts(opportunity: Opportunity, db: Session) -> None:
    """Closes any open posts for an opportunity if its deadline has passed."""
    if not opportunity or not opportunity.deadline:
        return
    now_utc = datetime.now(timezone.utc)
    dl = opportunity.deadline if opportunity.deadline.tzinfo else opportunity.deadline.replace(tzinfo=timezone.utc)
    if dl < now_utc:
        open_posts = (
            db.query(TeamPost)
            .filter(TeamPost.opportunity_id == opportunity.id, TeamPost.status == "open")
            .all()
        )
        if open_posts:
            for p in open_posts:
                p.status = "closed"
            db.commit()


def _format_team_post_response(
    post: TeamPost,
    current_user: User,
    db: Session,
    include_requests: bool = False,
) -> TeamPostResponse:
    """Formats a TeamPost with match metrics, privacy-guarded creator info, and viewer state."""
    opp_title = post.opportunity.title if post.opportunity else f"Opportunity #{post.opportunity_id}"

    # Check if contact details for creator should be revealed
    # Contact is revealed ONLY if there is an accepted team request between current_user and creator
    is_creator = (post.user_id == current_user.id)
    is_contact_revealed = False
    if is_creator:
        is_contact_revealed = True
    else:
        accepted_req = (
            db.query(TeamRequest)
            .filter(
                TeamRequest.opportunity_id == post.opportunity_id,
                TeamRequest.status == "accepted",
                or_(
                    (TeamRequest.from_user_id == current_user.id) & (TeamRequest.to_user_id == post.user_id),
                    (TeamRequest.from_user_id == post.user_id) & (TeamRequest.to_user_id == current_user.id),
                ),
            )
            .first()
        )
        if accepted_req:
            is_contact_revealed = True

    creator_summary = _build_user_summary(post.user, is_contact_revealed=is_contact_revealed)

    # Calculate skill match relative to current user
    user_skills_lower = set()
    if current_user.profile and current_user.profile.student_skills:
        user_skills_lower = {
            ss.skill.name.lower()
            for ss in current_user.profile.student_skills
            if ss.skill
        }

    needed_skills = post.needed_skills or []
    matched = [s for s in needed_skills if s.lower() in user_skills_lower]
    match_count = len(matched)
    match_percentage = (
        round((match_count / len(needed_skills)) * 100, 1) if needed_skills else 0.0
    )

    # Check if current user has sent a request for this post or to this creator for this opp
    my_req = (
        db.query(TeamRequest)
        .filter(
            TeamRequest.from_user_id == current_user.id,
            TeamRequest.opportunity_id == post.opportunity_id,
            or_(
                TeamRequest.team_post_id == post.id,
                TeamRequest.to_user_id == post.user_id,
            ),
        )
        .order_by(TeamRequest.created_at.desc())
        .first()
    )

    has_requested = bool(my_req is not None)
    my_request_status = my_req.status if my_req else None
    my_request_id = my_req.id if my_req else None

    # Requests on this post
    requests_count = len(post.team_requests)
    formatted_requests = None
    if include_requests or is_creator:
        formatted_requests = [
            _format_team_request_response(r, current_user.id)
            for r in post.team_requests
        ]

    return TeamPostResponse(
        id=post.id,
        user_id=post.user_id,
        opportunity_id=post.opportunity_id,
        opportunity_title=opp_title,
        message=post.message,
        needed_skills=needed_skills,
        team_size_needed=post.team_size_needed,
        status=post.status,
        created_at=post.created_at,
        updated_at=post.updated_at,
        creator=creator_summary,
        matched_skills=matched,
        match_count=match_count,
        match_percentage=match_percentage,
        is_creator=is_creator,
        has_requested=has_requested,
        my_request_status=my_request_status,
        my_request_id=my_request_id,
        requests_count=requests_count,
        requests=formatted_requests,
    )


def _validate_skills_against_taxonomy(needed_skills: List[str], db: Session) -> List[str]:
    """Ensures each skill exists in the Skill taxonomy and returns canonical skill names."""
    if not needed_skills:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one needed skill must be specified."
        )

    all_db_skills = {s.name.lower(): s.name for s in db.query(Skill).all()}
    canonical_list = []
    invalid_skills = []

    for sk in needed_skills:
        sk_clean = sk.strip()
        if not sk_clean:
            continue
        canonical = all_db_skills.get(sk_clean.lower())
        if canonical:
            if canonical not in canonical_list:
                canonical_list.append(canonical)
        else:
            invalid_skills.append(sk_clean)

    if invalid_skills:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The following skills are not recognized in the skill taxonomy: {', '.join(invalid_skills)}"
        )

    return canonical_list


# =====================================================================
# Opportunity Scoped Endpoints: /api/opportunities/{id}/team-posts
# =====================================================================

@router.get("/opportunities/{id}/team-posts", response_model=List[TeamPostResponse])
def list_opportunity_team_posts(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List open team recruitment posts for an opportunity (Team Board).
    Includes skill match calculation against current user's skills.
    Auto-closes posts if the opportunity deadline has passed.
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == id).first()
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunity with ID {id} not found."
        )

    # 1. Auto-close if deadline passed
    _auto_close_expired_opportunity_posts(opportunity, db)

    now_utc = datetime.now(timezone.utc)
    dl = opportunity.deadline if (opportunity.deadline and opportunity.deadline.tzinfo) else (
        opportunity.deadline.replace(tzinfo=timezone.utc) if opportunity.deadline else None
    )
    if dl and dl < now_utc:
        # Event is past deadline, no open posts remain
        return []

    # 2. Query open posts
    posts = (
        db.query(TeamPost)
        .filter(TeamPost.opportunity_id == id, TeamPost.status == "open")
        .order_by(TeamPost.created_at.desc())
        .all()
    )

    return [_format_team_post_response(p, current_user, db) for p in posts]


@router.post("/opportunities/{id}/team-posts", response_model=TeamPostResponse, status_code=status.HTTP_201_CREATED)
def create_opportunity_team_post(
    id: int,
    payload: TeamPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new team post for an opportunity.
    Enforces:
    - Opportunity must not be expired.
    - Max 5 posts created per 24 hours (anti-spam).
    - Only 1 open post per user per event.
    - Skills must be validated from standard Skill taxonomy.
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == id).first()
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunity with ID {id} not found."
        )

    # 1. Expiry check
    now_utc = datetime.now(timezone.utc)
    dl = opportunity.deadline if (opportunity.deadline and opportunity.deadline.tzinfo) else (
        opportunity.deadline.replace(tzinfo=timezone.utc) if opportunity.deadline else None
    )
    if dl and dl < now_utc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create a team post for an event whose deadline has passed."
        )

    # 2. Daily anti-spam limit (max 5 posts per 24h)
    day_ago = now_utc - timedelta(hours=24)
    recent_posts_count = (
        db.query(TeamPost)
        .filter(TeamPost.user_id == current_user.id, TeamPost.created_at >= day_ago)
        .count()
    )
    if recent_posts_count >= MAX_POSTS_PER_24H:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily limit reached. You can create at most {MAX_POSTS_PER_24H} team posts in 24 hours."
        )

    # 3. Single open post per user per event check
    existing_open = (
        db.query(TeamPost)
        .filter(
            TeamPost.user_id == current_user.id,
            TeamPost.opportunity_id == id,
            TeamPost.status == "open",
        )
        .first()
    )
    if existing_open:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an open team post for this event. Please edit or close your existing post before creating a new one."
        )

    # 4. Taxonomy validation
    canonical_skills = _validate_skills_against_taxonomy(payload.needed_skills, db)

    # 5. Create TeamPost
    new_post = TeamPost(
        user_id=current_user.id,
        opportunity_id=id,
        message=payload.message.strip(),
        needed_skills=canonical_skills,
        team_size_needed=payload.team_size_needed,
        status="open",
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return _format_team_post_response(new_post, current_user, db, include_requests=True)


# =====================================================================
# Standalone Post Endpoints: /api/team-posts
# =====================================================================

@router.get("/team-posts/me", response_model=List[TeamPostResponse])
def get_my_team_posts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve all team posts created by the current student (both open and closed).
    Includes received team requests on each post.
    Auto-closes posts for events that have passed their deadline.
    """
    my_posts = (
        db.query(TeamPost)
        .filter(TeamPost.user_id == current_user.id)
        .order_by(TeamPost.created_at.desc())
        .all()
    )

    now_utc = datetime.now(timezone.utc)
    has_updates = False
    for p in my_posts:
        if p.status == "open" and p.opportunity and p.opportunity.deadline:
            dl = p.opportunity.deadline if p.opportunity.deadline.tzinfo else p.opportunity.deadline.replace(tzinfo=timezone.utc)
            if dl < now_utc:
                p.status = "closed"
                has_updates = True

    if has_updates:
        db.commit()

    return [_format_team_post_response(p, current_user, db, include_requests=True) for p in my_posts]


@router.patch("/team-posts/{id}", response_model=TeamPostResponse)
def edit_team_post(
    id: int,
    payload: TeamPostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Edit a team post. Only the creator of the post is authorized to modify it.
    """
    post = db.query(TeamPost).filter(TeamPost.id == id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team post was not found."
        )

    # Authorization check
    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to edit this team post."
        )

    if payload.message is not None:
        post.message = payload.message.strip()

    if payload.team_size_needed is not None:
        post.team_size_needed = payload.team_size_needed

    if payload.needed_skills is not None:
        post.needed_skills = _validate_skills_against_taxonomy(payload.needed_skills, db)

    if payload.status is not None:
        post.status = payload.status

    db.commit()
    db.refresh(post)

    return _format_team_post_response(post, current_user, db, include_requests=True)


@router.post("/team-posts/{id}/close", response_model=TeamPostResponse)
def close_team_post(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark a team post as closed. Only the creator can close it.
    """
    post = db.query(TeamPost).filter(TeamPost.id == id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team post was not found."
        )

    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to close this team post."
        )

    post.status = "closed"
    db.commit()
    db.refresh(post)

    return _format_team_post_response(post, current_user, db, include_requests=True)


@router.post("/team-posts/{id}/join", response_model=TeamRequestResponse, status_code=status.HTTP_201_CREATED)
def join_team_post(
    id: int,
    payload: TeamPostJoinRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a join request to a team post.
    Creates a TeamRequest linked to the post and the post creator.
    Enforces:
    - Creator cannot join their own post.
    - Post must be 'open'.
    - Opportunity deadline must not have passed.
    - Rate limit: max 10 requests per 24 hours.
    - Duplicate prevention: cannot send duplicate requests for the same event to the same creator.
    """
    post = db.query(TeamPost).filter(TeamPost.id == id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team post was not found."
        )

    # 1. Prevent self join
    if post.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot join your own team post."
        )

    # 2. Check post status
    if post.status != "open":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This team post is closed and no longer accepting join requests."
        )

    # 3. Check opportunity deadline
    now_utc = datetime.now(timezone.utc)
    if post.opportunity and post.opportunity.deadline:
        dl = post.opportunity.deadline if post.opportunity.deadline.tzinfo else post.opportunity.deadline.replace(tzinfo=timezone.utc)
        if dl < now_utc:
            post.status = "closed"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This event's deadline has passed."
            )

    # 4. Check daily request limit (max 10 requests in 24h)
    day_ago = now_utc - timedelta(hours=24)
    recent_requests_count = (
        db.query(TeamRequest)
        .filter(TeamRequest.from_user_id == current_user.id, TeamRequest.created_at >= day_ago)
        .count()
    )
    if recent_requests_count >= MAX_REQUESTS_PER_24H:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily limit reached. You can send at most {MAX_REQUESTS_PER_24H} team requests in 24 hours."
        )

    # 5. Duplicate check
    existing_req = (
        db.query(TeamRequest)
        .filter(
            TeamRequest.from_user_id == current_user.id,
            TeamRequest.to_user_id == post.user_id,
            TeamRequest.opportunity_id == post.opportunity_id,
        )
        .first()
    )
    if existing_req:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You have already sent a request to this user for this event (Status: {existing_req.status})."
        )

    # 6. Create TeamRequest linked to team_post
    msg_text = payload.message.strip() if payload.message else f"Hi, I would like to join your team for {post.opportunity.title}!"
    new_req = TeamRequest(
        from_user_id=current_user.id,
        to_user_id=post.user_id,
        opportunity_id=post.opportunity_id,
        team_post_id=post.id,
        status="pending",
        message=msg_text,
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)

    return _format_team_request_response(new_req, current_user.id)
