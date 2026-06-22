from __future__ import annotations

import sys
import unittest
from datetime import date

sys.path.insert(0, "src")

from finance_news.peso_curve import (
    CurvePoint,
    PesoCurveBuilder,
    PesoCurveProxy,
    RateInput,
    build_peso_curve_proxy,
)


class TestRateInput(unittest.TestCase):
    """Test RateInput dataclass."""

    def test_to_dict(self) -> None:
        """Test to_dict method."""
        rate_input = RateInput(
            source="tesoro_corte",
            horizon_days=30,
            rate=0.05,
            as_of_date=date(2024, 1, 15),
            classification="primary",
        )
        result = rate_input.to_dict()
        self.assertEqual(result["source"], "tesoro_corte")
        self.assertEqual(result["horizon_days"], 30)
        self.assertEqual(result["rate"], 0.05)
        self.assertEqual(result["as_of_date"], "2024-01-15")
        self.assertEqual(result["classification"], "primary")

    def test_from_dict(self) -> None:
        """Test from_dict method."""
        data = {
            "source": "tesoro_corte",
            "horizon_days": 30,
            "rate": 0.05,
            "as_of_date": "2024-01-15",
            "classification": "primary",
        }
        rate_input = RateInput.from_dict(data)
        self.assertEqual(rate_input.source, "tesoro_corte")
        self.assertEqual(rate_input.horizon_days, 30)
        self.assertEqual(rate_input.rate, 0.05)
        self.assertEqual(rate_input.as_of_date, date(2024, 1, 15))
        self.assertEqual(rate_input.classification, "primary")

    def test_floating_horizon_none(self) -> None:
        """Test floating rate with None horizon."""
        rate_input = RateInput(
            source="bcra_tamar",
            horizon_days=None,
            rate=0.045,
            as_of_date=date(2024, 1, 15),
            classification="proxy",
        )
        self.assertIsNone(rate_input.horizon_days)
        self.assertEqual(rate_input.source, "bcra_tamar")


class TestCurvePoint(unittest.TestCase):
    """Test CurvePoint dataclass."""

    def test_to_dict(self) -> None:
        """Test to_dict method."""
        point = CurvePoint(
            horizon_days=30,
            rate=0.05,
            contributing_sources=["tesoro_corte"],
            classification="proxy",
        )
        result = point.to_dict()
        self.assertEqual(result["horizon_days"], 30)
        self.assertEqual(result["rate"], 0.05)
        self.assertEqual(result["contributing_sources"], ["tesoro_corte"])
        self.assertEqual(result["classification"], "proxy")

    def test_from_dict(self) -> None:
        """Test from_dict method."""
        data = {
            "horizon_days": 30,
            "rate": 0.05,
            "contributing_sources": ["tesoro_corte"],
            "classification": "proxy",
        }
        point = CurvePoint.from_dict(data)
        self.assertEqual(point.horizon_days, 30)
        self.assertEqual(point.rate, 0.05)
        self.assertEqual(point.contributing_sources, ["tesoro_corte"])
        self.assertEqual(point.classification, "proxy")

    def test_default_classification(self) -> None:
        """Test default classification is proxy."""
        data = {
            "horizon_days": 60,
            "rate": 0.06,
            "contributing_sources": ["cafci"],
        }
        point = CurvePoint.from_dict(data)
        self.assertEqual(point.classification, "proxy")


