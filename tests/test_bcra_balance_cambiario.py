from __future__ import annotations

import csv
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.connectors._http import HttpResponse
from finance_news.connectors.bcra_balance_cambiario import (
    CONNECTOR_NAME,
    DEFAULT_TTL_SECONDS,
    DEFAULT_XLSX_URL,
    DOES_NOT_REPLACE_NET_INTERVENTION,
    MissingXlsxExtractorError,
    OpenpyxlRowExtractor,
    PARSER_VERSION,
    ParsedBalanceObservation,
    SOURCE_NAME,
    BcraBalanceCambiarioConnector,
    normalize_balance_observations,
    parse_balance_csv,
    parse_balance_rows,
    _parse_decimal,
)
from finance_news.connectors.models import RecoverableConnectorError

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "bcra_balance_cambiario"


class _CsvRowExtractor:
    """Test-only row extractor backed by semicolon-delimited CSV bytes."""

    def __init__(self) -> None:
        self.calls = 0

    def extract_rows(self, data: bytes) -> list[list[str]]:
        self.calls += 1
        text = data.decode("utf-8")
        return list(csv.reader(text.splitlines(), delimiter=";"))


class _FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests = []

    async def send(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.response


def _csv_bytes() -> bytes:
    return (FIXTURES_DIR / "balance_mensual.csv").read_bytes()


class ParseDecimalTests(unittest.TestCase):
    def test_na_tokens_return_none(self) -> None:
        for value in ("", "NA", "N/A", "N.A.", "-", "—", "  ", "n/a"):
            with self.subTest(value=value):
                self.assertIsNone(_parse_decimal(value))

    def test_plain_decimal_dot(self) -> None:
        self.assertEqual(_parse_decimal("1234.56"), 1234.56)

    def test_plain_decimal_comma(self) -> None:
        self.assertEqual(_parse_decimal("1234,56"), 1234.56)

    def test_european_thousands(self) -> None:
        self.assertEqual(_parse_decimal("1.234,56"), 1234.56)

    def test_us_thousands(self) -> None:
        self.assertEqual(_parse_decimal("1,234.56"), 1234.56)

    def test_thousands_and_single_decimal_digit(self) -> None:
        # Prior-attempt bug: thousands + decimal must parse correctly.
        self.assertEqual(_parse_decimal("1,000.5"), 1000.5)

    def test_single_separator_thousands_three_digits(self) -> None:
        self.assertEqual(_parse_decimal("500.000"), 500000.0)
        self.assertEqual(_parse_decimal("1.234"), 1234.0)

    def test_single_separator_one_decimal_digit(self) -> None:
        self.assertEqual(_parse_decimal("120.5"), 120.5)

    def test_plain_integer(self) -> None:
        self.assertEqual(_parse_decimal("1000"), 1000.0)

    def test_garbage_returns_none(self) -> None:
        self.assertIsNone(_parse_decimal("abc"))


class BalanceParserTests(unittest.TestCase):
    def test_parse_fixture_csv_returns_observations(self) -> None:
        observations = parse_balance_csv(_csv_bytes().decode("utf-8"))
        self.assertEqual(len(observations), 5)

        by_rubro = {obs.rubro: obs for obs in observations}

        total = by_rubro["Total"]
        self.assertEqual(total.period, "2026-01")
        self.assertEqual(total.compras_usd, 1234.56)
        self.assertEqual(total.ventas_usd, 987.65)
        self.assertEqual(total.saldo_neto_usd, 246.91)

        agro = by_rubro["Agropecuario"]
        self.assertEqual(agro.compras_usd, 500000.0)
        self.assertEqual(agro.ventas_usd, 250.5)
        # NA saldo falls back to compras - ventas when both are present.
        self.assertEqual(agro.saldo_neto_usd, 500000.0 - 250.5)

        energia = by_rubro["Energia"]
        self.assertIsNone(energia.compras_usd)
        self.assertEqual(energia.ventas_usd, 120.5)
        # No fallback when compras is also None.
        self.assertIsNone(energia.saldo_neto_usd)

        industria = by_rubro["Industria"]
        self.assertEqual(industria.compras_usd, 1234.56)
        self.assertEqual(industria.ventas_usd, 1000.0)
        self.assertEqual(industria.saldo_neto_usd, 234.56)

        servicios = by_rubro["Servicios"]
        self.assertEqual(servicios.compras_usd, 1000.5)
        self.assertEqual(servicios.ventas_usd, 800.0)
        self.assertEqual(servicios.saldo_neto_usd, 200.5)

    def test_parser_uses_header_keywords_deterministically(self) -> None:
        # Reordered + extra columns must still map by header, not position.
        rows = [
            ["Sector", "Periodo", "Ventas", "Compras", "Saldo Neto", "Extra"],
            ["Rubro-X", "2026-03", "100,50", "200,25", "300,75", "ignore"],
        ]
        observations = parse_balance_rows(rows)
        self.assertEqual(len(observations), 1)
        obs = observations[0]
        self.assertEqual(obs.period, "2026-03")
        self.assertEqual(obs.rubro, "Rubro-X")
        self.assertEqual(obs.compras_usd, 200.25)
        self.assertEqual(obs.ventas_usd, 100.50)
        self.assertEqual(obs.saldo_neto_usd, 300.75)

    def test_parser_skips_blank_rows(self) -> None:
        rows = [
            ["Periodo", "Rubro", "Compras", "Ventas", "Saldo Neto"],
            ["", "", "", "", ""],
            ["2026-01", "", "10.0", "4.0", "6.0"],
            ["", "Sin Periodo", "10.0", "4.0", "6.0"],
            ["2026-01", "Real", "10.0", "4.0", "6.0"],
        ]
        observations = parse_balance_rows(rows)
        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0].rubro, "Real")

    def test_parser_raises_when_no_header(self) -> None:
        with self.assertRaises(ValueError):
            parse_balance_rows([["a", "b"], ["c", "d"]])

    def test_parser_raises_when_zero_observations(self) -> None:
        rows = [
            ["Periodo", "Rubro", "Compras", "Ventas", "Saldo Neto"],
            ["", "", "", "", ""],
        ]
        with self.assertRaises(ValueError):
            parse_balance_rows(rows)

    def test_parsed_observation_roundtrip(self) -> None:
        obs = ParsedBalanceObservation(
            period="2026-01",
            rubro="Total",
            compras_usd=100.0,
            ventas_usd=40.0,
            saldo_neto_usd=60.0,
        )
        restored = ParsedBalanceObservation.from_dict(obs.to_dict())
        self.assertEqual(obs, restored)


