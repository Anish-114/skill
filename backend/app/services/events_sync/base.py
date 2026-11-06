import abc
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import urllib.robotparser
import urllib.parse
import zoneinfo
import httpx

logger = logging.getLogger(__name__)

# Default timezone for naive datetimes from Indian sources is Asia/Kolkata (IST: UTC+05:30)
IST = zoneinfo.ZoneInfo("Asia/Kolkata")


def parse_and_normalize_to_utc(val: Any) -> Optional[datetime]:
    """
    Parses and normalizes any datetime input into a timezone-aware UTC datetime.
    Rules:
    1. If source provides timezone info (Z, +05:30, -04:00), respect it and convert to UTC.
    2. If source provides naive datetime (no timezone), assume Asia/Kolkata (IST), then convert to UTC.
    3. Handles ISO strings, timestamps, and standard string formats.
    """
    if val is None:
        return None

    if isinstance(val, (int, float)):
        # Handle millisecond vs second timestamps
        ts = val / 1000.0 if val > 1e11 else float(val)
        return datetime.fromtimestamp(ts, tz=timezone.utc)

    if isinstance(val, str):
        val = val.strip()
        if not val:
            return None
        # Handle trailing Z or z
        if val.endswith("Z") or val.endswith("z"):
            val = val[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(val)
        except ValueError:
            dt = None
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    dt = datetime.strptime(val, fmt)
                    break
                except ValueError:
                    continue
            if dt is None:
                return None
    elif isinstance(val, datetime):
        dt = val
    else:
        return None

    if dt.tzinfo is None:
        # Naive datetime: assume Asia/Kolkata (IST), then convert to UTC
        dt = dt.replace(tzinfo=IST).astimezone(timezone.utc)
    else:
        # Timezone-aware: convert to UTC
        dt = dt.astimezone(timezone.utc)

    return dt


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensures a datetime object is explicitly UTC-aware."""
    return parse_and_normalize_to_utc(dt)


@dataclass
class NormalizedEvent:
    """
    Standardized event data structure mapped to Opportunity schema.
    """
    title: str
    description: str
    official_url: str
    source: str
    external_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None  # Maps to opportunity.deadline
    location: Optional[str] = None
    mode: str = "Online"  # Online | Hybrid | In-Person
    tags: List[str] = field(default_factory=list)  # Maps to required_skills
    organizer: str = "SkillBridge Community"
    category: str = "Hackathon"
    prize_pool: Optional[str] = None
    eligibility_criteria: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True

    def to_opportunity_dict(self) -> Dict[str, Any]:
        """Convert normalized event to database dictionary representation."""
        deadline_val = ensure_utc(self.end_date or self.start_date)
        start_val = ensure_utc(self.start_date)
        return {
            "title": self.title[:255],
            "organizer": self.organizer[:255],
            "category": self.category[:100],
            "description": self.description,
            "required_skills": self.tags,
            "eligibility_criteria": self.eligibility_criteria or {
                "degrees": ["B.Tech", "B.E.", "BCA", "MCA", "M.Tech", "Any Degree"],
                "allowed_years": [1, 2, 3, 4],
                "notes": f"Sourced directly from {self.source}"
            },
            "deadline": deadline_val,
            "start_date": start_val,
            "mode": self.mode[:50],
            "location": self.location[:255] if self.location else None,
            "official_url": self.official_url[:512],
            "source": self.source[:100],
            "external_id": str(self.external_id)[:255] if self.external_id else None,
            "prize_pool": self.prize_pool[:255] if self.prize_pool else None,
            "is_active": self.is_active,
        }


class BaseEventFetcher(abc.ABC):
    """
    Abstract base class for all event sources.
    Enforces a common interface and respectful HTTP interactions.
    """
    def __init__(self, user_agent: str = "SkillBridgeAI/1.0 (+https://skillbridge.ai)"):
        self.user_agent = user_agent
        self._robots_parsers: Dict[str, urllib.robotparser.RobotFileParser] = {}

    @property
    @abc.abstractmethod
    def source_name(self) -> str:
        """Name of the event source (e.g. 'Devfolio', 'Unstop')."""
        pass

    @abc.abstractmethod
    async def fetch_events(self) -> List[NormalizedEvent]:
        """Fetch and return a list of normalized events from this source."""
        pass

    def can_fetch(self, url: str) -> bool:
        """
        Check robots.txt compliance before scraping.
        Defaults to True if robots.txt cannot be fetched or parsed.
        """
        try:
            parsed = urllib.parse.urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            if base_url not in self._robots_parsers:
                rp = urllib.robotparser.RobotFileParser()
                rp.set_url(f"{base_url}/robots.txt")
                try:
                    rp.read()
                    self._robots_parsers[base_url] = rp
                except Exception:
                    # If robots.txt cannot be read, default to allow
                    return True
            return self._robots_parsers[base_url].can_fetch(self.user_agent, url)
        except Exception:
            return True
