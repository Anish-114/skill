from datetime import datetime
import logging
from typing import List
from bs4 import BeautifulSoup
import httpx

from .base import BaseEventFetcher, NormalizedEvent

logger = logging.getLogger(__name__)


class Hack2skillFetcher(BaseEventFetcher):
    """
    Fetcher for Hack2skill events.
    Note: Hack2skill's catalog is rendered as a client-side JavaScript Single Page Application (SPA)
    without an open public JSON API or SSR HTML. This fetcher attempts to detect any server-rendered
    events and gracefully reports if none are exposed.
    """
    URL = "https://hack2skill.com/hackathons"

    @property
    def source_name(self) -> str:
        return "Hack2skill"

    async def fetch_events(self) -> List[NormalizedEvent]:
        events: List[NormalizedEvent] = []

        if not self.can_fetch(self.URL):
            logger.info("Robots.txt disallows scraping Hack2skill; skipping.")
            return events

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                headers = {
                    "User-Agent": self.user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/json"
                }
                resp = await client.get(self.URL, headers=headers)
                if resp.status_code != 200:
                    logger.warning(f"Hack2skill returned HTTP {resp.status_code}")
                    return events

                soup = BeautifulSoup(resp.text, "html.parser")
                # Look for event cards or schema tags
                cards = soup.select(".hackathon-card, [data-event], .event-card")
                if not cards:
                    logger.info("Hack2skill does not render static HTML event cards (client-side SPA). Skipping source gracefully.")
                    return events

                # If static cards ever appear, parse them here
                for c in cards:
                    title_el = c.select_one("h3, h4, .title")
                    if title_el:
                        title = title_el.get_text(strip=True)
                        link_el = c.select_one("a[href]")
                        link = link_el.get("href") if link_el else "https://hack2skill.com"
                        events.append(
                            NormalizedEvent(
                                title=title,
                                description=f"{title} on Hack2skill platform.",
                                official_url=link,
                                source=self.source_name,
                                external_id=link,
                                category="Hackathon"
                            )
                        )

            logger.info(f"Fetched {len(events)} events from Hack2skill.")
        except Exception as exc:
            logger.warning(f"Could not fetch Hack2skill events (non-fatal): {exc}")

        return events
