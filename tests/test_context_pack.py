import sys
import unittest
from datetime import datetime

sys.path.insert(0, "src")

from finance_news.connectors.models import Freshness, Provenance, SourceItem
from finance_news.context_pack import (
    ContextPackBuilder,
    ContextPackItem,
    OpenGap,
    ReportContextPack,
    SourceIndexEntry,
    to_json,
    to_markdown,
)
from finance_news.scoring import NormalizedSignal, ScoredSignal


class TestContextPackItem(unittest.TestCase):
    """Test ContextPackItem dataclass and serialization."""

    def test_to_dict(self) -> None:
        """Test ContextPackItem serialization to dict."""
        item = ContextPackItem(
            topic="IPC Núcleo",
            score=3,
            fact="2.5% mensual",
            interpretation="Aceleración inflacionaria",
            mechanism="Presión de demanda agregada",
            confirm_variable="IPC mensual > 3%",
            invalidate_variable="IPC mensual < 2%",
            confidence="alta",
            source_ids=["src_1"],
            excerpt="El IPC núcleo muestra aceleración",
        )
        result = item.to_dict()
        self.assertEqual(result["tema"], "IPC Núcleo")
        self.assertEqual(result["score"], 3)
        self.assertEqual(result["dato"], "2.5% mensual")
        self.assertEqual(result["lectura"], "Aceleración inflacionaria")
        self.assertEqual(result["mecanismo"], "Presión de demanda agregada")
        self.assertEqual(result["precio_o_variable_que_confirma"], "IPC mensual > 3%")
        self.assertEqual(result["precio_o_variable_que_invalida"], "IPC mensual < 2%")
        self.assertEqual(result["confianza"], "alta")
        self.assertEqual(result["fuente_ids"], ["src_1"])
        self.assertEqual(result["extracto"], "El IPC núcleo muestra aceleración")

    def test_from_dict(self) -> None:
        """Test ContextPackItem deserialization from dict."""
        data = {
            "tema": "Reservas BCRA",
            "score": 4,
            "dato": "-5.2B USD",
            "lectura": "Pérdida significativa",
            "mecanismo": "Drenaje por intervenciones",
            "precio_o_variable_que_confirma": "Reservas < -6B",
            "precio_o_variable_que_invalida": "Reservas > -4B",
            "confianza": "alta",
            "fuente_ids": ["src_2"],
            "extracto": "Reservas internacionales caen",
        }
        item = ContextPackItem.from_dict(data)
        self.assertEqual(item.topic, "Reservas BCRA")
        self.assertEqual(item.score, 4)
        self.assertEqual(item.fact, "-5.2B USD")
        self.assertEqual(item.interpretation, "Pérdida significativa")
        self.assertEqual(item.mechanism, "Drenaje por intervenciones")
        self.assertEqual(item.confirm_variable, "Reservas < -6B")
        self.assertEqual(item.invalidate_variable, "Reservas > -4B")
        self.assertEqual(item.confidence, "alta")
        self.assertEqual(item.source_ids, ["src_2"])
        self.assertEqual(item.excerpt, "Reservas internacionales caen")

    def test_roundtrip(self) -> None:
        """Test ContextPackItem serialization roundtrip."""
        original = ContextPackItem(
            topic="MEP",
            score=2,
            fact="1050 ARS/USD",
            interpretation="Estabilidad cambiaria",
            mechanism="Equilibrio oferta/demanda",
            confirm_variable="MEP < 1070",
            invalidate_variable="MEP > 1100",
            confidence="media",
            source_ids=["src_3"],
            excerpt="Dólar MEP estable",
        )
        data = original.to_dict()
        restored = ContextPackItem.from_dict(data)
        self.assertEqual(restored, original)


