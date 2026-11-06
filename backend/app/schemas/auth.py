from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.student_profile import StudentProfileResponse


class UserRegisterRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=4, description="Password")
    full_name: str = Field(..., min_length=1, description="User full name")
    degree: Optional[str] = "B.Tech"
    branch: Optional[str] = "Computer Science"
    year: Optional[int] = Field(1, ge=1, le=6)
    college_name: Optional[str] = None
    experience_level: Optional[str] = "Beginner"


class UserLoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    profile: Optional[StudentProfileResponse] = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
