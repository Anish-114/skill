from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class OpportunityBase(BaseModel):
    title: str = Field(..., description="Opportunity title")
    organizer: str = Field(..., description="Host institution / company / government body")
    category: str = Field(..., description="Hackathon | Coding Contest | Hiring Challenge | Fellowship")
    description: str
    required_skills: List[str] = Field(default_factory=list)
    eligibility_criteria: Dict[str, Any] = Field(default_factory=dict)
    deadline: datetime
    start_date: Optional[datetime] = None
    mode: str = Field("Online", description="Online | Hybrid | In-Person")
    location: Optional[str] = None
    official_url: str
    source: str = Field("Unstop", description="Smart India Hackathon | Devfolio | Unstop | MLH")
    external_id: Optional[str] = None
    prize_pool: Optional[str] = None
    is_active: bool = True


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityUpdate(BaseModel):
    title: Optional[str] = None
    organizer: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    eligibility_criteria: Optional[Dict[str, Any]] = None
    deadline: Optional[datetime] = None
    start_date: Optional[datetime] = None
    mode: Optional[str] = None
    location: Optional[str] = None
    official_url: Optional[str] = None
    source: Optional[str] = None
    external_id: Optional[str] = None
    prize_pool: Optional[str] = None
    is_active: Optional[bool] = None


class OpportunityResponse(OpportunityBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OpportunityDetailResponse(OpportunityResponse):
    is_saved: bool = False
    saved_status: Optional[str] = None
    saved_notes: Optional[str] = None


class OpportunityFilterParams(BaseModel):
    category: Optional[str] = None
    mode: Optional[str] = None
    min_deadline: Optional[datetime] = None
    is_active: Optional[bool] = True
    search: Optional[str] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)