class TestSourceIndexEntry(unittest.TestCase):
    """Test SourceIndexEntry dataclass and serialization."""

    def test_to_dict(self) -> None:
        """Test SourceIndexEntry serialization to dict."""
        entry = SourceIndexEntry(
            id="src_1",
            label="BCRA - Reservas internacionales",
            type="primaria_oficial",
            region="AR",
            url="https://bcra.gob.ar/reservas",
            published_at="2026-06-10",
            accessed_at="2026-06-11",
            supports=["argentina.dolar_y_reservas[0]"],
            confidence_impact="none",
        )
        result = entry.to_dict()
        self.assertEqual(result["id"], "src_1")
        self.assertEqual(result["label"], "BCRA - Reservas internacionales")
        self.assertEqual(result["type"], "primaria_oficial")
        self.assertEqual(result["region"], "AR")
        self.assertEqual(result["url"], "https://bcra.gob.ar/reservas")
        self.assertEqual(result["published_at"], "2026-06-10")
        self.assertEqual(result["accessed_at"], "2026-06-11")
        self.assertEqual(result["supports"], ["argentina.dolar_y_reservas[0]"])
        self.assertEqual(result["confidence_impact"], "none")

    def test_from_dict(self) -> None:
        """Test SourceIndexEntry deserialization from dict."""
        data = {
            "id": "src_2",
            "label": "Fed - FOMC Minutes",
            "type": "primaria_oficial",
            "region": "US",
            "url": "https://federalreserve.gov/minutes",
            "published_at": "2026-06-08",
            "accessed_at": "2026-06-09",
            "supports": ["internacional.fed_bancos_centrales[0]"],
            "confidence_impact": "none",
        }
        entry = SourceIndexEntry.from_dict(data)
        self.assertEqual(entry.id, "src_2")
        self.assertEqual(entry.label, "Fed - FOMC Minutes")


class TestOpenGap(unittest.TestCase):
    """Test OpenGap dataclass and serialization."""

    def test_to_dict(self) -> None:
        """Test OpenGap serialization to dict."""
        gap = OpenGap(
            section="internacional.geopolitica",
            missing_input="comunicado oficial",
            fallback_used="medio confiable",
            confidence_adjustment="baja",
            note="mantener lectura condicional",
        )
        result = gap.to_dict()
        self.assertEqual(result["section"], "internacional.geopolitica")
        self.assertEqual(result["missing_input"], "comunicado oficial")
        self.assertEqual(result["fallback_used"], "medio confiable")
        self.assertEqual(result["confidence_adjustment"], "baja")
        self.assertEqual(result["note"], "mantener lectura condicional")

    def test_from_dict(self) -> None:
        """Test OpenGap deserialization from dict."""
        data = {
            "section": "argentina.inflacion_y_actividad",
            "missing_input": "dato oficial INDEC",
            "fallback_used": None,
            "confidence_adjustment": "media",
            "note": "esperar publicación",
        }
        gap = OpenGap.from_dict(data)
        self.assertEqual(gap.section, "argentina.inflacion_y_actividad")
        self.assertIsNone(gap.fallback_used)
        self.assertEqual(gap.confidence_adjustment, "media")


class TestReportContextPack(unittest.TestCase):
    """Test ReportContextPack dataclass and serialization."""

    def test_to_dict(self) -> None:
        """Test ReportContextPack serialization to dict."""
        pack = ReportContextPack(
            week_end_date="2026-06-12",
            generated_at="2026-06-13T10:00:00",
            timezone="America/Argentina/Buenos_Aires",
            argentina_items=[],
            international_items=[],
            market_items=[],
            source_index=[],
            open_gaps=[],
            summary_stats={"total_signals": 0},
        )
        result = pack.to_dict()
        self.assertEqual(result["reporting_window"]["week_end_date"], "2026-06-12")
        self.assertEqual(result["generated_at"], "2026-06-13T10:00:00")
        self.assertIn("generator_profile", result)
        self.assertIn("editorial_rules", result)
        self.assertIn("source_policy", result)
        self.assertIn("signal_selection", result)
        self.assertIn("sections", result)
        self.assertIn("source_index", result)
        self.assertIn("open_gaps", result)
        self.assertIn("summary_stats", result)


