from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_student_profile
from app.db.session import get_db
from app.models import Opportunity, StudentProfile
from app.schemas.evaluation import (
    FullEvaluationResponse,
    EligibilityCheckResult,
    SkillGapAnalysisResponse,
)
from app.services.eligibility_engine import evaluate_eligibility
from app.services.skill_gap_engine import analyze_skill_gap
from app.services.recommendation_engine import (
    calculate_recommendation_score,
    _extract_student_skill_names,
)

router = APIRouter(tags=["Evaluation"])


@router.get("/opportunities/{id}/evaluate", response_model=FullEvaluationResponse)
@router.get("/evaluation/{id}", response_model=FullEvaluationResponse, include_in_schema=False)
def evaluate_opportunity_for_student(
    id: int,
    db: Session = Depends(get_db),
    profile: StudentProfile = Depends(get_current_student_profile)
):
    """
    Evaluates both deterministic eligibility rules and skill gap readiness
    for the current student against a specific opportunity.
    Provides detailed passed/failed checks and an actionable study checklist.
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == id).first()
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunity with ID {id} not found."
        )

    # 1. Deterministic Eligibility Check
    eligibility_result = evaluate_eligibility(
        profile=profile,
        criteria=opportunity.eligibility_criteria or {}
    )

    # 2. Skill Gap Analysis
    student_skills = _extract_student_skill_names(profile)
    skill_gap_result = analyze_skill_gap(
        student_skills=student_skills,
        required_skills=opportunity.required_skills or []
    )

    # 3. Overall Recommendation Score & Explanation
    rec_result = calculate_recommendation_score(
        profile=profile,
        opportunity=opportunity
    )

    return FullEvaluationResponse(
        opportunity_id=opportunity.id,
        opportunity_title=opportunity.title,
        eligibility=EligibilityCheckResult(
            status=eligibility_result["status"],
            reasons=eligibility_result["reasons"],
            passed_checks=eligibility_result["passed_checks"],
            failed_checks=eligibility_result["failed_checks"],
            missing_data_checks=eligibility_result["missing_data_checks"]
        ),
        skill_gap=SkillGapAnalysisResponse(
            matched_skills=skill_gap_result["matched_skills"],
            missing_skills=skill_gap_result["missing_skills"],
            readiness_score=skill_gap_result["readiness_score"],
            preparation_checklist=skill_gap_result["preparation_checklist"]
        ),
        recommendation={
            "final_score": rec_result["final_score"],
            "breakdown": rec_result["breakdown"],
            "explanation": rec_result["explanation"]
        }
    )
