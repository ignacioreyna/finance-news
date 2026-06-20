"""Fed Speeches connector for annual speech listings."""

from __future__ import annotations

import html.parser as hp
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from ._http import AsyncHttpTransport, HttpRequest
from .models import (
    Freshness,
    PageResult,
    Provenance,
    RateLimitPolicy,
    RecoverableConnectorError,
    RetryPolicy,
    SourceItem,
)

CONNECTOR_NAME = "fed_speeches"
SOURCE_NAME = "fed"
PARSER_VERSION = "0.1.0"
BASE_URL = "https://www.federalreserve.gov/newsevents/speech"
DEFAULT_TTL_SECONDS = 24 * 60 * 60

# Tag keyword patterns for editorial classification
_TAG_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "monetary_policy",
        re.compile(
            r"\b(monetary policy|interest rates|inflation|federal funds|rate hike|rate cut|policy stance)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "banking",
        re.compile(
            r"\b(banking|banks|lender|credit|deposits|loans|financial institution|bank supervision)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "financial_stability",
        re.compile(
            r"\b(financial stability|systemic risk|stress test|capital requirements|liquidity|market stability)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "economy",
        re.compile(
            r"\b(economy|economic|growth|gdp|employment|labor market|recession|expansion|outlook)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "regulation",
        re.compile(
            r"\b(regulation|regulatory|compliance|oversight|supervision|regulatory framework)\b",
            re.IGNORECASE,
        ),
    ),
)


@dataclass(frozen=True)
class ParsedFedSpeech:
    """A parsed Fed speech entry."""

    date: datetime | None
    speaker: str
    title: str
    url: str
    external_id: str

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary for serialization."""
        return {
            "date": self.date.isoformat() if self.date else None,
            "speaker": self.speaker,
            "title": self.title,
            "url": self.url,
            "external_id": self.external_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ParsedFedSpeech":
        """Create from dictionary for deserialization."""
        date_str = data.get("date")
        date = datetime.fromisoformat(date_str) if isinstance(date_str, str) else None
        return cls(
            date=date,
            speaker=str(data["speaker"]),
            title=str(data["title"]),
            url=str(data["url"]),
            external_id=str(data["external_id"]),
        )


@dataclass(frozen=True)
class FedSpeechClassification:
    """Editorial classification of a Fed speech."""

    tags: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary for serialization."""
        return {"tags": self.tags}

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "FedSpeechClassification":
        """Create from dictionary for deserialization."""
        tags = data.get("tags", [])
        if not isinstance(tags, (list, tuple)):
            tags = []
        return cls(tags=tuple(str(tag) for tag in tags))


class _SpeechListingParser(hp.HTMLParser):
    """Extract Fed speech entries from annual speeches HTML."""

    def __init__(self, *, page_url: str) -> None:
        super().__init__()
        self._page_url = page_url
        self._div_depth = 0
        self._entry_depth: int | None = None
        self._current_date: str | None = None
        self._current_speaker: str | None = None
        self._current_title_parts: list[str] = []
        self._current_url: str | None = None
        self._in_date = False
        self._in_speaker = False
        self._in_title = False
        self._speeches: list[ParsedFedSpeech] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)

        if tag == "div":
            self._div_depth += 1

        # Look for speech entry divs (mimicking FOMC calendar pattern)
        if tag == "div" and attrs_dict.get("class") == "speech-entry" and self._entry_depth is None:
            self._entry_depth = self._div_depth
            self._current_date = None
            self._current_speaker = None
            self._current_title_parts = []
            self._current_url = None
            self._in_date = False
            self._in_speaker = False
            self._in_title = False
            return

        # Inside a speech entry
        if self._entry_depth is not None:
            if tag == "div" and attrs_dict.get("class") == "speech-date":
                self._in_date = True
                self._current_date = ""
            elif tag == "div" and attrs_dict.get("class") == "speech-speaker":
                self._in_speaker = True
                self._current_speaker = ""
            elif tag == "a" and "href" in attrs_dict:
                self._current_url = attrs_dict["href"]
                self._in_title = True
                self._current_title_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "div" and self._entry_depth is not None:
            if self._in_date:
                self._in_date = False
                if self._current_date is not None:
                    self._current_date = self._current_date.strip()
            elif self._in_speaker:
                self._in_speaker = False
                if self._current_speaker is not None:
                    self._current_speaker = self._current_speaker.strip()

        if tag == "a" and self._in_title:
            self._in_title = False

        if tag != "div":
            return

        # End of speech entry
        if self._entry_depth is not None and self._div_depth == self._entry_depth:
            self._create_speech()
            self._current_date = None
            self._current_speaker = None
            self._current_title_parts = []
            self._current_url = None
            self._in_date = False
            self._in_speaker = False
            self._in_title = False
            self._entry_depth = None

        self._div_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._entry_depth is None:
            return

        if self._in_date and self._current_date is not None:
            self._current_date += data
        elif self._in_speaker and self._current_speaker is not None:
            self._current_speaker += data
        elif self._in_title:
            self._current_title_parts.append(data)

    def _create_speech(self) -> None:
        """Create a ParsedFedSpeech from current state."""
        if not self._current_url or not self._current_title_parts:
            return

        title = " ".join(self._current_title_parts).strip()
        if not title:
            return

        date = self._parse_date(self._current_date) if self._current_date else None
        speaker = self._current_speaker.strip() if self._current_speaker else "Unknown"

        # Generate external_id from URL or date+speaker
        url_path = self._current_url.split("/")[-1] if self._current_url else ""
        date_str = date.strftime("%Y-%m-%d") if date else "unknown"
        speaker_clean = re.sub(r"[^a-zA-Z0-9]", "_", speaker.lower())[:30]
        external_id = f"fed_speech_{date_str}_{speaker_clean}"

        speech = ParsedFedSpeech(
            date=date,
            speaker=speaker,
            title=title,
            url=self._current_url,
            external_id=external_id,
        )
        self._speeches.append(speech)

    def _parse_date(self, date_str: str) -> datetime | None:
        """Parse date string like 'January 15, 2025' to datetime."""
        if not date_str:
            return None

        date_str = date_str.strip()
        # Try format like "January 15, 2025"
        match = re.match(r"([A-Za-z]+)\s+(\d+),\s*(\d{4})", date_str)
        if not match:
            return None

        month_str, day_str, year_str = match.groups()

        month_map = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
        }

        month = month_map.get(month_str.lower())
        if month is None:
            return None

        try:
            day = int(day_str)
            year = int(year_str)
            return datetime(year, month, day, tzinfo=timezone.utc)
        except (ValueError, IndexError):
            return None

    def get_speeches(self) -> list[ParsedFedSpeech]:
        """Return parsed Fed speeches."""
        return self._speeches


