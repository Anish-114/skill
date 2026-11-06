from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User
    from .skill import StudentSkill


class StudentProfile(Base):
    """
    StudentProfile model storing academic, personal, and professional
    background for recommendation and eligibility filtering.
    """
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        unique=True, 
        nullable=False, 
        index=True
    )
    
    # Personal & Academic Details
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    college_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    degree: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    branch: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # 1st, 2nd, 3rd, 4th, 5th
    cgpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Technical background
    experience_level: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        default="Beginner", 
        index=True
    )  # Beginner, Intermediate, Advanced
    raw_bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Profiles / Portfolios
    github_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Teammate Matching Opt-In
    looking_for_team: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profile")
    
    student_skills: Mapped[List["StudentSkill"]] = relationship(
        "StudentSkill",
        back_populates="student_profile",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<StudentProfile(id={self.id}, user_id={self.user_id}, degree='{self.degree}', branch='{self.branch}', year={self.year})>"
