from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.fed_speeches import (
    DEFAULT_TTL_SECONDS,
    classify_speech_by_title,
    FedSpeechesConnector,
    FedSpeechClassification,
    filter_speeches,
    normalize_fed_speech,
    parse_fed_speeches_html,
    ParsedFedSpeech,
)
from finance_news.connectors.models import RecoverableConnectorError

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "fed_speeches"


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.response


class FedSpeechesParserTests(unittest.TestCase):
    def test_parse_speeches_html_returns_five_speeches(self) -> None:
        html = (FIXTURES_DIR / "speeches_listing.html").read_text(encoding="utf-8")
        speeches = parse_fed_speeches_html(html)

        self.assertEqual(len(speeches), 5)

    def test_parse_first_speech_powell_monetary_policy(self) -> None:
        html = (FIXTURES_DIR / "speeches_listing.html").read_text(encoding="utf-8")
        speeches = parse_fed_speeches_html(html)

        speech = next((s for s in speeches if "powell20250115a" in s.url), None)
        self.assertIsNotNone(speech)

        self.assertEqual(speech.date, datetime(2025, 1, 15, tzinfo=timezone.utc))
        self.assertEqual(speech.speaker, "Chair Jerome H. Powell")
        self.assertEqual(speech.title, "Monetary Policy and Economic Outlook")
        self.assertEqual(speech.url, "/newsevents/speech/powell20250115a.htm")
        self.assertIn("fed_speech_2025-01-15", speech.external_id)

    def test_parse_second_speech_barr_banking_supervision(self) -> None:
        html = (FIXTURES_DIR / "speeches_listing.html").read_text(encoding="utf-8")
        speeches = parse_fed_speeches_html(html)

        speech = next((s for s in speeches if "barr20250203a" in s.url), None)
        self.assertIsNotNone(speech)

        self.assertEqual(speech.date, datetime(2025, 2, 3, tzinfo=timezone.utc))
        self.assertEqual(speech.speaker, "Vice Chair for Supervision Michael S. Barr")
        self.assertEqual(speech.title, "Banking Supervision and Financial Stability")
        self.assertEqual(speech.url, "/newsevents/speech/barr20250203a.htm")

    def test_parse_third_speech_bowman_economic_outlook(self) -> None:
        html = (FIXTURES_DIR / "speeches_listing.html").read_text(encoding="utf-8")
        speeches = parse_fed_speeches_html(html)

        speech = next((s for s in speeches if "bowman20250310a" in s.url), None)
        self.assertIsNotNone(speech)

        self.assertEqual(speech.date, datetime(2025, 3, 10, tzinfo=timezone.utc))
        self.assertEqual(speech.speaker, "Governor Michelle W. Bowman")
        self.assertIn("Economic Outlook", speech.title)

    def test_parse_fourth_speech_kugler_labor_markets(self) -> None:
        html = (FIXTURES_DIR / "speeches_listing.html").read_text(encoding="utf-8")
        speeches = parse_fed_speeches_html(html)

        speech = next((s for s in speeches if "kugler20250422a" in s.url), None)
        self.assertIsNotNone(speech)

        self.assertEqual(speech.date, datetime(2025, 4, 22, tzinfo=timezone.utc))
        self.assertEqual(speech.speaker, "Governor Adriana D. Kugler")
        self.assertIn("Labor Markets", speech.title)

    def test_parse_fifth_speech_jefferson_regulation(self) -> None:
        html = (FIXTURES_DIR / "speeches_listing.html").read_text(encoding="utf-8")
        speeches = parse_fed_speeches_html(html)

        speech = next((s for s in speeches if "jefferson20250508a" in s.url), None)
        self.assertIsNotNone(speech)

        self.assertEqual(speech.date, datetime(2025, 5, 8, tzinfo=timezone.utc))
        self.assertEqual(speech.speaker, "Vice Chair Philip N. Jefferson")
        self.assertIn("Financial Regulation", speech.title)

    def test_parsed_speech_serialization(self) -> None:
        speech = ParsedFedSpeech(
            date=datetime(2025, 1, 15, tzinfo=timezone.utc),
            speaker="Chair Jerome H. Powell",
            title="Monetary Policy and Economic Outlook",
            url="/newsevents/speech/powell20250115a.htm",
            external_id="fed_speech_2025-01-15_chair_jerome_h_powell",
        )

        data = speech.to_dict()
        self.assertEqual(data["speaker"], "Chair Jerome H. Powell")
        self.assertEqual(data["date"], "2025-01-15T00:00:00+00:00")
        self.assertEqual(data["title"], "Monetary Policy and Economic Outlook")

        restored = ParsedFedSpeech.from_dict(data)
        self.assertEqual(restored.speaker, speech.speaker)
        self.assertEqual(restored.date, speech.date)
        self.assertEqual(restored.external_id, speech.external_id)


