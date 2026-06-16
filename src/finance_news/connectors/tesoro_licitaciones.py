"""Tesoro argentino - licitaciones (llamados y resultados) connector.

Scrapes the official Ministerio de Economia / Secretaria de Finanzas pages for
Argentine Treasury debt auctions: it normalizes per-instrument ``llamado`` (call)
and ``resultado`` (result) events and resolves the listing/download links that
the CMS exposes for cronogramas, resultados historicos and colocaciones.

The source is plain HTML (no API, no key). Parsing is performed with the stdlib
``html.parser.HTMLParser`` only.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from typing import Any, Mapping
from urllib.parse import urljoin

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

CONNECTOR_NAME = "tesoro_licitaciones"
SOURCE_NAME = "tesoro"
PARSER_VERSION = "0.1.0"
DEFAULT_TTL_SECONDS = 24 * 60 * 60

BASE_ORIGIN = "https://www.argentina.gob.ar"
DEFAULT_PAGE_URL = (
    "https://www.argentina.gob.ar/noticias/"
    "resultado-de-la-licitacion-por-efectivo-de-instrumentos-del-tesoro-"
    "nacional-denominados-4"
)
DEFAULT_LISTING_URL = "https://www.argentina.gob.ar/economia/licitaciones"

_MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

_DATE_RE = re.compile(
    r"(\d{1,2})\s+de\s+("
    + "|".join(_MONTHS.keys())
    + r")\s+de\s+(\d{4})",
    re.IGNORECASE,
)
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_DOWNLOAD_EXT_RE = re.compile(r"\.(xlsx?|pdf|csv|docx?|zip|rtf)(?:[?#]|$)", re.IGNORECASE)
_CURRENCY_RE = re.compile(r"^\s*(USD|US\$|U\$S|ARS\$|\$)", re.IGNORECASE)
_NUMBER_RE = re.compile(r"-?\d[\d.\s]*(?:,\d+)?")
_WHITESPACE_RE = re.compile(r"\s+")

# Header-cell classifiers used to map columns inside instrument tables.
_HEADER_CLASSIFIERS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("instrumento", re.compile(r"instrumento", re.IGNORECASE)),
    ("vencimiento", re.compile(r"fecha\s+de\s+vencimiento|vencimiento", re.IGNORECASE)),
    ("vno_ofertado", re.compile(r"vno.*ofertado", re.IGNORECASE)),
    ("vno_adjudicado", re.compile(r"vno.*adjudicado", re.IGNORECASE)),
    ("ve_adjudicado", re.compile(r"valor\s+efectivo", re.IGNORECASE)),
    ("precio_corte", re.compile(r"precio\s+de\s+(corte|colocaci)", re.IGNORECASE)),
    ("tna", re.compile(r"\btna\b", re.IGNORECASE)),
    ("tirea", re.compile(r"tirea", re.IGNORECASE)),
    ("monto_maximo", re.compile(r"monto", re.IGNORECASE)),
)

# A table is treated as an instrument table when its header carries at least one
# of these value-column markers.
_INSTRUMENT_TABLE_RE = re.compile(
    r"vno|valor\s+efectivo|precio\s+de\s+(corte|colocaci)|\b TireA| TireA|\btna\b|"
    r"monto",
    re.IGNORECASE,
)
_SOCIAL_HOSTS = (
    "facebook.",
    "linkedin.",
    "twitter.",
    "x.com",
    "t.me",
    "telegram",
    "whatsapp",
    "mailto:",
    "javascript:",
    "instagram.",
    "youtube.",
)
_LISTING_KEYWORDS_RE = re.compile(
    r"licitaci|cronograma|resultado|colocaci|llamado|conversi|canje|bono|letra",
    re.IGNORECASE,
)
_SUMMARY_ROW_RE = re.compile(r"^(cantidad|total|instrumentos\s|resultado\b)", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Dataclasses
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ParsedTesoroInstrumento:
    """A single normalized llamado/resultado event for one instrument."""

    instrumento: str
    event_type: str
    fecha: datetime
    moneda: str
    source_url: str
    vno_ofertado: float | None = None
    vno_adjudicado: float | None = None
    ve_adjudicado: float | None = None
    precio_corte: float | None = None
    tna: float | None = None
    tirea: float | None = None
    monto_maximo: float | None = None
    monto_maximo_text: str | None = None
    vencimiento: str | None = None
    currency_group: str | None = None

    @property
    def external_id(self) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", self.instrumento.lower()).strip("-")
        slug = slug[:60].strip("-") or "instrumento"
        return f"{self.event_type}-{self.fecha.strftime('%Y%m%d')}-{slug}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrumento": self.instrumento,
            "event_type": self.event_type,
            "fecha": self.fecha.isoformat(),
            "moneda": self.moneda,
            "source_url": self.source_url,
            "vno_ofertado": self.vno_ofertado,
            "vno_adjudicado": self.vno_adjudicado,
            "ve_adjudicado": self.ve_adjudicado,
            "precio_corte": self.precio_corte,
            "tna": self.tna,
            "tirea": self.tirea,
            "monto_maximo": self.monto_maximo,
            "monto_maximo_text": self.monto_maximo_text,
            "vencimiento": self.vencimiento,
            "currency_group": self.currency_group,
            "external_id": self.external_id,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ParsedTesoroInstrumento":
        fecha = data["fecha"]
        if isinstance(fecha, str):
            fecha = datetime.fromisoformat(fecha)
        return cls(
            instrumento=str(data["instrumento"]),
            event_type=str(data["event_type"]),
            fecha=fecha,
            moneda=str(data["moneda"]),
            source_url=str(data["source_url"]),
            vno_ofertado=data.get("vno_ofertado"),
            vno_adjudicado=data.get("vno_adjudicado"),
            ve_adjudicado=data.get("ve_adjudicado"),
            precio_corte=data.get("precio_corte"),
            tna=data.get("tna"),
            tirea=data.get("tirea"),
            monto_maximo=data.get("monto_maximo"),
            monto_maximo_text=data.get("monto_maximo_text"),
            vencimiento=data.get("vencimiento"),
            currency_group=data.get("currency_group"),
        )


@dataclass(frozen=True)
class ParsedTesoroLink:
    """A discovered link on a Tesoro listing/cronograma page."""

    text: str
    url: str
    kind: str  # "download" | "page"

    def to_dict(self) -> dict[str, Any]:
        return {"text": self.text, "url": self.url, "kind": self.kind}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ParsedTesoroLink":
        return cls(
            text=str(data["text"]),
            url=str(data["url"]),
            kind=str(data["kind"]),
        )


# --------------------------------------------------------------------------- #
# HTML extraction primitives (stdlib only)
# --------------------------------------------------------------------------- #
class _TableExtractor(HTMLParser):
    """Extract tables as a list of rows of cleaned cell text."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "table" and self._table is not None:
            if self._table:
                self.tables.append(self._table)
            self._table = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            self._table.append(self._row)
            self._row = None
        elif tag in ("td", "th") and self._cell is not None:
            if self._row is not None:
                self._row.append(_normalize_ws("".join(self._cell)))
            self._cell = None

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)


