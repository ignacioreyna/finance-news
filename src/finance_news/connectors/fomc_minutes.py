"""FOMC Minutes connector."""

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

CONNECTOR_NAME = "fomc_minutes"
SOURCE_NAME = "fed"
PARSER_VERSION = "0.1.0"
DEFAULT_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days for minutes


@dataclass(frozen=True)
class ParsedFomcMinutes:
    """A parsed FOMC minutes document."""

    date: datetime | None
    clean_text: str | None
    sections: dict[str, str]
    external_id: str
    minutes_url: str

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary for serialization."""
        return {
            "date": self.date.isoformat() if self.date else None,
            "clean_text": self.clean_text,
            "sections": self.sections,
            "external_id": self.external_id,
            "minutes_url": self.minutes_url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ParsedFomcMinutes":
        """Create from dictionary for deserialization."""
        date_str = data.get("date")
        date = datetime.fromisoformat(date_str) if isinstance(date_str, str) else None
        sections = data.get("sections")
        if not isinstance(sections, dict):
            sections = {}
        return cls(
            date=date,
            clean_text=data.get("clean_text") if isinstance(data.get("clean_text"), str) else None,
            sections=sections,
            external_id=str(data["external_id"]),
            minutes_url=str(data["minutes_url"]),
        )


class _MinutesParser(hp.HTMLParser):
    """Extract FOMC minutes data from Federal Reserve HTML."""

    def __init__(self, *, minutes_url: str) -> None:
        super().__init__()
        self._minutes_url = minutes_url
        self._div_depth = 0
        self._main_depth: int | None = None
        self._paragraphs: list[str] = []
        self._current_text: str = ""
        self._sections: dict[str, str] = {}
        self._current_section: str | None = None
        self._section_text: list[str] = []
        self._date_str: str | None = None
        self._in_h4 = False
        self._seen_date = False
        self._seen_h4 = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)

        if tag == "div":
            self._div_depth += 1

        if tag == "div" and attrs_dict.get("class") == "col-xs-12 col-sm-8 col-md-9":
            self._main_depth = self._div_depth

        if self._main_depth is not None and self._div_depth >= self._main_depth:
            if tag == "h4":
                self._seen_h4 = True
                if self._current_section and self._section_text:
                    self._sections[self._current_section] = " ".join(self._section_text)
                    self._section_text = []
                self._current_section = None
                self._in_h4 = True
                self._current_text = ""

            if tag == "p":
                self._current_text = ""

    def handle_endtag(self, tag: str) -> None:
        if self._main_depth is not None and self._div_depth >= self._main_depth:
            if tag == "h4" and self._in_h4:
                self._current_section = self._current_text.strip()
                self._in_h4 = False
                self._current_text = ""

            if tag == "p" and self._current_text:
                text = self._current_text.strip()
                if text:
                    self._paragraphs.append(text)
                    if self._current_section:
                        self._section_text.append(text)
                    elif not self._seen_h4 and not self._seen_date and self._is_date_text(text):
                        self._date_str = text
                        self._seen_date = True
                self._current_text = ""

            if tag == "div" and self._main_depth is not None and self._div_depth == self._main_depth:
                if self._current_section and self._section_text:
                    self._sections[self._current_section] = " ".join(self._section_text)
                    self._section_text = []
                self._current_section = None
                self._main_depth = None

        if tag == "div":
            self._div_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._main_depth is not None and self._div_depth >= self._main_depth:
            self._current_text += data

    def _is_date_text(self, text: str) -> bool:
        """Check if text looks like a FOMC minutes date."""
        if not text:
            return False
        return bool(re.search(r"[A-Za-z]+\s+\d{1,2}(?:-\d{1,2})?,\s*\d{4}", text))

    def get_data(self) -> tuple[str | None, list[str], dict[str, str]]:
        """Return parsed date, paragraphs, and sections."""
        return self._date_str, self._paragraphs, self._sections


def _parse_fed_date(date_str: str | None) -> datetime | None:
    """Parse Federal Reserve date string like 'June 18-19, 2025' to datetime."""
    if not date_str:
        return None

    date_str = date_str.strip()
    match = re.search(r"([A-Za-z]+)\s+(\d{1,2})(?:-\d{1,2})?,\s*(\d{4})", date_str)
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


def _normalize_sections(sections: dict[str, str]) -> dict[str, str]:
    """Normalize section names to standard keys."""
    normalized: dict[str, str] = {}
    section_mapping = {
        "developments in financial markets and open market operations": "financial_markets",
        "developments in the economy and economic outlook": "economic_outlook",
        "staff economic outlook": "staff_outlook",
        "discussion of economic conditions and policy": "policy_discussion",
        "staff review of the financial situation": "financial_review",
        "committee policy action": "policy_action",
        "inflation": "inflation",
        "employment": "employment",
        "balance of risks": "risks",
        "balance sheet": "balance_sheet",
        "directive": "directive",
    }

    for raw_name, content in sections.items():
        key = None
        lower_name = raw_name.lower()
        for pattern, standard_key in section_mapping.items():
            if pattern in lower_name:
                key = standard_key
                break
        if key is None:
            key = raw_name
        normalized[key] = content

    return normalized


def _clean_text(paragraphs: list[str]) -> str:
    """Clean and join paragraphs into clean text."""
    if not paragraphs:
        return ""

    filtered = [p.strip() for p in paragraphs if len(p.strip()) > 20]
    return "\n\n".join(filtered)


def parse_fomc_minutes_html(
    html: str,
    *,
    minutes_url: str,
) -> ParsedFomcMinutes:
    """Parse FOMC minutes HTML into structured data."""
    parser = _MinutesParser(minutes_url=minutes_url)
    parser.feed(html)
    date_str, paragraphs, sections = parser.get_data()

    date = _parse_fed_date(date_str)
    clean_text = _clean_text(paragraphs)
    normalized_sections = _normalize_sections(sections)

    url_match = re.search(r"fomcminutes(\d{8})\.htm", minutes_url)
    if url_match:
        date_suffix = url_match.group(1)
        external_id = f"fomc_minutes_{date_suffix}"
    else:
        external_id = f"fomc_minutes_{hash(minutes_url)}"

    return ParsedFomcMinutes(
        date=date,
        clean_text=clean_text,
        sections=normalized_sections,
        external_id=external_id,
        minutes_url=minutes_url,
    )


def normalize_fomc_minutes(
    *,
    parsed: ParsedFomcMinutes,
    fetched_at: datetime,
    fetch_url: str,
    cursor: str | None,
    transport_metadata: dict[str, object] | None = None,
) -> SourceItem:
    """Normalize a parsed FOMC minutes into a SourceItem."""
    metadata: dict[str, object] = {
        "sections": parsed.sections,
        "minutes_url": parsed.minutes_url,
        "section_count": len(parsed.sections),
    }

    date_str = parsed.date.strftime("%Y-%m-%d") if parsed.date else "fecha no especificada"
    title = f"FOMC Minutes - {date_str}"

    summary_parts = [f"Date: {date_str}"]
    if parsed.sections:
        section_names = ", ".join(parsed.sections.keys())
        summary_parts.append(f"Sections: {section_names}")
    summary = ". ".join(summary_parts) + "."

    source_url = parsed.minutes_url

    return SourceItem(
        external_id=parsed.external_id,
        source=SOURCE_NAME,
        published_at=parsed.date,
        title=title,
        body=parsed.clean_text,
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
            published_at=parsed.date,
            first_seen_at=fetched_at,
            fetched_at=fetched_at,
            is_stale=False,
            ttl_seconds=DEFAULT_TTL_SECONDS,
        ),
    )


class FomcMinutesConnector:
    """Fetch FOMC minutes."""

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
        """Fetch a page of FOMC minutes."""
        del since

        if not cursor:
            raise ValueError("cursor (minutes URL) is required for FOMC minutes connector")

        minutes_url = cursor

        response = await self._transport.send(
            HttpRequest(
                method="GET",
                url=minutes_url,
                headers={"Accept": "text/html"},
            )
        )

        if response.status_code == 404:
            return PageResult(items=(), next_cursor=None, has_more=False)
        if 500 <= response.status_code <= 599:
            raise RecoverableConnectorError(
                f"Federal Reserve returned {response.status_code} for {minutes_url}."
            )
        if response.status_code != 200:
            raise ValueError(
                f"Unexpected status code {response.status_code} for {minutes_url}."
            )

        html = response.text()
        fetched_at = datetime.now(timezone.utc)
        parsed = parse_fomc_minutes_html(html, minutes_url=response.url)

        item = normalize_fomc_minutes(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url=response.url,
            cursor=cursor,
            transport_metadata={
                "status_code": response.status_code,
                "content_type": response.headers.get("Content-Type"),
            },
        )

        return PageResult(items=(item,), next_cursor=None, has_more=False)