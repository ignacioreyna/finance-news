from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class RateInput:
    """Input rate for peso curve construction."""

    source: str  # "tesoro_corte" | "bcra_cer" | "bcra_tamar" | "cafci"
    horizon_days: int | None  # Tenor in days, None for floating/indexed
    rate: float  # Rate as decimal (e.g., 0.05 for 5%)
    as_of_date: date
    classification: str  # "primary" | "proxy"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source": self.source,
            "horizon_days": self.horizon_days,
            "rate": self.rate,
            "as_of_date": self.as_of_date.isoformat(),
            "classification": self.classification,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RateInput":
        """Create from dictionary."""
        return cls(
            source=data["source"],
            horizon_days=data.get("horizon_days"),
            rate=data["rate"],
            as_of_date=date.fromisoformat(data["as_of_date"]),
            classification=data["classification"],
        )


@dataclass(frozen=True)
class CurvePoint:
    """Point on the peso curve proxy."""

    horizon_days: int
    rate: float
    contributing_sources: list[str]
    classification: str = "proxy"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "horizon_days": self.horizon_days,
            "rate": self.rate,
            "contributing_sources": self.contributing_sources,
            "classification": self.classification,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CurvePoint":
        """Create from dictionary."""
        return cls(
            horizon_days=data["horizon_days"],
            rate=data["rate"],
            contributing_sources=data["contributing_sources"],
            classification=data.get("classification", "proxy"),
        )


@dataclass(frozen=True)
class PesoCurveProxy:
    """Proxy peso curve built from multiple rate sources."""

    as_of_date: date
    points: list[CurvePoint]
    assumptions: list[str]
    data_classification: str = "proxy"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "as_of_date": self.as_of_date.isoformat(),
            "points": [p.to_dict() for p in self.points],
            "assumptions": self.assumptions,
            "data_classification": self.data_classification,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PesoCurveProxy":
        """Create from dictionary."""
        return cls(
            as_of_date=date.fromisoformat(data["as_of_date"]),
            points=[CurvePoint.from_dict(p) for p in data["points"]],
            assumptions=data["assumptions"],
            data_classification=data.get("data_classification", "proxy"),
        )


