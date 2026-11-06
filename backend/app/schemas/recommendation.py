from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.opportunity import OpportunityResponse


class RecommendationScoreBreakdown(BaseModel):
    skill_match: float = Field(..., ge=0.0, le=100.0, description="Readiness score based on required vs student skills")
    interest_match: float = Field(..., ge=0.0, le=100.0, description="Semantic vector similarity between profile and opportunity")
    experience_match: float = Field(..., ge=0.0, le=100.0, description="Experience level and year compatibility")
    mode_match: float = Field(..., ge=0.0, le=100.0, description="Mode accessibility (Online/Hybrid/In-Person)")
    eligibility_confidence: float = Field(..., ge=0.0, le=100.0, description="100.0 for ELIGIBLE, 50.0 for NEEDS_VERIFICATION, 0.0 for NOT_ELIGIBLE")


class OpportunityRecommendationResponse(BaseModel):
    opportunity: OpportunityResponse
    final_score: float = Field(..., ge=0.0, le=100.0, description="Weighted composite match score")
    breakdown: RecommendationScoreBreakdown
    explanation: str = Field(..., description="Personalized natural language explanation of why this matches")
    eligibility_status: str = Field(..., description="ELIGIBLE | NOT_ELIGIBLE | NEEDS_VERIFICATION")
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    readiness_score: float = Field(..., ge=0.0, le=100.0)