class TestContextPackBuilder(unittest.TestCase):
    """Test ContextPackBuilder inclusion rules and pack building."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.builder = ContextPackBuilder(score_threshold=2, confidence_threshold="media")
        self.now = datetime.now()

    def _create_source_item(
        self,
        external_id: str,
        source: str,
        title: str,
        url: str,
        summary: str = "",
    ) -> SourceItem:
        """Create a test SourceItem."""
        return SourceItem(
            external_id=external_id,
            source=source,
            published_at=self.now,
            title=title,
            body=None,
            summary=summary,
            url=url,
            metadata={},
            provenance=Provenance(
                connector="test",
                source=source,
                fetch_url=url,
                canonical_url=url,
                cursor=None,
                fetched_at=self.now,
                parser_version="1.0",
            ),
            freshness=Freshness(
                published_at=self.now,
                first_seen_at=self.now,
                fetched_at=self.now,
                is_stale=False,
                ttl_seconds=None,
            ),
        )

    def _create_scored_signal(
        self,
        domain: str,
        name: str,
        value: float,
        unit: str,
        region: str,
        score: int,
    ) -> ScoredSignal:
        """Create a test ScoredSignal."""
        signal = NormalizedSignal(
            domain=domain,
            name=name,
            value=value,
            unit=unit,
            period="2026-06-12",
            region=region,
            notes="",
        )
        return ScoredSignal(
            signal=signal,
            score=score,
            rationale=f"Score {score} rationale",
            inputs_used=[unit],
            breakout_triggers=[],
        )

    def test_inclusion_rules_by_score(self) -> None:
        """Test inclusion rules filter by score threshold."""
        items = [
            self._create_source_item("IPC Núcleo", "primaria_oficial", "IPC Núcleo", "https://indec.gob.ar", "Acelera inflación"),
            self._create_source_item("Reservas BCRA", "primaria_oficial", "Reservas", "https://bcra.gob.ar", "Caen reservas"),
        ]
        scored_signals = [
            self._create_scored_signal("inflacion", "IPC Núcleo", 2.5, "%", "argentina", 3),
            self._create_scored_signal("bcra_reservas", "Reservas BCRA", -5.2, "B USD", "argentina", 1),
        ]
        pack = self.builder.build(items, scored_signals, "2026-06-12")
        self.assertEqual(len(pack.argentina_items), 1)
        self.assertEqual(len(pack.open_gaps), 1)
        self.assertIn("score 1", pack.open_gaps[0].missing_input)

    def test_inclusion_rules_by_confidence(self) -> None:
        """Test inclusion rules filter by confidence threshold."""
        items = [
            self._create_source_item("EMAE -2.0%", "secundaria", "Dato secundario", "https://secondary.com", "Dato no verificado"),
            self._create_source_item("EMAE -3.0%", "primaria_oficial", "Dato oficial", "https://official.com", "Dato verificado"),
        ]
        scored_signals = [
            self._create_scored_signal("actividad_empleo", "EMAE -2.0%", -2.0, "%", "argentina", 2),
            self._create_scored_signal("actividad_empleo", "EMAE -3.0%", -3.0, "%", "argentina", 2),
        ]
        pack = self.builder.build(items, scored_signals, "2026-06-12")
        self.assertEqual(len(pack.argentina_items), 2)

    def test_region_classification(self) -> None:
        """Test region classification logic."""
        items = [
            self._create_source_item("Rollover Tesoro", "primaria_oficial", "Rollover Tesoro", "https://tesoro.gob.ar", "Rollover"),
            self._create_source_item("Fed FOMC", "primaria_oficial", "Fed FOMC", "https://fed.gov", "FOMC"),
            self._create_source_item("MEP", "primaria_oficial", "MEP", "https://byma.com.ar", "Dólar MEP"),
        ]
        scored_signals = [
            self._create_scored_signal("tesoro_y_deuda", "Rollover Tesoro", 85.0, "%", "argentina", 3),
            self._create_scored_signal("fed_bancos_centrales", "Fed FOMC", 4.5, "%", "internacional", 3),
            self._create_scored_signal("cambiario", "MEP", 1050.0, "ARS/USD", "argentina", 2),
        ]
        pack = self.builder.build(items, scored_signals, "2026-06-12")
        self.assertEqual(len(pack.market_items), 2)
        self.assertEqual(len(pack.international_items), 1)
        self.assertEqual(len(pack.argentina_items), 0)

    def test_source_index_generation(self) -> None:
        """Test source index is generated correctly."""
        items = [
            self._create_source_item("Reservas BCRA", "primaria_oficial", "BCRA Reservas", "https://bcra.gob.ar", "Reservas netas"),
        ]
        scored_signals = [
            self._create_scored_signal("bcra_reservas", "Reservas BCRA", -3.5, "B USD", "argentina", 3),
        ]
        pack = self.builder.build(items, scored_signals, "2026-06-12")
        self.assertEqual(len(pack.source_index), 1)
        entry = pack.source_index[0]
        self.assertEqual(entry.id, "src_0")
        self.assertIn("BCRA Reservas", entry.label)
        self.assertEqual(entry.type, "primaria_oficial")
        self.assertEqual(entry.region, "argentina")

    def test_open_gaps_population(self) -> None:
        """Test open gaps are populated for missing sources and excluded signals."""
        items = [
            self._create_source_item("IPC Núcleo", "primaria_oficial", "Dato disponible", "https://available.com", "Dato OK"),
        ]
        scored_signals = [
            self._create_scored_signal("inflacion", "IPC Núcleo", 2.5, "%", "argentina", 2),
            self._create_scored_signal("inflacion", "IPC General", 3.0, "%", "argentina", 4),
        ]
        pack = self.builder.build(items, scored_signals, "2026-06-12")
        self.assertEqual(len(pack.open_gaps), 1)
        self.assertIn("No source item found", pack.open_gaps[0].note)

    def test_complete_pack_building(self) -> None:
        """Test building a complete context pack with multiple items."""
        items = [
            self._create_source_item("IPC Núcleo", "primaria_oficial", "IPC Núcleo", "https://indec.gob.ar", "Acelera"),
            self._create_source_item("Fed FOMC", "primaria_oficial", "Fed FOMC", "https://fed.gov", "Sin cambios"),
            self._create_source_item("MEP", "primaria_oficial", "MEP", "https://byma.com.ar", "Estable"),
        ]
        scored_signals = [
            self._create_scored_signal("inflacion", "IPC Núcleo", 2.5, "%", "argentina", 3),
            self._create_scored_signal("fed_bancos_centrales", "Fed FOMC", 4.5, "%", "internacional", 2),
            self._create_scored_signal("cambiario", "MEP", 1050.0, "ARS/USD", "argentina", 2),
        ]
        pack = self.builder.build(items, scored_signals, "2026-06-12")
        self.assertEqual(len(pack.argentina_items), 1)
        self.assertEqual(len(pack.international_items), 1)
        self.assertEqual(len(pack.market_items), 1)
        self.assertEqual(len(pack.source_index), 3)
        self.assertEqual(pack.week_end_date, "2026-06-12")
        self.assertIn("total_signals", pack.summary_stats)
        self.assertEqual(pack.summary_stats["total_signals"], 3)


class TestSerializers(unittest.TestCase):
    """Test JSON and Markdown serializers."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.pack = ReportContextPack(
            week_end_date="2026-06-12",
            generated_at="2026-06-13T10:00:00",
            timezone="America/Argentina/Buenos_Aires",
            argentina_items=[
                ContextPackItem(
                    topic="IPC Núcleo",
                    score=3,
                    fact="2.5% mensual",
                    interpretation="Aceleración inflacionaria",
                    mechanism="Presión de demanda",
                    confirm_variable="IPC > 3%",
                    invalidate_variable="IPC < 2%",
                    confidence="alta",
                    source_ids=["src_1"],
                    excerpt="Acelera",
                ),
            ],
            international_items=[],
            market_items=[],
            source_index=[
                SourceIndexEntry(
                    id="src_1",
                    label="INDEC - IPC",
                    type="primaria_oficial",
                    region="AR",
                    url="https://indec.gob.ar",
                    published_at="2026-06-10",
                    accessed_at="2026-06-11",
                    supports=["argentina.inflacion_y_actividad[0]"],
                    confidence_impact="none",
                ),
            ],
            open_gaps=[],
            summary_stats={"total_signals": 1, "included_signals": 1, "excluded_signals": 0, "argentina_count": 1, "international_count": 0, "market_count": 0, "source_count": 1},
        )

    def test_to_json(self) -> None:
        """Test JSON serialization."""
        json_str = to_json(self.pack)
        self.assertIn("week_end_date", json_str)
        self.assertIn("source_index", json_str)
        self.assertIn("open_gaps", json_str)
        self.assertIn("2026-06-12", json_str)
        self.assertIn("IPC Núcleo", json_str)

    def test_to_markdown(self) -> None:
        """Test Markdown serialization."""
        md_str = to_markdown(self.pack)
        self.assertIn("# Weekly Report Context Pack", md_str)
        self.assertIn("## Reporting Window", md_str)
        self.assertIn("Week End Date: 2026-06-12", md_str)
        self.assertIn("## Source Index", md_str)
        self.assertIn("IPC Núcleo", md_str)
        self.assertIn("## Input Payload (JSON)", md_str)