class PesoCurveBuilder:
    """Builds a proxy peso curve from multiple rate sources."""

    def __init__(self) -> None:
        """Initialize the builder."""
        self._assumptions: list[str] = []

    def build_peso_curve_proxy(self, rates: list[RateInput]) -> PesoCurveProxy:
        """
        Build a proxy peso curve from rate inputs.

        Combines Tesoro cutoff rates (licitaciones) + BCRA CER/TAMAR
        (+ CAFCI fund rates if available) to build a proxy peso curve
        by horizon.

        Args:
            rates: List of rate inputs from various sources.

        Returns:
            PesoCurveProxy with points sorted by horizon.
        """
        if not rates:
            return self._empty_curve(date.today())

        self._assumptions = []
        as_of_date = max(r.as_of_date for r in rates)
        self._assumptions.append("no liquid peso curve; this is a proxy")

        # Group rates by horizon
        horizon_map: dict[int, list[RateInput]] = {}
        floating_rates: list[RateInput] = []

        for rate in rates:
            if rate.horizon_days is None:
                floating_rates.append(rate)
            else:
                if rate.horizon_days not in horizon_map:
                    horizon_map[rate.horizon_days] = []
                horizon_map[rate.horizon_days].append(rate)

        # Build curve points
        points: list[CurvePoint] = []
        sources_used: set[str] = set()

        # Process fixed horizons
        for horizon in sorted(horizon_map.keys()):
            horizon_rates = horizon_map[horizon]
            point = self._build_curve_point(horizon, horizon_rates)
            points.append(point)
            sources_used.update(point.contributing_sources)

        # Track floating rate usage
        if floating_rates:
            floating_sources = set(r.source for r in floating_rates)
            self._assumptions.append(
                f"floating/indexed sources available: {', '.join(sorted(floating_sources))}"
            )
            sources_used.update(floating_sources)

        # Document source usage in assumptions
        if sources_used:
            self._assumptions.append(f"sources used: {', '.join(sorted(sources_used))}")

        # Document specific methodology
        self._document_methodology(horizon_map, floating_rates)

        # Sort points by horizon (deterministic)
        points = sorted(points, key=lambda p: p.horizon_days)

        return PesoCurveProxy(
            as_of_date=as_of_date,
            points=points,
            assumptions=self._assumptions,
            data_classification="proxy",
        )

    def _build_curve_point(
        self, horizon: int, rates: list[RateInput]
    ) -> CurvePoint:
        """
        Build a single curve point for a given horizon.

        Uses Tesoro cutoff as primary anchor if available,
        otherwise falls back to other sources.

        Args:
            horizon: Horizon in days.
            rates: Rates for this horizon.

        Returns:
            CurvePoint with rate and contributing sources.
        """
        if not rates:
            # This should not happen given the logic in build_peso_curve_proxy
            return CurvePoint(
                horizon_days=horizon,
                rate=0.0,
                contributing_sources=[],
                classification="proxy",
            )

        # Prioritize Tesoro cutoff
        tesoro_rates = [r for r in rates if r.source == "tesoro_corte"]
        if tesoro_rates:
            # Use Tesoro as primary anchor
            rate = sum(r.rate for r in tesoro_rates) / len(tesoro_rates)
            sources = ["tesoro_corte"]

            # Add assumption about Tesoro anchoring
            if len(tesoro_rates) > 0:
                self._assumptions.append(
                    f"Tesoro cutoff used as primary anchor for {horizon}-day horizon"
                )

            return CurvePoint(
                horizon_days=horizon,
                rate=rate,
                contributing_sources=sources,
                classification="proxy",
            )

        # Fallback: use BCRA CER for short term, TAMAR for floating
        bcra_rates = [r for r in rates if r.source.startswith("bcra_")]
        if bcra_rates:
            rate = sum(r.rate for r in bcra_rates) / len(bcra_rates)
            sources = sorted(set(r.source for r in bcra_rates))
            self._assumptions.append(
                f"BCRA sources used for {horizon}-day horizon (no Tesoro cutoff available)"
            )
            return CurvePoint(
                horizon_days=horizon,
                rate=rate,
                contributing_sources=sources,
                classification="proxy",
            )

        # Fallback: use CAFCI fund rates
        cafci_rates = [r for r in rates if r.source == "cafci"]
        if cafci_rates:
            rate = sum(r.rate for r in cafci_rates) / len(cafci_rates)
            self._assumptions.append(
                f"CAFCI fund rate used for {horizon}-day horizon (no Tesoro/BCRA available)"
            )
            return CurvePoint(
                horizon_days=horizon,
                rate=rate,
                contributing_sources=["cafci"],
                classification="proxy",
            )

        # Last resort: average all available rates
        rate = sum(r.rate for r in rates) / len(rates)
        sources = sorted(set(r.source for r in rates))
        self._assumptions.append(
            f"mixed sources averaged for {horizon}-day horizon: {', '.join(sources)}"
        )
        return CurvePoint(
            horizon_days=horizon,
            rate=rate,
            contributing_sources=sources,
            classification="proxy",
        )

    def _document_methodology(
        self,
        horizon_map: dict[int, list[RateInput]],
        floating_rates: list[RateInput],
    ) -> None:
        """Document methodology in assumptions."""
        # Document short-term CER usage
        cer_horizons = [
            h
            for h, rates in horizon_map.items()
            if any(r.source == "bcra_cer" for r in rates) and h < 30
        ]
        if cer_horizons:
            self._assumptions.append(
                f"CER used for short-term horizons: {sorted(set(cer_horizons))}"
            )

        # Document TAMAR floating usage
        if any(r.source == "bcra_tamar" for r in floating_rates):
            self._assumptions.append("TAMAR used for floating-rate benchmark")

        # Document CAFCI fund usage
        cafci_used = any(
            r.source == "cafci" for rates in horizon_map.values() for r in rates
        ) or any(r.source == "cafci" for r in floating_rates)
        if cafci_used:
            self._assumptions.append("CAFCI fund rates used as fund benchmark")

    def _empty_curve(self, as_of_date: date) -> PesoCurveProxy:
        """Create an empty curve with minimal assumptions."""
        return PesoCurveProxy(
            as_of_date=as_of_date,
            points=[],
            assumptions=["no rate inputs provided; empty proxy curve"],
            data_classification="proxy",
        )


def build_peso_curve_proxy(rates: list[RateInput]) -> PesoCurveProxy:
    """
    Build a proxy peso curve from rate inputs.

    Convenience function that uses PesoCurveBuilder internally.

    Args:
        rates: List of rate inputs from various sources.

    Returns:
        PesoCurveProxy with points sorted by horizon.
    """
    builder = PesoCurveBuilder()
    return builder.build_peso_curve_proxy(rates)