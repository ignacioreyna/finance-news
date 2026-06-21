from __future__ import annotations

import sys
import unittest

sys.path.insert(0, "src")

from finance_news.scoring import NormalizedSignal, ScoredSignal, ScoringEngine


class TestNormalizedSignal(unittest.TestCase):
    """Test NormalizedSignal dataclass."""

    def test_to_dict(self) -> None:
        """Test to_dict method."""
        signal = NormalizedSignal(
            domain="tesoro_y_deuda",
            name="rollover",
            value=115.0,
            unit="rollover",
            period="2024-W01",
            region="argentina",
            notes="High rollover",
        )
        result = signal.to_dict()
        self.assertEqual(result["domain"], "tesoro_y_deuda")
        self.assertEqual(result["name"], "rollover")
        self.assertEqual(result["value"], 115.0)
        self.assertEqual(result["unit"], "rollover")
        self.assertEqual(result["period"], "2024-W01")
        self.assertEqual(result["region"], "argentina")
        self.assertEqual(result["notes"], "High rollover")

    def test_from_dict(self) -> None:
        """Test from_dict method."""
        data = {
            "domain": "tesoro_y_deuda",
            "name": "rollover",
            "value": 115.0,
            "unit": "rollover",
            "period": "2024-W01",
            "region": "argentina",
            "notes": "High rollover",
        }
        signal = NormalizedSignal.from_dict(data)
        self.assertEqual(signal.domain, "tesoro_y_deuda")
        self.assertEqual(signal.name, "rollover")
        self.assertEqual(signal.value, 115.0)
        self.assertEqual(signal.unit, "rollover")
        self.assertEqual(signal.period, "2024-W01")
        self.assertEqual(signal.region, "argentina")
        self.assertEqual(signal.notes, "High rollover")

    def test_from_dict_without_notes(self) -> None:
        """Test from_dict without notes field."""
        data = {
            "domain": "tesoro_y_deuda",
            "name": "rollover",
            "value": 115.0,
            "unit": "rollover",
            "period": "2024-W01",
            "region": "argentina",
        }
        signal = NormalizedSignal.from_dict(data)
        self.assertEqual(signal.notes, "")


class TestScoredSignal(unittest.TestCase):
    """Test ScoredSignal dataclass."""

    def test_to_dict(self) -> None:
        """Test to_dict method."""
        signal = NormalizedSignal(
            domain="tesoro_y_deuda",
            name="rollover",
            value=115.0,
            unit="rollover",
            period="2024-W01",
            region="argentina",
        )
        scored = ScoredSignal(
            signal=signal,
            score=0,
            rationale="Sin senal nueva o ruido normal",
            inputs_used=["rollover"],
            breakout_triggers=[],
        )
        result = scored.to_dict()
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["rationale"], "Sin senal nueva o ruido normal")
        self.assertEqual(result["inputs_used"], ["rollover"])
        self.assertEqual(result["breakout_triggers"], [])

    def test_from_dict(self) -> None:
        """Test from_dict method."""
        data = {
            "signal": {
                "domain": "tesoro_y_deuda",
                "name": "rollover",
                "value": 115.0,
                "unit": "rollover",
                "period": "2024-W01",
                "region": "argentina",
                "notes": "",
            },
            "score": 0,
            "rationale": "Sin senal nueva o ruido normal",
            "inputs_used": ["rollover"],
            "breakout_triggers": [],
        }
        scored = ScoredSignal.from_dict(data)
        self.assertEqual(scored.score, 0)
        self.assertEqual(scored.rationale, "Sin senal nueva o ruido normal")
        self.assertEqual(scored.inputs_used, ["rollover"])
        self.assertEqual(scored.breakout_triggers, [])