class TestInclusionExclusion(unittest.TestCase):
    """Test inclusion and exclusion logic comprehensively."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.now = datetime.now()

    def _create_source_item(self, external_id: str, source: str, title: str, url: str) -> SourceItem:
        """Create a test SourceItem."""
        return SourceItem(
            external_id=external_id,
            source=source,
            published_at=self.now,
            title=title,
            body=None,
            summary="",
            url=url,
            metadata={},
            provenance=Provenance(
                connector="test",
                source=source,
                fetch_url=url,
                canonical_url=url,
                cursor=None,
                fetched_at=self.now,
                parser_version="1.0",
            ),
            freshness=Freshness(
                published_at=self.now,
                first_seen_at=self.now,
                fetched_at=self.now,
                is_stale=False,
                ttl_seconds=None,
            ),
        )

    def _create_scored_signal(
        self,
        domain: str,
        name: str,
        value: float,
        unit: str,
        region: str,
        score: int,
    ) -> ScoredSignal:
        """Create a test ScoredSignal."""
        signal = NormalizedSignal(
            domain=domain,
            name=name,
            value=value,
            unit=unit,
            period="2026-06-12",
            region=region,
            notes="",
        )
        return ScoredSignal(
            signal=signal,
            score=score,
            rationale=f"Score {score}",
            inputs_used=[unit],
            breakout_triggers=[],
        )

    def test_low_score_exclusion(self) -> None:
        """Test signals with low scores are excluded."""
        items = [self._create_source_item("IPC", "primaria_oficial", "Dato bajo", "https://test.com")]
        scored_signals = [self._create_scored_signal("inflacion", "IPC", 1.0, "%", "argentina", 1)]
        builder = ContextPackBuilder(score_threshold=2, confidence_threshold="media")
        pack = builder.build(items, scored_signals, "2026-06-12")
        self.assertEqual(len(pack.argentina_items), 0)
        self.assertEqual(len(pack.open_gaps), 1)
        self.assertIn("score 1", pack.open_gaps[0].missing_input)

    def test_high_score_inclusion(self) -> None:
        """Test signals with high scores are included."""
        items = [self._create_source_item("IPC", "primaria_oficial", "Dato alto", "https://test.com")]
        scored_signals = [self._create_scored_signal("inflacion", "IPC", 4.0, "%", "argentina", 4)]
        builder = ContextPackBuilder(score_threshold=2, confidence_threshold="media")
        pack = builder.build(items, scored_signals, "2026-06-12")
        self.assertEqual(len(pack.argentina_items), 1)
        self.assertEqual(len(pack.open_gaps), 0)

    def test_mixed_scores(self) -> None:
        """Test mixed scores result in correct inclusion/exclusion."""
        items = [
            self._create_source_item("IPC 1", "primaria_oficial", "Dato 1", "https://test1.com"),
            self._create_source_item("IPC 2", "primaria_oficial", "Dato 2", "https://test2.com"),
            self._create_source_item("IPC 3", "primaria_oficial", "Dato 3", "https://test3.com"),
        ]
        scored_signals = [
            self._create_scored_signal("inflacion", "IPC 1", 1.0, "%", "argentina", 1),
            self._create_scored_signal("inflacion", "IPC 2", 3.0, "%", "argentina", 3),
            self._create_scored_signal("inflacion", "IPC 3", 2.0, "%", "argentina", 2),
        ]
        builder = ContextPackBuilder(score_threshold=2, confidence_threshold="media")
        pack = builder.build(items, scored_signals, "2026-06-12")
        self.assertEqual(len(pack.argentina_items), 2)
        self.assertEqual(len(pack.open_gaps), 1)


if __name__ == "__main__":
    unittest.main()