class _LinkExtractor(HTMLParser):
    """Extract page and download links from a listing/cronograma page."""

    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.links: list[ParsedTesoroLink] = []
        self._seen: set[str] = set()
        self._href: str | None = None
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or self._href is None:
            return
        href = self._href
        text = _normalize_ws("".join(self._parts))
        self._href = None
        self._parts = []
        if not href:
            return
        lower = href.lower()
        if any(social in lower for social in _SOCIAL_HOSTS):
            return
        absolute = urljoin(self.base_url, href.strip())
        if absolute in self._seen:
            return
        kind = "download" if _DOWNLOAD_EXT_RE.search(absolute) else None
        if kind is None:
            if not _LISTING_KEYWORDS_RE.search(text) and not _LISTING_KEYWORDS_RE.search(
                absolute
            ):
                return
            kind = "page"
        self._seen.add(absolute)
        self.links.append(ParsedTesoroLink(text=text, url=absolute, kind=kind))


def extract_tables(html: str) -> list[list[list[str]]]:
    """Return every ``<table>`` in ``html`` as a list of rows of cell text."""
    parser = _TableExtractor()
    parser.feed(html)
    parser.close()
    return parser.tables


def _extract_title(html: str) -> str:
    match = _TITLE_RE.search(html)
    if match is None:
        return ""
    return _normalize_ws(unescape(match.group(1)))


def _extract_fecha(html: str, default: datetime | None = None) -> datetime | None:
    match = _DATE_RE.search(html)
    if match is None:
        return default
    day = int(match.group(1))
    month = _MONTHS[match.group(2).lower()]
    year = int(match.group(3))
    return datetime(year, month, day, tzinfo=timezone.utc)


