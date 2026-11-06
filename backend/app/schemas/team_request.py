from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TeammateCandidateResponse(BaseModel):
    user_id: int
    full_name: str
    college_name: Optional[str] = None
    degree: Optional[str] = None
    branch: Optional[str] = None
    year: Optional[int] = None
    skills: List[str] = []
    match_score: float
    complementary_skills: List[str] = []
    explanation: str
    request_status: Optional[str] = None  # None | "pending" | "accepted" | "declined"
    request_id: Optional[int] = None
    is_outgoing_request: Optional[bool] = None

    # Sensitive contact fields (STRICTLY masked/None unless request_status == "accepted")
    email: Optional[str] = None
    phone: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TeamUserSummary(BaseModel):
    user_id: int
    full_name: str
    college_name: Optional[str] = None
    degree: Optional[str] = None
    branch: Optional[str] = None
    year: Optional[int] = None
    skills: List[str] = []

    # Sensitive contact fields (STRICTLY masked/None unless request_status == "accepted")
    email: Optional[str] = None
    phone: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TeamRequestCreate(BaseModel):
    to_user_id: int
    opportunity_id: int
    message: Optional[str] = Field(None, max_length=1000)


class TeamRequestUpdate(BaseModel):
    status: str = Field(..., pattern="^(accepted|declined)$", description="Must be 'accepted' or 'declined'")


class TeamRequestResponse(BaseModel):
    id: int
    from_user_id: int
    to_user_id: int
    opportunity_id: int
    opportunity_title: str
    status: str
    message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    from_user: TeamUserSummary
    to_user: TeamUserSummary
    is_sender: bool = False

    model_config = ConfigDict(from_attributes=True)
