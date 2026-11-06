from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_student_profile
from app.db.session import get_db
from app.models import Opportunity, StudentProfile, User
from app.schemas.opportunity import OpportunityResponse
from app.schemas.recommendation import (
    OpportunityRecommendationResponse,
    RecommendationScoreBreakdown,
)
from app.services.recommendation_engine import calculate_recommendation_score

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("", response_model=List[OpportunityRecommendationResponse])
def get_personalized_recommendations(
    min_score: float = 0.0,
    category: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    profile: StudentProfile = Depends(get_current_student_profile)
):
    """
    Ranks all active opportunities tailored to the student's degree,
    skills, academic year, and interests using the hybrid AI scoring engine.
    """
    now = datetime.now(timezone.utc)
    query = db.query(Opportunity).filter(
        Opportunity.is_active == True,
        or_(Opportunity.deadline == None, Opportunity.deadline >= now)
    )
    if category and isinstance(category, str):
        query = query.filter(Opportunity.category.ilike(f"%{category}%"))

    opportunities = query.all()

    scored_results = []
    for opp in opportunities:
        rec = calculate_recommendation_score(profile=profile, opportunity=opp)
        final_score = rec["final_score"]

        if final_score < min_score:
            continue

        breakdown_data = rec["breakdown"]
        breakdown_schema = RecommendationScoreBreakdown(
            skill_match=breakdown_data["skill_match"],
            interest_match=breakdown_data["interest_match"],
            experience_match=breakdown_data["experience_match"],
            mode_match=breakdown_data["mode_match"],
            eligibility_confidence=breakdown_data["eligibility_confidence"]
        )

        opp_response = OpportunityResponse.model_validate(opp)

        scored_results.append(
            OpportunityRecommendationResponse(
                opportunity=opp_response,
                final_score=final_score,
                breakdown=breakdown_schema,
                explanation=rec["explanation"],
                eligibility_status=rec["eligibility"]["status"],
                matched_skills=rec["skill_gap"]["matched_skills"],
                missing_skills=rec["skill_gap"]["missing_skills"],
                readiness_score=rec["skill_gap"]["readiness_score"]
            )
        )

    # Sort descending by final recommendation score
    scored_results.sort(key=lambda x: x.final_score, reverse=True)

    return scored_results[:limit]