class FedSpeechesClassificationTests(unittest.TestCase):
    def test_classify_monetary_policy_tag(self) -> None:
        classification = classify_speech_by_title("Monetary Policy and Economic Outlook")

        self.assertIn("monetary_policy", classification.tags)

    def test_classify_banking_tag(self) -> None:
        classification = classify_speech_by_title("Banking Supervision and Financial Stability")

        self.assertIn("banking", classification.tags)

    def test_classify_financial_stability_tag(self) -> None:
        classification = classify_speech_by_title("Banking Supervision and Financial Stability")

        self.assertIn("financial_stability", classification.tags)

    def test_classify_economy_tag(self) -> None:
        classification = classify_speech_by_title("Labor Markets and Economic Growth")

        self.assertIn("economy", classification.tags)

    def test_classify_regulation_tag(self) -> None:
        classification = classify_speech_by_title("Financial Regulation and Systemic Risk")

        self.assertIn("regulation", classification.tags)

    def test_classify_multiple_tags(self) -> None:
        classification = classify_speech_by_title("Banking Supervision and Financial Stability")

        self.assertIn("banking", classification.tags)
        self.assertIn("financial_stability", classification.tags)

    def test_classify_no_tags(self) -> None:
        classification = classify_speech_by_title("Opening Remarks")

        self.assertEqual(len(classification.tags), 0)

    def test_classification_serialization(self) -> None:
        classification = FedSpeechClassification(tags=("monetary_policy", "economy"))

        data = classification.to_dict()
        self.assertEqual(data["tags"], ("monetary_policy", "economy"))

        restored = FedSpeechClassification.from_dict(data)
        self.assertEqual(restored.tags, classification.tags)


class FedSpeechesFilterTests(unittest.TestCase):
    def test_filter_by_speaker_powell(self) -> None:
        html = (FIXTURES_DIR / "speeches_listing.html").read_text(encoding="utf-8")
        speeches = parse_fed_speeches_html(html)

        filtered = filter_speeches(speeches, speaker="Powell")

        self.assertEqual(len(filtered), 1)
        self.assertIn("Powell", filtered[0].speaker)

    def test_filter_by_speaker_jefferson(self) -> None:
        html = (FIXTURES_DIR / "speeches_listing.html").read_text(encoding="utf-8")
        speeches = parse_fed_speeches_html(html)

        filtered = filter_speeches(speeches, speaker="Jefferson")

        self.assertEqual(len(filtered), 1)
        self.assertIn("Jefferson", filtered[0].speaker)

    def test_filter_by_tag_monetary_policy(self) -> None:
        html = (FIXTURES_DIR / "speeches_listing.html").read_text(encoding="utf-8")
        speeches = parse_fed_speeches_html(html)

        filtered = filter_speeches(speeches, tag="monetary_policy")

        self.assertEqual(len(filtered), 1)
        self.assertIn("Monetary Policy", filtered[0].title)

    def test_filter_by_tag_banking(self) -> None:
        html = (FIXTURES_DIR / "speeches_listing.html").read_text(encoding="utf-8")
        speeches = parse_fed_speeches_html(html)

        filtered = filter_speeches(speeches, tag="banking")

        # Should match Barr and Bowman speeches (both have banking keywords)
        self.assertEqual(len(filtered), 2)

    def test_filter_by_tag_financial_stability(self) -> None:
        html = (FIXTURES_DIR / "speeches_listing.html").read_text(encoding="utf-8")
        speeches = parse_fed_speeches_html(html)

        filtered = filter_speeches(speeches, tag="financial_stability")

        self.assertGreaterEqual(len(filtered), 1)
        # Should match both Barr and Jefferson speeches
        for speech in filtered:
            classification = classify_speech_by_title(speech.title)
            self.assertIn("financial_stability", classification.tags)

    def test_filter_by_tag_economy(self) -> None:
        html = (FIXTURES_DIR / "speeches_listing.html").read_text(encoding="utf-8")
        speeches = parse_fed_speeches_html(html)

        filtered = filter_speeches(speeches, tag="economy")

        self.assertGreaterEqual(len(filtered), 2)

    def test_filter_by_tag_regulation(self) -> None:
        html = (FIXTURES_DIR / "speeches_listing.html").read_text(encoding="utf-8")
        speeches = parse_fed_speeches_html(html)

        filtered = filter_speeches(speeches, tag="regulation")

        # Should match Barr and Jefferson speeches (both have regulation keywords)
        self.assertEqual(len(filtered), 2)

    def test_filter_by_speaker_and_tag(self) -> None:
        html = (FIXTURES_DIR / "speeches_listing.html").read_text(encoding="utf-8")
        speeches = parse_fed_speeches_html(html)

        filtered = filter_speeches(speeches, speaker="Powell", tag="monetary_policy")

        self.assertEqual(len(filtered), 1)
        self.assertIn("Powell", filtered[0].speaker)
        self.assertIn("Monetary Policy", filtered[0].title)

    def test_filter_no_match_returns_empty(self) -> None:
        html = (FIXTURES_DIR / "speeches_listing.html").read_text(encoding="utf-8")
        speeches = parse_fed_speeches_html(html)

        filtered = filter_speeches(speeches, speaker="Yellen")

        self.assertEqual(len(filtered), 0)