class NormalizeTests(unittest.TestCase):
    def test_normalize_populates_required_metadata(self) -> None:
        from datetime import datetime, timezone

        observations = parse_balance_csv(_csv_bytes().decode("utf-8"))
        fetched_at = datetime(2026, 6, 16, 12, 0, tzinfo=timezone.utc)
        items = normalize_balance_observations(
            observations=observations,
            fetched_at=fetched_at,
            fetch_url=DEFAULT_XLSX_URL,
            cursor=None,
            transport_metadata={"raw_hash": "deadbeef"},
        )
        self.assertEqual(len(items), len(observations))

        first = items[0]
        self.assertEqual(first.source, SOURCE_NAME)
        self.assertEqual(first.url, DEFAULT_XLSX_URL)
        self.assertEqual(first.metadata["unidad"], "USD")
        self.assertEqual(first.metadata["fuente"], SOURCE_NAME)
        self.assertEqual(first.metadata["rubro"], observations[0].rubro)
        self.assertEqual(first.metadata["period"], observations[0].period)
        self.assertEqual(first.metadata["saldo_neto_usd"], observations[0].saldo_neto_usd)
        # AC#3 surfaced into metadata.
        self.assertIs(
            first.metadata["does_not_replace_net_intervention"],
            DOES_NOT_REPLACE_NET_INTERVENTION,
        )
        self.assertTrue(first.metadata["does_not_replace_net_intervention"])

        prov = first.provenance
        self.assertEqual(prov.connector, CONNECTOR_NAME)
        self.assertEqual(prov.source, SOURCE_NAME)
        self.assertEqual(prov.fetch_url, DEFAULT_XLSX_URL)
        self.assertEqual(prov.parser_version, PARSER_VERSION)
        self.assertEqual(prov.transport_metadata["raw_hash"], "deadbeef")
        self.assertEqual(first.freshness.ttl_seconds, DEFAULT_TTL_SECONDS)
        self.assertEqual(first.freshness.first_seen_at, fetched_at)

    def test_monto_falls_back_to_ventas_when_saldo_missing(self) -> None:
        from datetime import datetime, timezone

        observations = [
            ParsedBalanceObservation(
                period="2026-01",
                rubro="Energia",
                compras_usd=None,
                ventas_usd=120.5,
                saldo_neto_usd=None,
            )
        ]
        items = normalize_balance_observations(
            observations=observations,
            fetched_at=datetime(2026, 6, 16, tzinfo=timezone.utc),
            fetch_url=DEFAULT_XLSX_URL,
            cursor=None,
        )
        self.assertEqual(items[0].metadata["monto"], 120.5)
        self.assertNotIn("saldo_neto_usd", items[0].metadata)
        self.assertEqual(items[0].metadata["ventas_usd"], 120.5)


