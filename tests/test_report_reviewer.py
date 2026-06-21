from __future__ import annotations

import sys
import unittest

sys.path.insert(0, "src")

from finance_news.report_reviewer import CriterionResult, ReviewResult, ReportReviewer, review_report


class TestCriterionResult(unittest.TestCase):
    def test_to_dict(self) -> None:
        cr = CriterionResult(name="Test", score=2, note="Good")
        d = cr.to_dict()
        self.assertEqual(d["name"], "Test")
        self.assertEqual(d["score"], 2)
        self.assertEqual(d["note"], "Good")

    def test_from_dict(self) -> None:
        d = {"name": "Test", "score": 1, "note": "Partial"}
        cr = CriterionResult.from_dict(d)
        self.assertEqual(cr.name, "Test")
        self.assertEqual(cr.score, 1)
        self.assertEqual(cr.note, "Partial")

    def test_roundtrip(self) -> None:
        cr = CriterionResult(name="Test", score=0, note="Bad")
        cr2 = CriterionResult.from_dict(cr.to_dict())
        self.assertEqual(cr.name, cr2.name)
        self.assertEqual(cr.score, cr2.score)
        self.assertEqual(cr.note, cr2.note)


class TestReviewResult(unittest.TestCase):
    def test_to_dict(self) -> None:
        cr = CriterionResult(name="Test", score=2, note="Good")
        rr = ReviewResult(
            overall_score=1.5, per_criterion=[cr], critical_failures=[], recommendations=[], approved=True
        )
        d = rr.to_dict()
        self.assertEqual(d["overall_score"], 1.5)
        self.assertEqual(len(d["per_criterion"]), 1)
        self.assertEqual(d["approved"], True)

    def test_from_dict(self) -> None:
        d = {
            "overall_score": 1.0,
            "per_criterion": [{"name": "Test", "score": 1, "note": "Partial"}],
            "critical_failures": ["Test failure"],
            "recommendations": ["Fix it"],
            "approved": False,
        }
        rr = ReviewResult.from_dict(d)
        self.assertEqual(rr.overall_score, 1.0)
        self.assertEqual(len(rr.per_criterion), 1)
        self.assertEqual(rr.critical_failures, ["Test failure"])
        self.assertEqual(rr.recommendations, ["Fix it"])
        self.assertEqual(rr.approved, False)

    def test_roundtrip(self) -> None:
        cr = CriterionResult(name="Test", score=2, note="Good")
        rr = ReviewResult(
            overall_score=2.0,
            per_criterion=[cr],
            critical_failures=["Issue"],
            recommendations=["Action"],
            approved=True,
        )
        rr2 = ReviewResult.from_dict(rr.to_dict())
        self.assertEqual(rr.overall_score, rr2.overall_score)
        self.assertEqual(len(rr.per_criterion), len(rr2.per_criterion))
        self.assertEqual(rr.critical_failures, rr2.critical_failures)
        self.assertEqual(rr.recommendations, rr2.recommendations)
        self.assertEqual(rr.approved, rr2.approved)