class FedSpeechesNormalizeTests(unittest.TestCase):
    def test_normalize_creates_source_item(self) -> None:
        parsed = ParsedFedSpeech(
            date=datetime(2025, 1, 15, tzinfo=timezone.utc),
            speaker="Chair Jerome H. Powell",
            title="Monetary Policy and Economic Outlook",
            url="/newsevents/speech/powell20250115a.htm",
            external_id="fed_speech_2025-01-15_chair_jerome_h_powell",
        )

        fetched_at = datetime(2026, 6, 20, 10, 0, tzinfo=timezone.utc)
        item = normalize_fed_speech(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://www.federalreserve.gov/newsevents/speech/2025-speeches.htm",
            cursor="2025",
        )

        self.assertEqual(item.external_id, "fed_speech_2025-01-15_chair_jerome_h_powell")
        self.assertEqual(item.source, "fed")
        self.assertEqual(item.published_at, datetime(2025, 1, 15, tzinfo=timezone.utc))
        self.assertIn("Powell", item.title)
        self.assertIn("Monetary Policy", item.title)
        self.assertEqual(item.url, "https://www.federalreserve.gov/newsevents/speech/powell20250115a.htm")
        self.assertEqual(item.metadata["speaker"], "Chair Jerome H. Powell")
        self.assertEqual(item.metadata["title"], "Monetary Policy and Economic Outlook")
        self.assertIn("monetary_policy", item.metadata["tags"])
        self.assertEqual(item.provenance.connector, "fed_speeches")
        self.assertEqual(item.provenance.parser_version, "0.1.0")
        self.assertEqual(item.freshness.ttl_seconds, DEFAULT_TTL_SECONDS)
        self.assertFalse(item.freshness.is_stale)

    def test_normalize_includes_tags_in_summary(self) -> None:
        parsed = ParsedFedSpeech(
            date=datetime(2025, 2, 3, tzinfo=timezone.utc),
            speaker="Vice Chair for Supervision Michael S. Barr",
            title="Banking Supervision and Financial Stability",
            url="/newsevents/speech/barr20250203a.htm",
            external_id="fed_speech_2025-02-03_vice_chair_for_supe",
        )

        fetched_at = datetime(2026, 6, 20, 10, 0, tzinfo=timezone.utc)
        item = normalize_fed_speech(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://www.federalreserve.gov/newsevents/speech/2025-speeches.htm",
            cursor="2025",
        )

        self.assertIn("Tags:", item.summary)
        self.assertIn("banking", item.summary)
        self.assertIn("financial_stability", item.summary)

    def test_normalize_resolves_relative_url(self) -> None:
        parsed = ParsedFedSpeech(
            date=datetime(2025, 1, 15, tzinfo=timezone.utc),
            speaker="Chair Jerome H. Powell",
            title="Monetary Policy and Economic Outlook",
            url="/newsevents/speech/powell20250115a.htm",
            external_id="fed_speech_2025-01-15_chair_jerome_h_powell",
        )

        fetched_at = datetime(2026, 6, 20, 10, 0, tzinfo=timezone.utc)
        item = normalize_fed_speech(
            parsed=parsed,
            fetched_at=fetched_at,
            fetch_url="https://www.federalreserve.gov/newsevents/speech/2025-speeches.htm",
            cursor="2025",
        )

        self.assertEqual(item.url, "https://www.federalreserve.gov/newsevents/speech/powell20250115a.htm")


class FedSpeechesConnectorTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_page_200_returns_speeches(self) -> None:
        html = (FIXTURES_DIR / "speeches_listing.html").read_text(encoding="utf-8")
        response = HttpResponse(
            status_code=200,
            url="https://www.federalreserve.gov/newsevents/speech/2025-speeches.htm",
            headers={"Content-Type": "text/html"},
            body=html.encode("utf-8"),
        )

        transport = _FakeTransport(response)
        connector = FedSpeechesConnector(transport=transport)

        result = await connector.fetch_page(cursor="2025")

        self.assertEqual(len(result.items), 5)
        self.assertIsNone(result.next_cursor)
        self.assertFalse(result.has_more)

        first_item = result.items[0]
        self.assertEqual(first_item.source, "fed")
        self.assertIn("speaker", first_item.metadata)
        self.assertIn("title", first_item.metadata)
        self.assertIn("tags", first_item.metadata)

    async def test_fetch_page_404_returns_empty(self) -> None:
        response = HttpResponse(
            status_code=404,
            url="https://www.federalreserve.gov/newsevents/speech/2025-speeches.htm",
            headers={},
            body=b"Not found",
        )

        transport = _FakeTransport(response)
        connector = FedSpeechesConnector(transport=transport)

        result = await connector.fetch_page(cursor="2025")

        self.assertEqual(len(result.items), 0)
        self.assertIsNone(result.next_cursor)
        self.assertFalse(result.has_more)

    async def test_fetch_page_500_raises_recoverable_error(self) -> None:
        response = HttpResponse(
            status_code=503,
            url="https://www.federalreserve.gov/newsevents/speech/2025-speeches.htm",
            headers={},
            body=b"Service unavailable",
        )

        transport = _FakeTransport(response)
        connector = FedSpeechesConnector(transport=transport)

        with self.assertRaises(RecoverableConnectorError):
            await connector.fetch_page(cursor="2025")

    async def test_fetch_page_unexpected_status_raises_value_error(self) -> None:
        response = HttpResponse(
            status_code=403,
            url="https://www.federalreserve.gov/newsevents/speech/2025-speeches.htm",
            headers={},
            body=b"Forbidden",
        )

        transport = _FakeTransport(response)
        connector = FedSpeechesConnector(transport=transport)

        with self.assertRaises(ValueError) as cm:
            await connector.fetch_page(cursor="2025")

        self.assertIn("403", str(cm.exception))

    def test_connector_metadata(self) -> None:
        connector = FedSpeechesConnector(transport=_FakeTransport(HttpResponse(200, "", {}, b"")))

        self.assertEqual(connector.name, "fed_speeches")
        self.assertEqual(connector.source, "fed")
        self.assertEqual(connector.retry_policy.max_attempts, 3)
        self.assertEqual(connector.rate_limit_policy.concurrency, 1)


class FedSpeechesFreshnessTests(unittest.IsolatedAsyncioTestCase):
    async def test_freshness_metadata_integration(self) -> None:
        html = (FIXTURES_DIR / "speeches_listing.html").read_text(encoding="utf-8")
        response = HttpResponse(
            status_code=200,
            url="https://www.federalreserve.gov/newsevents/speech/2025-speeches.htm",
            headers={"Content-Type": "text/html"},
            body=html.encode("utf-8"),
        )

        transport = _FakeTransport(response)
        connector = FedSpeechesConnector(transport=transport)
        result = await connector.fetch_page(cursor="2025")

        for item in result.items:
            self.assertIsNotNone(item.freshness)
            self.assertIsNotNone(item.freshness.fetched_at)
            self.assertIsNotNone(item.freshness.first_seen_at)
            self.assertFalse(item.freshness.is_stale)
            self.assertEqual(item.freshness.ttl_seconds, DEFAULT_TTL_SECONDS)
            if item.published_at is not None:
                self.assertEqual(item.freshness.published_at, item.published_at)


