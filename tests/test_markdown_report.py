import sys
import unittest

sys.path.insert(0, "src")

from datetime import datetime

from finance_news.context_pack import (
    ContextPackItem,
    OpenGap,
    ReportContextPack,
    SourceIndexEntry,
)
from finance_news.markdown_report import MarkdownReportGenerator, generate_report


class TestMarkdownReportGenerator(unittest.TestCase):
    """Test MarkdownReportGenerator deterministic output."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.generator = MarkdownReportGenerator()

    def test_generate_empty_pack(self) -> None:
        """Test generating report from an empty context pack."""
        pack = ReportContextPack(
            week_end_date="2026-06-12",
            generated_at="2026-06-13T10:00:00",
            timezone="America/Argentina/Buenos_Aires",
            argentina_items=[],
            international_items=[],
            market_items=[],
            source_index=[],
            open_gaps=[],
            summary_stats={
                "total_signals": 0,
                "included_signals": 0,
                "excluded_signals": 0,
                "argentina_count": 0,
                "international_count": 0,
                "market_count": 0,
                "source_count": 0,
            },
        )

        result = self.generator.generate(pack)

        self.assertIn("# Reporte Semanal", result)
        self.assertIn("## Argentina", result)
        self.assertIn("## Internacional", result)
        self.assertIn("## Mercado", result)
        self.assertIn("## Escenarios", result)
        self.assertIn("## Riesgos que rompen el escenario", result)
        self.assertIn("## Qué mirar la semana próxima", result)

    def test_generate_full_pack(self) -> None:
        """Test generating report from a complete context pack."""
        argentina_items = [
            ContextPackItem(
                topic="IPC Núcleo",
                score=3,
                fact="3.5% mensual",
                interpretation="Aceleración respecto al mes anterior",
                mechanism="Canal: inflacion",
                confirm_variable="IPC < 3.0% confirma desaceleración",
                invalidate_variable="IPC > 4.0% invalida tesis de desinflación",
                confidence="alta",
                source_ids=["src_1"],
                excerpt="El IPC núcleo mostró un incremento...",
            ),
            ContextPackItem(
                topic="Reservas Netas",
                score=4,
                fact="-USD 2.1B",
                interpretation="Pérdida significativa de reservas",
                mechanism="Canal: bcra_reservas",
                confirm_variable="Estabilidad de reservas confirma",
                invalidate_variable="Pérdida > USD 1B/semana invalida",
                confidence="alta",
                source_ids=["src_2"],
                excerpt="El BCRA reportó...",
            ),
        ]

        international_items = [
            ContextPackItem(
                topic="Fed Policy",
                score=2,
                fact="Tasa 5.25-5.50%",
                interpretation="Mantención de tasa",
                mechanism="Canal: fed_bancos_centrales",
                confirm_variable="Tasa estable confirma",
                invalidate_variable="Corte agresivo invalida",
                confidence="media",
                source_ids=["src_3"],
                excerpt="El FOMC decidió...",
            ),
        ]

        market_items = [
            ContextPackItem(
                topic="MEP",
                score=3,
                fact="1,050 ARS/USD",
                interpretation="Estabilidad relativa",
                mechanism="Canal: cambiario",
                confirm_variable="MEP < 1,100 confirma",
                invalidate_variable="MEP > 1,200 invalida",
                confidence="alta",
                source_ids=["src_4"],
                excerpt="El tipo de cambio MEP...",
            ),
        ]

        source_index = [
            SourceIndexEntry(
                id="src_1",
                label="INDEC - IPC",
                type="primaria_oficial",
                region="AR",
                url="https://indec.gob.ar/ipc",
                published_at="2026-06-12",
                accessed_at="2026-06-13T10:00:00",
                supports=["argentina.inflacion_y_actividad[0]"],
                confidence_impact="none",
            ),
            SourceIndexEntry(
                id="src_2",
                label="BCRA - Reservas",
                type="primaria_oficial",
                region="AR",
                url="https://bcra.gob.ar/reservas",
                published_at="2026-06-12",
                accessed_at="2026-06-13T10:00:00",
                supports=["argentina.dolar_y_reservas[0]"],
                confidence_impact="none",
            ),
            SourceIndexEntry(
                id="src_3",
                label="Fed - FOMC",
                type="primaria_oficial",
                region="US",
                url="https://federalreserve.gov/monetarypolicy/fomccalendars.htm",
                published_at="2026-06-12",
                accessed_at="2026-06-13T10:00:00",
                supports=["internacional.fed_bancos_centrales[0]"],
                confidence_impact="none",
            ),
            SourceIndexEntry(
                id="src_4",
                label="Mercado - MEP",
                type="mercado",
                region="AR",
                url="https://mercado.com.ar/mep",
                published_at="2026-06-12",
                accessed_at="2026-06-13T10:00:00",
                supports=["mercado.fx[0]"],
                confidence_impact="none",
            ),
        ]

        open_gaps = [
            OpenGap(
                section="tesoro_y_deuda",
                missing_input="Rollover mensual",
                fallback_used="Estimación de mercado",
                confidence_adjustment="media",
                note="Falta dato oficial de licitación",
            ),
        ]

        pack = ReportContextPack(
            week_end_date="2026-06-12",
            generated_at="2026-06-13T10:00:00",
            timezone="America/Argentina/Buenos_Aires",
            argentina_items=argentina_items,
            international_items=international_items,
            market_items=market_items,
            source_index=source_index,
            open_gaps=open_gaps,
            summary_stats={
                "total_signals": 4,
                "included_signals": 4,
                "excluded_signals": 1,
                "argentina_count": 2,
                "international_count": 1,
                "market_count": 1,
                "source_count": 4,
            },
        )

        result = self.generator.generate(pack)

        self.assertIn("# Reporte Semanal", result)
        self.assertIn("**Semana finaliza:** 2026-06-12", result)
        self.assertIn("**IPC Núcleo** (score: 3, confianza: alta)", result)
        self.assertIn("**Reservas Netas** (score: 4, confianza: alta)", result)
        self.assertIn("**Fed Policy** (score: 2, confianza: media)", result)
        self.assertIn("**MEP** (score: 3, confianza: alta)", result)
        self.assertIn("## Índice de Fuentes", result)
        self.assertIn("**src_1**: INDEC - IPC", result)
        self.assertIn("## Riesgos que rompen el escenario", result)
        self.assertIn("**Sección:** tesoro_y_deuda", result)

    def test_deterministic_ordering(self) -> None:
        """Test that output is deterministic regardless of input order."""
        items = [
            ContextPackItem(
                topic="Item B",
                score=2,
                fact="Fact B",
                interpretation="Interpretation B",
                mechanism="Canal: test",
                confirm_variable="Confirma B",
                invalidate_variable="Invalida B",
                confidence="media",
                source_ids=["src_2"],
            ),
            ContextPackItem(
                topic="Item A",
                score=3,
                fact="Fact A",
                interpretation="Interpretation A",
                mechanism="Canal: test",
                confirm_variable="Confirma A",
                invalidate_variable="Invalida A",
                confidence="alta",
                source_ids=["src_1"],
            ),
        ]

        source_index = [
            SourceIndexEntry(
                id="src_2",
                label="Source B",
                type="secundaria",
                region="AR",
                url="https://example.com/b",
                published_at="2026-06-12",
                accessed_at="2026-06-13T10:00:00",
                supports=["test[1]"],
                confidence_impact="lower",
            ),
            SourceIndexEntry(
                id="src_1",
                label="Source A",
                type="primaria_oficial",
                region="AR",
                url="https://example.com/a",
                published_at="2026-06-12",
                accessed_at="2026-06-13T10:00:00",
                supports=["test[0]"],
                confidence_impact="none",
            ),
        ]

        pack1 = ReportContextPack(
            week_end_date="2026-06-12",
            generated_at="2026-06-13T10:00:00",
            timezone="America/Argentina/Buenos_Aires",
            argentina_items=items,
            international_items=[],
            market_items=[],
            source_index=source_index,
            open_gaps=[],
            summary_stats={
                "total_signals": 2,
                "included_signals": 2,
                "excluded_signals": 0,
                "argentina_count": 2,
                "international_count": 0,
                "market_count": 0,
                "source_count": 2,
            },
        )

        pack2 = ReportContextPack(
            week_end_date="2026-06-12",
            generated_at="2026-06-13T10:00:00",
            timezone="America/Argentina/Buenos_Aires",
            argentina_items=list(reversed(items)),
            international_items=[],
            market_items=[],
            source_index=list(reversed(source_index)),
            open_gaps=[],
            summary_stats={
                "total_signals": 2,
                "included_signals": 2,
                "excluded_signals": 0,
                "argentina_count": 2,
                "international_count": 0,
                "market_count": 0,
                "source_count": 2,
            },
        )

        result1 = self.generator.generate(pack1)
        result2 = self.generator.generate(pack2)

        self.assertEqual(result1, result2)

    def test_module_level_function(self) -> None:
        """Test the module-level generate_report convenience function."""
        pack = ReportContextPack(
            week_end_date="2026-06-12",
            generated_at="2026-06-13T10:00:00",
            timezone="America/Argentina/Buenos_Aires",
            argentina_items=[
                ContextPackItem(
                    topic="Test",
                    score=2,
                    fact="Test fact",
                    interpretation="Test interpretation",
                    mechanism="Canal: test",
                    confirm_variable="Test confirma",
                    invalidate_variable="Test invalida",
                    confidence="media",
                    source_ids=[],
                )
            ],
            international_items=[],
            market_items=[],
            source_index=[],
            open_gaps=[],
            summary_stats={
                "total_signals": 1,
                "included_signals": 1,
                "excluded_signals": 0,
                "argentina_count": 1,
                "international_count": 0,
                "market_count": 0,
                "source_count": 0,
            },
        )

        result = generate_report(pack)
        self.assertIn("# Reporte Semanal", result)
        self.assertIn("**Test** (score: 2, confianza: media)", result)


class TestMarkdownReportSnapshots(unittest.TestCase):
    """Snapshot tests for Markdown report generation."""

    maxDiff = None

    def test_full_report_snapshot(self) -> None:
        """Generate and compare snapshot of a full report."""
        argentina_items = [
            ContextPackItem(
                topic="IPC Núcleo",
                score=3,
                fact="3.5% mensual",
                interpretation="Aceleración respecto al mes anterior",
                mechanism="Canal: inflacion",
                confirm_variable="IPC < 3.0% confirma desaceleración",
                invalidate_variable="IPC > 4.0% invalida tesis de desinflación",
                confidence="alta",
                source_ids=["src_1"],
                excerpt="El IPC núcleo mostró un incremento...",
            ),
            ContextPackItem(
                topic="Reservas Netas",
                score=4,
                fact="-USD 2.1B",
                interpretation="Pérdida significativa de reservas",
                mechanism="Canal: bcra_reservas",
                confirm_variable="Estabilidad de reservas confirma",
                invalidate_variable="Pérdida > USD 1B/semana invalida",
                confidence="alta",
                source_ids=["src_2"],
                excerpt="El BCRA reportó...",
            ),
        ]

        international_items = [
            ContextPackItem(
                topic="Fed Policy",
                score=2,
                fact="Tasa 5.25-5.50%",
                interpretation="Mantención de tasa",
                mechanism="Canal: fed_bancos_centrales",
                confirm_variable="Tasa estable confirma",
                invalidate_variable="Corte agresivo invalida",
                confidence="media",
                source_ids=["src_3"],
                excerpt="El FOMC decidió...",
            ),
        ]

        market_items = [
            ContextPackItem(
                topic="MEP",
                score=3,
                fact="1,050 ARS/USD",
                interpretation="Estabilidad relativa",
                mechanism="Canal: cambiario",
                confirm_variable="MEP < 1,100 confirma",
                invalidate_variable="MEP > 1,200 invalida",
                confidence="alta",
                source_ids=["src_4"],
                excerpt="El tipo de cambio MEP...",
            ),
        ]

        source_index = [
            SourceIndexEntry(
                id="src_1",
                label="INDEC - IPC",
                type="primaria_oficial",
                region="AR",
                url="https://indec.gob.ar/ipc",
                published_at="2026-06-12",
                accessed_at="2026-06-13T10:00:00",
                supports=["argentina.inflacion_y_actividad[0]"],
                confidence_impact="none",
            ),
            SourceIndexEntry(
                id="src_2",
                label="BCRA - Reservas",
                type="primaria_oficial",
                region="AR",
                url="https://bcra.gob.ar/reservas",
                published_at="2026-06-12",
                accessed_at="2026-06-13T10:00:00",
                supports=["argentina.dolar_y_reservas[0]"],
                confidence_impact="none",
            ),
            SourceIndexEntry(
                id="src_3",
                label="Fed - FOMC",
                type="primaria_oficial",
                region="US",
                url="https://federalreserve.gov/monetarypolicy/fomccalendars.htm",
                published_at="2026-06-12",
                accessed_at="2026-06-13T10:00:00",
                supports=["internacional.fed_bancos_centrales[0]"],
                confidence_impact="none",
            ),
            SourceIndexEntry(
                id="src_4",
                label="Mercado - MEP",
                type="mercado",
                region="AR",
                url="https://mercado.com.ar/mep",
                published_at="2026-06-12",
                accessed_at="2026-06-13T10:00:00",
                supports=["mercado.fx[0]"],
                confidence_impact="none",
            ),
        ]

        open_gaps = [
            OpenGap(
                section="tesoro_y_deuda",
                missing_input="Rollover mensual",
                fallback_used="Estimación de mercado",
                confidence_adjustment="media",
                note="Falta dato oficial de licitación",
            ),
        ]

        pack = ReportContextPack(
            week_end_date="2026-06-12",
            generated_at="2026-06-13T10:00:00",
            timezone="America/Argentina/Buenos_Aires",
            argentina_items=argentina_items,
            international_items=international_items,
            market_items=market_items,
            source_index=source_index,
            open_gaps=open_gaps,
            summary_stats={
                "total_signals": 4,
                "included_signals": 4,
                "excluded_signals": 1,
                "argentina_count": 2,
                "international_count": 1,
                "market_count": 1,
                "source_count": 4,
            },
        )

        generator = MarkdownReportGenerator()
        actual = generator.generate(pack)

        snapshot_path = "tests/fixtures/markdown_report/full_report_snapshot.md"
        with open(snapshot_path, "r", encoding="utf-8") as f:
            expected = f.read()

        self.assertEqual(
            actual.rstrip(),
            expected.rstrip(),
            msg="Snapshot mismatch. Update with: cp tests/fixtures/markdown_report/full_report_snapshot.md tests/fixtures/markdown_report/full_report_snapshot.md.new && "
            f"echo '{actual}' > tests/fixtures/markdown_report/full_report_snapshot.md",
        )

    def test_empty_report_snapshot(self) -> None:
        """Generate and compare snapshot of an empty report."""
        pack = ReportContextPack(
            week_end_date="2026-06-12",
            generated_at="2026-06-13T10:00:00",
            timezone="America/Argentina/Buenos_Aires",
            argentina_items=[],
            international_items=[],
            market_items=[],
            source_index=[],
            open_gaps=[],
            summary_stats={
                "total_signals": 0,
                "included_signals": 0,
                "excluded_signals": 0,
                "argentina_count": 0,
                "international_count": 0,
                "market_count": 0,
                "source_count": 0,
            },
        )

        generator = MarkdownReportGenerator()
        actual = generator.generate(pack)

        snapshot_path = "tests/fixtures/markdown_report/empty_report_snapshot.md"
        with open(snapshot_path, "r", encoding="utf-8") as f:
            expected = f.read()

        self.assertEqual(
            actual.rstrip(),
            expected.rstrip(),
            msg="Snapshot mismatch. Update with: cp tests/fixtures/markdown_report/empty_report_snapshot.md tests/fixtures/markdown_report/empty_report_snapshot.md.new && "
            f"echo '{actual}' > tests/fixtures/markdown_report/empty_report_snapshot.md",
        )


if __name__ == "__main__":
    unittest.main()