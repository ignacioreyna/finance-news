"""BCRA Calendario de Informes connector."""

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

CONNECTOR_NAME = "bcra_calendario"
SOURCE_NAME = "bcra"
PARSER_VERSION = "0.1.0"
BASE_CALENDAR_URL = "https://www.bcra.gob.ar/calendario-de-informes/"
DEFAULT_TTL_SECONDS = 24 * 60 * 60  # 24 hours for calendar

_MONTH_MAP_ES = {
    "ene": 1,
    "feb": 2,
    "mar": 3,
    "abr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dic": 12,
}


@dataclass(frozen=True)
class ParsedCalendarEvent:
    """A parsed BCRA calendar event."""

    informe: str
    fecha: datetime | None
    frecuencia: str
    fuente: str
    external_id: str


class _CalendarTableParser(hp.HTMLParser):
    """Extract calendar table data from BCRA HTML."""

    def __init__(self) -> None:
        super().__init__()
        self._in_target_div = False
        self._in_table = False
        self._in_row = False
        self._in_cell = False
        self._cell_index = 0
        self._current_row_cells: list[str] = []
        self._events: list[tuple[str, str]] = []
        self._skip_headers = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "div":
            for attr_name, attr_value in attrs:
                if attr_name == "id" and attr_value == "tabla-rowcolspan-events":
                    self._in_target_div = True
                    break

        if not self._in_target_div:
            return

        if tag == "table":
            self._in_table = True
        elif self._in_table and tag == "tr":
            self._in_row = True
            self._cell_index = 0
            self._current_row_cells = []
        elif self._in_row and tag == "td":
            self._in_cell = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "div" and self._in_target_div:
            self._in_target_div = False
            self._in_table = False
            return

        if not self._in_target_div:
            return

        if tag == "table" and self._in_table:
            self._in_table = False
        elif tag == "tr" and self._in_row:
            self._in_row = False
            # Only add events that have exactly 2 cells (informe, fecha)
            if len(self._current_row_cells) >= 2:
                self._events.append(
                    (self._current_row_cells[0], self._current_row_cells[1])
                )
            self._current_row_cells = []
        elif tag == "td" and self._in_cell:
            self._in_cell = False
            self._cell_index += 1

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._current_row_cells.append(data.strip())

    def get_events(self) -> list[tuple[str, str]]:
        """Return parsed (informe, fecha) tuples."""
        return self._events


def _parse_spanish_date(date_str: str) -> datetime | None:
    """Parse a Spanish date string like '07 ene 2026' to datetime."""
    if not date_str or date_str == "Actualización diaria *":
        return None

    date_str = date_str.strip().lower()
    parts = date_str.split()

    if len(parts) != 3:
        return None

    try:
        day = int(parts[0])
        month_str = parts[1]
        year = int(parts[2])

        month = _MONTH_MAP_ES.get(month_str)
        if month is None:
            return None

        return datetime(year, month, day, tzinfo=timezone.utc)
    except (ValueError, IndexError):
        return None


def _infer_frequency(informe: str) -> str:
    """Infer frequency from report name."""
    informe_lower = informe.lower()

    if "diario" in informe_lower:
        return "diaria"
    elif any(
        word in informe_lower
        for word in [
            "mensual",
            "mensualmente",
            "boletín estadístico",
            "rem",
            "balance cambiario",
            "mercado de cambios",
            "bancos",
            "inversión extranjera",
            "pagos minoristas",
            "condiciones crediticias",
            "estabilidad financiera",
            "inclusión financiera",
            "protección a las personas usuarias",
            "estados contables",
        ]
    ):
        return "mensual"
    elif any(
        word in informe_lower
        for word in [
            "trimestral",
            "trimestralmente",
        ]
    ):
        return "trimestral"
    elif "periódico" in informe_lower or "ipom" in informe_lower:
        return "periódica"
    else:
        return "no especificada"


def parse_bcra_calendario_html(html: str) -> list[ParsedCalendarEvent]:
    """Parse BCRA calendar HTML into structured events."""
    parser = _CalendarTableParser()
    parser.feed(html)

    events: list[ParsedCalendarEvent] = []
    seen_ids = set()

    for idx, (informe, fecha_str) in enumerate(parser.get_events()):
        # Skip the daily update row - it's not a real event
        if "Informe Monetario Diario" in informe and fecha_str == "Actualización diaria *":
            continue

        fecha = _parse_spanish_date(fecha_str)
        frecuencia = _infer_frequency(informe)
        fuente = "BCRA"

        # Create external_id from informe and date for uniqueness
        fecha_part = fecha.strftime("%Y-%m-%d") if fecha else "fecha-no-especificada"
        informe_slug = re.sub(r"[^\w]", "_", informe.lower())[:50]
        external_id = f"{informe_slug}_{fecha_part}"

        if external_id not in seen_ids:
            seen_ids.add(external_id)
            events.append(
                ParsedCalendarEvent(
                    informe=informe,
                    fecha=fecha,
                    frecuencia=frecuencia,
                    fuente=fuente,
                    external_id=external_id,
                )
            )

    return events


def normalize_bcra_calendario_event(
    *,
    parsed: ParsedCalendarEvent,
    fetched_at: datetime,
    fetch_url: str,
    cursor: str | None,
    transport_metadata: dict[str, object] | None = None,
) -> SourceItem:
    """Normalize a parsed calendar event into a SourceItem."""
    metadata: dict[str, object] = {
        "informe": parsed.informe,
        "frecuencia": parsed.frecuencia,
        "fuente": parsed.fuente,
    }

    # Create a human-readable title
    fecha_str = parsed.fecha.strftime("%Y-%m-%d") if parsed.fecha else "fecha no especificada"
    title = f"{parsed.informe} - {fecha_str}"

    # Create a summary with key information
    summary_parts = [f"Fecha: {fecha_str}", f"Frecuencia: {parsed.frecuencia}"]
    summary = ". ".join(summary_parts) + "."

    return SourceItem(
        external_id=parsed.external_id,
        source=SOURCE_NAME,
        published_at=parsed.fecha,
        title=title,
        body=None,  # Calendar events don't have body content
        summary=summary,
        url=fetch_url,
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
            published_at=parsed.fecha,
            first_seen_at=fetched_at,
            fetched_at=fetched_at,
            is_stale=False,
            ttl_seconds=DEFAULT_TTL_SECONDS,
        ),
    )


class BcraCalendarioConnector:
    """Fetch BCRA publication calendar events."""

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
        """Fetch a page of calendar events."""
        del since, cursor  # Calendar doesn't support pagination or filtering

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
                f"BCRA returned {response.status_code} for {BASE_CALENDAR_URL}."
            )
        if response.status_code != 200:
            raise ValueError(
                f"Unexpected BCRA status code {response.status_code} for {BASE_CALENDAR_URL}."
            )

        html = response.text()
        fetched_at = datetime.now(timezone.utc)
        events = parse_bcra_calendario_html(html)

        # Normalize all events
        items = []
        for event in events:
            item = normalize_bcra_calendario_event(
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