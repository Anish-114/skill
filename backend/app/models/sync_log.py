from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import DateTime, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class EventSyncLog(Base):
    """
    Log model tracking every synchronization execution for external events.
    """
    __tablename__ = "event_sync_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="success")  # success, partial, failed
    sources_attempted: Mapped[str] = mapped_column(String(255), nullable=False)
    new_events: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_events: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expired_events: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<EventSyncLog(id={self.id}, status='{self.status}', synced_at={self.synced_at}, new={self.new_events})>"
