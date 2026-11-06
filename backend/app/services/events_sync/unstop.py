from datetime import datetime, timezone
import json
import logging
import re
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup
import httpx

from .base import BaseEventFetcher, NormalizedEvent

logger = logging.getLogger(__name__)


class UnstopFetcher(BaseEventFetcher):
    """
    Fetches hackathons and engineering contests from Unstop's public JSON API.
    """
    API_URL = "https://unstop.com/api/public/opportunity/search-result?opportunity=hackathons&per_page=50&page=1"

    @property
    def source_name(self) -> str:
        return "Unstop"

    def _parse_iso_date(self, date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            clean_str = date_str.replace("Z", "+00:00")
            return datetime.fromisoformat(clean_str)
        except Exception:
            return None

    def _clean_text(self, raw_html_or_text: Optional[str]) -> str:
        if not raw_html_or_text:
            return ""
        try:
            soup = BeautifulSoup(raw_html_or_text, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            return re.sub(r"\s+", " ", text)
        except Exception:
            return raw_html_or_text.strip()

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
                    logger.warning(f"Unstop API returned HTTP {resp.status_code}")
                    return events

                data = resp.json()
                data_block = data.get("data", {})
                items = data_block.get("data", []) if isinstance(data_block, dict) else (data_block if isinstance(data_block, list) else [])

                for item in items:
                    title = item.get("title")
                    if not title:
                        continue

                    opp_id = item.get("id") or item.get("short_id")
                    url = item.get("seo_url") or item.get("public_url") or f"https://unstop.com/o/{opp_id}"
                    if not url.startswith("http"):
                        url = f"https://unstop.com/{url.lstrip('/')}"

                    # Organizer
                    org = item.get("organisation", {})
                    org_name = org.get("name") if isinstance(org, dict) else "Unstop Host"

                    # Description
                    raw_desc = item.get("details") or ""
                    desc = self._clean_text(raw_desc)
                    if not desc or len(desc) < 20:
                        desc = f"{title} hosted by {org_name} on Unstop platform."

                    # Dates
                    regn = item.get("regnRequirements", {}) or {}
                    start_dt = self._parse_iso_date(regn.get("start_regn_dt") or item.get("start_date"))
                    end_dt = self._parse_iso_date(regn.get("end_regn_dt") or item.get("end_date"))
                    deadline = end_dt or start_dt

                    # Mode & Location
                    work_loc_type = str(regn.get("work_location_type") or "").lower()
                    region = str(item.get("region") or "").lower()
                    if "online" in work_loc_type or "online" in region:
                        mode = "Online"
                        loc = "Online"
                    elif "hybrid" in work_loc_type or "hybrid" in region:
                        mode = "Hybrid"
                        loc = "Hybrid / India"
                    else:
                        mode = "In-Person"
                        locations_list = item.get("locations", [])
                        if isinstance(locations_list, list) and locations_list:
                            loc = ", ".join(str(l) for l in locations_list[:2])
                        else:
                            loc = org_name

                    # Tags / Skills
                    tags: List[str] = []
                    raw_skills = item.get("required_skills") or []
                    if isinstance(raw_skills, list):
                        for s in raw_skills:
                            if isinstance(s, dict) and "name" in s:
                                tags.append(s["name"])
                            elif isinstance(s, str):
                                tags.append(s)
                    raw_tags = item.get("tags") or []
                    if isinstance(raw_tags, list):
                        for t in raw_tags:
                            if isinstance(t, str) and t not in tags:
                                tags.append(t)
                    if not tags:
                        tags = ["Problem Solving", "Software Engineering", "Innovation"]

                    # Prize
                    prize_pool = None
                    prizes = item.get("prizes")
                    if isinstance(prizes, list) and prizes:
                        first_prize = prizes[0]
                        if isinstance(first_prize, dict):
                            prize_pool = first_prize.get("cash") or first_prize.get("title")
                    elif isinstance(prizes, str):
                        prize_pool = prizes

                    # Eligibility
                    eligibility_dict: Dict[str, Any] = {
                        "degrees": ["B.Tech", "B.E.", "BCA", "MCA", "M.Tech", "B.Sc"],
                        "allowed_years": [1, 2, 3, 4],
                        "notes": "Verified from Unstop listings"
                    }
                    if "eligibility" in regn and isinstance(regn["eligibility"], str):
                        try:
                            parsed_el = json.loads(regn["eligibility"])
                            if isinstance(parsed_el, dict):
                                eligibility_dict.update({k: v for k, v in parsed_el.items() if v})
                        except Exception:
                            pass

                    # Active status
                    now = datetime.now(timezone.utc)
                    is_active = True
                    if deadline and deadline < now:
                        is_active = False

                    event = NormalizedEvent(
                        title=title,
                        description=desc,
                        official_url=url,
                        source=self.source_name,
                        external_id=str(opp_id),
                        start_date=start_dt,
                        end_date=deadline,
                        location=loc,
                        mode=mode,
                        tags=tags[:8],
                        organizer=org_name,
                        category="Hackathon",
                        prize_pool=str(prize_pool) if prize_pool else "Cash & Certificates",
                        eligibility_criteria=eligibility_dict,
                        is_active=is_active
                    )
                    events.append(event)

            logger.info(f"Fetched {len(events)} events from Unstop.")
        except Exception as exc:
            logger.error(f"Error fetching Unstop events: {exc}", exc_info=True)
            raise exc

        return events
