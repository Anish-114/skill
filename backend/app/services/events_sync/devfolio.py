from datetime import datetime, timezone
import logging
from typing import List, Optional
import httpx

from .base import BaseEventFetcher, NormalizedEvent, parse_and_normalize_to_utc

logger = logging.getLogger(__name__)


class DevfolioFetcher(BaseEventFetcher):
    """
    Fetches hackathons from Devfolio's public JSON API.
    """
    API_URL = "https://api.devfolio.co/api/hackathons?filter=all&page=1&size=50"

    @property
    def source_name(self) -> str:
        return "Devfolio"

    def _parse_iso_date(self, date_str: Optional[str]) -> Optional[datetime]:
        return parse_and_normalize_to_utc(date_str)

    async def fetch_events(self) -> List[NormalizedEvent]:
        events: List[NormalizedEvent] = []
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                headers = {
                    "User-Agent": self.user_agent,
                    "Accept": "application/json"
                }
                resp = await client.get(self.API_URL, headers=headers)
                if resp.status_code != 200:
                    logger.warning(f"Devfolio API returned HTTP {resp.status_code}")
                    return events

                data = resp.json()
                items = data.get("result", [])

                for item in items:
                    name = item.get("name")
                    if not name:
                        continue

                    uuid = item.get("uuid") or item.get("slug")
                    slug = item.get("slug") or ""
                    setting = item.get("hackathon_setting") or {}
                    site = setting.get("site") or f"https://{slug}.devfolio.co"

                    starts_at = self._parse_iso_date(item.get("starts_at"))
                    # Deadline can be registration end date or event end date
                    reg_ends = self._parse_iso_date(setting.get("reg_ends_at"))
                    ends_at = self._parse_iso_date(item.get("ends_at"))
                    deadline = reg_ends or ends_at or starts_at

                    is_online = bool(item.get("is_online"))
                    mode = "Online" if is_online else "In-Person"

                    # Location
                    city = item.get("city")
                    country = item.get("country")
                    loc = item.get("location")
                    location_parts = [p for p in [city, country, loc] if p]
                    location_str = ", ".join(location_parts) if location_parts else ("Online" if is_online else "Various")

                    # Themes/tags
                    tags = []
                    for t in item.get("themes", []):
                        if isinstance(t, dict) and "name" in t:
                            t_name = t["name"].strip()
                            if t_name and t_name.lower() != "no restrictions":
                                tags.append(t_name)
                    if not tags:
                        tags = ["Full-Stack", "Web Development", "AI/ML"]

                    desc = item.get("desc") or f"{name} hosted on Devfolio. Collaborative hackathon bringing developers together."

                    # Determine if active based on deadline
                    now = datetime.now(timezone.utc)
                    is_active = True
                    if deadline and deadline < now:
                        is_active = False

                    event = NormalizedEvent(
                        title=name,
                        description=desc,
                        official_url=site,
                        source=self.source_name,
                        external_id=str(uuid),
                        start_date=starts_at,
                        end_date=deadline,
                        location=location_str,
                        mode=mode,
                        tags=tags,
                        organizer=item.get("hackathon_brand", {}).get("name") if isinstance(item.get("hackathon_brand"), dict) else "Devfolio Community",
                        category="Hackathon",
                        prize_pool=item.get("prizes_total") or "Prizes & Recognition",
                        is_active=is_active
                    )
                    events.append(event)

            logger.info(f"Fetched {len(events)} events from Devfolio.")
        except Exception as exc:
            logger.error(f"Error fetching Devfolio events: {exc}", exc_info=True)
            raise exc

        return events
