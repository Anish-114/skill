from datetime import datetime, timezone
import hashlib
import logging
from typing import List, Optional
from bs4 import BeautifulSoup
import httpx

from .base import BaseEventFetcher, NormalizedEvent

logger = logging.getLogger(__name__)


class MLHFetcher(BaseEventFetcher):
    """
    Fetches official student hackathons from Major League Hacking (MLH)
    by parsing standard Schema.org Event microdata.
    """
    SEASONS = ["2025", "2026"]

    @property
    def source_name(self) -> str:
        return "Major League Hacking (MLH)"

    def _parse_iso_date(self, date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            clean_str = date_str.replace("Z", "+00:00")
            return datetime.fromisoformat(clean_str)
        except Exception:
            return None

    async def fetch_events(self) -> List[NormalizedEvent]:
        events: List[NormalizedEvent] = []
        seen_urls = set()

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml"
            }

            for season in self.SEASONS:
                url = f"https://mlh.io/seasons/{season}/events"
                if not self.can_fetch(url):
                    logger.info(f"Robots.txt disallows scraping {url}; skipping.")
                    continue

                try:
                    resp = await client.get(url, headers=headers)
                    if resp.status_code != 200:
                        logger.warning(f"MLH {url} returned HTTP {resp.status_code}")
                        continue

                    soup = BeautifulSoup(resp.text, "html.parser")
                    event_elements = soup.find_all(attrs={"itemtype": lambda v: v and "Event" in v})

                    for el in event_elements:
                        # Extract official URL
                        url_meta = el.find("meta", attrs={"itemprop": "url"})
                        event_url = url_meta.get("content") if url_meta else el.get("href")
                        if not event_url or event_url in seen_urls:
                            continue
                        seen_urls.add(event_url)

                        # Extract name
                        name_el = el.find(attrs={"itemprop": "name"}) or el.find(["h3", "h4"])
                        title = name_el.get_text(strip=True) if name_el else None
                        if not title:
                            # Fallback to card text
                            text_lines = [l.strip() for l in el.get_text(separator="\n").split("\n") if l.strip()]
                            title = text_lines[0] if text_lines else "MLH Hackathon"

                        # Extract start and end dates
                        start_meta = el.find("meta", attrs={"itemprop": "startDate"})
                        end_meta = el.find("meta", attrs={"itemprop": "endDate"})
                        start_dt = self._parse_iso_date(start_meta.get("content") if start_meta else None)
                        end_dt = self._parse_iso_date(end_meta.get("content") if end_meta else None)
                        deadline = end_dt or start_dt

                        # Extract Attendance Mode
                        mode_meta = el.find("meta", attrs={"itemprop": "eventAttendanceMode"})
                        mode_str = mode_meta.get("content", "") if mode_meta else ""
                        card_text = el.get_text(separator=" ", strip=True).lower()
                        if "online" in mode_str.lower() or "online" in card_text or "digital" in card_text:
                            mode = "Online"
                        elif "mixed" in mode_str.lower() or "hybrid" in card_text:
                            mode = "Hybrid"
                        else:
                            mode = "In-Person"

                        # Location
                        loc_name_el = el.find(attrs={"itemprop": "location"})
                        loc_str = loc_name_el.get_text(strip=True) if loc_name_el else None
                        if not loc_str:
                            loc_str = "Global / North America" if mode != "Online" else "Online"

                        # External ID: hash from URL or slug
                        external_id = hashlib.md5(event_url.encode()).hexdigest()[:16]

                        # Description
                        desc = f"{title} — official Major League Hacking (MLH) Member Hackathon for student developers and innovators."

                        now = datetime.now(timezone.utc)
                        is_active = True
                        if deadline and deadline < now:
                            is_active = False

                        event = NormalizedEvent(
                            title=title,
                            description=desc,
                            official_url=event_url,
                            source=self.source_name,
                            external_id=external_id,
                            start_date=start_dt,
                            end_date=deadline,
                            location=loc_str,
                            mode=mode,
                            tags=["Hackathon", "MLH", "Rapid Prototyping", "Full-Stack"],
                            organizer="Major League Hacking (MLH)",
                            category="Hackathon",
                            prize_pool="Sponsor Swag & Category Prizes",
                            eligibility_criteria={
                                "degrees": ["Undergraduate", "Graduate", "High School", "Any"],
                                "notes": "Must adhere to the MLH Code of Conduct."
                            },
                            is_active=is_active
                        )
                        events.append(event)

                except Exception as season_err:
                    logger.warning(f"Failed to fetch MLH season {season}: {season_err}")

            logger.info(f"Fetched {len(events)} events from MLH.")
        return events