def _detect_event_type(title: str, tables: list[list[list[str]]]) -> str:
    lower = title.lower()
    if "resultado" in lower or "segunda vuelta" in lower or "adjudicado" in lower:
        return "resultado"
    if "llamado" in lower:
        return "llamado"
    # Infer from headers: presence of adjudicado columns => result page.
    for table in tables:
        if not table:
            continue
        header_blob = " ".join(table[0])
        if "adjudicado" in header_blob.lower():
            return "resultado"
        if "licitar" in header_blob.lower() or "colocar" in header_blob.lower():
            return "llamado"
    return "resultado"


def _normalize_ws(value: str) -> str:
    if not value:
        return ""
    value = value.replace("\xa0", " ")
    return _WHITESPACE_RE.sub(" ", value).strip()


def _parse_spanish_number(raw: str) -> float | None:
    """Parse a Spanish-locale numeric token (``1.940.448`` / ``890,00``)."""
    match = _NUMBER_RE.search(raw)
    if match is None:
        return None
    token = match.group(0).replace(" ", "")
    # Spanish thousands separators use '.'; decimal uses ','.
    token = token.replace(".", "").replace(",", ".")
    try:
        return float(token)
    except ValueError:
        return None


def _parse_cell(raw: str) -> tuple[str | None, float | None]:
    """Return ``(currency, number)`` parsed from a cell.

    ``currency`` is ``"ARS"`` for ``$`` prefixes, ``"USD"`` for dollar prefixes,
    or ``None`` when the cell carries no currency token.
    """
    text = (raw or "").strip()
    if not text:
        return None, None
    cur_match = _CURRENCY_RE.match(text)
    currency: str | None = None
    body = text
    if cur_match is not None:
        token = cur_match.group(1).upper()
        currency = "USD" if token in {"USD", "US$", "U$S"} else "ARS"
        body = text[cur_match.end():]
    number = _parse_spanish_number(body)
    return currency, number


# --------------------------------------------------------------------------- #
# Public pure parsers
# --------------------------------------------------------------------------- #
def parse_tesoro_licitaciones_html(
    html: str,
    *,
    page_url: str = "",
) -> list[ParsedTesoroInstrumento]:
    """Parse a Tesoro llamado/resultado page into per-instrument events.

    Pure and synchronous: takes the raw HTML and returns normalized instrument
    events with fecha, moneda, montos and ``source_url``. Tables that are pure
    summary/totals blocks are skipped; only per-instrument rows are emitted.
    """
    title = _extract_title(html)
    fecha = _extract_fecha(html)
    tables = extract_tables(html)
    event_type = _detect_event_type(title, tables)
    fallback_fecha = fecha or datetime(1970, 1, 1, tzinfo=timezone.utc)

    instruments: list[ParsedTesoroInstrumento] = []
    for table in tables:
        rows = [r for r in table if r]
        if len(rows) < 2:
            continue
        header = rows[0]
        header_blob = " ".join(header)
        if not _INSTRUMENT_TABLE_RE.search(header_blob):
            continue
        column_map = _map_columns(header)
        group_label = _normalize_ws(header[0]) if header else None

        for row in rows[1:]:
            if not row:
                continue
            instrumento = _cell_at(row, column_map.get("instrumento", 0)) or _cell_at(row, 0)
            instrumento = _normalize_ws(instrumento)
            if not instrumento:
                continue
            if _SUMMARY_ROW_RE.match(instrumento):
                continue
            # Skip repeated header rows.
            if instrumento.lower() == (_normalize_ws(header[0] if header else "")).lower():
                continue

            moneda, vno_ofertado = _currency_and_number(row, column_map.get("vno_ofertado"))
            _, vno_adjudicado = _currency_and_number(row, column_map.get("vno_adjudicado"))
            ve_cur, ve_adjudicado = _currency_and_number(row, column_map.get("ve_adjudicado"))
            _, precio_corte = _currency_and_number(row, column_map.get("precio_corte"))
            _, tna = _currency_and_number(row, column_map.get("tna"))
            _, tirea = _currency_and_number(row, column_map.get("tirea"))
            monto_cur, monto_maximo = _currency_and_number(row, column_map.get("monto_maximo"))
            monto_maximo_text = _normalize_ws(_cell_at(row, column_map.get("monto_maximo"))) or None
            vencimiento = _normalize_ws(_cell_at(row, column_map.get("vencimiento"))) or None

            # Resolve moneda preferring VNO currency, then VE, then monto maximo.
            if moneda is None:
                moneda = ve_cur or monto_cur or "ARS"

            instruments.append(
                ParsedTesoroInstrumento(
                    instrumento=instrumento,
                    event_type=event_type,
                    fecha=fecha or fallback_fecha,
                    moneda=moneda,
                    source_url=page_url,
                    vno_ofertado=vno_ofertado,
                    vno_adjudicado=vno_adjudicado,
                    ve_adjudicado=ve_adjudicado,
                    precio_corte=precio_corte,
                    tna=tna,
                    tirea=tirea,
                    monto_maximo=monto_maximo,
                    monto_maximo_text=monto_maximo_text,
                    vencimiento=vencimiento,
                    currency_group=group_label,
                )
            )
    return instruments


