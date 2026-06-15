"""Boletin Oficial connector focused on financial signals."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser

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

CONNECTOR_NAME = "bora_financial"
SOURCE_NAME = "bora"
PARSER_VERSION = "0.1.0"
BASE_URL = "https://www.boletinoficial.gob.ar"
DEFAULT_TTL_SECONDS = 24 * 60 * 60

_DATE_RE = re.compile(r"(\d{2}/\d{2}/\d{4})")
_NOTICE_ID_RE = re.compile(r"/detalleAviso/primera/(?P<notice_id>\d+)/(?P<edition_date>\d{8})")
_WHITESPACE_RE = re.compile(r"\s+")

_ORGANIZATION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "bcra",
        re.compile(
            r"\b(bcra|banco central de la rep[uú]blica argentina)\b",
            re.IGNORECASE,
        ),
    ),
    ("economia", re.compile(r"\b(ministerio de econom[ií]a|secretar[ií]a de energ[ií]a)\b", re.IGNORECASE)),
    ("arca", re.compile(r"\b(arca|agencia de recaudaci[oó]n y control aduanero)\b", re.IGNORECASE)),
    ("cnv", re.compile(r"\b(cnv|comisi[oó]n nacional de valores)\b", re.IGNORECASE)),
)

_KEYWORD_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("deuda", re.compile(r"\bdeuda\b", re.IGNORECASE)),
    ("cambios", re.compile(r"\bcambi(?:o|os|aria|ario)\b", re.IGNORECASE)),
    ("energia", re.compile(r"\benerg[ií]a\b", re.IGNORECASE)),
    ("mineria", re.compile(r"\bminer[ií]a\b", re.IGNORECASE)),
    ("agro", re.compile(r"\b(agro|agricultura|ganader[ií]a|pesca)\b", re.IGNORECASE)),
)


@dataclass(frozen=True)
class ParsedBoraListingEntry:
    notice_id: str
    edition_date: str
    section: str
    document_type: str
    organism: str
    title: str
    summary: str | None
    detail_url: str

    @property
    def external_id(self) -> str:
        return f"primera-{self.notice_id}"


@dataclass(frozen=True)
class BoraClassification:
    is_relevant: bool
    matched_organizations: tuple[str, ...]
    matched_keywords: tuple[str, ...]


@dataclass(frozen=True)
class ParsedBoraDetail:
    body: str
    publication_date: datetime
    signed_date: datetime | None


class _ListingParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.entries: list[ParsedBoraListingEntry] = []
        self._current_heading_level: int | None = None
        self._current_heading_parts: list[str] = []
        self._current_document_type = ""
        self._current_anchor_href: str | None = None
        self._current_anchor_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._current_heading_level = int(tag[1])
            self._current_heading_parts = []
            return

        if tag == "a":
            self._current_anchor_href = dict(attrs).get("href")
            self._current_anchor_parts = []

    def handle_data(self, data: str) -> None:
        if self._current_heading_level is not None:
            self._current_heading_parts.append(data)
        if self._current_anchor_href is not None:
            self._current_anchor_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._current_heading_level is not None and tag == f"h{self._current_heading_level}":
            heading_text = _normalize_space("".join(self._current_heading_parts))
            if heading_text:
                self._current_document_type = heading_text
            self._current_heading_level = None
            self._current_heading_parts = []
            return

        if tag == "a" and self._current_anchor_href is not None:
            href = self._current_anchor_href
            anchor_text = _normalize_space("".join(self._current_anchor_parts))
            self._current_anchor_href = None
            self._current_anchor_parts = []

            if not href or "/detalleAviso/primera/" not in href or not anchor_text:
                return

            entry = _build_listing_entry(
                href=href,
                anchor_text=anchor_text,
                document_type=self._current_document_type,
            )
            if entry is not None:
                self.entries.append(entry)


def build_listing_url(edition_date: str | datetime) -> str:
    if isinstance(edition_date, datetime):
        normalized = edition_date.strftime("%Y%m%d")
    else:
        normalized = str(edition_date).strip()
    if not re.fullmatch(r"\d{8}", normalized):
        raise ValueError(f"Invalid BORA edition date: {edition_date!r}")
    return f"{BASE_URL}/seccion/primera/{normalized}"


def build_detail_url(notice_id: str | int, edition_date: str | datetime) -> str:
    normalized_notice_id = str(notice_id).strip()
    if not normalized_notice_id.isdigit():
        raise ValueError(f"Invalid BORA notice id: {notice_id!r}")
    if isinstance(edition_date, datetime):
        normalized_date = edition_date.strftime("%Y%m%d")
    else:
        normalized_date = str(edition_date).strip()
    if not re.fullmatch(r"\d{8}", normalized_date):
        raise ValueError(f"Invalid BORA edition date: {edition_date!r}")
    return f"{BASE_URL}/detalleAviso/primera/{normalized_notice_id}/{normalized_date}"


def parse_bora_listing(html: str) -> list[ParsedBoraListingEntry]:
    parser = _ListingParser()
    parser.feed(html)
    return parser.entries


def parse_bora_detail(html: str) -> ParsedBoraDetail:
    lines = _extract_text_lines(html)
    publication_date = _parse_publication_date(lines)
    signed_date = _parse_signed_date(lines)

    start_index = None
    for index, line in enumerate(lines):
        if line.startswith("# "):
            start_index = index + 1
            break
    if start_index is None:
        raise ValueError("Unable to locate BORA detail body start.")

    body_lines: list[str] = []
    for line in lines[start_index:]:
        if line.startswith("Fecha de publicación"):
            break
        if line in {
            "Ver páginas publicadas",
            "Ver texto del aviso",
            "Compartir por email",
            "Cerrar",
            "Enviar",
        }:
            continue
        if re.fullmatch(r"#{1,6}\s+.+", line):
            continue
        body_lines.append(line)

    body = _normalize_space("\n".join(body_lines)).strip()
    if not body:
        raise ValueError("Unable to extract BORA detail body.")

    return ParsedBoraDetail(
        body=body,
        publication_date=publication_date,
        signed_date=signed_date,
    )


def classify_bora_entry(
    *,
    organism: str,
    title: str,
    summary: str | None = None,
    body: str | None = None,
) -> BoraClassification:
    haystack = "\n".join(
        part for part in (organism, title, summary or "", body or "") if part
    )
    matched_organizations = tuple(
        label for label, pattern in _ORGANIZATION_PATTERNS if pattern.search(haystack)
    )
    matched_keywords = tuple(
        label for label, pattern in _KEYWORD_PATTERNS if pattern.search(haystack)
    )
    return BoraClassification(
        is_relevant=bool(matched_organizations or matched_keywords),
        matched_organizations=matched_organizations,
        matched_keywords=matched_keywords,
    )


def normalize_bora_entry(
    *,
    entry: ParsedBoraListingEntry,
    detail: ParsedBoraDetail,
    fetched_at: datetime,
    cursor: str,
    transport_metadata: dict[str, object] | None = None,
) -> SourceItem:
    classification = classify_bora_entry(
        organism=entry.organism,
        title=entry.title,
        summary=entry.summary,
        body=detail.body,
    )
    if not classification.is_relevant:
        raise ValueError("Entry does not match financial-signal filters.")

    metadata: dict[str, object] = {
        "edition_date": entry.edition_date,
        "section": entry.section,
        "document_type": entry.document_type,
        "organism": entry.organism,
        "matched_organizations": list(classification.matched_organizations),
        "matched_keywords": list(classification.matched_keywords),
    }
    if entry.summary is not None:
        metadata["summary_excerpt"] = entry.summary
    if detail.signed_date is not None:
        metadata["signed_date"] = detail.signed_date.isoformat()

    return SourceItem(
        external_id=entry.external_id,
        source=SOURCE_NAME,
        published_at=detail.publication_date,
        title=f"{entry.organism} - {entry.title}",
        body=detail.body,
        summary=entry.summary,
        url=entry.detail_url,
        metadata=metadata,
        provenance=Provenance(
            connector=CONNECTOR_NAME,
            source=SOURCE_NAME,
            fetch_url=entry.detail_url,
            canonical_url=entry.detail_url,
            cursor=cursor,
            fetched_at=fetched_at,
            parser_version=PARSER_VERSION,
            transport_metadata=transport_metadata or {},
        ),
        freshness=Freshness(
            published_at=detail.publication_date,
            first_seen_at=fetched_at,
            fetched_at=fetched_at,
            is_stale=False,
            ttl_seconds=DEFAULT_TTL_SECONDS,
        ),
    )


class BoraFinancialConnector:
    """Fetch and filter Boletin Oficial first-section notices by edition date."""

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
        del since
        if cursor is None:
            raise ValueError("BORA financial connector requires a YYYYMMDD cursor.")

        listing_url = build_listing_url(cursor)
        listing_response = await self._transport.send(
            HttpRequest(
                method="GET",
                url=listing_url,
                headers={"Accept": "text/html"},
            )
        )

        if 500 <= listing_response.status_code <= 599:
            raise RecoverableConnectorError(
                f"BORA returned {listing_response.status_code} for {listing_url}."
            )
        if listing_response.status_code != 200:
            raise ValueError(
                f"Unexpected BORA status code {listing_response.status_code} for {listing_url}."
            )

        fetched_at = datetime.now(timezone.utc)
        listing_entries = parse_bora_listing(listing_response.text())

        items: list[SourceItem] = []
        for entry in listing_entries:
            detail_response = await self._transport.send(
                HttpRequest(
                    method="GET",
                    url=entry.detail_url,
                    headers={"Accept": "text/html"},
                )
            )
            if 500 <= detail_response.status_code <= 599:
                raise RecoverableConnectorError(
                    f"BORA returned {detail_response.status_code} for {entry.detail_url}."
                )
            if detail_response.status_code != 200:
                raise ValueError(
                    f"Unexpected BORA status code {detail_response.status_code} for {entry.detail_url}."
                )

            detail = parse_bora_detail(detail_response.text())
            classification = classify_bora_entry(
                organism=entry.organism,
                title=entry.title,
                summary=entry.summary,
                body=detail.body,
            )
            if not classification.is_relevant:
                continue

            items.append(
                normalize_bora_entry(
                    entry=entry,
                    detail=detail,
                    fetched_at=fetched_at,
                    cursor=str(cursor),
                    transport_metadata={
                        "listing_status_code": listing_response.status_code,
                        "detail_status_code": detail_response.status_code,
                        "content_type": detail_response.headers.get("Content-Type"),
                    },
                )
            )

        return PageResult(items=tuple(items), next_cursor=None, has_more=False)


def _build_listing_entry(
    *,
    href: str,
    anchor_text: str,
    document_type: str,
) -> ParsedBoraListingEntry | None:
    match = _NOTICE_ID_RE.search(href)
    if match is None:
        return None

    detail_url = href if href.startswith("http") else f"{BASE_URL}{href}"
    organism, title = _split_listing_anchor_text(anchor_text)
    summary = None
    if " - " in title:
        main_title, summary = title.split(" - ", 1)
        title = main_title.strip()
        summary = summary.strip()

    return ParsedBoraListingEntry(
        notice_id=match.group("notice_id"),
        edition_date=match.group("edition_date"),
        section="primera",
        document_type=document_type.lower(),
        organism=organism,
        title=title,
        summary=summary,
        detail_url=detail_url,
    )


def _split_listing_anchor_text(anchor_text: str) -> tuple[str, str]:
    text = _normalize_space(anchor_text)
    separators = (" Resolución ", " Resolución General ", " Decreto ", " Aviso Oficial ")
    for separator in separators:
        if separator in text:
            organism, remainder = text.split(separator, 1)
            title = f"{separator.strip()} {remainder}".strip()
            return organism.strip(), title
    parts = text.split(" ", 1)
    if len(parts) == 1:
        return text, text
    return parts[0].strip(), parts[1].strip()


def _extract_text_lines(html: str) -> list[str]:
    text = html
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|div|section|article|li|ul|ol|table|tr|td|h1|h2|h3|h4|h5|h6)>", "\n", text)
    text = re.sub(r"(?i)<h([1-6])[^>]*>", lambda match: "\n" + ("#" * int(match.group(1))) + " ", text)
    text = re.sub(r"(?is)<script.*?</script>", "", text)
    text = re.sub(r"(?is)<style.*?</style>", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    lines = [_normalize_space(line) for line in text.splitlines()]
    return [line for line in lines if line]


def _parse_publication_date(lines: list[str]) -> datetime:
    for line in reversed(lines):
        if line.startswith("Fecha de publicación"):
            match = _DATE_RE.search(line)
            if match is None:
                break
            return datetime.strptime(match.group(1), "%d/%m/%Y").replace(tzinfo=timezone.utc)
    raise ValueError("Unable to parse BORA publication date.")


def _parse_signed_date(lines: list[str]) -> datetime | None:
    for line in lines:
        if line.startswith("Ciudad de Buenos Aires"):
            match = _DATE_RE.search(line)
            if match is None:
                return None
            return datetime.strptime(match.group(1), "%d/%m/%Y").replace(tzinfo=timezone.utc)
    return None


def _normalize_space(value: str) -> str:
    return _WHITESPACE_RE.sub(" ", value).strip()