def parse_fed_speeches_html(
    html: str,
    *,
    page_url: str = BASE_URL,
) -> list[ParsedFedSpeech]:
    """Parse Fed speeches HTML into structured speech entries."""
    parser = _SpeechListingParser(page_url=page_url)
    parser.feed(html)
    return parser.get_speeches()


def classify_speech_by_title(title: str) -> FedSpeechClassification:
    """Classify a speech by title keywords.

    Args:
        title: The speech title.

    Returns:
        Classification with matched tags.
    """
    matched_tags = tuple(
        label for label, pattern in _TAG_PATTERNS if pattern.search(title)
    )
    return FedSpeechClassification(tags=matched_tags)


def filter_speeches(
    speeches: list[ParsedFedSpeech],
    *,
    speaker: str | None = None,
    tag: str | None = None,
) -> list[ParsedFedSpeech]:
    """Filter speeches by speaker or tag.

    This helper prioritizes speeches without summarizing body text.
    It performs substring matching on speaker name and tag filtering
    based on title classification.

    Args:
        speeches: List of parsed speeches.
        speaker: Optional speaker substring to filter by.
        tag: Optional tag to filter by.

    Returns:
        Filtered list of speeches matching the criteria.
    """
    filtered = speeches

    if speaker is not None:
        speaker_lower = speaker.lower()
        filtered = [
            s for s in filtered
            if speaker_lower in s.speaker.lower()
        ]

    if tag is not None:
        filtered = [
            s for s in filtered
            if tag in classify_speech_by_title(s.title).tags
        ]

    return filtered


