import logging
from typing import List

from .base import BaseEventFetcher, NormalizedEvent

logger = logging.getLogger(__name__)


class SIHFetcher(BaseEventFetcher):
    """
    Fetcher for Smart India Hackathon (SIH).
    Note: SIH portal (sih.gov.in) does not currently provide a public JSON/RSS/iCal API
    for structured event listings. To strictly ensure that NO synthetic or mock opportunities
    are ever inserted into the database, this fetcher is disabled and returns an empty list.
    """
    PORTAL_URL = "https://sih.gov.in/"

    @property
    def source_name(self) -> str:
        return "Smart India Hackathon"

    async def fetch_events(self) -> List[NormalizedEvent]:
        logger.info(
            "SIHFetcher: Smart India Hackathon portal does not provide a public structured API. "
            "Skipping to prevent synthetic or unverified entries."
        )
        return []
