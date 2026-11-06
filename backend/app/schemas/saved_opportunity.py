from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.opportunity import OpportunityResponse


class SavedOpportunityCreate(BaseModel):
    status: Optional[str] = Field("saved", description="saved | applied | in_progress | shortlisted | selected | rejected | archived")
    notes: Optional[str] = None


class SavedOpportunityUpdate(BaseModel):
    status: Optional[str] = Field(None, description="saved | applied | in_progress | shortlisted | selected | rejected | archived")
    notes: Optional[str] = None


class SavedOpportunityResponse(BaseModel):
    id: int
    user_id: int
    opportunity_id: int
    status: str
    notes: Optional[str] = None
    saved_at: datetime
    opportunity: OpportunityResponse

    model_config = ConfigDict(from_attributes=True)