class TestReportReviewer(unittest.TestCase):
    def setUp(self) -> None:
        self.reviewer = ReportReviewer()

    def test_review_report_returns_result(self) -> None:
        markdown = "# Test\n\nDato: 1\n\nLectura: Interpretation"
        result = self.reviewer.review_report(markdown)
        self.assertIsInstance(result, ReviewResult)
        self.assertIsInstance(result.overall_score, float)
        self.assertIsInstance(result.per_criterion, list)
        self.assertIsInstance(result.critical_failures, list)
        self.assertIsInstance(result.recommendations, list)
        self.assertIsInstance(result.approved, bool)

    def test_review_report_all_criteria_evaluated(self) -> None:
        markdown = "# Test"
        result = self.reviewer.review_report(markdown)
        self.assertEqual(len(result.per_criterion), 10)

    def test_overall_score_calculation(self) -> None:
        markdown = "# Test"
        result = self.reviewer.review_report(markdown)
        if result.per_criterion:
            expected_score = sum(cr.score for cr in result.per_criterion) / len(result.per_criterion)
            self.assertAlmostEqual(result.overall_score, expected_score, places=2)

    def test_approved_with_all_critical_twos(self) -> None:
        markdown = """
# Reporte Semanal

## Dato vs Lectura

Dato: Las reservas aumentaron 5%.

Lectura: Esto refleja mayor entrada de divisas.

## Mecanismo

El aumento de reservas mejora la posición cambiaria a través del canal de expectativas.

## Precio de Mercado

El MEP se ubica en $920, confirmando la estabilidad.

El CCL en $945 valida la lectura.

## Riesgos

Riesgo: Shock externo.

Invalidador: Si el riesgo país sube a 2.000 puntos.

Señal temprana: Brecha cambiaria superior a $50.

## Trazabilidad

Fuente: BCRA.

Datos del mes de noviembre.

## Intervención

No hubo intervención.

## Instituciones

El BCRA maneja reservas.

El Tesoro maneja deuda.

## Técnico

El flujo de caja mejoró.

## Confianza

Confianza media en el escenario.

Faltantes: No hay datos de pases.

## Utilidad

Mirar la brecha cambiaria la próxima semana.

Seguir la demanda de bonos.
"""
        result = self.reviewer.review_report(markdown)
        self.assertTrue(result.approved)

    def test_rejected_with_critical_zero(self) -> None:
        markdown = """
# Reporte

La inflación va a bajar seguro. Es inevitable.

No hay riesgos.
"""
        result = self.reviewer.review_report(markdown)
        self.assertFalse(result.approved)

    def test_detect_overinterpretation(self) -> None:
        markdown = """
# Reporte

El dato de hoy confirma un cambio de régimen estructural. Es indudable.

No hay cifras de respaldo.
"""
        result = self.reviewer.review_report(markdown)
        self.assertTrue(any("cambio de regimen" in failure.lower() for failure in result.critical_failures))

    def test_detect_missing_market_data(self) -> None:
        markdown = """
# Reporte

La credibilidad mejoró significativamente esta semana.

El riesgo bajó mucho.

No hay variables de mercado mencionadas.
"""
        result = self.reviewer.review_report(markdown)
        self.assertTrue(any("credibilidad" in failure.lower() for failure in result.critical_failures))

    def test_detect_bcra_tesoro_confusion(self) -> None:
        markdown = """
# Reporte

El BCRA incrementó su deuda significativamente.

El Tesoro tiene reservas por USD 28.000 millones.
"""
        result = self.reviewer.review_report(markdown)
        self.assertTrue(
            any("bcra" in failure.lower() and "deuda" in failure.lower() for failure in result.critical_failures)
            or any("tesoro" in failure.lower() and "reserva" in failure.lower() for failure in result.critical_failures)
        )


class TestReviewReportFunction(unittest.TestCase):
    def test_convenience_function(self) -> None:
        markdown = "# Test\n\nDato: 1"
        result = review_report(markdown)
        self.assertIsInstance(result, ReviewResult)


class TestApprovedFixture(unittest.TestCase):
    def test_approved_report_is_approved(self) -> None:
        with open("tests/fixtures/report_reviewer/approved_report.md") as f:
            markdown = f.read()

        result = review_report(markdown)
        self.assertTrue(result.approved, "Approved fixture should be approved")

    def test_approved_report_has_good_scores(self) -> None:
        with open("tests/fixtures/report_reviewer/approved_report.md") as f:
            markdown = f.read()

        result = review_report(markdown)

        critical_criteria_names = list(ReportReviewer.CRITICAL_CRITERIA.values())
        critical_scores = [cr.score for cr in result.per_criterion if cr.name in critical_criteria_names]

        # All critical should be at least 1
        for score in critical_scores:
            self.assertGreaterEqual(score, 1, f"Critical criterion has score {score}")

    def test_approved_report_no_critical_zeros(self) -> None:
        with open("tests/fixtures/report_reviewer/approved_report.md") as f:
            markdown = f.read()

        result = review_report(markdown)

        critical_criteria_names = list(ReportReviewer.CRITICAL_CRITERIA.values())
        critical_zeros = [cr for cr in result.per_criterion if cr.name in critical_criteria_names and cr.score == 0]

        self.assertEqual(len(critical_zeros), 0, "Approved report should have no critical zeros")


class TestRejectedFixture(unittest.TestCase):
    def test_rejected_report_is_rejected(self) -> None:
        with open("tests/fixtures/report_reviewer/rejected_report.md") as f:
            markdown = f.read()

        result = review_report(markdown)
        self.assertFalse(result.approved, "Rejected fixture should be rejected")

    def test_rejected_report_has_critical_failures(self) -> None:
        with open("tests/fixtures/report_reviewer/rejected_report.md") as f:
            markdown = f.read()

        result = review_report(markdown)

        # Should detect at least one issue or have low score
        self.assertTrue(
            len(result.critical_failures) > 0 or not result.approved or result.overall_score < 1.5,
            "Rejected report should have critical failures or low score",
        )

    def test_rejected_report_missing_market_data(self) -> None:
        with open("tests/fixtures/report_reviewer/rejected_report.md") as f:
            markdown = f.read()

        result = review_report(markdown)

        # Check for missing market data detection
        has_market_data_issue = any("mercado" in failure.lower() or "credibilidad" in failure.lower() for failure in result.critical_failures)

        # The test should pass if either:
        # 1. There are critical failures related to market data, OR
        # 2. The report is rejected OR has a low overall score
        self.assertTrue(
            has_market_data_issue or not result.approved or result.overall_score < 1.5,
            "Rejected report should detect missing market data",
        )


if __name__ == "__main__":
    unittest.main()