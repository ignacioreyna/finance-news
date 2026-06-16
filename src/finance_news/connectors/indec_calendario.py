"""INDEC Calendar connector.

This connector fetches the official INDEC publication calendar, which includes
scheduled releases for key economic indicators such as IPC (inflation), EMAE
(activity), EPH (employment), Salarios (wages), Canasta (baskets), and Pobreza
(poverty indicators).

The calendar data is embedded as JSON in the HTML page at:
https://www.indec.gob.ar/Calendario/Fecha/0
"""

from __future__ import annotations

import json
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

CONNECTOR_NAME = "indec_calendario"
SOURCE_NAME = "indec"
PARSER_VERSION = "0.1.0"
CALENDARIO_URL = "https://www.indec.gob.ar/Calendario/Fecha/0"
DEFAULT_TTL_SECONDS = 6 * 60 * 60  # 6 hours

# Relevant datasets for weekly report filtering
WEEKLY_REPORT_DATASETS = {
    "IPC",
    "EMAE",
    "EPH",
    "Salarios",
    "Canasta",
    "Pobreza",
}


@dataclass(frozen=True)
class ParsedCalendarioEvent:
    """A single calendar event from INDEC.

    Attributes:
        event_id: Unique event identifier
        fecha: Publication date (YYYY-MM-DD format)
        hora: Publication time (HH:MM format)
        dataset: Dataset name (e.g., "IPC", "EMAE", "EPH", "Salarios", "Canasta", "Pobreza")
        titulo: Event title/description
        fuente: Source URL for more information
        tipo: Publication frequency (e.g., "mensual", "trimestral", "semestral")
    """

    event_id: str
    fecha: str
    hora: str
    dataset: str
    titulo: str
    fuente: str
    tipo: str

    @property
    def published_at(self) -> datetime:
        """Parse fecha and hora into a datetime object."""
        dt = datetime.strptime(f"{self.fecha} {self.hora}", "%Y-%m-%d %H:%M")
        return dt.replace(tzinfo=timezone.utc)


def extract_json_from_html(html_text: str) -> str:
    """Extract JSON content from the embedded script tag.

    Args:
        html_text: Raw HTML text from the calendar page.

    Returns:
        The JSON string extracted from the script tag with id="calendario-data".

    Raises:
        ValueError: If the script tag or JSON content is not found.
    """
    # Find the script tag with id="calendario-data"
    pattern = r'<script\s+id="calendario-data"\s+type="application/json">\s*(.*?)\s*</script>'
    match = re.search(pattern, html_text, re.DOTALL)

    if match is None:
        raise ValueError(
            "Could not find script tag with id='calendario-data' in HTML"
        )

    json_text = match.group(1).strip()
    if not json_text:
        raise ValueError("JSON content is empty in script tag")

    return json_text


def parse_calendario_json(json_text: str) -> list[ParsedCalendarioEvent]:
    """Parse INDEC calendar JSON text into structured events.

    Args:
        json_text: Raw JSON text extracted from the calendar page.

    Returns:
        List of parsed calendar events.

    Raises:
        ValueError: If the JSON is invalid or has unexpected structure.
    """
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object, got {type(data).__name__}")

    if "eventos" not in data:
        raise ValueError("Missing 'eventos' key in JSON")

    eventos = data["eventos"]
    if not isinstance(eventos, list):
        raise ValueError(f"Expected 'eventos' to be a list, got {type(eventos).__name__}")

    parsed_events: list[ParsedCalendarioEvent] = []
    for idx, evento in enumerate(eventos):
        if not isinstance(evento, dict):
            raise ValueError(f"Event {idx} is not a JSON object")

        # Validate required fields
        required_fields = ["id", "fecha", "hora", "dataset", "titulo", "fuente", "tipo"]
        for field in required_fields:
            if field not in evento:
                raise ValueError(f"Event {idx} missing required field: {field}")
            if not isinstance(evento[field], str):
                raise ValueError(
                    f"Event {idx} field '{field}' must be string, got {type(evento[field]).__name__}"
                )

        parsed_events.append(
            ParsedCalendarioEvent(
                event_id=evento["id"],
                fecha=evento["fecha"],
                hora=evento["hora"],
                dataset=evento["dataset"],
                titulo=evento["titulo"],
                fuente=evento["fuente"],
                tipo=evento["tipo"],
            )
        )

    return parsed_events


def parse_calendario_html(html_text: str) -> list[ParsedCalendarioEvent]:
    """Parse INDEC calendar HTML page into structured events.

    Args:
        html_text: Raw HTML text from the calendar page.

    Returns:
        List of parsed calendar events.

    Raises:
        ValueError: If the HTML cannot be parsed or JSON is invalid.
    """
    json_text = extract_json_from_html(html_text)
    return parse_calendario_json(json_text)


