import logging
from typing import List, Optional
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from app.models import Opportunity, StudentProfile, TeamRequest, User
from app.schemas.team_request import TeammateCandidateResponse
from app.services.skill_gap_engine import _skills_match, analyze_skill_gap

logger = logging.getLogger(__name__)


def find_teammates_for_opportunity(
    db: Session,
    current_user: User,
    opportunity: Opportunity
) -> List[TeammateCandidateResponse]:
    """
    Suggests teammates whose skills complement the current user's missing skills
    for a hackathon or technical competition.

    Privacy Rules:
    - Only users with `looking_for_team == True` and active accounts are included.
    - Current user is strictly excluded.
    - Contact details (email, phone, github_url, linkedin_url, portfolio_url) are
      STRICTLY masked (None) unless an accepted TeamRequest exists for this opportunity.
    """
    # 1. Gather current user's profile and skills
    curr_profile = current_user.profile
    curr_skills: List[str] = []
    if curr_profile and curr_profile.student_skills:
        curr_skills = [
            ss.skill.name for ss in curr_profile.student_skills if ss.skill
        ]

    # 2. Compute current user's missing skills for this opportunity
    req_skills: List[str] = opportunity.required_skills or []
    gap = analyze_skill_gap(curr_skills, req_skills)
    missing_skills: List[str] = gap["missing_skills"]

    # 3. Query all other active users with looking_for_team enabled
    candidate_profiles = (
        db.query(StudentProfile)
        .join(User, StudentProfile.user_id == User.id)
        .filter(
            StudentProfile.looking_for_team == True,
            StudentProfile.user_id != current_user.id,
            User.is_active == True,
        )
        .all()
    )

    if not candidate_profiles:
        return []

    # 4. Fetch existing team requests between current_user and candidate users for this opportunity
    candidate_user_ids = [p.user_id for p in candidate_profiles]
    existing_requests = (
        db.query(TeamRequest)
        .filter(
            TeamRequest.opportunity_id == opportunity.id,
            or_(
                and_(TeamRequest.from_user_id == current_user.id, TeamRequest.to_user_id.in_(candidate_user_ids)),
                and_(TeamRequest.to_user_id == current_user.id, TeamRequest.from_user_id.in_(candidate_user_ids)),
            )
        )
        .all()
    )

    # Map (other_user_id) -> TeamRequest
    request_map = {}
    for req in existing_requests:
        other_id = req.to_user_id if req.from_user_id == current_user.id else req.from_user_id
        request_map[other_id] = req

    candidates: List[TeammateCandidateResponse] = []

    for profile in candidate_profiles:
        cand_user = profile.user
        if not cand_user:
            continue

        cand_skills: List[str] = []
        if profile.student_skills:
            cand_skills = [
                ss.skill.name for ss in profile.student_skills if ss.skill
            ]

        # Calculate complementary coverage
        # Skills in missing_skills covered by this candidate
        covered_missing = [
            m for m in missing_skills
            if any(_skills_match(cs, m) for cs in cand_skills)
        ]

        # Skills in required_skills covered by this candidate
        covered_required = [
            r for r in req_skills
            if any(_skills_match(cs, r) for cs in cand_skills)
        ]

        # General skills candidate has that current user lacks
        other_new_skills = [
            cs for cs in cand_skills
            if not any(_skills_match(cs, us) for us in curr_skills)
        ]

        # Calculate complementary score (0 - 100)
        if missing_skills:
            coverage_ratio = len(covered_missing) / max(len(missing_skills), 1)
            score = round(coverage_ratio * 80.0 + min(20.0, len(other_new_skills) * 4.0), 1)
        elif req_skills:
            coverage_ratio = len(covered_required) / max(len(req_skills), 1)
            score = round(coverage_ratio * 70.0 + min(30.0, len(other_new_skills) * 5.0), 1)
        else:
            score = round(min(90.0, 50.0 + len(cand_skills) * 5.0), 1)

        score = max(5.0, min(100.0, score))

        # Explainable complementary message
        if covered_missing:
            joined_missing = " aur ".join(covered_missing[:2]) if len(covered_missing) <= 2 else f"{', '.join(covered_missing[:2])} aur {covered_missing[2]}"
            explanation = f"Ye teammate aapki missing skills ({joined_missing}) cover karta hai."
        elif covered_required:
            joined_req = ", ".join(covered_required[:3])
            explanation = f"Ye teammate is hackathon ke key skills ({joined_req}) mein proficient hai."
        elif cand_skills:
            joined_cand = ", ".join(cand_skills[:3])
            explanation = f"Ye teammate {joined_cand} skills ke saath aapki team ko complement karega."
        else:
            explanation = "Ye teammate collaborative hackathon experience ke liye tayyar hai."

        # Existing request status
        existing_req = request_map.get(cand_user.id)
        req_status = existing_req.status if existing_req else None
        req_id = existing_req.id if existing_req else None
        is_outgoing = (existing_req.from_user_id == current_user.id) if existing_req else None

        # Privacy gate: STRICTLY mask contact details unless accepted
        is_accepted = (req_status == "accepted")

        candidates.append(
            TeammateCandidateResponse(
                user_id=cand_user.id,
                full_name=cand_user.full_name,
                college_name=profile.college_name,
                degree=profile.degree,
                branch=profile.branch,
                year=profile.year,
                skills=cand_skills,
                match_score=score,
                complementary_skills=covered_missing if covered_missing else covered_required[:3],
                explanation=explanation,
                request_status=req_status,
                request_id=req_id,
                is_outgoing_request=is_outgoing,
                email=cand_user.email if is_accepted else None,
                phone=profile.phone if is_accepted else None,
                github_url=profile.github_url if is_accepted else None,
                linkedin_url=profile.linkedin_url if is_accepted else None,
                portfolio_url=profile.portfolio_url if is_accepted else None,
            )
        )

    # Rank candidates: prioritize candidates covering missing skills, then by match score
    candidates.sort(
        key=lambda c: (len(c.complementary_skills), c.match_score),
        reverse=True
    )

    return candidates
