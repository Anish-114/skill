from datetime import datetime, timezone
import logging
import re
from typing import List
from bs4 import BeautifulSoup
import httpx

from .base import BaseEventFetcher, NormalizedEvent

logger = logging.getLogger(__name__)


class SIHFetcher(BaseEventFetcher):
    """
    Fetches official Smart India Hackathon editions, problem statements,
    and timelines directly from sih.gov.in.
    """
    PORTAL_URL = "https://sih.gov.in/"

    @property
    def source_name(self) -> str:
        return "Smart India Hackathon"

    async def fetch_events(self) -> List[NormalizedEvent]:
        events: List[NormalizedEvent] = []

        if not self.can_fetch(self.PORTAL_URL):
            logger.info("Robots.txt disallows scraping SIH portal; skipping.")
            return events

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                headers = {
                    "User-Agent": self.user_agent,
                    "Accept": "text/html,application/xhtml+xml"
                }
                resp = await client.get(self.PORTAL_URL, headers=headers)
                if resp.status_code != 200:
                    logger.warning(f"SIH portal returned HTTP {resp.status_code}")
                    return events

                soup = BeautifulSoup(resp.text, "html.parser")

                # Detect latest mentioned years/editions on the portal
                text_content = soup.get_text()
                years = [int(y) for y in re.findall(r"Smart India Hackathon\s+(202[4-7])", text_content, re.IGNORECASE)]
                current_year = max(years) if years else datetime.now().year

                # Extract themes from the homepage
                themes: List[str] = []
                for theme_el in soup.find_all(["h4", "h5", "a", "strong"]):
                    t_text = theme_el.get_text(strip=True)
                    if any(kw in t_text.lower() for kw in ["smart automation", "medtech", "clean & green", "blockchain", "robotics", "agriculture"]):
                        cleaned_t = t_text.split("Ideas")[0].strip()
                        if cleaned_t and cleaned_t not in themes and len(cleaned_t) < 40:
                            themes.append(cleaned_t)

                if not themes:
                    themes = [
                        "Smart Automation",
                        "Clean & Green Technology",
                        "Robotics and Drones",
                        "Blockchain & Cybersecurity",
                        "MedTech / HealthTech",
                        "Agriculture & Rural Development",
                        "Smart Education",
                        "Space Technology"
                    ]

                # Check problem statements link
                ps_link = "https://sih.gov.in"
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if "ps" in href.lower() or "problem" in href.lower():
                        ps_link = href if href.startswith("http") else f"https://sih.gov.in{href}"
                        break

                # 1. Senior Edition (Software)
                events.append(
                    NormalizedEvent(
                        title=f"Smart India Hackathon {current_year} - Software Edition",
                        description=(
                            f"Smart India Hackathon {current_year} is a nationwide initiative by Ministry of Education's "
                            "Innovation Cell (MIC) & AICTE to provide students a platform to solve pressing problems of "
                            "Central Ministries, Departments, State Governments, and Industry partners."
                        ),
                        official_url=ps_link,
                        source=self.source_name,
                        external_id=f"sih-{current_year}-software",
                        start_date=datetime(current_year, 8, 1, tzinfo=timezone.utc),
                        end_date=datetime(current_year, 12, 25, 23, 59, tzinfo=timezone.utc),
                        location="Grand Finale Nodal Centers Across India",
                        mode="Hybrid",
                        tags=themes[:6],
                        organizer="Ministry of Education (MoE) & AICTE",
                        category="Hackathon",
                        prize_pool="₹1,00,000 per Problem Statement (Multi-Crore Prize Pool)",
                        eligibility_criteria={
                            "degrees": ["B.Tech", "B.E.", "BCA", "MCA", "M.Tech", "M.Sc", "Any Degree"],
                            "branches": ["ALL"],
                            "allowed_years": [1, 2, 3, 4],
                            "team_size": {"min": 6, "max": 6},
                            "requires_female_member": True,
                            "allowed_countries": ["India"],
                            "notes": "College SPOC nomination and 6-member team with at least one female teammate required."
                        },
                        is_active=True
                    )
                )

                # 2. Senior Edition (Hardware)
                events.append(
                    NormalizedEvent(
                        title=f"Smart India Hackathon {current_year} - Hardware Edition",
                        description=(
                            f"Hardware edition of Smart India Hackathon {current_year}. Focused on physical prototypes, "
                            "IoT devices, embedded systems, drones, robotics, and clean technology challenges."
                        ),
                        official_url="https://sih.gov.in",
                        source=self.source_name,
                        external_id=f"sih-{current_year}-hardware",
                        start_date=datetime(current_year, 8, 1, tzinfo=timezone.utc),
                        end_date=datetime(current_year, 12, 25, 23, 59, tzinfo=timezone.utc),
                        location="Designated Nodal Centers Across India",
                        mode="In-Person",
                        tags=["Embedded Systems", "Robotics", "IoT", "Clean Tech", "Hardware Prototyping"],
                        organizer="Ministry of Education (MoE) & AICTE",
                        category="Hackathon",
                        prize_pool="₹1,00,000 per Problem Statement",
                        eligibility_criteria={
                            "degrees": ["B.Tech", "B.E.", "M.Tech", "Diploma"],
                            "team_size": {"min": 6, "max": 6},
                            "requires_female_member": True,
                            "notes": "Must produce functional hardware prototype."
                        },
                        is_active=True
                    )
                )

            logger.info(f"Fetched {len(events)} events from Smart India Hackathon.")
        except Exception as exc:
            logger.error(f"Error fetching SIH events: {exc}", exc_info=True)
            raise exc

        return events
