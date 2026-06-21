from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NormalizedSignal:
    """Input signal for scoring."""

    domain: str
    name: str
    value: float
    unit: str
    period: str
    region: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "period": self.period,
            "region": self.region,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NormalizedSignal":
        """Create from dictionary."""
        return cls(
            domain=data["domain"],
            name=data["name"],
            value=data["value"],
            unit=data["unit"],
            period=data["period"],
            region=data["region"],
            notes=data.get("notes", ""),
        )


@dataclass(frozen=True)
class ScoredSignal:
    """Output of scoring engine."""

    signal: NormalizedSignal
    score: int
    rationale: str
    inputs_used: list[str]
    breakout_triggers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "signal": self.signal.to_dict(),
            "score": self.score,
            "rationale": self.rationale,
            "inputs_used": self.inputs_used,
            "breakout_triggers": self.breakout_triggers,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScoredSignal":
        """Create from dictionary."""
        return cls(
            signal=NormalizedSignal.from_dict(data["signal"]),
            score=data["score"],
            rationale=data["rationale"],
            inputs_used=data["inputs_used"],
            breakout_triggers=data.get("breakout_triggers", []),
        )


class ScoringEngine:
    """Engine for scoring weekly signals."""

    ARG_THRESHOLDS = {
        "tesoro_y_deuda": {
            0: {"rollover": lambda v: v >= 110.0},
            2: {"rollover": lambda v: v >= 90.0 and v < 110.0},
            3: {"rollover": lambda v: v < 90.0 and v >= 70.0},
            4: {"rollover": lambda v: v < 70.0},
        },
        "bcra_reservas": {
            0: {"reservas_netas": lambda v: v >= 0.0},
            2: {"reservas_netas": lambda v: v >= -1.0 and v < 0.0},
            3: {"reservas_netas": lambda v: v < -1.0 and v >= -3.0},
            4: {"reservas_netas": lambda v: v < -3.0},
        },
        "cambiario": {
            0: {"mecccl": lambda v: v <= 5.0},
            2: {"mecccl": lambda v: v > 5.0 and v <= 10.0},
            3: {"mecccl": lambda v: v > 10.0 and v <= 20.0},
            4: {"mecccl": lambda v: v > 20.0},
        },
        "inflacion": {
            0: {"ipc_vs_consenso": lambda v: abs(v) <= 0.5},
            2: {"ipc_vs_consenso": lambda v: abs(v) > 0.5 and abs(v) <= 1.0},
            3: {"ipc_vs_consenso": lambda v: abs(v) > 1.0 and abs(v) <= 2.0},
            4: {"ipc_vs_consenso": lambda v: abs(v) > 2.0},
        },
        "actividad_empleo": {
            0: {"emae_vs_consenso": lambda v: abs(v) <= 1.0},
            2: {"emae_vs_consenso": lambda v: abs(v) > 1.0 and abs(v) <= 2.0},
            3: {"emae_vs_consenso": lambda v: abs(v) > 2.0 and abs(v) <= 3.0},
            4: {"emae_vs_consenso": lambda v: abs(v) > 3.0},
        },
    }

    INTL_THRESHOLDS = {
        "fed_bancos_centrales": {
            0: {"ust_2y": lambda v: abs(v) <= 15.0},
            2: {"ust_2y": lambda v: abs(v) > 15.0 and abs(v) <= 30.0},
            3: {"ust_2y": lambda v: abs(v) > 30.0 and abs(v) <= 50.0},
            4: {"ust_2y": lambda v: abs(v) > 50.0},
        },
        "liquidez_global_curva": {
            0: {"ust_10y": lambda v: abs(v) <= 20.0},
            2: {"ust_10y": lambda v: abs(v) > 20.0 and abs(v) <= 40.0},
            3: {"ust_10y": lambda v: abs(v) > 40.0 and abs(v) <= 60.0},
            4: {"ust_10y": lambda v: abs(v) > 60.0},
        },
        "geopolitica_commodities": {
            0: {"brent": lambda v: abs(v) <= 7.0},
            2: {"brent": lambda v: abs(v) > 7.0 and abs(v) <= 14.0},
            3: {"brent": lambda v: abs(v) > 14.0 and abs(v) <= 21.0},
            4: {"brent": lambda v: abs(v) > 21.0},
        },
    }

    ARG_BREAKOUT_TRIGGERS = {
        "tesoro_y_deuda": [
            "Tesoro no logra rollover suficiente y debe convalidar tasa muy superior a curva",
            "Canje defensivo o asistencia indirecta",
        ],
        "bcra_reservas": [
            "BCRA pierde reservas liquidas de forma persistente mientras suben brecha y futuros",
            "Cambio de regla cambiaria o monetaria",
        ],
        "cambiario": [
            "Mercado pricea salto discreto pese a intervencion",
            "Ruptura de banda o cepo/regla nueva",
        ],
        "inflacion": [
            "IPC nucleo reacelera por mas de un dato y obliga a endurecer tasa/crawling",
        ],
        "actividad_empleo": [
            "Actividad o empleo se deterioran lo suficiente para afectar recaudacion o gobernabilidad",
        ],
    }

    INTL_BREAKOUT_TRIGGERS = {
        "fed_bancos_centrales": [
            "Fed pasa de discusion de timing a cambio de funcion de reaccion",
        ],
        "liquidez_global_curva": [
            "Suba de UST reales, DXY y VIX al mismo tiempo cierra apetito por emergentes",
            "Stress de liquidez por Treasury/QT/repo fuerza ventas de riesgo",
        ],
        "geopolitica_commodities": [
            "Escalada que cambia inflacion global, comercio o riesgo soberano",
        ],
    }

    def __init__(self) -> None:
        """Initialize scoring engine."""
        pass

    def _get_thresholds(self, region: str, domain: str) -> dict[int, dict[str, Any]]:
        """Get threshold table for region and domain."""
        if region == "argentina":
            return self.ARG_THRESHOLDS.get(domain, {})
        else:
            return self.INTL_THRESHOLDS.get(domain, {})

    def _get_breakout_triggers(self, region: str, domain: str) -> list[str]:
        """Get breakout triggers for region and domain."""
        if region == "argentina":
            return self.ARG_BREAKOUT_TRIGGERS.get(domain, [])
        else:
            return self.INTL_BREAKOUT_TRIGGERS.get(domain, [])

    def _calculate_score(self, signal: NormalizedSignal) -> tuple[int, list[str]]:
        """Calculate score for a single signal."""
        thresholds = self._get_thresholds(signal.region, signal.domain)
        if not thresholds:
            return 0, []

        inputs_used: list[str] = []
        score = 0

        for score_level in sorted(thresholds.keys(), reverse=True):
            conditions = thresholds[score_level]
            matched_all = True
            for key, check in conditions.items():
                if key == signal.unit or key == signal.name:
                    inputs_used.append(key)
                    if not check(signal.value):
                        matched_all = False
                        break
                else:
                    matched_all = False
                    break

            if matched_all:
                score = score_level
                break

        if score >= 4:
            breakout_triggers = self._get_breakout_triggers(signal.region, signal.domain)
        else:
            breakout_triggers = []

        return score, breakout_triggers

    def score_signals(self, signals: list[NormalizedSignal]) -> list[ScoredSignal]:
        """Score a list of normalized signals."""
        results: list[ScoredSignal] = []

        for signal in signals:
            score, breakout_triggers = self._calculate_score(signal)

            if score == 0:
                rationale = "Sin senal nueva o ruido normal"
            elif score == 1:
                rationale = "Senal leve, esperada o ya priceada"
            elif score == 2:
                rationale = "Senal relevante pero contenida"
            elif score == 3:
                rationale = "Stress alto o cambio de tendencia"
            else:
                rationale = "Ruptura potencial de escenario base"

            inputs_used = [signal.unit]
            if breakout_triggers:
                inputs_used.append("breakout_triggers")

            scored = ScoredSignal(
                signal=signal,
                score=score,
                rationale=rationale,
                inputs_used=inputs_used,
                breakout_triggers=breakout_triggers,
            )
            results.append(scored)

        return results