class FedSpeechesAcceptanceCriteriaTests(unittest.TestCase):
    def test_ac1_connector_returns_normalized_speeches_with_required_fields(self) -> None:
        html = (FIXTURES_DIR / "speeches_listing.html").read_text(encoding="utf-8")
        speeches = parse_fed_speeches_html(html)

        self.assertGreater(len(speeches), 0)

        for speech in speeches:
            self.assertIsNotNone(speech.date)
            self.assertIsNotNone(speech.speaker)
            self.assertIsNotNone(speech.title)
            self.assertIsNotNone(speech.url)
            self.assertIsNotNone(speech.external_id)

    def test_ac1_speeches_include_tags_from_title_keywords(self) -> None:
        html = (FIXTURES_DIR / "speeches_listing.html").read_text(encoding="utf-8")
        speeches = parse_fed_speeches_html(html)

        for speech in speeches:
            classification = classify_speech_by_title(speech.title)
            # All speeches should have at least some tags based on our fixture
            if "Monetary Policy" in speech.title:
                self.assertIn("monetary_policy", classification.tags)
            if "Banking" in speech.title:
                self.assertIn("banking", classification.tags)
            if "Financial Stability" in speech.title:
                self.assertIn("financial_stability", classification.tags)
            if "Economic" in speech.title or "Labor" in speech.title:
                self.assertIn("economy", classification.tags)
            if "Regulation" in speech.title:
                self.assertIn("regulation", classification.tags)

    def test_ac2_offline_fixture_parsing(self) -> None:
        html = (FIXTURES_DIR / "speeches_listing.html").read_text(encoding="utf-8")
        speeches = parse_fed_speeches_html(html)

        self.assertEqual(len(speeches), 5)

        # Verify specific speeches from fixture
        powell_speech = next((s for s in speeches if "powell20250115a" in s.url), None)
        self.assertIsNotNone(powell_speech)
        self.assertEqual(powell_speech.speaker, "Chair Jerome H. Powell")
        self.assertIn("Monetary Policy", powell_speech.title)

        barr_speech = next((s for s in speeches if "barr20250203a" in s.url), None)
        self.assertIsNotNone(barr_speech)
        self.assertEqual(barr_speech.speaker, "Vice Chair for Supervision Michael S. Barr")
        self.assertIn("Banking", barr_speech.title)

        bowman_speech = next((s for s in speeches if "bowman20250310a" in s.url), None)
        self.assertIsNotNone(bowman_speech)
        self.assertEqual(bowman_speech.speaker, "Governor Michelle W. Bowman")

    def test_ac3_filter_by_speaker_without_summarizing(self) -> None:
        html = (FIXTURES_DIR / "speeches_listing.html").read_text(encoding="utf-8")
        speeches = parse_fed_speeches_html(html)

        filtered = filter_speeches(speeches, speaker="Powell")

        self.assertEqual(len(filtered), 1)
        self.assertIn("Powell", filtered[0].speaker)
        # Verify we're not summarizing - just filtering
        self.assertEqual(filtered[0].title, "Monetary Policy and Economic Outlook")

    def test_ac3_filter_by_tag_without_summarizing(self) -> None:
        html = (FIXTURES_DIR / "speeches_listing.html").read_text(encoding="utf-8")
        speeches = parse_fed_speeches_html(html)

        filtered = filter_speeches(speeches, tag="monetary_policy")

        self.assertEqual(len(filtered), 1)
        # Verify we're not summarizing - just filtering
        self.assertEqual(filtered[0].title, "Monetary Policy and Economic Outlook")

    def test_ac3_filter_by_speaker_and_tag_combination(self) -> None:
        html = (FIXTURES_DIR / "speeches_listing.html").read_text(encoding="utf-8")
        speeches = parse_fed_speeches_html(html)

        filtered = filter_speeches(speeches, speaker="Barr", tag="banking")

        self.assertEqual(len(filtered), 1)
        self.assertIn("Barr", filtered[0].speaker)
        self.assertIn("Banking", filtered[0].title)


if __name__ == "__main__":
    unittest.main()