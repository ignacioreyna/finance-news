"""FOMC Statement connector."""

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

CONNECTOR_NAME = "fomc_statements"
SOURCE_NAME = "fed"
PARSER_VERSION = "0.1.0"
DEFAULT_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days for statement


@dataclass(frozen=True)
class ParsedFomcStatement:
    """A parsed FOMC statement."""

    date: datetime | None
    decision: str
    target_range: str | None
    votes_for: int
    votes_against: int
    body_text: str | None
    external_id: str
    statement_url: str

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary for serialization."""
        return {
            "date": self.date.isoformat() if self.date else None,
            "decision": self.decision,
            "target_range": self.target_range,
            "votes_for": self.votes_for,
            "votes_against": self.votes_against,
            "body_text": self.body_text,
            "external_id": self.external_id,
            "statement_url": self.statement_url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ParsedFomcStatement":
        """Create from dictionary for deserialization."""
        date_str = data.get("date")
        date = datetime.fromisoformat(date_str) if isinstance(date_str, str) else None
        return cls(
            date=date,
            decision=str(data["decision"]),
            target_range=data.get("target_range") if isinstance(data.get("target_range"), str) else None,
            votes_for=int(data["votes_for"]),
            votes_against=int(data["votes_against"]),
            body_text=data.get("body_text") if isinstance(data.get("body_text"), str) else None,
            external_id=str(data["external_id"]),
            statement_url=str(data["statement_url"]),
        )


class _StatementParser(hp.HTMLParser):
    """Extract FOMC statement data from Federal Reserve HTML."""

    def __init__(self, *, statement_url: str) -> None:
        super().__init__()
        self._statement_url = statement_url
        self._div_depth = 0
        self._panel_depth: int | None = None
        self._content_depth: int | None = None
        self._in_time = False
        self._current_time: str | None = None
        self._paragraphs: list[str] = []
        self._current_text: str = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)

        if tag == "div":
            self._div_depth += 1

        if tag == "div" and attrs_dict.get("class") == "col-xs-12 col-sm-8 col-md-9":
            self._panel_depth = self._div_depth

        if self._panel_depth is not None:
            if tag == "div" and "col-xs-12 col-sm-8" in attrs_dict.get("class", ""):
                self._content_depth = self._div_depth

            if tag == "time" and self._panel_depth is not None:
                self._in_time = True

            if tag == "p" and self._content_depth is not None and self._div_depth >= self._content_depth:
                self._current_text = ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "time" and self._in_time:
            self._in_time = False

        if tag == "p" and self._content_depth is not None and self._current_text:
            self._paragraphs.append(self._current_text.strip())
            self._current_text = ""

        if tag == "div" and self._content_depth is not None and self._div_depth == self._content_depth:
            self._content_depth = None

        if tag == "div" and self._panel_depth is not None and self._div_depth == self._panel_depth:
            self._panel_depth = None

        if tag == "div":
            self._div_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._in_time:
            self._current_time = data.strip()

        if self._content_depth is not None and self._current_text is not None:
            self._current_text += data

    def get_data(self) -> tuple[str | None, list[str]]:
        """Return parsed time and paragraphs."""
        return self._current_time, self._paragraphs


def _parse_fed_date(date_str: str | None) -> datetime | None:
    """Parse Federal Reserve date string like 'June 18, 2025' to datetime."""
    if not date_str:
        return None

    date_str = date_str.strip()
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
    except ValueError:
        return None


def _classify_decision(text: str) -> str:
    """Classify policy decision from statement text."""
    text_lower = text.lower()

    if "raise" in text_lower or "increase" in text_lower:
        return "raise"
    elif "lower" in text_lower or "cut" in text_lower or "decrease" in text_lower:
        return "cut"
    elif "maintain" in text_lower or "target range" in text_lower:
        return "hold"
    else:
        return "unknown"


def _extract_target_range(text: str) -> str | None:
    """Extract target range from statement text."""
    text_lower = text.lower()

    # Look for pattern like "5-1/4 to 5-1/2 percent"
    match = re.search(r"(\d+(?:-\d+/\d+)?\s+to\s+\d+(?:-\d+/\d+)?)\s+percent", text_lower)
    if match:
        return match.group(1).strip()

    return None


def _extract_votes(text: str) -> tuple[int, int]:
    """Extract vote counts from statement text."""
    text_lower = text.lower()

    votes_for = 0
    votes_against = 0

    # Look for "Voting for the FOMC monetary policy action were:"
    voting_for_match = re.search(r"voting for the fomc monetary policy action were:(.*?)(?:voting against|$)", text_lower, re.DOTALL)
    if voting_for_match:
        for_votes_text = voting_for_match.group(1)
        # Count names separated by semicolons or "and"
        names = re.split(r"[;]|\sand\s", for_votes_text)
        votes_for = len([n for n in names if n.strip()])

    # Look for "Voting against the action"
    voting_against_match = re.finditer(r"voting against the action(?: was)?\s+(.*?)(?:\.|voting|$)", text_lower, re.DOTALL)
    for match in voting_against_match:
        against_text = match.group(1)
        # Count names
        names = re.split(r"[;]|\sand\s", against_text)
        votes_against += len([n for n in names if n.strip() and not "preferred" in n])

    # Fallback: look for specific voting patterns
    if votes_for == 0 and votes_against == 0:
        # Try to find mentions of voting
        voting_match = re.search(r"voting.*?(\d+).*?to.*?(\d+)", text_lower)
        if voting_match:
            votes_for = int(voting_match.group(1))
            votes_against = int(voting_match.group(2))

    return votes_for, votes_against


def _clean_body_text(paragraphs: list[str]) -> str:
    """Clean and join body text paragraphs."""
    if not paragraphs:
        return ""

    # Filter out very short paragraphs (likely not part of main content)
    filtered = [p for p in paragraphs if len(p) > 20]
    return "\n\n".join(filtered)


def parse_fomc_statement_html(
    html: str,
    *,
    statement_url: str,
) -> ParsedFomcStatement:
    """Parse FOMC statement HTML into structured data."""
    parser = _StatementParser(statement_url=statement_url)
    parser.feed(html)
    time_str, paragraphs = parser.get_data()

    date = _parse_fed_date(time_str)
    body_text = _clean_body_text(paragraphs)

    # Classify decision and extract other fields from body text
    decision = "hold"
    target_range = None
    votes_for = 0
    votes_against = 0

    if body_text:
        decision = _classify_decision(body_text)
        target_range = _extract_target_range(body_text)
        votes_for, votes_against = _extract_votes(body_text)

    # Create external_id from URL
    url_match = re.search(r"monetary(\d{8})[a-z]?\.htm", statement_url)
    if url_match:
        date_suffix = url_match.group(1)
        external_id = f"fomc_statement_{date_suffix}"
    else:
        external_id = f"fomc_statement_{hash(statement_url)}"

    return ParsedFomcStatement(
        date=date,
        decision=decision,
        target_range=target_range,
        votes_for=votes_for,
        votes_against=votes_against,
        body_text=body_text,
        external_id=external_id,
        statement_url=statement_url,
    )


def normalize_fomc_statement(
    *,
    parsed: ParsedFomcStatement,
    fetched_at: datetime,
    fetch_url: str,
    cursor: str | None,
    transport_metadata: dict[str, object] | None = None,
) -> SourceItem:
    """Normalize a parsed FOMC statement into a SourceItem."""
    metadata: dict[str, object] = {
        "decision": parsed.decision,
        "target_range": parsed.target_range,
        "votes_for": parsed.votes_for,
        "votes_against": parsed.votes_against,
        "statement_url": parsed.statement_url,
    }

    date_str = parsed.date.strftime("%Y-%m-%d") if parsed.date else "fecha no especificada"
    title = f"FOMC Statement - {date_str}"

    summary_parts = [f"Date: {date_str}", f"Decision: {parsed.decision}"]
    if parsed.target_range:
        summary_parts.append(f"Target Range: {parsed.target_range}")
    if parsed.votes_for > 0 or parsed.votes_against > 0:
        summary_parts.append(f"Vote: {parsed.votes_for} for, {parsed.votes_against} against")
    summary = ". ".join(summary_parts) + "."

    source_url = parsed.statement_url

    return SourceItem(
        external_id=parsed.external_id,
        source=SOURCE_NAME,
        published_at=parsed.date,
        title=title,
        body=parsed.body_text,
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


class FomcStatementsConnector:
    """Fetch FOMC statements."""

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
        """Fetch a page of FOMC statements."""
        del since  # Statement connector doesn't use since filter

        if not cursor:
            raise ValueError("cursor (statement URL) is required for FOMC statements connector")

        statement_url = cursor

        response = await self._transport.send(
            HttpRequest(
                method="GET",
                url=statement_url,
                headers={"Accept": "text/html"},
            )
        )

        if response.status_code == 404:
            return PageResult(items=(), next_cursor=None, has_more=False)
        if 500 <= response.status_code <= 599:
            raise RecoverableConnectorError(
                f"Federal Reserve returned {response.status_code} for {statement_url}."
            )
        if response.status_code != 200:
            raise ValueError(
                f"Unexpected status code {response.status_code} for {statement_url}."
            )

        html = response.text()
        fetched_at = datetime.now(timezone.utc)
        parsed = parse_fomc_statement_html(html, statement_url=response.url)

        item = normalize_fomc_statement(
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