def parse_tesoro_listing_html(
    html: str,
    *,
    base_url: str = BASE_ORIGIN,
) -> list[ParsedTesoroLink]:
    """Extract licitaciones-related page links and download links.

    Used against the licitaciones hub and cronograma pages to resolve the
    ``Descargar`` file URLs (XLSX/PDF/CSV) and the internal sub-page links
    (cronograma, histórico de resultados, colocaciones).
    """
    parser = _LinkExtractor(base_url=base_url)
    parser.feed(html)
    parser.close()
    return list(parser.links)


def resolve_download_link(href: str | None, *, base_url: str = BASE_ORIGIN) -> str | None:
    """Resolve a single ``href`` to an absolute download URL.

    Returns ``None`` when the href is not a file download (XLSX/PDF/CSV/...).
    """
    if not href:
        return None
    absolute = urljoin(base_url, href.strip())
    if _DOWNLOAD_EXT_RE.search(absolute):
        return absolute
    return None


def resolve_download_links(
    html: str,
    *,
    base_url: str = BASE_ORIGIN,
) -> list[str]:
    """Return every absolute download URL discovered in ``html``."""
    return [
        link.url
        for link in parse_tesoro_listing_html(html, base_url=base_url)
        if link.kind == "download"
    ]


def normalize_tesoro_instrumento(
    *,
    parsed: ParsedTesoroInstrumento,
    fetched_at: datetime,
    fetch_url: str,
    raw_hash: str,
    cursor: str | None = None,
    transport_metadata: dict[str, object] | None = None,
) -> SourceItem:
    """Normalize a parsed instrument event into a ``SourceItem``.

    Official fields (read straight from the page) and derived calculations are
    kept in separate metadata sub-dicts so callers can distinguish primary
    official data from connector-computed values.
    """
    official: dict[str, object] = {
        "instrumento": parsed.instrumento,
        "moneda": parsed.moneda,
        "fecha_licitacion": parsed.fecha.date().isoformat(),
        "currency_group": parsed.currency_group,
        "vno_ofertado": parsed.vno_ofertado,
        "vno_adjudicado": parsed.vno_adjudicado,
        "ve_adjudicado": parsed.ve_adjudicado,
        "precio_corte": parsed.precio_corte,
        "tna": parsed.tna,
        "tirea": parsed.tirea,
        "monto_maximo": parsed.monto_maximo,
        "monto_maximo_text": parsed.monto_maximo_text,
        "vencimiento": parsed.vencimiento,
    }

    derived: dict[str, object] = {"is_derived": True}
    if (
        parsed.vno_ofertado
        and parsed.vno_adjudicado is not None
        and parsed.vno_ofertado > 0
    ):
        derived["adjudication_rate"] = (
            parsed.vno_adjudicado / parsed.vno_ofertado
        )
    if not any(
        k != "is_derived" for k in derived
    ):
        derived["is_derived"] = False

    monto = parsed.ve_adjudicado
    if monto is None:
        monto = parsed.vno_adjudicado
    if monto is None:
        monto = parsed.monto_maximo
    if monto is None:
        # Carry the official textual statement when no numeric monto exists
        # (e.g. llamado pages publish "Hasta el monto máximo autorizado...").
        monto = parsed.monto_maximo_text

    metadata: dict[str, object] = {
        "event_type": parsed.event_type,
        # The row itself is official primary data straight from the page.
        "data_classification": "official_primary",
        "moneda": parsed.moneda,
        "fecha_licitacion": parsed.fecha.date().isoformat(),
        "monto": monto,
        "official": official,
        "derived": derived,
    }

    title = f"[{parsed.event_type.upper()}] {parsed.instrumento} ({parsed.moneda})"
    summary_parts = [f"{parsed.event_type.capitalize()} {parsed.moneda}"]
    if parsed.vno_adjudicado is not None:
        summary_parts.append(
            f"VNO adjudicado {parsed.moneda} {parsed.vno_adjudicado:,.2f}"
        )
    if parsed.ve_adjudicado is not None:
        summary_parts.append(f"VE adjudicado {parsed.ve_adjudicado:,.2f}")
    if parsed.monto_maximo is not None:
        summary_parts.append(
            f"monto máximo {parsed.moneda} {parsed.monto_maximo:,.2f}"
        )
    summary = " - ".join(summary_parts)

    return SourceItem(
        external_id=parsed.external_id,
        source=SOURCE_NAME,
        published_at=parsed.fecha,
        title=title,
        body=parsed.instrumento,
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
            transport_metadata={
                **(transport_metadata or {}),
                "raw_hash": raw_hash,
            },
        ),
        freshness=Freshness(
            published_at=parsed.fecha,
            first_seen_at=fetched_at,
            fetched_at=fetched_at,
            is_stale=False,
            ttl_seconds=DEFAULT_TTL_SECONDS,
        ),
    )