class OpenpyxlExtractorTests(unittest.TestCase):
    def test_construction_raises_when_openpyxl_missing(self) -> None:
        # openpyxl is not installed in this environment; the lazy import must
        # surface a MissingXlsxExtractorError instead of ImportError.
        with self.assertRaises(MissingXlsxExtractorError):
            OpenpyxlRowExtractor()


class BcraBalanceCambiarioConnectorTests(unittest.IsolatedAsyncioTestCase):
    def _connector(self, transport: _FakeTransport) -> BcraBalanceCambiarioConnector:
        return BcraBalanceCambiarioConnector(
            transport=transport,
            row_extractor=_CsvRowExtractor(),
        )

    def test_class_attributes(self) -> None:
        self.assertEqual(BcraBalanceCambiarioConnector.name, CONNECTOR_NAME)
        self.assertEqual(BcraBalanceCambiarioConnector.source, SOURCE_NAME)
        self.assertEqual(CONNECTOR_NAME, "bcra_balance_cambiario")
        self.assertIsNotNone(BcraBalanceCambiarioConnector.retry_policy)
        self.assertIsNotNone(BcraBalanceCambiarioConnector.rate_limit_policy)
        self.assertEqual(BcraBalanceCambiarioConnector.retry_policy.max_attempts, 3)

    async def test_fetch_page_200_returns_items_with_full_metadata(self) -> None:
        transport = _FakeTransport(
            HttpResponse(
                status_code=200,
                url=DEFAULT_XLSX_URL,
                headers={"Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
                body=_csv_bytes(),
            )
        )
        connector = self._connector(transport)

        result = await connector.fetch_page()

        self.assertFalse(result.has_more)
        self.assertIsNone(result.next_cursor)
        self.assertEqual(len(result.items), 5)

        item = result.items[0]
        for key in ("rubro", "period", "monto", "unidad", "fuente", "does_not_replace_net_intervention"):
            with self.subTest(key=key):
                self.assertIn(key, item.metadata)
        self.assertEqual(item.metadata["unidad"], "USD")
        self.assertEqual(item.metadata["fuente"], "bcra")
        self.assertTrue(item.metadata["does_not_replace_net_intervention"])
        self.assertEqual(item.provenance.connector, CONNECTOR_NAME)
        self.assertEqual(item.provenance.parser_version, PARSER_VERSION)
        self.assertIn("raw_hash", item.provenance.transport_metadata)
        self.assertTrue(item.provenance.transport_metadata["raw_hash"])

        # Request targeted the default artifact URL.
        self.assertEqual(transport.requests[0].url, DEFAULT_XLSX_URL)
        self.assertEqual(transport.requests[0].method, "GET")

    async def test_fetch_page_404_raises_recoverable(self) -> None:
        connector = self._connector(
            _FakeTransport(
                HttpResponse(
                    status_code=404,
                    url=DEFAULT_XLSX_URL,
                    headers={},
                    body=b"",
                )
            )
        )
        with self.assertRaises(RecoverableConnectorError):
            await connector.fetch_page()

    async def test_fetch_page_5xx_raises_recoverable(self) -> None:
        connector = self._connector(
            _FakeTransport(
                HttpResponse(
                    status_code=503,
                    url=DEFAULT_XLSX_URL,
                    headers={},
                    body=b"",
                )
            )
        )
        with self.assertRaises(RecoverableConnectorError):
            await connector.fetch_page()

    async def test_fetch_page_other_status_raises_value_error(self) -> None:
        for status in (100, 302, 400, 418):
            with self.subTest(status=status):
                connector = self._connector(
                    _FakeTransport(
                        HttpResponse(
                            status_code=status,
                            url=DEFAULT_XLSX_URL,
                            headers={},
                            body=b"",
                        )
                    )
                )
                with self.assertRaises(ValueError):
                    await connector.fetch_page()

    async def test_fetch_page_propagates_missing_extractor_when_openpyxl_absent(self) -> None:
        # No row_extractor injected and openpyxl is absent: fetch_page must
        # surface MissingXlsxExtractorError (lazily) rather than ImportError.
        connector = BcraBalanceCambiarioConnector(
            transport=_FakeTransport(
                HttpResponse(
                    status_code=200,
                    url=DEFAULT_XLSX_URL,
                    headers={},
                    body=b"not actually xlsx",
                )
            ),
            row_extractor=None,
        )
        with self.assertRaises(MissingXlsxExtractorError):
            await connector.fetch_page()


if __name__ == "__main__":
    unittest.main()
