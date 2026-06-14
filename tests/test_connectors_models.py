from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors.models import Freshness, Provenance, SourceItem


class SourceItemSerializationTests(unittest.TestCase):
    def test_source_item_round_trip_serialization(self) -> None:
        published_at = datetime(2026, 6, 13, 18, 30, tzinfo=timezone.utc)
        fetched_at = datetime(2026, 6, 14, 9, 0, tzinfo=timezone.utc)
        first_seen_at = datetime(2026, 6, 14, 9, 5, tzinfo=timezone.utc)
        item = SourceItem(
            external_id="fomc-2026-06-13",
            source="fomc",
            published_at=published_at,
            title="FOMC statement",
            body=None,
            summary="Rates unchanged.",
            url="https://www.federalreserve.gov/newsevents/pressreleases/monetary20260613a.htm",
            metadata={"macro_topic": "rates", "tickers": ["SPY", "TLT"]},
            provenance=Provenance(
                connector="fomc_press_releases",
                source="fomc",
                fetch_url="https://www.federalreserve.gov/newsevents/pressreleases.htm",
                canonical_url="https://www.federalreserve.gov/newsevents/pressreleases/monetary20260613a.htm",
                cursor="page=1",
                fetched_at=fetched_at,
                parser_version="0.1.0",
                transport_metadata={"status_code": 200, "etag": "abc123"},
            ),
            freshness=Freshness(
                published_at=published_at,
                first_seen_at=first_seen_at,
                fetched_at=fetched_at,
                is_stale=False,
                ttl_seconds=3600,
            ),
        )

        payload = item.to_dict()
        restored = SourceItem.from_dict(payload)

        self.assertEqual(restored, item)
        self.assertEqual(payload["published_at"], "2026-06-13T18:30:00+00:00")
        self.assertEqual(payload["provenance"]["transport_metadata"]["status_code"], 200)


if __name__ == "__main__":
    unittest.main()