class TestPesoCurveProxy(unittest.TestCase):
    """Test PesoCurveProxy dataclass."""

    def test_to_dict(self) -> None:
        """Test to_dict method."""
        point = CurvePoint(
            horizon_days=30,
            rate=0.05,
            contributing_sources=["tesoro_corte"],
        )
        curve = PesoCurveProxy(
            as_of_date=date(2024, 1, 15),
            points=[point],
            assumptions=["no liquid peso curve"],
            data_classification="proxy",
        )
        result = curve.to_dict()
        self.assertEqual(result["as_of_date"], "2024-01-15")
        self.assertEqual(len(result["points"]), 1)
        self.assertEqual(result["assumptions"], ["no liquid peso curve"])
        self.assertEqual(result["data_classification"], "proxy")

    def test_from_dict(self) -> None:
        """Test from_dict method."""
        data = {
            "as_of_date": "2024-01-15",
            "points": [
                {
                    "horizon_days": 30,
                    "rate": 0.05,
                    "contributing_sources": ["tesoro_corte"],
                    "classification": "proxy",
                }
            ],
            "assumptions": ["no liquid peso curve"],
            "data_classification": "proxy",
        }
        curve = PesoCurveProxy.from_dict(data)
        self.assertEqual(curve.as_of_date, date(2024, 1, 15))
        self.assertEqual(len(curve.points), 1)
        self.assertEqual(curve.assumptions, ["no liquid peso curve"])
        self.assertEqual(curve.data_classification, "proxy")


