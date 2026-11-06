from typing import Any, Dict, List, Optional
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


class LearningResourceItem(BaseModel):
    title: str
    url: str
    type: str  # docs | course | video
    free: bool = True
    estimated_hours: float = 4.0


class RoadmapMilestone(BaseModel):
    skill: str
    priority: int
    estimated_hours: float
    duration_label: str
    resources: List[LearningResourceItem] = []


class LearningRoadmapResponse(BaseModel):
    is_feasible: bool
    warning_message: Optional[str] = None
    total_estimated_hours: float
    estimated_duration: str
    days_until_deadline: Optional[float] = None
    recommended_focus_skills: List[str] = []
    milestones: List[RoadmapMilestone] = []


class FullEvaluationResponse(BaseModel):
    opportunity_id: int
    opportunity_title: str
    eligibility: EligibilityCheckResult
    skill_gap: SkillGapAnalysisResponse
    recommendation: Dict[str, Any]
    roadmap: Optional[LearningRoadmapResponse] = None
