from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class StudentSkillItem(BaseModel):
    skill_id: Optional[int] = None
    name: str = Field(..., description="Canonical or display skill name")
    proficiency_level: str = Field("Intermediate", description="Beginner | Intermediate | Advanced | Expert")
    years_of_experience: Optional[float] = Field(1.0, ge=0.0)
    verified: bool = False

    model_config = ConfigDict(from_attributes=True)


class StudentProfileBase(BaseModel):
    phone: Optional[str] = None
    college_name: Optional[str] = None
    degree: str = Field(..., description="e.g. B.Tech, BCA, M.Tech, MCA")
    branch: str = Field(..., description="e.g. Computer Science, Information Technology")
    year: int = Field(..., ge=1, le=6, description="Academic year (1st, 2nd, 3rd, 4th, 5th)")
    cgpa: Optional[float] = Field(None, ge=0.0, le=10.0)
    experience_level: str = Field("Beginner", description="Beginner | Intermediate | Advanced")
    raw_bio: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None


class StudentProfileCreate(StudentProfileBase):
    skills: List[StudentSkillItem] = []


class StudentProfileUpdate(BaseModel):
    phone: Optional[str] = None
    college_name: Optional[str] = None
    degree: Optional[str] = None
    branch: Optional[str] = None
    year: Optional[int] = Field(None, ge=1, le=6)
    cgpa: Optional[float] = Field(None, ge=0.0, le=10.0)
    experience_level: Optional[str] = None
    raw_bio: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    skills: Optional[List[StudentSkillItem]] = None


class StudentProfileResponse(StudentProfileBase):
    id: int
    user_id: int
    email: Optional[str] = None
    full_name: Optional[str] = None
    skills: List[StudentSkillItem] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SkillParseRequest(BaseModel):
    raw_bio: Optional[str] = None


class SkillParseResponse(BaseModel):
    extracted_skills: List[str]
    matched_taxonomy_skills: List[dict]
    unmatched_tokens: List[str] = []
    extracted_text: Optional[str] = None