class TestPesoCurveBuilder(unittest.TestCase):
    """Test PesoCurveBuilder class."""

    def test_empty_rates(self) -> None:
        """Test building curve with no rate inputs."""
        builder = PesoCurveBuilder()
        curve = builder.build_peso_curve_proxy([])
        self.assertEqual(len(curve.points), 0)
        self.assertEqual(curve.data_classification, "proxy")
        self.assertIn("no rate inputs provided", curve.assumptions[0])

    def test_tesoro_corte_primary_anchor(self) -> None:
        """Test Tesoro cutoff used as primary anchor."""
        rates = [
            RateInput(
                source="tesoro_corte",
                horizon_days=30,
                rate=0.05,
                as_of_date=date(2024, 1, 15),
                classification="primary",
            )
        ]
        builder = PesoCurveBuilder()
        curve = builder.build_peso_curve_proxy(rates)
        self.assertEqual(len(curve.points), 1)
        self.assertEqual(curve.points[0].horizon_days, 30)
        self.assertEqual(curve.points[0].rate, 0.05)
        self.assertEqual(curve.points[0].contributing_sources, ["tesoro_corte"])
        self.assertEqual(curve.points[0].classification, "proxy")
        self.assertIn("Tesoro cutoff used as primary anchor", curve.assumptions[1])

    def test_multiple_sources_same_horizon(self) -> None:
        """Test multiple sources for same horizon prioritizes Tesoro."""
        rates = [
            RateInput(
                source="tesoro_corte",
                horizon_days=30,
                rate=0.05,
                as_of_date=date(2024, 1, 15),
                classification="primary",
            ),
            RateInput(
                source="bcra_cer",
                horizon_days=30,
                rate=0.045,
                as_of_date=date(2024, 1, 15),
                classification="proxy",
            ),
            RateInput(
                source="cafci",
                horizon_days=30,
                rate=0.055,
                as_of_date=date(2024, 1, 15),
                classification="proxy",
            ),
        ]
        builder = PesoCurveBuilder()
        curve = builder.build_peso_curve_proxy(rates)
        self.assertEqual(len(curve.points), 1)
        # Should use Tesoro rate, not average
        self.assertEqual(curve.points[0].rate, 0.05)
        self.assertEqual(curve.points[0].contributing_sources, ["tesoro_corte"])

    def test_bcra_fallback_no_tesoro(self) -> None:
        """Test BCRA CER/TAMAR used when no Tesoro available."""
        rates = [
            RateInput(
                source="bcra_cer",
                horizon_days=15,
                rate=0.04,
                as_of_date=date(2024, 1, 15),
                classification="proxy",
            )
        ]
        builder = PesoCurveBuilder()
        curve = builder.build_peso_curve_proxy(rates)
        self.assertEqual(len(curve.points), 1)
        self.assertEqual(curve.points[0].horizon_days, 15)
        self.assertEqual(curve.points[0].rate, 0.04)
        self.assertEqual(curve.points[0].contributing_sources, ["bcra_cer"])
        self.assertIn("BCRA sources used", curve.assumptions[1])

    def test_cafci_fallback_no_tesoro_bcra(self) -> None:
        """Test CAFCI fund rate used when no Tesoro/BCRA available."""
        rates = [
            RateInput(
                source="cafci",
                horizon_days=90,
                rate=0.06,
                as_of_date=date(2024, 1, 15),
                classification="proxy",
            )
        ]
        builder = PesoCurveBuilder()
        curve = builder.build_peso_curve_proxy(rates)
        self.assertEqual(len(curve.points), 1)
        self.assertEqual(curve.points[0].horizon_days, 90)
        self.assertEqual(curve.points[0].rate, 0.06)
        self.assertEqual(curve.points[0].contributing_sources, ["cafci"])
        self.assertIn("CAFCI fund rate used", curve.assumptions[1])

    def test_floating_rates(self) -> None:
        """Test floating/indexed rates handled separately."""
        rates = [
            RateInput(
                source="bcra_tamar",
                horizon_days=None,
                rate=0.045,
                as_of_date=date(2024, 1, 15),
                classification="proxy",
            )
        ]
        builder = PesoCurveBuilder()
        curve = builder.build_peso_curve_proxy(rates)
        # Floating rates don't create curve points but are documented
        self.assertEqual(len(curve.points), 0)
        self.assertIn("floating/indexed sources available", curve.assumptions[1])
        self.assertIn("bcra_tamar", curve.assumptions[1])

    def test_multiple_horizons_sorted(self) -> None:
        """Test points are sorted by horizon (deterministic)."""
        rates = [
            RateInput(
                source="tesoro_corte",
                horizon_days=90,
                rate=0.06,
                as_of_date=date(2024, 1, 15),
                classification="primary",
            ),
            RateInput(
                source="tesoro_corte",
                horizon_days=30,
                rate=0.05,
                as_of_date=date(2024, 1, 15),
                classification="primary",
            ),
            RateInput(
                source="tesoro_corte",
                horizon_days=60,
                rate=0.055,
                as_of_date=date(2024, 1, 15),
                classification="primary",
            ),
        ]
        builder = PesoCurveBuilder()
        curve = builder.build_peso_curve_proxy(rates)
        self.assertEqual(len(curve.points), 3)
        self.assertEqual(curve.points[0].horizon_days, 30)
        self.assertEqual(curve.points[1].horizon_days, 60)
        self.assertEqual(curve.points[2].horizon_days, 90)

    def test_proxy_classification_everywhere(self) -> None:
        """Test all points marked as proxy, even with primary inputs."""
        rates = [
            RateInput(
                source="tesoro_corte",
                horizon_days=30,
                rate=0.05,
                as_of_date=date(2024, 1, 15),
                classification="primary",
            )
        ]
        builder = PesoCurveBuilder()
        curve = builder.build_peso_curve_proxy(rates)
        # Overall classification
        self.assertEqual(curve.data_classification, "proxy")
        # Each point classification
        for point in curve.points:
            self.assertEqual(point.classification, "proxy")
        # Assumptions document this
        self.assertIn("no liquid peso curve", curve.assumptions[0])

    def test_assumptions_non_empty(self) -> None:
        """Test assumptions list is non-empty."""
        rates = [
            RateInput(
                source="tesoro_corte",
                horizon_days=30,
                rate=0.05,
                as_of_date=date(2024, 1, 15),
                classification="primary",
            )
        ]
        builder = PesoCurveBuilder()
        curve = builder.build_peso_curve_proxy(rates)
        self.assertGreater(len(curve.assumptions), 0)
        self.assertIn("no liquid peso curve", curve.assumptions[0])

    def test_mixed_sources_assumptions(self) -> None:
        """Test assumptions document source usage."""
        rates = [
            RateInput(
                source="tesoro_corte",
                horizon_days=30,
                rate=0.05,
                as_of_date=date(2024, 1, 15),
                classification="primary",
            ),
            RateInput(
                source="bcra_cer",
                horizon_days=15,
                rate=0.04,
                as_of_date=date(2024, 1, 15),
                classification="proxy",
            ),
            RateInput(
                source="bcra_tamar",
                horizon_days=None,
                rate=0.045,
                as_of_date=date(2024, 1, 15),
                classification="proxy",
            ),
        ]
        builder = PesoCurveBuilder()
        curve = builder.build_peso_curve_proxy(rates)
        # Should document CER for short-term
        cer_assumptions = [
            a for a in curve.assumptions if "CER used for short-term" in a
        ]
        self.assertGreater(len(cer_assumptions), 0)
        # Should document TAMAR for floating
        tamar_assumptions = [a for a in curve.assumptions if "TAMAR" in a]
        self.assertGreater(len(tamar_assumptions), 0)
        # Should document sources used
        sources_assumption = [a for a in curve.assumptions if "sources used:" in a]
        self.assertGreater(len(sources_assumption), 0)

    def test_as_of_date_max_of_inputs(self) -> None:
        """Test as_of_date is max of input dates."""
        rates = [
            RateInput(
                source="tesoro_corte",
                horizon_days=30,
                rate=0.05,
                as_of_date=date(2024, 1, 10),
                classification="primary",
            ),
            RateInput(
                source="bcra_cer",
                horizon_days=15,
                rate=0.04,
                as_of_date=date(2024, 1, 15),
                classification="proxy",
            ),
        ]
        builder = PesoCurveBuilder()
        curve = builder.build_peso_curve_proxy(rates)
        self.assertEqual(curve.as_of_date, date(2024, 1, 15))

    def test_average_multiple_tesoro_same_horizon(self) -> None:
        """Test averaging multiple Tesoro rates at same horizon."""
        rates = [
            RateInput(
                source="tesoro_corte",
                horizon_days=30,
                rate=0.05,
                as_of_date=date(2024, 1, 15),
                classification="primary",
            ),
            RateInput(
                source="tesoro_corte",
                horizon_days=30,
                rate=0.055,
                as_of_date=date(2024, 1, 15),
                classification="primary",
            ),
        ]
        builder = PesoCurveBuilder()
        curve = builder.build_peso_curve_proxy(rates)
        self.assertEqual(len(curve.points), 1)
        # Average of 0.05 and 0.055
        self.assertAlmostEqual(curve.points[0].rate, 0.0525)

    def test_average_multiple_bcra_same_horizon(self) -> None:
        """Test averaging multiple BCRA rates when no Tesoro."""
        rates = [
            RateInput(
                source="bcra_cer",
                horizon_days=15,
                rate=0.04,
                as_of_date=date(2024, 1, 15),
                classification="proxy",
            ),
            RateInput(
                source="bcra_tamar",
                horizon_days=15,
                rate=0.045,
                as_of_date=date(2024, 1, 15),
                classification="proxy",
            ),
        ]
        builder = PesoCurveBuilder()
        curve = builder.build_peso_curve_proxy(rates)
        self.assertEqual(len(curve.points), 1)
        # Average of 0.04 and 0.045
        self.assertAlmostEqual(curve.points[0].rate, 0.0425)
        # Both sources should be documented
        self.assertIn("bcra_cer", curve.points[0].contributing_sources)
        self.assertIn("bcra_tamar", curve.points[0].contributing_sources)


class TestBuildPesoCurveProxy(unittest.TestCase):
    """Test convenience function build_peso_curve_proxy."""

    def test_convenience_function(self) -> None:
        """Test build_peso_curve_proxy convenience function."""
        rates = [
            RateInput(
                source="tesoro_corte",
                horizon_days=30,
                rate=0.05,
                as_of_date=date(2024, 1, 15),
                classification="primary",
            )
        ]
        curve = build_peso_curve_proxy(rates)
        self.assertEqual(len(curve.points), 1)
        self.assertEqual(curve.points[0].horizon_days, 30)
        self.assertEqual(curve.data_classification, "proxy")

    def test_convenience_function_empty(self) -> None:
        """Test build_peso_curve_proxy with empty rates."""
        curve = build_peso_curve_proxy([])
        self.assertEqual(len(curve.points), 0)
        self.assertEqual(curve.data_classification, "proxy")


if __name__ == "__main__":
    unittest.main()