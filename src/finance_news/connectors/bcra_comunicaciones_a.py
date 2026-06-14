"""BCRA Comunicaciones A connector."""

from __future__ import annotations

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

CONNECTOR_NAME = "bcra_comunicaciones_a"
SOURCE_NAME = "bcra"
PARSER_VERSION = "0.1.0"
BASE_DOCUMENT_URL = "https://www.bcra.gob.ar/archivos/Pdfs/comytexord/A{number}.pdf"
DEFAULT_TTL_SECONDS = 30 * 24 * 60 * 60

_HEADER_RE = re.compile(
    r"COMUNICACIÓN\s+[\"“”]?A[\"“”]?\s+(?P<number>\d+)\s+(?P<date>\d{2}/\d{2}/\d{4})",
    re.IGNORECASE,
)


class PdfTextExtractor(Protocol):
    """Extract plain text from PDF bytes."""

    def extract_text(self, pdf_bytes: bytes) -> str:
        """Return extracted text for a PDF payload."""


class MissingPdfTextExtractorError(RuntimeError):
    """Raised when no PDF text extraction backend is available."""


class PypdfTextExtractor:
    """PDF text extractor backed by pypdf when present."""

    def __init__(self) -> None:
        try:
            from pypdf import PdfReader  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - depends on environment
            raise MissingPdfTextExtractorError(
                "PDF text extraction requires the optional 'pypdf' dependency."
            ) from exc

        self._reader_cls = PdfReader

    def extract_text(self, pdf_bytes: bytes) -> str:
        from io import BytesIO

        reader = self._reader_cls(BytesIO(pdf_bytes))
        parts: list[str] = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text:
                parts.append(page_text)

        text = "\n".join(parts).strip()
        if not text:
            raise ValueError("The PDF extractor returned empty text.")
        return text


@dataclass(frozen=True)
class ParsedBcraComunicacionA:
    number: str
    external_id: str
    published_at: datetime
    title: str
    text: str
    circular_reference: str | None


def build_document_url(number: int | str) -> str:
    normalized_number = _normalize_number(number)
    return BASE_DOCUMENT_URL.format(number=normalized_number)


def parse_bcra_comunicacion_a_text(text: str) -> ParsedBcraComunicacionA:
    cleaned_text = _clean_extracted_text(text)
    lines = [line.strip() for line in cleaned_text.splitlines()]
    non_empty_lines = [line for line in lines if line]

    header_match = _HEADER_RE.search(cleaned_text)
    if header_match is None:
        raise ValueError("Unable to parse BCRA communication header.")

    number = header_match.group("number")
    published_at = datetime.strptime(
        header_match.group("date"), "%d/%m/%Y"
    ).replace(tzinfo=timezone.utc)

    separator_index = next(
        (index for index, line in enumerate(non_empty_lines) if set(line) == {"_"}),
        None,
    )
    if separator_index is None:
        raise ValueError("Unable to locate BCRA communication title separator.")

    title_block = non_empty_lines[4:separator_index]
    circular_reference: str | None = None
    if title_block and title_block[0].lower().startswith("ref.: circular"):
        title_block = title_block[1:]
    if title_block and re.search(r"\d", title_block[0]):
        circular_reference = title_block[0].rstrip(":")
        title_block = title_block[1:]
    if not title_block:
        raise ValueError("Unable to extract BCRA communication title.")

    title = _join_wrapped_lines(title_block)
    return ParsedBcraComunicacionA(
        number=number,
        external_id=f"A{number}",
        published_at=published_at,
        title=title,
        text=cleaned_text,
        circular_reference=circular_reference,
    )


def normalize_bcra_comunicacion_a(
    *,
    parsed: ParsedBcraComunicacionA,
    fetched_at: datetime,
    fetch_url: str,
    cursor: str | None,
    transport_metadata: dict[str, object] | None = None,
) -> SourceItem:
    metadata: dict[str, object] = {
        "document_number": parsed.number,
        "document_type": "comunicacion_a",
    }
    if parsed.circular_reference is not None:
        metadata["circular_reference"] = parsed.circular_reference

    return SourceItem(
        external_id=parsed.external_id,
        source=SOURCE_NAME,
        published_at=parsed.published_at,
        title=parsed.title,
        body=parsed.text,
        summary=None,
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
            published_at=parsed.published_at,
            first_seen_at=fetched_at,
            fetched_at=fetched_at,
            is_stale=False,
            ttl_seconds=DEFAULT_TTL_SECONDS,
        ),
    )


class BcraComunicacionesAConnector:
    """Fetch a single Comunicación A PDF by number."""

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
        text_extractor: PdfTextExtractor | None = None,
    ) -> None:
        self._transport = transport
        self._text_extractor = text_extractor or PypdfTextExtractor()

    async def fetch_page(
        self,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> PageResult:
        del since
        if cursor is None:
            raise ValueError("BCRA Comunicaciones A requires a communication number cursor.")

        url = build_document_url(cursor)
        response = await self._transport.send(
            HttpRequest(
                method="GET",
                url=url,
                headers={"Accept": "application/pdf"},
            )
        )

        if response.status_code == 404:
            return PageResult(items=(), next_cursor=None, has_more=False)
        if 500 <= response.status_code <= 599:
            raise RecoverableConnectorError(
                f"BCRA returned {response.status_code} for {url}."
            )
        if response.status_code != 200:
            raise ValueError(f"Unexpected BCRA status code {response.status_code} for {url}.")

        text = self._text_extractor.extract_text(response.body)
        fetched_at = datetime.now(timezone.utc)
        parsed = parse_bcra_comunicacion_a_text(text)
        item = normalize_bcra_comunicacion_a(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url=response.url,
            cursor=str(cursor),
            transport_metadata={
                "status_code": response.status_code,
                "content_type": response.headers.get("Content-Type"),
            },
        )
        return PageResult(items=(item,), next_cursor=None, has_more=False)


def _normalize_number(number: int | str) -> str:
    normalized = str(number).strip()
    if not normalized.isdigit():
        raise ValueError(f"Invalid BCRA communication number: {number!r}")
    return normalized


def _clean_extracted_text(text: str) -> str:
    sanitized = text.replace("\r\n", "\n").replace("\r", "\n")
    sanitized = sanitized.replace("\u00ad", "")
    sanitized = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", sanitized)
    sanitized = re.sub(r"[ \t]+", " ", sanitized)
    sanitized = re.sub(r"\n{3,}", "\n\n", sanitized)
    return sanitized.strip()


def _join_wrapped_lines(lines: list[str]) -> str:
    merged = " ".join(line.strip(" -") for line in lines if line.strip())
    merged = re.sub(r"\s+", " ", merged)
    return merged.strip(" .") + "."