class TestScoringEngine(unittest.TestCase):
    """Test ScoringEngine class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.engine = ScoringEngine()

    def test_score_zero_argentina_tesoro(self) -> None:
        """Test score 0 for Argentina treasury."""
        signal = NormalizedSignal(
            domain="tesoro_y_deuda",
            name="rollover_semanal",
            value=115.0,
            unit="rollover",
            period="2024-W01",
            region="argentina",
        )
        results = self.engine.score_signals([signal])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, 0)
        self.assertEqual(results[0].rationale, "Sin senal nueva o ruido normal")
        self.assertEqual(len(results[0].breakout_triggers), 0)

    def test_score_one_argentina_tesoro(self) -> None:
        """Test score 1 for Argentina treasury."""
        signal = NormalizedSignal(
            domain="tesoro_y_deuda",
            name="rollover_semanal",
            value=110.0,
            unit="rollover",
            period="2024-W01",
            region="argentina",
        )
        results = self.engine.score_signals([signal])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, 0)
        self.assertEqual(results[0].rationale, "Sin senal nueva o ruido normal")

    def test_score_two_argentina_tesoro(self) -> None:
        """Test score 2 for Argentina treasury."""
        signal = NormalizedSignal(
            domain="tesoro_y_deuda",
            name="rollover_semanal",
            value=95.0,
            unit="rollover",
            period="2024-W01",
            region="argentina",
        )
        results = self.engine.score_signals([signal])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, 2)
        self.assertEqual(results[0].rationale, "Senal relevante pero contenida")

    def test_score_three_argentina_tesoro(self) -> None:
        """Test score 3 for Argentina treasury."""
        signal = NormalizedSignal(
            domain="tesoro_y_deuda",
            name="rollover_semanal",
            value=85.0,
            unit="rollover",
            period="2024-W01",
            region="argentina",
        )
        results = self.engine.score_signals([signal])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, 3)
        self.assertEqual(results[0].rationale, "Stress alto o cambio de tendencia")

    def test_score_four_argentina_tesoro(self) -> None:
        """Test score 4 for Argentina treasury."""
        signal = NormalizedSignal(
            domain="tesoro_y_deuda",
            name="rollover_semanal",
            value=65.0,
            unit="rollover",
            period="2024-W01",
            region="argentina",
        )
        results = self.engine.score_signals([signal])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, 4)
        self.assertEqual(results[0].rationale, "Ruptura potencial de escenario base")
        self.assertGreater(len(results[0].breakout_triggers), 0)

    def test_score_zero_argentina_bcra(self) -> None:
        """Test score 0 for Argentina BCRA."""
        signal = NormalizedSignal(
            domain="bcra_reservas",
            name="reservas_netas",
            value=1.0,
            unit="reservas_netas",
            period="2024-W01",
            region="argentina",
        )
        results = self.engine.score_signals([signal])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, 0)
        self.assertEqual(results[0].rationale, "Sin senal nueva o ruido normal")

    def test_score_four_argentina_bcra(self) -> None:
        """Test score 4 for Argentina BCRA."""
        signal = NormalizedSignal(
            domain="bcra_reservas",
            name="reservas_netas",
            value=-5.0,
            unit="reservas_netas",
            period="2024-W01",
            region="argentina",
        )
        results = self.engine.score_signals([signal])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, 4)
        self.assertEqual(results[0].rationale, "Ruptura potencial de escenario base")
        self.assertGreater(len(results[0].breakout_triggers), 0)

    def test_score_zero_argentina_cambiario(self) -> None:
        """Test score 0 for Argentina cambiario."""
        signal = NormalizedSignal(
            domain="cambiario",
            name="mecccl",
            value=3.0,
            unit="mecccl",
            period="2024-W01",
            region="argentina",
        )
        results = self.engine.score_signals([signal])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, 0)
        self.assertEqual(results[0].rationale, "Sin senal nueva o ruido normal")

    def test_score_four_argentina_cambiario(self) -> None:
        """Test score 4 for Argentina cambiario."""
        signal = NormalizedSignal(
            domain="cambiario",
            name="mecccl",
            value=25.0,
            unit="mecccl",
            period="2024-W01",
            region="argentina",
        )
        results = self.engine.score_signals([signal])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, 4)
        self.assertEqual(results[0].rationale, "Ruptura potencial de escenario base")
        self.assertGreater(len(results[0].breakout_triggers), 0)

    def test_score_zero_argentina_inflacion(self) -> None:
        """Test score 0 for Argentina inflacion."""
        signal = NormalizedSignal(
            domain="inflacion",
            name="ipc_vs_consenso",
            value=0.3,
            unit="ipc_vs_consenso",
            period="2024-W01",
            region="argentina",
        )
        results = self.engine.score_signals([signal])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, 0)
        self.assertEqual(results[0].rationale, "Sin senal nueva o ruido normal")

    def test_score_four_argentina_inflacion(self) -> None:
        """Test score 4 for Argentina inflacion."""
        signal = NormalizedSignal(
            domain="inflacion",
            name="ipc_vs_consenso",
            value=2.5,
            unit="ipc_vs_consenso",
            period="2024-W01",
            region="argentina",
        )
        results = self.engine.score_signals([signal])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, 4)
        self.assertEqual(results[0].rationale, "Ruptura potencial de escenario base")
        self.assertGreater(len(results[0].breakout_triggers), 0)

    def test_score_zero_argentina_actividad(self) -> None:
        """Test score 0 for Argentina actividad."""
        signal = NormalizedSignal(
            domain="actividad_empleo",
            name="emae_vs_consenso",
            value=0.5,
            unit="emae_vs_consenso",
            period="2024-W01",
            region="argentina",
        )
        results = self.engine.score_signals([signal])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, 0)
        self.assertEqual(results[0].rationale, "Sin senal nueva o ruido normal")

    def test_score_four_argentina_actividad(self) -> None:
        """Test score 4 for Argentina actividad."""
        signal = NormalizedSignal(
            domain="actividad_empleo",
            name="emae_vs_consenso",
            value=4.0,
            unit="emae_vs_consenso",
            period="2024-W01",
            region="argentina",
        )
        results = self.engine.score_signals([signal])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, 4)
        self.assertEqual(results[0].rationale, "Ruptura potencial de escenario base")
        self.assertGreater(len(results[0].breakout_triggers), 0)

    def test_score_zero_international_fed(self) -> None:
        """Test score 0 for international Fed."""
        signal = NormalizedSignal(
            domain="fed_bancos_centrales",
            name="ust_2y",
            value=10.0,
            unit="ust_2y",
            period="2024-W01",
            region="international",
        )
        results = self.engine.score_signals([signal])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, 0)
        self.assertEqual(results[0].rationale, "Sin senal nueva o ruido normal")

    def test_score_four_international_fed(self) -> None:
        """Test score 4 for international Fed."""
        signal = NormalizedSignal(
            domain="fed_bancos_centrales",
            name="ust_2y",
            value=60.0,
            unit="ust_2y",
            period="2024-W01",
            region="international",
        )
        results = self.engine.score_signals([signal])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, 4)
        self.assertEqual(results[0].rationale, "Ruptura potencial de escenario base")
        self.assertGreater(len(results[0].breakout_triggers), 0)

    def test_score_zero_international_liquidez(self) -> None:
        """Test score 0 for international liquidity."""
        signal = NormalizedSignal(
            domain="liquidez_global_curva",
            name="ust_10y",
            value=15.0,
            unit="ust_10y",
            period="2024-W01",
            region="international",
        )
        results = self.engine.score_signals([signal])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, 0)
        self.assertEqual(results[0].rationale, "Sin senal nueva o ruido normal")

    def test_score_four_international_liquidez(self) -> None:
        """Test score 4 for international liquidity."""
        signal = NormalizedSignal(
            domain="liquidez_global_curva",
            name="ust_10y",
            value=70.0,
            unit="ust_10y",
            period="2024-W01",
            region="international",
        )
        results = self.engine.score_signals([signal])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, 4)
        self.assertEqual(results[0].rationale, "Ruptura potencial de escenario base")
        self.assertGreater(len(results[0].breakout_triggers), 0)

    def test_score_zero_international_geopolitica(self) -> None:
        """Test score 0 for international geopolitics."""
        signal = NormalizedSignal(
            domain="geopolitica_commodities",
            name="brent",
            value=5.0,
            unit="brent",
            period="2024-W01",
            region="international",
        )
        results = self.engine.score_signals([signal])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, 0)
        self.assertEqual(results[0].rationale, "Sin senal nueva o ruido normal")

    def test_score_four_international_geopolitica(self) -> None:
        """Test score 4 for international geopolitics."""
        signal = NormalizedSignal(
            domain="geopolitica_commodities",
            name="brent",
            value=25.0,
            unit="brent",
            period="2024-W01",
            region="international",
        )
        results = self.engine.score_signals([signal])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, 4)
        self.assertEqual(results[0].rationale, "Ruptura potencial de escenario base")
        self.assertGreater(len(results[0].breakout_triggers), 0)

    def test_score_multiple_signals(self) -> None:
        """Test scoring multiple signals."""
        signals = [
            NormalizedSignal(
                domain="tesoro_y_deuda",
                name="rollover_semanal",
                value=115.0,
                unit="rollover",
                period="2024-W01",
                region="argentina",
            ),
            NormalizedSignal(
                domain="fed_bancos_centrales",
                name="ust_2y",
                value=60.0,
                unit="ust_2y",
                period="2024-W01",
                region="international",
            ),
        ]
        results = self.engine.score_signals(signals)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].score, 0)
        self.assertEqual(results[1].score, 4)

    def test_score_unknown_domain(self) -> None:
        """Test scoring unknown domain."""
        signal = NormalizedSignal(
            domain="unknown_domain",
            name="test",
            value=100.0,
            unit="test",
            period="2024-W01",
            region="argentina",
        )
        results = self.engine.score_signals([signal])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, 0)

    def test_separate_argentina_international_thresholds(self) -> None:
        """Test that Argentina and international thresholds are separate."""
        arg_signal = NormalizedSignal(
            domain="tesoro_y_deuda",
            name="rollover",
            value=65.0,
            unit="rollover",
            period="2024-W01",
            region="argentina",
        )
        intl_signal = NormalizedSignal(
            domain="fed_bancos_centrales",
            name="ust_2y",
            value=60.0,
            unit="ust_2y",
            period="2024-W01",
            region="international",
        )
        arg_results = self.engine.score_signals([arg_signal])
        intl_results = self.engine.score_signals([intl_signal])
        self.assertEqual(arg_results[0].score, 4)
        self.assertEqual(intl_results[0].score, 4)

    def test_inputs_used(self) -> None:
        """Test that inputs_used is populated."""
        signal = NormalizedSignal(
            domain="tesoro_y_deuda",
            name="rollover_semanal",
            value=65.0,
            unit="rollover",
            period="2024-W01",
            region="argentina",
        )
        results = self.engine.score_signals([signal])
        self.assertIn("rollover", results[0].inputs_used)
        self.assertIn("breakout_triggers", results[0].inputs_used)


if __name__ == "__main__":
    unittest.main()