# --------------------------------------------------------------------------- #
# Connector
# --------------------------------------------------------------------------- #
class TesoroLicitacionesConnector:
    """Fetch and normalize Tesoro licitaciones (llamados y resultados) pages."""

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
        default_url: str = DEFAULT_PAGE_URL,
    ) -> None:
        self._transport = transport
        self._default_url = default_url

    async def fetch_page(
        self,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> PageResult:
        del since
        url = cursor or self._default_url

        response = await self._transport.send(
            HttpRequest(
                method="GET",
                url=url,
                headers={"Accept": "text/html"},
            )
        )

        status = response.status_code
        if status == 200:
            pass
        elif 400 <= status <= 599:
            raise RecoverableConnectorError(
                f"Tesoro returned {status} for {url}."
            )
        elif 100 <= status <= 199 or 300 <= status <= 399:
            raise ValueError(
                f"Unexpected Tesoro status code {status} for {url}."
            )
        else:
            raise ValueError(
                f"Unexpected Tesoro status code {status} for {url}."
            )

        body = response.body
        html = response.text()
        raw_hash = hashlib.sha256(body).hexdigest()
        fetched_at = datetime.now(timezone.utc)

        parsed_rows = parse_tesoro_licitaciones_html(html=html, page_url=response.url)
        items = tuple(
            normalize_tesoro_instrumento(
                parsed=row,
                fetched_at=fetched_at,
                fetch_url=response.url,
                raw_hash=raw_hash,
                cursor=url,
                transport_metadata={
                    "status_code": status,
                    "content_type": response.headers.get("Content-Type"),
                },
            )
            for row in parsed_rows
        )

        return PageResult(items=items, next_cursor=None, has_more=False)


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #
def _map_columns(header: list[str]) -> dict[str, int]:
    """Map each known field to a column index from a header row."""
    mapping: dict[str, int] = {}
    used: set[int] = set()
    # Instrument column first: prefer an explicit 'instrumento' header,
    # otherwise default to the first column.
    for idx, cell in enumerate(header):
        if "instrumento" in cell.lower():
            mapping["instrumento"] = idx
            used.add(idx)
            break
    if "instrumento" not in mapping:
        mapping["instrumento"] = 0
        used.add(0)

    for kind, pattern in _HEADER_CLASSIFIERS:
        if kind == "instrumento":
            continue
        for idx, cell in enumerate(header):
            if idx in used:
                continue
            if pattern.search(cell):
                mapping[kind] = idx
                used.add(idx)
                break
    return mapping


def _cell_at(row: list[str], idx: int | None) -> str:
    if idx is None or idx < 0 or idx >= len(row):
        return ""
    return row[idx]


def _currency_and_number(
    row: list[str], idx: int | None
) -> tuple[str | None, float | None]:
    return _parse_cell(_cell_at(row, idx))


__all__ = [
    "BASE_ORIGIN",
    "CONNECTOR_NAME",
    "DEFAULT_LISTING_URL",
    "DEFAULT_PAGE_URL",
    "DEFAULT_TTL_SECONDS",
    "PARSER_VERSION",
    "ParsedTesoroInstrumento",
    "ParsedTesoroLink",
    "SOURCE_NAME",
    "TesoroLicitacionesConnector",
    "extract_tables",
    "normalize_tesoro_instrumento",
    "parse_tesoro_licitaciones_html",
    "parse_tesoro_listing_html",
    "resolve_download_link",
    "resolve_download_links",
]
