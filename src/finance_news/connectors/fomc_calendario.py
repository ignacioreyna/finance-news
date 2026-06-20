"""FOMC Calendar connector."""

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

CONNECTOR_NAME = "fomc_calendario"
SOURCE_NAME = "fed"
PARSER_VERSION = "0.1.0"
BASE_CALENDAR_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
DEFAULT_TTL_SECONDS = 24 * 60 * 60  # 24 hours for calendar


@dataclass(frozen=True)
class ParsedFomcMeeting:
    """A parsed FOMC meeting."""

    date: datetime | None
    meeting_type: str
    has_sep: bool
    statement_url: str | None
    minutes_url: str | None
    sep_url: str | None
    implementation_note_url: str | None
    press_conference_url: str | None
    external_id: str

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary for serialization."""
        return {
            "date": self.date.isoformat() if self.date else None,
            "meeting_type": self.meeting_type,
            "has_sep": self.has_sep,
            "statement_url": self.statement_url,
            "minutes_url": self.minutes_url,
            "sep_url": self.sep_url,
            "implementation_note_url": self.implementation_note_url,
            "press_conference_url": self.press_conference_url,
            "external_id": self.external_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ParsedFomcMeeting":
        """Create from dictionary for deserialization."""
        date_str = data.get("date")
        date = datetime.fromisoformat(date_str) if isinstance(date_str, str) else None
        return cls(
            date=date,
            meeting_type=str(data["meeting_type"]),
            has_sep=bool(data["has_sep"]),
            statement_url=data.get("statement_url") if isinstance(data.get("statement_url"), str) else None,
            minutes_url=data.get("minutes_url") if isinstance(data.get("minutes_url"), str) else None,
            sep_url=data.get("sep_url") if isinstance(data.get("sep_url"), str) else None,
            implementation_note_url=data.get("implementation_note_url") if isinstance(data.get("implementation_note_url"), str) else None,
            press_conference_url=data.get("press_conference_url") if isinstance(data.get("press_conference_url"), str) else None,
            external_id=str(data["external_id"]),
        )


class _CalendarParser(hp.HTMLParser):
    """Extract FOMC meeting data from Federal Reserve HTML."""

    def __init__(self, *, page_url: str) -> None:
        super().__init__()
        self._page_url = page_url
        self._div_depth = 0
        self._panel_depth: int | None = None
        self._meeting_depth: int | None = None
        self._current_date: str | None = None
        self._current_links: dict[str, str] = {}
        self._meetings: list[ParsedFomcMeeting] = []
        self._current_link_href: str | None = None
        self._current_link_text: str = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)

        if tag == "div":
            self._div_depth += 1

        if tag == "div" and attrs_dict.get("class") == "panel" and self._panel_depth is None:
            self._panel_depth = self._div_depth
            self._current_date = None
            self._current_links = {}
            return

        if self._panel_depth is None:
            return

        if tag == "div" and attrs_dict.get("class") == "meeting" and self._meeting_depth is None:
            self._meeting_depth = self._div_depth
            self._current_date = None
            self._current_links = {}
            return

        if tag == "div" and attrs_dict.get("class") == "date" and self._meeting_depth is not None:
            self._current_date = ""

        if tag == "a" and self._meeting_depth is not None and "href" in attrs_dict:
            self._current_link_href = attrs_dict["href"]
            self._current_link_text = ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._current_link_href is not None:
            if self._current_link_href and self._current_link_text:
                self._categorize_link(self._current_link_href, self._current_link_text)
            self._current_link_href = None
            self._current_link_text = ""

        if tag != "div":
            return

        if self._meeting_depth is not None and self._div_depth == self._meeting_depth:
            if self._current_date:
                self._create_meeting()
            self._current_date = None
            self._current_links = {}
            self._meeting_depth = None
        elif self._panel_depth is not None and self._div_depth == self._panel_depth:
            self._panel_depth = None

        self._div_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._current_link_href is not None:
            self._current_link_text += data
        if self._current_date is not None:
            self._current_date += data

    def _categorize_link(self, href: str, text: str) -> None:
        """Categorize a link by its URL and text."""
        text_lower = text.lower()
        href_lower = href.lower()

        if "implementation" in text_lower and "note" in text_lower:
            self._current_links["implementation_note_url"] = href
        elif "press conference" in text_lower or "presconf" in href_lower:
            self._current_links["press_conference_url"] = href
        elif "minutes" in text_lower or "fomcminutes" in href_lower:
            self._current_links["minutes_url"] = href
        elif "sep" in text_lower or "projection" in text_lower or "tealbook" in text_lower or "fomcprojtabl" in href_lower:
            self._current_links["sep_url"] = href
        elif "statement" in text_lower or "pressrelease" in href_lower:
            self._current_links["statement_url"] = href

    def _create_meeting(self) -> None:
        """Create a ParsedFomcMeeting from current state."""
        date = self._parse_date(self._current_date) if self._current_date else None
        has_sep = "sep_url" in self._current_links

        meeting_type = "regular"
        if has_sep:
            meeting_type = "sep"

        date_str = date.strftime("%Y-%m-%d") if date else "unknown"
        external_id = f"fomc_meeting_{date_str}"

        meeting = ParsedFomcMeeting(
            date=date,
            meeting_type=meeting_type,
            has_sep=has_sep,
            statement_url=self._current_links.get("statement_url"),
            minutes_url=self._current_links.get("minutes_url"),
            sep_url=self._current_links.get("sep_url"),
            implementation_note_url=self._current_links.get("implementation_note_url"),
            press_conference_url=self._current_links.get("press_conference_url"),
            external_id=external_id,
        )
        self._meetings.append(meeting)

    def _parse_date(self, date_str: str) -> datetime | None:
        """Parse date string like 'January 28-29, 2025' to datetime."""
        if not date_str:
            return None

        date_str = date_str.strip()
        match = re.match(r"([A-Za-z]+)\s+(\d+)(?:-\d+)?,\s*(\d{4})", date_str)
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
            day = int(day_str.split("-")[0])
            year = int(year_str)
            return datetime(year, month, day, tzinfo=timezone.utc)
        except (ValueError, IndexError):
            return None

    def get_meetings(self) -> list[ParsedFomcMeeting]:
        """Return parsed FOMC meetings."""
        return self._meetings


def parse_fomc_calendario_html(
    html: str,
    *,
    page_url: str = BASE_CALENDAR_URL,
) -> list[ParsedFomcMeeting]:
    """Parse FOMC calendar HTML into structured meetings."""
    parser = _CalendarParser(page_url=page_url)
    parser.feed(html)
    return parser.get_meetings()


def normalize_fomc_meeting(
    *,
    parsed: ParsedFomcMeeting,
    fetched_at: datetime,
    fetch_url: str,
    cursor: str | None,
    transport_metadata: dict[str, object] | None = None,
) -> SourceItem:
    """Normalize a parsed FOMC meeting into a SourceItem."""
    metadata: dict[str, object] = {
        "meeting_type": parsed.meeting_type,
        "has_sep": parsed.has_sep,
        "statement_url": parsed.statement_url,
        "minutes_url": parsed.minutes_url,
        "sep_url": parsed.sep_url,
        "implementation_note_url": parsed.implementation_note_url,
        "press_conference_url": parsed.press_conference_url,
    }

    date_str = parsed.date.strftime("%Y-%m-%d") if parsed.date else "fecha no especificada"
    title = f"FOMC Meeting - {date_str}"
    if parsed.has_sep:
        title += " (with SEP)"

    summary_parts = [f"Date: {date_str}", f"Type: {parsed.meeting_type}"]
    if parsed.has_sep:
        summary_parts.append("Includes SEP/Projections")
    summary = ". ".join(summary_parts) + "."

    source_url = fetch_url

    return SourceItem(
        external_id=parsed.external_id,
        source=SOURCE_NAME,
        published_at=parsed.date,
        title=title,
        body=None,
        summary=summary,
        url=source_url,
        metadata=metadata,
        provenance=Provenance(
            connector=CONNECTOR_NAME,
            source=SOURCE_NAME,
            fetch_url=fetch_url,
            canonical_url=fetch_url,
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


class FomcCalendarioConnector:
    """Fetch FOMC calendar meetings."""

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
        """Fetch a page of FOMC calendar meetings."""
        del since, cursor

        response = await self._transport.send(
            HttpRequest(
                method="GET",
                url=BASE_CALENDAR_URL,
                headers={"Accept": "text/html"},
            )
        )

        if response.status_code == 404:
            return PageResult(items=(), next_cursor=None, has_more=False)
        if 500 <= response.status_code <= 599:
            raise RecoverableConnectorError(
                f"Federal Reserve returned {response.status_code} for {BASE_CALENDAR_URL}."
            )
        if response.status_code != 200:
            raise ValueError(
                f"Unexpected status code {response.status_code} for {BASE_CALENDAR_URL}."
            )

        html = response.text()
        fetched_at = datetime.now(timezone.utc)
        meetings = parse_fomc_calendario_html(html, page_url=response.url)

        items = []
        for meeting in meetings:
            item = normalize_fomc_meeting(
                parsed=meeting,
                fetched_at=fetched_at,
                fetch_url=response.url,
                cursor=None,
                transport_metadata={
                    "status_code": response.status_code,
                    "content_type": response.headers.get("Content-Type"),
                },
            )
            items.append(item)

        return PageResult(items=tuple(items), next_cursor=None, has_more=False)