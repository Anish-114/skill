from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User
    from .opportunity import Opportunity


class SavedOpportunity(Base):
    """
    SavedOpportunity model representing bookmarks and application tracking
    of an opportunity by a student.
    """
    __tablename__ = "saved_opportunities"

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
    
    # Tracking status: "saved", "applied", "in_progress", "shortlisted", "archived"
    status: Mapped[str] = mapped_column(
        String(50), 
        default="saved", 
        nullable=False, 
        index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="saved_opportunities")
    opportunity: Mapped["Opportunity"] = relationship("Opportunity", back_populates="saved_by_users", lazy="joined")

    __table_args__ = (
        UniqueConstraint("user_id", "opportunity_id", name="uq_user_opportunity_saved"),
    )

    def __repr__(self) -> str:
        return f"<SavedOpportunity(user_id={self.user_id}, opportunity_id={self.opportunity_id}, status='{self.status}')>"
