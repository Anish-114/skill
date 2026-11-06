from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .student_profile import StudentProfile


class Skill(Base):
    """
    Standardized skill entity (e.g., Python, Docker, NLP, PyTorch).
    Used for profile indexing and matching with opportunity requirements.
    """
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )

    # Relationships
    student_skills: Mapped[List["StudentSkill"]] = relationship(
        "StudentSkill",
        back_populates="skill",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Skill(id={self.id}, name='{self.name}', category='{self.category}')>"


class StudentSkill(Base):
    """
    Association model representing the many-to-many relationship
    between StudentProfile and Skill with proficiency metadata.
    """
    __tablename__ = "student_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("student_profiles.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    skill_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("skills.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Metadata
    proficiency_level: Mapped[str] = mapped_column(
        String(50), 
        default="Intermediate", 
        nullable=False
    )  # Beginner, Intermediate, Advanced, Expert
    years_of_experience: Mapped[Optional[float]] = mapped_column(Float, default=1.0, nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )

    # Relationships
    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="student_skills")
    skill: Mapped["Skill"] = relationship("Skill", back_populates="student_skills", lazy="joined")

    __table_args__ = (
        UniqueConstraint("student_profile_id", "skill_id", name="uq_student_profile_skill"),
    )

    def __repr__(self) -> str:
        return f"<StudentSkill(profile_id={self.student_profile_id}, skill_id={self.skill_id}, level='{self.proficiency_level}')>"
