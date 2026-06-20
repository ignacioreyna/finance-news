"""OPEC Eventos connector.

This connector extracts OPEC meeting events from press releases and public tables.

LIMITATIONS: The full Monthly Oil Market Report (MOMR) is NOT freely available
and requires a paid/restricted subscription. This connector only processes
publicly available press releases and public tables from opec.org.
"""

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

CONNECTOR_NAME = "opec_eventos"
SOURCE_NAME = "opec"
PARSER_VERSION = "0.1.0"
BASE_PRESS_RELEASE_URL = "https://www.opec.org/opec_web/en/press_room/28.htm"
DEFAULT_TTL_SECONDS = 24 * 60 * 60  # 24 hours


@dataclass(frozen=True)
class ParsedOpecEvent:
    """A parsed OPEC meeting event."""

    meeting_date: datetime | None
    decision: str
    affected_countries: list[str]
    effective_date: datetime | None
    event_url: str | None
    external_id: str

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary for serialization."""
        return {
            "meeting_date": self.meeting_date.isoformat() if self.meeting_date else None,
            "decision": self.decision,
            "affected_countries": self.affected_countries,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "event_url": self.event_url,
            "external_id": self.external_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ParsedOpecEvent":
        """Create from dictionary for deserialization."""
        meeting_date_str = data.get("meeting_date")
        meeting_date = datetime.fromisoformat(meeting_date_str) if isinstance(meeting_date_str, str) else None

        effective_date_str = data.get("effective_date")
        effective_date = datetime.fromisoformat(effective_date_str) if isinstance(effective_date_str, str) else None

        affected_countries = data.get("affected_countries", [])
        if not isinstance(affected_countries, list):
            affected_countries = []

        return cls(
            meeting_date=meeting_date,
            decision=str(data["decision"]),
            affected_countries=[str(c) for c in affected_countries],
            effective_date=effective_date,
            event_url=data.get("event_url") if isinstance(data.get("event_url"), str) else None,
            external_id=str(data["external_id"]),
        )


class _PressReleaseParser(hp.HTMLParser):
    """Extract OPEC event data from press release HTML."""

    def __init__(self, *, page_url: str) -> None:
        super().__init__()
        self._page_url = page_url
        self._div_depth = 0
        self._event_depth: int | None = None
        self._current_event: dict[str, object] = {}
        self._events: list[ParsedOpecEvent] = []
        self._current_text: str = ""
        self._current_link_href: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)

        if tag == "div":
            self._div_depth += 1

        if tag == "div" and attrs_dict.get("class") == "opec-event" and self._event_depth is None:
            self._event_depth = self._div_depth
            self._current_event = {}
            return

        if self._event_depth is None:
            return

        if tag == "a" and "href" in attrs_dict:
            self._current_link_href = attrs_dict["href"]

    def handle_endtag(self, tag: str) -> None:
        if tag != "div":
            return

        if self._event_depth is not None and self._div_depth == self._event_depth:
            self._finalize_event()
            self._current_event = {}
            self._event_depth = None

        self._div_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._event_depth is None:
            return

        self._current_text += data

        # Parse meeting date
        if "Meeting Date:" in data and "meeting_date" not in self._current_event:
            match = re.search(r"Meeting Date:\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})", data)
            if match:
                self._current_event["meeting_date"] = self._parse_date(match.group(1))

        # Parse decision
        if "Decision:" in data and "decision" not in self._current_event:
            match = re.search(r"Decision:\s*(.+?)(?:\n|Affected Countries:|$)", data)
            if match:
                decision = match.group(1).strip()
                self._current_event["decision"] = decision

        # Parse affected countries
        if "Affected Countries:" in data and "affected_countries" not in self._current_event:
            match = re.search(r"Affected Countries:\s*(.+?)(?:\n|Effective Date:|$)", data)
            if match:
                countries_str = match.group(1).strip()
                countries = [c.strip() for c in countries_str.split(",")]
                self._current_event["affected_countries"] = countries

        # Parse effective date
        if "Effective Date:" in data and "effective_date" not in self._current_event:
            match = re.search(r"Effective Date:\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})", data)
            if match:
                self._current_event["effective_date"] = self._parse_date(match.group(1))

    def _finalize_event(self) -> None:
        """Create a ParsedOpecEvent from current state."""
        meeting_date = self._current_event.get("meeting_date")
        decision = self._current_event.get("decision", "unknown decision")
        affected_countries = self._current_event.get("affected_countries", [])
        effective_date = self._current_event.get("effective_date")
        event_url = self._current_link_href

        date_str = meeting_date.strftime("%Y-%m-%d") if meeting_date else "unknown"
        external_id = f"opec_event_{date_str}"

        event = ParsedOpecEvent(
            meeting_date=meeting_date,
            decision=str(decision),
            affected_countries=[str(c) for c in affected_countries],
            effective_date=effective_date,
            event_url=event_url,
            external_id=external_id,
        )
        self._events.append(event)
        self._current_link_href = None
        self._current_text = ""

    def _parse_date(self, date_str: str) -> datetime | None:
        """Parse date string like 'June 5, 2024' to datetime."""
        if not date_str:
            return None

        date_str = date_str.strip()
        match = re.match(r"([A-Za-z]+)\s+(\d{1,2}),?\s*(\d{4})", date_str)
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
        except ValueError:
            return None

    def get_events(self) -> list[ParsedOpecEvent]:
        """Return parsed OPEC events."""
        return self._events


def parse_opec_press_release_html(
    html: str,
    *,
    page_url: str = BASE_PRESS_RELEASE_URL,
) -> list[ParsedOpecEvent]:
    """Parse OPEC press release HTML into structured events."""
    parser = _PressReleaseParser(page_url=page_url)
    parser.feed(html)
    return parser.get_events()


def normalize_opec_event(
    *,
    parsed: ParsedOpecEvent,
    fetched_at: datetime,
    fetch_url: str,
    cursor: str | None,
    transport_metadata: dict[str, object] | None = None,
) -> SourceItem:
    """Normalize a parsed OPEC event into a SourceItem."""
    metadata: dict[str, object] = {
        "meeting_date": parsed.meeting_date.isoformat() if parsed.meeting_date else None,
        "decision": parsed.decision,
        "affected_countries": parsed.affected_countries,
        "effective_date": parsed.effective_date.isoformat() if parsed.effective_date else None,
        "event_url": parsed.event_url,
    }

    date_str = parsed.meeting_date.strftime("%Y-%m-%d") if parsed.meeting_date else "fecha no especificada"
    title = f"OPEC Event - {date_str}: {parsed.decision}"

    summary_parts = [f"Date: {date_str}", f"Decision: {parsed.decision}"]
    if parsed.affected_countries:
        summary_parts.append(f"Countries: {', '.join(parsed.affected_countries)}")
    if parsed.effective_date:
        effective_str = parsed.effective_date.strftime("%Y-%m-%d")
        summary_parts.append(f"Effective: {effective_str}")
    summary = ". ".join(summary_parts) + "."

    source_url = parsed.event_url if parsed.event_url else fetch_url

    return SourceItem(
        external_id=parsed.external_id,
        source=SOURCE_NAME,
        published_at=parsed.meeting_date,
        title=title,
        body=None,
        summary=summary,
        url=source_url,
        metadata=metadata,
        provenance=Provenance(
            connector=CONNECTOR_NAME,
            source=SOURCE_NAME,
            fetch_url=fetch_url,
            canonical_url=source_url,
            cursor=cursor,
            fetched_at=fetched_at,
            parser_version=PARSER_VERSION,
            transport_metadata=transport_metadata or {},
        ),
        freshness=Freshness(
            published_at=parsed.meeting_date,
            first_seen_at=fetched_at,
            fetched_at=fetched_at,
            is_stale=False,
            ttl_seconds=DEFAULT_TTL_SECONDS,
        ),
    )


class OpecEventosConnector:
    """Fetch OPEC event data from press releases."""

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
        """Fetch a page of OPEC events."""
        del since, cursor

        response = await self._transport.send(
            HttpRequest(
                method="GET",
                url=BASE_PRESS_RELEASE_URL,
                headers={"Accept": "text/html"},
            )
        )

        if response.status_code == 404:
            return PageResult(items=(), next_cursor=None, has_more=False)
        if 500 <= response.status_code <= 599:
            raise RecoverableConnectorError(
                f"OPEC returned {response.status_code} for {BASE_PRESS_RELEASE_URL}."
            )
        if response.status_code != 200:
            raise ValueError(
                f"Unexpected status code {response.status_code} for {BASE_PRESS_RELEASE_URL}."
            )

        html = response.text()
        fetched_at = datetime.now(timezone.utc)
        events = parse_opec_press_release_html(html, page_url=response.url)

        items = []
        for event in events:
            item = normalize_opec_event(
                parsed=event,
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