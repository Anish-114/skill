from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .saved_opportunity import SavedOpportunity


class Opportunity(Base):
    """
    Opportunity model representing hackathons, coding contests,
    internships, and technical challenges.
    """
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    organizer: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str] = mapped_column(
        String(100), 
        nullable=False, 
        index=True
    )  # Hackathon, Coding Contest, Hiring Challenge, Fellowship
    
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Required skills stored as JSON array of skill names, e.g. ["Python", "FastAPI", "React"]
    required_skills: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    
    # Granular eligibility rules stored as JSON:
    # {
    #   "degrees": ["B.Tech", "B.E.", "BCA", "MCA", "M.Tech"],
    #   "branches": ["Computer Science", "Information Technology", "AI/ML", "ALL"],
    #   "allowed_years": [1, 2, 3, 4],
    #   "min_cgpa": 6.5,
    #   "team_size": {"min": 2, "max": 4},
    #   "requires_female_member": False,
    #   "allowed_countries": ["India"],
    #   "notes": "Must be enrolled in a recognised college."
    # }
    eligibility_criteria: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    mode: Mapped[str] = mapped_column(String(50), nullable=False, default="Online", index=True)  # Online, Hybrid, In-Person
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    official_url: Mapped[str] = mapped_column(String(512), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # Smart India Hackathon, Unstop, Devfolio, MLH
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    prize_pool: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

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
    saved_by_users: Mapped[List["SavedOpportunity"]] = relationship(
        "SavedOpportunity",
        back_populates="opportunity",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Opportunity(id={self.id}, title='{self.title}', organizer='{self.organizer}', deadline={self.deadline})>"
