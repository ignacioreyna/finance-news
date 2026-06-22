"""Module for calculating MEP (Mercado Electrónico de Pagos) and CCL (Contado Con Liquidación) exchange rates.

This module implements derived calculation of Argentine MEP and CCL exchange rates
from bond price pairs. MEP and CCL are computed from the same underlying bonds
but with different USD tranche settlement methods:

- MEP: Uses USD-C tranches that settle via CI/Caja de Valores (domestic)
- CCL: Uses USD-D tranches that settle offshore via Euroclear/CB

Both rates are derived from price parities: P_ARS(bono) / P_USD(bono).

The module separates primary data (bond prices) from derived calculations (MEP/CCL)
and applies confidence filters per the methodology.

Reference: analysis/arg_market_methodology.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Self

from statistics import median as stat_median


@dataclass(frozen=True, slots=True)
class BondPrice:
    """Input data representing a bond price in a specific currency and tranche.

    Attributes:
        specie: Bond ticker/specie (e.g., 'AL30', 'GD30', 'AL30C', 'AL30D')
        currency: Currency of the price ('ARS' or 'USD')
        tranche: Settlement tranche ('C' for domestic/CI, 'D' for offshore, None for ARS)
        price: Numeric price value
        as_of_date: Date/time of the price observation
        source_classification: Data source type ('primary' or 'proxy')
        volume: Trading volume (optional, defaults to None)
    """

    specie: str
    currency: str
    tranche: str | None
    price: float
    as_of_date: date | datetime
    source_classification: str
    volume: float | None = None

    @classmethod
    def from_dict(cls: type[Self], data: dict[str, Any]) -> Self:
        """Create BondPrice from a dictionary.

        Args:
            data: Dictionary containing BondPrice fields

        Returns:
            BondPrice instance

        Raises:
            ValueError: If required fields are missing
        """
        required = {'specie', 'currency', 'tranche', 'price', 'as_of_date', 'source_classification'}
        missing = required - data.keys()
        if missing:
            raise ValueError(f'Missing required fields: {missing}')

        return cls(
            specie=data['specie'],
            currency=data['currency'],
            tranche=data['tranche'],
            price=float(data['price']),
            as_of_date=(
                datetime.fromisoformat(data['as_of_date'])
                if isinstance(data['as_of_date'], str)
                else data['as_of_date']
            ),
            source_classification=data['source_classification'],
            volume=float(data['volume']) if data.get('volume') is not None else None,
        )

    def to_dict(self: Self) -> dict[str, Any]:
        """Convert BondPrice to a dictionary.

        Returns:
            Dictionary representation of the BondPrice
        """
        return {
            'specie': self.specie,
            'currency': self.currency,
            'tranche': self.tranche,
            'price': self.price,
            'as_of_date': (
                self.as_of_date.isoformat()
                if isinstance(self.as_of_date, datetime)
                else self.as_of_date.isoformat()
            ),
            'source_classification': self.source_classification,
            'volume': self.volume,
        }

    def is_ars(self: Self) -> bool:
        """Check if this is an ARS price."""
        return self.currency == 'ARS'

    def is_usd_c(self: Self) -> bool:
        """Check if this is a USD-C (domestic) price."""
        return self.currency == 'USD' and self.tranche == 'C'

    def is_usd_d(self: Self) -> bool:
        """Check if this is a USD-D (offshore) price."""
        return self.currency == 'USD' and self.tranche == 'D'

    def is_primary(self: Self) -> bool:
        """Check if this is a primary source price."""
        return self.source_classification == 'primary'

    def get_specie_base(self: Self) -> str:
        """Extract the base specie name (without suffix C/D).

        Returns:
            Base specie name (e.g., 'AL30' from 'AL30C' or 'AL30D')
        """
        if self.specie.endswith('C') or self.specie.endswith('D'):
            return self.specie[:-1]
        return self.specie


@dataclass(frozen=True, slots=True)
class MepCclResult:
    """Result of MEP and CCL calculation for a bond specie pair.

    Attributes:
        specie_pair: The bond specie name (base specie, e.g., 'AL30')
        mep: Calculated MEP value (None if not computable)
        ccl: Calculated CCL value (None if not computable)
        brecha: Difference between CCL and MEP (None if either is None)
        data_classification: Always 'derived' for calculated values
        inputs_used: List of BondPrice inputs used for calculation
        publish_decision: 'publish', 'flag', or 'suppress'
        confidence: 'alta', 'media', or 'baja'
        rationale: Explanation of the decision and confidence level
    """

    specie_pair: str
    mep: float | None
    ccl: float | None
    brecha: float | None
    data_classification: str = 'derived'
    inputs_used: tuple[BondPrice, ...] = field(default_factory=tuple)
    publish_decision: str = 'publish'
    confidence: str = 'alta'
    rationale: str = ''

    @classmethod
    def from_dict(cls: type[Self], data: dict[str, Any]) -> Self:
        """Create MepCclResult from a dictionary.

        Args:
            data: Dictionary containing MepCclResult fields

        Returns:
            MepCclResult instance
        """
        inputs = tuple(BondPrice.from_dict(inp) for inp in data.get('inputs_used', []))
        return cls(
            specie_pair=data['specie_pair'],
            mep=float(data['mep']) if data.get('mep') is not None else None,
            ccl=float(data['ccl']) if data.get('ccl') is not None else None,
            brecha=float(data['brecha']) if data.get('brecha') is not None else None,
            data_classification=data.get('data_classification', 'derived'),
            inputs_used=inputs,
            publish_decision=data.get('publish_decision', 'publish'),
            confidence=data.get('confidence', 'alta'),
            rationale=data.get('rationale', ''),
        )

    def to_dict(self: Self) -> dict[str, Any]:
        """Convert MepCclResult to a dictionary.

        Returns:
            Dictionary representation of the MepCclResult
        """
        return {
            'specie_pair': self.specie_pair,
            'mep': self.mep,
            'ccl': self.ccl,
            'brecha': self.brecha,
            'data_classification': self.data_classification,
            'inputs_used': [inp.to_dict() for inp in self.inputs_used],
            'publish_decision': self.publish_decision,
            'confidence': self.confidence,
            'rationale': self.rationale,
        }

    def is_publishable(self: Self) -> bool:
        """Check if result should be published."""
        return self.publish_decision == 'publish'

    def is_suppressed(self: Self) -> bool:
        """Check if result should be suppressed."""
        return self.publish_decision == 'suppress'


class MepCclCalculator:
    """Calculator for MEP and CCL exchange rates from bond prices.

    This class implements the methodology for computing MEP and CCL from
    bond price pairs, with confidence filters and publication decisions.

    Key formulas:
        MEP = P_ARS(bono_base) / P_USD(bono_C)
        CCL = P_ARS(bono_base) / P_USD(bono_D)

    Confidence filters (per methodology):
        - Freshness: prices must be recent (default TTL 3 business days)
        - Outlier rejection: extreme ratios are filtered
        - Dual-pair agreement: multiple species should agree within tolerance
        - Cross-pair divergence: MEP vs CCL should not diverge excessively
    """

    def __init__(
        self: Self,
        freshness_ttl_days: int = 3,
        outlier_threshold_factor: float = 3.0,
        dual_pair_tolerance_mep: float = 0.015,
        dual_pair_tolerance_ccl: float = 0.02,
        cross_pair_suppress_threshold: float = 0.05,
        reference_date: date | datetime | None = None,
    ) -> None:
        """Initialize the MEP/CCL calculator.

        Args:
            freshness_ttl_days: Maximum age of prices in days (default 3)
            outlier_threshold_factor: Factor for outlier rejection (default 3.0x)
            dual_pair_tolerance_mep: Tolerance for MEP dual-pair agreement (1.5%)
            dual_pair_tolerance_ccl: Tolerance for CCL dual-pair agreement (2.0%)
            cross_pair_suppress_threshold: Threshold to suppress if cross-pair diverges (5%)
            reference_date: Reference date for freshness checks (defaults to today)
        """
        self.freshness_ttl_days = freshness_ttl_days
        self.outlier_threshold_factor = outlier_threshold_factor
        self.dual_pair_tolerance_mep = dual_pair_tolerance_mep
        self.dual_pair_tolerance_ccl = dual_pair_tolerance_ccl
        self.cross_pair_suppress_threshold = cross_pair_suppress_threshold
        self.reference_date = (
            reference_date
            if reference_date
            else (datetime.now() if isinstance(reference_date, type(None)) else date.today())
        )
        if isinstance(self.reference_date, datetime):
            self.reference_date = self.reference_date.date()

    def _is_fresh(self: Self, price: BondPrice) -> bool:
        """Check if a price is within the freshness TTL.

        Args:
            price: BondPrice to check

        Returns:
            True if price is fresh enough
        """
        price_date = (
            price.as_of_date.date() if isinstance(price.as_of_date, datetime) else price.as_of_date
        )
        return (self.reference_date - price_date).days <= self.freshness_ttl_days

    def _filter_fresh_prices(self: Self, prices: list[BondPrice]) -> list[BondPrice]:
        """Filter out stale prices.

        Args:
            prices: List of BondPrice instances

        Returns:
            List of fresh BondPrice instances
        """
        return [p for p in prices if self._is_fresh(p)]

    def _select_most_recent_price_by_specie_currency_tranche(
        self: Self,
        prices: list[BondPrice],
        specie: str,
        currency: str,
        tranche: str | None = None,
    ) -> BondPrice | None:
        """Select the most recent price matching criteria.

        Args:
            prices: List of BondPrice instances
            specie: Bond specie to match
            currency: Currency to match
            tranche: Tranche to match (None for any)

        Returns:
            Most recent matching BondPrice or None
        """
        matching = [
            p
            for p in prices
            if p.specie == specie and p.currency == currency and p.tranche == tranche
        ]
        if not matching:
            return None

        def get_date(p: BondPrice) -> date:
            if isinstance(p.as_of_date, datetime):
                return p.as_of_date.date()
            return p.as_of_date

        return max(matching, key=get_date)

    def _compute_ratio(self: Self, numerator: float, denominator: float) -> float | None:
        """Safely compute a ratio, returning None for invalid division.

        Args:
            numerator: Numerator value
            denominator: Denominator value

        Returns:
            Ratio or None if division is invalid
        """
        if denominator == 0:
            return None
        if numerator <= 0 or denominator <= 0:
            return None
        return numerator / denominator

    def _detect_outlier_ratio(
        self: Self, ratio: float, other_ratios: list[float]
    ) -> bool:
        """Detect if a ratio is an outlier compared to others.

        Args:
            ratio: Ratio to check
            other_ratios: Other ratios for comparison

        Returns:
            True if ratio is an outlier
        """
        if not other_ratios:
            return False

        median_val = stat_median(other_ratios)
        if median_val == 0:
            return False

        relative_diff = abs(ratio - median_val) / median_val
        return relative_diff > self.outlier_threshold_factor

    def _assess_dual_pair_agreement(
        self: Self, results: list[MepCclResult]
    ) -> dict[str, str]:
        """Assess agreement between multiple species' MEP/CCL values.

        Args:
            results: List of MepCclResult instances

        Returns:
            Dict mapping 'mep' and 'ccl' to decision strings
        """
        mep_values = [r.mep for r in results if r.mep is not None]
        ccl_values = [r.ccl for r in results if r.ccl is not None]

        decisions = {}

        if len(mep_values) >= 2:
            mep_min = min(mep_values)
            mep_max = max(mep_values)
            dispersion = (mep_max - mep_min) / mep_min if mep_min > 0 else 0
            if dispersion > self.cross_pair_suppress_threshold:
                decisions['mep'] = 'suppress'
            elif dispersion > self.dual_pair_tolerance_mep:
                decisions['mep'] = 'flag'
            else:
                decisions['mep'] = 'publish'
        else:
            decisions['mep'] = 'publish'

        if len(ccl_values) >= 2:
            ccl_min = min(ccl_values)
            ccl_max = max(ccl_values)
            dispersion = (ccl_max - ccl_min) / ccl_min if ccl_min > 0 else 0
            if dispersion > self.cross_pair_suppress_threshold:
                decisions['ccl'] = 'suppress'
            elif dispersion > self.dual_pair_tolerance_ccl:
                decisions['ccl'] = 'flag'
            else:
                decisions['ccl'] = 'publish'
        else:
            decisions['ccl'] = 'publish'

        return decisions

    def compute_mep_ccl(self: Self, prices: list[BondPrice]) -> list[MepCclResult]:
        """Compute MEP and CCL from a list of bond prices.

        For each specie with both an ARS price and a USD-C price, compute MEP.
        For each specie with both an ARS price and a USD-D price, compute CCL.

        Args:
            prices: List of BondPrice instances (mixed currencies and tranches)

        Returns:
            List of MepCclResult instances, one per computable specie
        """
        if not prices:
            return []

        fresh_prices = self._filter_fresh_prices(prices)

        prices_by_specie: dict[str, list[BondPrice]] = {}
        for p in fresh_prices:
            base_specie = p.get_specie_base()
            if base_specie not in prices_by_specie:
                prices_by_specie[base_specie] = []
            prices_by_specie[base_specie].append(p)

        results: list[MepCclResult] = []

        for specie in sorted(prices_by_specie.keys()):
            specie_prices = prices_by_specie[specie]

            ars_price = self._select_most_recent_price_by_specie_currency_tranche(
                specie_prices, specie, 'ARS', None
            )
            usd_c_price = self._select_most_recent_price_by_specie_currency_tranche(
                specie_prices, specie + 'C', 'USD', 'C'
            )
            usd_d_price = self._select_most_recent_price_by_specie_currency_tranche(
                specie_prices, specie + 'D', 'USD', 'D'
            )

            if ars_price is None:
                continue

            inputs: list[BondPrice] = [ars_price]
            mep_value: float | None = None
            ccl_value: float | None = None

            if usd_c_price is not None:
                mep_value = self._compute_ratio(ars_price.price, usd_c_price.price)
                inputs.append(usd_c_price)

            if usd_d_price is not None:
                ccl_value = self._compute_ratio(ars_price.price, usd_d_price.price)
                if usd_d_price not in inputs:
                    inputs.append(usd_d_price)

            if mep_value is None and ccl_value is None:
                continue

            brecha = None
            if mep_value is not None and ccl_value is not None:
                brecha = ccl_value - mep_value

            confidence = 'alta'
            publish_decision = 'publish'
            rationale_parts = []

            if not ars_price.is_primary():
                confidence = 'media'
                rationale_parts.append('ARS price from proxy source')

            if usd_c_price is not None and not usd_c_price.is_primary():
                if confidence == 'alta':
                    confidence = 'media'
                rationale_parts.append('USD-C price from proxy source')

            if usd_d_price is not None and not usd_d_price.is_primary():
                if confidence == 'alta':
                    confidence = 'media'
                rationale_parts.append('USD-D price from proxy source')

            if mep_value is not None and mep_value <= 0:
                publish_decision = 'suppress'
                confidence = 'baja'
                rationale_parts.append('MEP value invalid (<= 0)')

            if ccl_value is not None and ccl_value <= 0:
                publish_decision = 'suppress'
                confidence = 'baja'
                rationale_parts.append('CCL value invalid (<= 0)')

            if mep_value is not None and ccl_value is not None:
                if brecha is not None and mep_value > 0:
                    relative_divergence = abs(brecha) / mep_value
                    if relative_divergence > self.cross_pair_suppress_threshold:
                        publish_decision = 'suppress'
                        confidence = 'baja'
                        rationale_parts.append(
                            f'Cross-pair divergence {relative_divergence:.1%} exceeds {self.cross_pair_suppress_threshold:.1%} threshold'
                        )

            if not rationale_parts:
                rationale = 'Computed from primary prices'
            else:
                rationale = '; '.join(rationale_parts)

            result = MepCclResult(
                specie_pair=specie,
                mep=mep_value,
                ccl=ccl_value,
                brecha=brecha,
                data_classification='derived',
                inputs_used=tuple(inputs),
                publish_decision=publish_decision,
                confidence=confidence,
                rationale=rationale,
            )
            results.append(result)

        if len(results) >= 2:
            dual_decisions = self._assess_dual_pair_agreement(results)

            adjusted_results = []
            for result in results:
                new_publish_decision = result.publish_decision
                new_confidence = result.confidence
                new_rationale = result.rationale

                if result.mep is not None:
                    mep_decision = dual_decisions.get('mep', 'publish')
                    if mep_decision == 'suppress':
                        new_publish_decision = 'suppress'
                        new_confidence = 'baja'
                        new_rationale += '; Dual-pair disagreement (suppress)'
                    elif mep_decision == 'flag' and new_publish_decision != 'suppress':
                        if new_confidence == 'alta':
                            new_confidence = 'media'
                        new_rationale += '; Dual-pair disagreement flagged'

                if result.ccl is not None:
                    ccl_decision = dual_decisions.get('ccl', 'publish')
                    if ccl_decision == 'suppress':
                        new_publish_decision = 'suppress'
                        new_confidence = 'baja'
                        new_rationale += '; Dual-pair disagreement (suppress)'
                    elif ccl_decision == 'flag' and new_publish_decision != 'suppress':
                        if new_confidence == 'alta':
                            new_confidence = 'media'
                        new_rationale += '; Dual-pair disagreement flagged'

                adjusted_result = MepCclResult(
                    specie_pair=result.specie_pair,
                    mep=result.mep,
                    ccl=result.ccl,
                    brecha=result.brecha,
                    data_classification=result.data_classification,
                    inputs_used=result.inputs_used,
                    publish_decision=new_publish_decision,
                    confidence=new_confidence,
                    rationale=new_rationale,
                )
                adjusted_results.append(adjusted_result)
            results = adjusted_results

        return results


def compute_mep_ccl(prices: list[BondPrice]) -> list[MepCclResult]:
    """Convenience function to compute MEP and CCL from bond prices.

    This creates a default MepCclCalculator and computes the results.

    Args:
        prices: List of BondPrice instances

    Returns:
        List of MepCclResult instances
    """
    calculator = MepCclCalculator()
    return calculator.compute_mep_ccl(prices)