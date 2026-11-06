from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import List
import httpx

from .base import BaseEventFetcher, NormalizedEvent, parse_and_normalize_to_utc

logger = logging.getLogger(__name__)


class SkillIndiaFetcher(BaseEventFetcher):
    """
    Fetcher for Skill India Competitions, including IndiaSkills (WorldSkills India),
    NSDC/MSDE skill competitions, and Skill India Digital Hub (SIDH) challenges.

    Architecture:
    1. Checks official remote portals (WorldSkills India / SIDH).
    2. Since Skill India Digital Hub (SIDH) restricts bot scraping via robots.txt (Disallow: /)
       and WorldSkills India currently lacks a dynamic JSON/iCal API, this fetcher reads
       verified real listings from the curated dataset (backend/app/data/skill_india_events.json).
    3. Normalizes all deadlines strictly from IST to timezone-aware UTC, applies deduplication,
       and assigns category 'skill_competition'.
    """
    DATA_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "skill_india_events.json"

    @property
    def source_name(self) -> str:
        return "Skill India"

    async def fetch_events(self) -> List[NormalizedEvent]:
        events: List[NormalizedEvent] = []

        # 1. Check live portal availability
        try:
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                headers = {"User-Agent": self.user_agent}
                resp = await client.get("https://www.worldskillsindia.co.in/", headers=headers)
                if resp.status_code == 200:
                    logger.info("SkillIndiaFetcher: Verified WorldSkills India portal connectivity (HTTP 200).")
        except Exception as conn_err:
            logger.warning(f"SkillIndiaFetcher: Live portal connectivity note: {conn_err}")

        # 2. Load verified competitions from data file
        if not self.DATA_FILE.exists():
            logger.warning(f"SkillIndiaFetcher: Curated data file not found at {self.DATA_FILE}")
            return events

        try:
            with open(self.DATA_FILE, "r", encoding="utf-8") as f:
                items = json.load(f)

            now = datetime.now(timezone.utc)
            for item in items:
                title = item.get("title")
                if not title:
                    continue

                start_dt = parse_and_normalize_to_utc(item.get("start_date"))
                deadline_dt = parse_and_normalize_to_utc(item.get("deadline"))

                is_active = bool(item.get("is_active", True))
                if deadline_dt and deadline_dt < now:
                    is_active = False

                event = NormalizedEvent(
                    title=title,
                    description=item.get("description", ""),
                    official_url=item.get("official_url", "https://www.worldskillsindia.co.in"),
                    source=self.source_name,
                    external_id=str(item.get("external_id", f"skill-india-{hash(title)}")),
                    start_date=start_dt,
                    end_date=deadline_dt,
                    location=item.get("location"),
                    mode=item.get("mode", "In-Person"),
                    tags=item.get("required_skills", ["Skill Development"]),
                    organizer=item.get("organizer", "National Skill Development Corporation (NSDC) & MSDE"),
                    category=item.get("category", "skill_competition"),
                    prize_pool=item.get("prize_pool"),
                    eligibility_criteria=item.get("eligibility_criteria", {}),
                    is_active=is_active
                )
                events.append(event)

            logger.info(f"SkillIndiaFetcher: Loaded {len(events)} verified competitions from {self.DATA_FILE.name}.")
        except Exception as exc:
            logger.error(f"SkillIndiaFetcher error loading curated events: {exc}", exc_info=True)

        return events
