from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import or_, nullslast
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import Opportunity, EventSyncLog
from app.schemas.opportunity import OpportunityResponse
from app.services.events_sync import EventSyncEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("/sync", summary="Trigger external event synchronization")
async def trigger_events_sync(
    x_sync_token: Optional[str] = Header(None, alias="X-Sync-Token"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Protected synchronization endpoint that fetches hackathons and events
    from Smart India Hackathon, Unstop, Devfolio, MLH, etc.
    Requires header X-Sync-Token matching configured EVENTS_SYNC_TOKEN.
    """
    if not x_sync_token or x_sync_token.strip() != settings.EVENTS_SYNC_TOKEN:
        logger.warning("Unauthorized events sync attempt with invalid or missing X-Sync-Token.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Sync-Token header"
        )

    logger.info("Authorized events sync request initiated.")
    engine = EventSyncEngine()
    result = await engine.run_sync(db)
    return result


@router.get("/sync-status", summary="Get status and history of recent event synchronizations")
def get_sync_status(
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns recent sync run logs and last synchronization timestamp.
    """
    logs = (
        db.query(EventSyncLog)
        .order_by(EventSyncLog.synced_at.desc())
        .limit(limit)
        .all()
    )
    last_log = logs[0] if logs else None

    return {
        "last_synced_at": last_log.synced_at.isoformat() if last_log else None,
        "last_status": last_log.status if last_log else "never",
        "sync_history": [
            {
                "id": log.id,
                "synced_at": log.synced_at.isoformat(),
                "status": log.status,
                "new_events": log.new_events,
                "updated_events": log.updated_events,
                "expired_events": log.expired_events,
                "sources": log.details,
                "error": log.error_message
            }
            for log in logs
        ]
    }


@router.get("", response_model=List[OpportunityResponse], summary="List active and upcoming events")
def list_active_events(
    category: Optional[str] = None,
    mode: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Returns active, upcoming hackathons and events sorted chronologically by deadline.
    """
    now = datetime.now(timezone.utc)
    query = db.query(Opportunity).filter(
        Opportunity.is_active == True,
        or_(Opportunity.deadline == None, Opportunity.deadline >= now)
    )

    if category:
        query = query.filter(Opportunity.category.ilike(f"%{category}%"))

    if mode:
        query = query.filter(Opportunity.mode.ilike(f"%{mode}%"))

    events = query.order_by(nullslast(Opportunity.deadline.asc())).offset(skip).limit(limit).all()
    return events