def normalize_fed_speech(
    *,
    parsed: ParsedFedSpeech,
    fetched_at: datetime,
    fetch_url: str,
    cursor: str | None,
    transport_metadata: dict[str, object] | None = None,
) -> SourceItem:
    """Normalize a parsed Fed speech into a SourceItem."""
    classification = classify_speech_by_title(parsed.title)

    date_str = parsed.date.strftime("%Y-%m-%d") if parsed.date else "date not specified"
    title = f"{parsed.speaker} - {parsed.title}"

    summary_parts = [f"Date: {date_str}", f"Speaker: {parsed.speaker}"]
    if classification.tags:
        summary_parts.append(f"Tags: {', '.join(classification.tags)}")
    summary = ". ".join(summary_parts) + "."

    metadata: dict[str, object] = {
        "speaker": parsed.speaker,
        "title": parsed.title,
        "tags": list(classification.tags),
    }

    # Resolve relative URLs
    url = parsed.url
    if url.startswith("/"):
        url = f"https://www.federalreserve.gov{url}"

    return SourceItem(
        external_id=parsed.external_id,
        source=SOURCE_NAME,
        published_at=parsed.date,
        title=title,
        body=None,
        summary=summary,
        url=url,
        metadata=metadata,
        provenance=Provenance(
            connector=CONNECTOR_NAME,
            source=SOURCE_NAME,
            fetch_url=fetch_url,
            canonical_url=url,
            cursor=cursor,
            fetched_at=fetched_at,
            parser_version=PARSER_VERSION,
            transport_metadata=transport_metadata or {},
        ),
        freshness=Freshness(
            published_at=parsed.date,
            first_seen_at=fetched_at,
            fetched_at=fetched_at,
            is_stale=False,
            ttl_seconds=DEFAULT_TTL_SECONDS,
        ),
    )


class FedSpeechesConnector:
    """Fetch Fed speeches from annual listings."""

    name = CONNECTOR_NAME
    source = SOURCE_NAME
    retry_policy = RetryPolicy(
        max_attempts=3,
        base_delay_seconds=1.0,
        max_delay_seconds=8.0,
    )
    rate_limit_policy = RateLimitPolicy(concurrency=1, burst=1)

    def __init__(self, *, transport: AsyncHttpTransport) -> None:
        self._transport = transport

    async def fetch_page(
        self,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> PageResult:
        """Fetch a page of Fed speeches.

        Args:
            cursor: Optional year string (e.g., "2025") for annual listing.
                If None, defaults to current year's listing.
            since: Optional datetime filter for speeches.

        Returns:
            PageResult with parsed and normalized speeches.
        """
        del since

        # Build URL for year-specific listing
        year = cursor if cursor else datetime.now(timezone.utc).year
        url = f"{BASE_URL}/{year}-speeches.htm"

        response = await self._transport.send(
            HttpRequest(
                method="GET",
                url=url,
                headers={"Accept": "text/html"},
            )
        )

        if response.status_code == 404:
            return PageResult(items=(), next_cursor=None, has_more=False)
        if 500 <= response.status_code <= 599:
            raise RecoverableConnectorError(
                f"Federal Reserve returned {response.status_code} for {url}."
            )
        if response.status_code != 200:
            raise ValueError(
                f"Unexpected status code {response.status_code} for {url}."
            )

        html = response.text()
        fetched_at = datetime.now(timezone.utc)
        speeches = parse_fed_speeches_html(html, page_url=response.url)

        items = []
        for speech in speeches:
            item = normalize_fed_speech(
                parsed=speech,
                fetched_at=fetched_at,
                fetch_url=response.url,
                cursor=str(year),
                transport_metadata={
                    "status_code": response.status_code,
                    "content_type": response.headers.get("Content-Type"),
                },
            )
            items.append(item)

        return PageResult(items=tuple(items), next_cursor=None, has_more=False)