from datetime import datetime, timezone, timedelta
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Opportunity, EventSyncLog
from .base import BaseEventFetcher, NormalizedEvent
from .devfolio import DevfolioFetcher
from .unstop import UnstopFetcher
from .mlh import MLHFetcher
from .sih import SIHFetcher
from .hack2skill import Hack2skillFetcher

logger = logging.getLogger(__name__)


class EventSyncEngine:
    """
    Orchestrates event fetching from multiple configured sources,
    normalizes data, performs safe upserts into the Opportunity catalog,
    deactivates expired opportunities, and logs sync status.
    """

    AVAILABLE_FETCHERS = {
        "devfolio": DevfolioFetcher,
        "unstop": UnstopFetcher,
        "mlh": MLHFetcher,
        "sih": SIHFetcher,
        "hack2skill": Hack2skillFetcher,
    }

    def __init__(self, sources: Optional[List[str]] = None):
        if sources is None:
            # Parse configured sources from comma-separated string
            raw = getattr(settings, "EVENTS_SYNC_SOURCES", "devfolio,unstop")
            self.source_keys = [s.strip().lower() for s in raw.split(",") if s.strip()]
        else:
            self.source_keys = [s.strip().lower() for s in sources if s.strip()]

        self.fetchers: List[BaseEventFetcher] = []
        for key in self.source_keys:
            fetcher_cls = self.AVAILABLE_FETCHERS.get(key)
            if fetcher_cls:
                self.fetchers.append(fetcher_cls())
            else:
                logger.warning(f"Unknown event source '{key}' configured in settings.")

    @staticmethod
    def is_sync_needed(db: Session, max_age_hours: int = 6) -> bool:
        """
        Check if the last sync is older than max_age_hours or if no sync has ever run.
        """
        try:
            last_log = (
                db.query(EventSyncLog)
                .order_by(EventSyncLog.synced_at.desc())
                .first()
            )
            if not last_log:
                return True

            last_sync_time = last_log.synced_at
            if last_sync_time.tzinfo is None:
                last_sync_time = last_sync_time.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            return (now - last_sync_time) > timedelta(hours=max_age_hours)
        except Exception as exc:
            logger.warning(f"Could not determine last sync age: {exc}. Defaulting to needed.")
            return True

    async def run_sync(self, db: Session) -> Dict[str, Any]:
        """
        Executes full sync across all enabled fetchers.
        Updates DB with new/modified opportunities, marks expired events as inactive,
        and records a comprehensive sync log.
        """
        now = datetime.now(timezone.utc)
        results: Dict[str, Any] = {
            "synced_at": now.isoformat(),
            "status": "success",
            "new_events": 0,
            "updated_events": 0,
            "expired_events": 0,
            "sources": {}
        }

        all_normalized_events: List[NormalizedEvent] = []
        failed_sources = []

        # 1. Fetch from each source with isolated error handling
        for fetcher in self.fetchers:
            src_name = fetcher.source_name
            try:
                logger.info(f"Starting fetch for source: {src_name}...")
                events = await fetcher.fetch_events()
                results["sources"][src_name] = {
                    "status": "success",
                    "count": len(events)
                }
                all_normalized_events.extend(events)
            except Exception as src_err:
                logger.error(f"Source {src_name} failed during fetch: {src_err}", exc_info=True)
                results["sources"][src_name] = {
                    "status": "failed",
                    "error": str(src_err),
                    "count": 0
                }
                failed_sources.append(src_name)

        if failed_sources:
            if len(failed_sources) == len(self.fetchers):
                results["status"] = "failed"
            else:
                results["status"] = "partial"

        # 2. Upsert events into database
        new_count = 0
        updated_count = 0

        try:
            for norm_ev in all_normalized_events:
                opp_dict = norm_ev.to_opportunity_dict()

                # Find match by (source, external_id) or official_url
                existing_opp = None
                if norm_ev.external_id:
                    existing_opp = (
                        db.query(Opportunity)
                        .filter(
                            Opportunity.source == norm_ev.source,
                            Opportunity.external_id == str(norm_ev.external_id)
                        )
                        .first()
                    )

                if not existing_opp and norm_ev.official_url:
                    existing_opp = (
                        db.query(Opportunity)
                        .filter(Opportunity.official_url == norm_ev.official_url)
                        .first()
                    )

                if existing_opp:
                    # Update fields
                    existing_opp.title = opp_dict["title"]
                    existing_opp.organizer = opp_dict["organizer"]
                    existing_opp.category = opp_dict["category"]
                    existing_opp.description = opp_dict["description"]
                    existing_opp.required_skills = opp_dict["required_skills"]
                    existing_opp.deadline = opp_dict["deadline"]
                    existing_opp.start_date = opp_dict["start_date"]
                    existing_opp.mode = opp_dict["mode"]
                    existing_opp.location = opp_dict["location"]
                    existing_opp.official_url = opp_dict["official_url"]
                    existing_opp.external_id = opp_dict["external_id"]
                    existing_opp.prize_pool = opp_dict["prize_pool"]
                    existing_opp.is_active = opp_dict["is_active"]
                    if opp_dict["eligibility_criteria"]:
                        existing_opp.eligibility_criteria = opp_dict["eligibility_criteria"]
                    updated_count += 1
                else:
                    new_opp = Opportunity(**opp_dict)
                    db.add(new_opp)
                    new_count += 1

            # 3. Deactivate expired events (where deadline is specified and has passed)
            # Opportunities with deadline == None are treated as ongoing/open and remain active
            expired_query = (
                db.query(Opportunity)
                .filter(
                    Opportunity.is_active == True,
                    Opportunity.deadline.isnot(None),
                    Opportunity.deadline < now
                )
            )
            expired_count = expired_query.count()
            expired_query.update({"is_active": False}, synchronize_session=False)

            # Commit all changes
            db.commit()

            results["new_events"] = new_count
            results["updated_events"] = updated_count
            results["expired_events"] = expired_count

            logger.info(
                f"Sync completed successfully: {new_count} new, {updated_count} updated, {expired_count} expired."
            )

        except Exception as db_err:
            db.rollback()
            logger.error(f"Database error during event upsert: {db_err}", exc_info=True)
            results["status"] = "failed"
            results["error"] = str(db_err)

        # 4. Record EventSyncLog
        try:
            log_entry = EventSyncLog(
                status=results["status"],
                sources_attempted=",".join(self.source_keys),
                new_events=results["new_events"],
                updated_events=results["updated_events"],
                expired_events=results["expired_events"],
                details=results["sources"],
                error_message=results.get("error")
            )
            db.add(log_entry)
            db.commit()
        except Exception as log_err:
            db.rollback()
            logger.warning(f"Could not save sync log entry: {log_err}")

        return results