def normalize_calendario_event(
    *,
    parsed: ParsedCalendarioEvent,
    fetched_at: datetime,
    fetch_url: str,
    cursor: str | None,
    transport_metadata: dict[str, object] | None = None,
) -> SourceItem:
    """Normalize a parsed calendar event into a SourceItem.

    Args:
        parsed: The parsed calendar event.
        fetched_at: When the data was fetched.
        fetch_url: The URL used to fetch the data.
        cursor: Optional cursor for pagination.
        transport_metadata: Optional metadata from the HTTP transport.

    Returns:
        A normalized SourceItem.
    """
    metadata: dict[str, object] = {
        "dataset": parsed.dataset,
        "event_type": parsed.tipo,
        "publication_time": parsed.hora,
    }

    return SourceItem(
        external_id=parsed.event_id,
        source=SOURCE_NAME,
        published_at=parsed.published_at,
        title=parsed.titulo,
        body=None,
        summary=f"{parsed.dataset} - {parsed.titulo}",
        url=parsed.fuente,
        metadata=metadata,
        provenance=Provenance(
            connector=CONNECTOR_NAME,
            source=SOURCE_NAME,
            fetch_url=fetch_url,
            canonical_url=CALENDARIO_URL,
            cursor=cursor,
            fetched_at=fetched_at,
            parser_version=PARSER_VERSION,
            transport_metadata=transport_metadata or {},
        ),
        freshness=Freshness(
            published_at=parsed.published_at,
            first_seen_at=fetched_at,
            fetched_at=fetched_at,
            is_stale=False,
            ttl_seconds=DEFAULT_TTL_SECONDS,
        ),
    )


def filter_weekly_report_events(
    events: list[ParsedCalendarioEvent],
) -> list[ParsedCalendarioEvent]:
    """Filter calendar events to only those relevant for weekly reports.

    Args:
        events: List of parsed calendar events.

    Returns:
        Filtered list containing only events for datasets in WEEKLY_REPORT_DATASETS.
    """
    return [event for event in events if event.dataset in WEEKLY_REPORT_DATASETS]


class IndecCalendarioConnector:
    """Fetch INDEC publication calendar events.

    This connector fetches the official INDEC calendar and returns scheduled
    publication events for key economic indicators.
    """

    name = CONNECTOR_NAME
    source = SOURCE_NAME
    retry_policy = RetryPolicy(
        max_attempts=3,
        base_delay_seconds=1.0,
        max_delay_seconds=8.0,
    )
    rate_limit_policy = RateLimitPolicy(concurrency=1, burst=1)

    def __init__(
        self,
        *,
        transport: AsyncHttpTransport,
        filter_weekly_report: bool = False,
    ) -> None:
        """Initialize the connector.

        Args:
            transport: The HTTP transport to use for requests.
            filter_weekly_report: If True, filter events to only those relevant
                for weekly reports (IPC, EMAE, EPH, Salarios, Canasta, Pobreza).
        """
        self._transport = transport
        self._filter_weekly_report = filter_weekly_report

    async def fetch_page(
        self,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> PageResult:
        """Fetch a page of calendar events.

        Args:
            cursor: Optional cursor (not used for this connector).
            since: Optional datetime to filter events (not used for this connector).

        Returns:
            PageResult containing calendar events.

        Raises:
            ValueError: If the response status code is unexpected.
            RecoverableConnectorError: If the server returns a 5xx error.
        """
        del cursor, since  # Not used for this connector

        response = await self._transport.send(
            HttpRequest(
                method="GET",
                url=CALENDARIO_URL,
                headers={"Accept": "text/html,application/xhtml+xml"},
            )
        )

        if 500 <= response.status_code <= 599:
            raise RecoverableConnectorError(
                f"INDEC returned {response.status_code} for {CALENDARIO_URL}"
            )
        if response.status_code != 200:
            raise ValueError(
                f"Unexpected INDEC status code {response.status_code} for {CALENDARIO_URL}"
            )

        html_text = response.text(encoding="utf-8")
        fetched_at = datetime.now(timezone.utc)

        parsed_events = parse_calendario_html(html_text)

        # Apply weekly report filter if requested
        if self._filter_weekly_report:
            parsed_events = filter_weekly_report_events(parsed_events)

        # Normalize events to SourceItems
        items = []
        for event in parsed_events:
            item = normalize_calendario_event(
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

        # Calendar returns all events at once, no pagination
        return PageResult(items=tuple(items), next_cursor=None, has_more=False)