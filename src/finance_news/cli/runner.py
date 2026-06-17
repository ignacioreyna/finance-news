"""CLI runner for finance-news connectors.

Provides list and run subcommands for connectors, with support for offline mode
using fixtures when connectors expose separate parsers.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from finance_news.connectors import available_connectors, get_connector
from finance_news.connectors._http import AsyncHttpTransport, HttpRequest, HttpResponse
from finance_news.connectors.models import RecoverableConnectorError
from finance_news.settings import load_env
from finance_news.storage.local import LocalStorage
from finance_news.testing import fixtures


@dataclass(frozen=True)
class RunSummary:
    """Summary of a connector run."""

    items_count: int
    recoverable_errors_count: int
    storage_path: str


def _create_http_transport() -> AsyncHttpTransport:
    """Create a simple HTTP transport using stdlib asyncio+http.client."""

    class _SimpleHttpTransport:
        async def send(self, request: HttpRequest) -> HttpResponse:
            import http.client
            import urllib.parse

            parsed_url = urllib.parse.urlparse(request.url)
            host = parsed_url.netloc
            path = parsed_url.path
            if parsed_url.query:
                path = f"{path}?{parsed_url.query}"

            conn = http.client.HTTPSConnection(host, timeout=request.timeout_seconds)
            try:
                headers = dict(request.headers)
                if request.body:
                    conn.request(
                        request.method,
                        path,
                        body=request.body,
                        headers=headers,
                    )
                else:
                    conn.request(request.method, path, headers=headers)
                response = conn.getresponse()
                body = response.read()
                return HttpResponse(
                    status_code=response.status,
                    url=request.url,
                    headers=dict(response.headers),
                    body=body,
                )
            finally:
                conn.close()

    return _SimpleHttpTransport()


async def run_connector(
    name: str,
    *,
    offline: bool = False,
    storage_root: str = "./storage",
    limit: int | None = None,
    cursor: str | None = None,
    since: datetime | None = None,
) -> RunSummary:
    """Run a connector and return summary.

    Args:
        name: Connector name.
        offline: Use fixtures instead of fetching (requires connector support).
        storage_root: Storage root directory path.
        limit: Maximum number of pages to fetch (None for unlimited).
        cursor: Optional cursor to start from.
        since: Optional since date for filtering.

    Returns:
        RunSummary with items count, recoverable errors count, and storage path.

    Raises:
        ValueError: If connector not found or offline not supported.
        RecoverableConnectorError: If connector fails in recoverable way.
    """
    try:
        connector_cls = get_connector(name)
    except KeyError as e:
        available = ", ".join(sorted(available_connectors()))
        raise ValueError(
            f"Unknown connector '{name}'. Available connectors: {available}"
        ) from e

    # Offline mode: try fixture-based parsing
    if offline:
        return await _run_offline(connector_cls, name, storage_root, cursor)

    # Online mode: fetch via HTTP
    return await _run_online(connector_cls, storage_root, limit, cursor, since)


async def _run_offline(
    connector_cls: type,
    name: str,
    storage_root: str,
    cursor: str | None,
) -> RunSummary:
    """Run connector in offline mode using fixtures."""
    storage = LocalStorage(Path(storage_root))
    items_count = 0
    recoverable_errors_count = 0

    # BCRA-specific offline handling
    if name == "bcra_comunicaciones_a":
        from finance_news.connectors.bcra_comunicaciones_a import (
            normalize_bcra_comunicacion_a,
            parse_bcra_comunicacion_a_text,
        )

        fixture_name = f"{cursor or 'A8060'}.txt"
        try:
            text = fixtures.load_fixture_text(name, fixture_name)
            parsed = parse_bcra_comunicacion_a_text(text)
            fetched_at = datetime.now(timezone.utc)
            item = normalize_bcra_comunicacion_a(
                parsed=parsed,
                fetched_at=fetched_at,
                fetch_url=f"file://fixtures/{name}/{fixture_name}",
                cursor=str(cursor or "A8060"),
                transport_metadata={"offline": True},
            )
            storage.put_raw(text.encode("utf-8"), name, item.external_id, fetched_at)
            storage.put_item(item)
            items_count = 1
        except FileNotFoundError:
            raise ValueError(
                f"Connector '{name}' does not support offline mode with fixture '{fixture_name}'"
            )
        except Exception as e:
            if isinstance(e, RecoverableConnectorError):
                recoverable_errors_count += 1
            raise

    else:
        raise ValueError(
            f"Connector '{name}' does not support offline mode. "
            f"Remove --offline flag to run online, or add fixture support."
        )

    return RunSummary(
        items_count=items_count,
        recoverable_errors_count=recoverable_errors_count,
        storage_path=str(Path(storage_root).resolve()),
    )


async def _run_online(
    connector_cls: type,
    storage_root: str,
    limit: int | None,
    cursor: str | None,
    since: datetime | None,
) -> RunSummary:
    """Run connector in online mode."""
    transport = _create_http_transport()
    connector = connector_cls(transport=transport)
    storage = LocalStorage(Path(storage_root))
    items_count = 0
    recoverable_errors_count = 0
    pages_fetched = 0

    current_cursor = cursor
    while True:
        if limit is not None and pages_fetched >= limit:
            break

        try:
            result = await connector.fetch_page(cursor=current_cursor, since=since)
        except RecoverableConnectorError:
            recoverable_errors_count += 1
            raise

        items_count += len(result.items)
        pages_fetched += 1

        for item in result.items:
            # Store raw payload (simplified - in real implementation, capture actual response)
            storage.put_raw(
                item.body.encode("utf-8") if item.body else b"",
                item.provenance.connector,
                item.external_id,
                item.provenance.fetched_at,
            )
            storage.put_item(item)

        if not result.has_more:
            break

        current_cursor = result.next_cursor

    return RunSummary(
        items_count=items_count,
        recoverable_errors_count=recoverable_errors_count,
        storage_path=str(Path(storage_root).resolve()),
    )


def list_connectors() -> None:
    """Print available connector names."""
    for name in sorted(available_connectors()):
        print(name)


def main() -> None:
    """CLI entry point."""
    load_env()
    parser = argparse.ArgumentParser(description="Finance-news connector runner")
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # List subcommand
    subparsers.add_parser("list", help="List available connectors")

    # Run subcommand
    run_parser = subparsers.add_parser("run", help="Run a connector")
    run_parser.add_argument("name", help="Connector name")
    run_parser.add_argument("--offline", action="store_true", help="Use fixtures instead of fetching")
    run_parser.add_argument("--storage", default="./storage", help="Storage root directory (default: ./storage)")
    run_parser.add_argument("--limit", type=int, help="Maximum pages to fetch")
    run_parser.add_argument("--cursor", help="Starting cursor")
    run_parser.add_argument("--from", dest="since", help="Start date (ISO format)")

    args = parser.parse_args()

    if args.command == "list":
        list_connectors()
        return

    if args.command == "run":
        since = None
        if args.since:
            since = datetime.fromisoformat(args.since)

        try:
            summary = asyncio.run(
                run_connector(
                    args.name,
                    offline=args.offline,
                    storage_root=args.storage,
                    limit=args.limit,
                    cursor=args.cursor,
                    since=since,
                )
            )
            print(f"Items: {summary.items_count}")
            print(f"Recoverable errors: {summary.recoverable_errors_count}")
            print(f"Storage path: {summary.storage_path}")
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()