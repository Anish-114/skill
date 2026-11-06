from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User
    from .opportunity import Opportunity
    from .team_post import TeamPost


class TeamRequest(Base):
    """
    TeamRequest model represents collaboration requests between students
    looking for teammates for hackathons/competitions.
    """
    __tablename__ = "team_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    from_user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    to_user_id: Mapped[int] = mapped_column(
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
    team_post_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("team_posts.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), 
        default="pending", 
        nullable=False, 
        index=True
    )  # pending, accepted, declined
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
    from_user: Mapped["User"] = relationship("User", foreign_keys=[from_user_id])
    to_user: Mapped["User"] = relationship("User", foreign_keys=[to_user_id])
    opportunity: Mapped["Opportunity"] = relationship("Opportunity")
    team_post: Mapped[Optional["TeamPost"]] = relationship("TeamPost", back_populates="team_requests")

    __table_args__ = (
        UniqueConstraint("from_user_id", "to_user_id", "opportunity_id", name="uq_team_request_from_to_opp"),
    )

    def __repr__(self) -> str:
        return f"<TeamRequest(id={self.id}, from={self.from_user_id}, to={self.to_user_id}, opp={self.opportunity_id}, status='{self.status}')>"
