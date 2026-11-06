from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User
    from .opportunity import Opportunity
    from .team_request import TeamRequest


class TeamPost(Base):
    """
    TeamPost model represents a recruitment post created by a student
    looking for teammates for a specific hackathon/opportunity.
    """
    __tablename__ = "team_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    opportunity_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("opportunities.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    message: Mapped[str] = mapped_column(String(300), nullable=False)
    needed_skills: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    team_size_needed: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False, index=True)  # open, closed

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
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    opportunity: Mapped["Opportunity"] = relationship("Opportunity")
    team_requests: Mapped[List["TeamRequest"]] = relationship(
        "TeamRequest", 
        back_populates="team_post", 
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<TeamPost(id={self.id}, user={self.user_id}, opp={self.opportunity_id}, status='{self.status}')>"
