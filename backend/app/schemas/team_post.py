from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.team_request import TeamUserSummary, TeamRequestResponse


class TeamPostCreate(BaseModel):
    message: str = Field(..., min_length=5, max_length=300, description="Recruitment note or project pitch, max 300 characters")
    needed_skills: List[str] = Field(..., min_length=1, max_length=15, description="Skills needed from joining teammates")
    team_size_needed: int = Field(default=2, ge=1, le=10, description="Number of additional teammates needed")


class TeamPostUpdate(BaseModel):
    message: Optional[str] = Field(None, min_length=5, max_length=300)
    needed_skills: Optional[List[str]] = Field(None, min_length=1, max_length=15)
    team_size_needed: Optional[int] = Field(None, ge=1, le=10)
    status: Optional[str] = Field(None, pattern="^(open|closed)$")


class TeamPostJoinRequest(BaseModel):
    message: Optional[str] = Field(None, max_length=500, description="Optional note to the post creator")


class TeamPostResponse(BaseModel):
    id: int
    user_id: int
    opportunity_id: int
    opportunity_title: str
    message: str
    needed_skills: List[str]
    team_size_needed: int
    status: str
    created_at: datetime
    updated_at: datetime

    # Creator summary (privacy masked until accepted)
    creator: TeamUserSummary

    # Skill match metrics relative to the requesting viewer
    matched_skills: List[str] = []
    match_count: int = 0
    match_percentage: float = 0.0

    # Viewer status
    is_creator: bool = False
    has_requested: bool = False
    my_request_status: Optional[str] = None  # None, "pending", "accepted", "declined"
    my_request_id: Optional[int] = None

    # Requests received on this post (populated for creator)
    requests_count: int = 0
    requests: Optional[List[TeamRequestResponse]] = None

    model_config = ConfigDict(from_attributes=True)
