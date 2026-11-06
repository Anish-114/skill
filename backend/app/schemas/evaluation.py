from typing import Any, Dict, List
from pydantic import BaseModel, Field
from app.schemas.recommendation import RecommendationScoreBreakdown


class EligibilityCheckResult(BaseModel):
    status: str = Field(..., description="ELIGIBLE | NOT_ELIGIBLE | NEEDS_VERIFICATION")
    reasons: List[str]
    passed_checks: List[str]
    failed_checks: List[str]
    missing_data_checks: List[str]


class SkillGapAnalysisResponse(BaseModel):
    matched_skills: List[str]
    missing_skills: List[str]
    readiness_score: float = Field(..., ge=0.0, le=100.0)
    preparation_checklist: List[str]


class FullEvaluationResponse(BaseModel):
    opportunity_id: int
    opportunity_title: str
    eligibility: EligibilityCheckResult
    skill_gap: SkillGapAnalysisResponse
    recommendation: Dict[str, Any]
