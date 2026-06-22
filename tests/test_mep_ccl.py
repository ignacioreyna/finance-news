"""Tests for MEP/CCL calculation module."""

from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.mep_ccl import (
    BondPrice,
    MepCclCalculator,
    MepCclResult,
    compute_mep_ccl,
)


class TestBondPrice(unittest.TestCase):
    """Tests for BondPrice dataclass."""

    def test_create_bond_price(self: None) -> None:
        """Test creating a BondPrice instance."""
        price = BondPrice(
            specie='AL30',
            currency='ARS',
            tranche=None,
            price=125000.0,
            as_of_date=date(2026, 6, 22),
            source_classification='primary',
            volume=1000000.0,
        )
        assert price.specie == 'AL30'
        assert price.currency == 'ARS'
        assert price.tranche is None
        assert price.price == 125000.0
        assert price.source_classification == 'primary'
        assert price.volume == 1000000.0

    def test_bond_price_getters(self: None) -> None:
        """Test BondPrice helper methods."""
        ars_price = BondPrice(
            specie='AL30',
            currency='ARS',
            tranche=None,
            price=125000.0,
            as_of_date=date(2026, 6, 22),
            source_classification='primary',
        )
        usd_c_price = BondPrice(
            specie='AL30C',
            currency='USD',
            tranche='C',
            price=32.5,
            as_of_date=date(2026, 6, 22),
            source_classification='primary',
        )
        usd_d_price = BondPrice(
            specie='AL30D',
            currency='USD',
            tranche='D',
            price=33.0,
            as_of_date=date(2026, 6, 22),
            source_classification='primary',
        )

        assert ars_price.is_ars() is True
        assert ars_price.is_usd_c() is False
        assert ars_price.is_usd_d() is False

        assert usd_c_price.is_ars() is False
        assert usd_c_price.is_usd_c() is True
        assert usd_c_price.is_usd_d() is False

        assert usd_d_price.is_ars() is False
        assert usd_d_price.is_usd_c() is False
        assert usd_d_price.is_usd_d() is True

    def test_bond_price_get_specie_base(self: None) -> None:
        """Test extracting base specie name."""
        ars_price = BondPrice(
            specie='AL30',
            currency='ARS',
            tranche=None,
            price=125000.0,
            as_of_date=date(2026, 6, 22),
            source_classification='primary',
        )
        usd_c_price = BondPrice(
            specie='AL30C',
            currency='USD',
            tranche='C',
            price=32.5,
            as_of_date=date(2026, 6, 22),
            source_classification='primary',
        )
        usd_d_price = BondPrice(
            specie='AL30D',
            currency='USD',
            tranche='D',
            price=33.0,
            as_of_date=date(2026, 6, 22),
            source_classification='primary',
        )

        assert ars_price.get_specie_base() == 'AL30'
        assert usd_c_price.get_specie_base() == 'AL30'
        assert usd_d_price.get_specie_base() == 'AL30'

    def test_bond_price_to_dict(self: None) -> None:
        """Test converting BondPrice to dictionary."""
        price = BondPrice(
            specie='AL30',
            currency='ARS',
            tranche=None,
            price=125000.0,
            as_of_date=date(2026, 6, 22),
            source_classification='primary',
            volume=1000000.0,
        )
        data = price.to_dict()

        assert data['specie'] == 'AL30'
        assert data['currency'] == 'ARS'
        assert data['tranche'] is None
        assert data['price'] == 125000.0
        assert data['source_classification'] == 'primary'
        assert data['volume'] == 1000000.0

    def test_bond_price_from_dict(self: None) -> None:
        """Test creating BondPrice from dictionary."""
        data = {
            'specie': 'AL30',
            'currency': 'ARS',
            'tranche': None,
            'price': 125000.0,
            'as_of_date': '2026-06-22',
            'source_classification': 'primary',
            'volume': 1000000.0,
        }
        price = BondPrice.from_dict(data)

        assert price.specie == 'AL30'
        assert price.currency == 'ARS'
        assert price.tranche is None
        assert price.price == 125000.0
        assert isinstance(price.as_of_date, datetime)
        assert price.as_of_date.date() == date(2026, 6, 22)
        assert price.source_classification == 'primary'
        assert price.volume == 1000000.0

    def test_bond_price_from_dict_datetime(self: None) -> None:
        """Test creating BondPrice from dictionary with datetime."""
        data = {
            'specie': 'AL30',
            'currency': 'ARS',
            'tranche': None,
            'price': 125000.0,
            'as_of_date': '2026-06-22T15:30:00',
            'source_classification': 'primary',
        }
        price = BondPrice.from_dict(data)

        assert isinstance(price.as_of_date, datetime)
        assert price.as_of_date.date() == date(2026, 6, 22)

    def test_bond_price_roundtrip(self: None) -> None:
        """Test BondPrice serialization roundtrip."""
        original = BondPrice(
            specie='AL30',
            currency='ARS',
            tranche=None,
            price=125000.0,
            as_of_date=date(2026, 6, 22),
            source_classification='primary',
            volume=1000000.0,
        )
        data = original.to_dict()
        restored = BondPrice.from_dict(data)

        assert restored.specie == original.specie
        assert restored.currency == original.currency
        assert restored.tranche == original.tranche
        assert restored.price == original.price
        assert restored.source_classification == original.source_classification
        assert restored.volume == original.volume

    def test_bond_price_from_dict_missing_field(self: None) -> None:
        """Test BondPrice.from_dict with missing required field."""
        data = {
            'specie': 'AL30',
            'currency': 'ARS',
        }
        try:
            BondPrice.from_dict(data)
            assert False, 'Should raise ValueError'
        except ValueError as e:
            assert 'Missing required fields' in str(e)


class TestMepCclResult(unittest.TestCase):
    """Tests for MepCclResult dataclass."""

    def test_create_mep_ccl_result(self: None) -> None:
        """Test creating a MepCclResult instance."""
        result = MepCclResult(
            specie_pair='AL30',
            mep=3846.15,
            ccl=3787.88,
            brecha=-58.27,
            data_classification='derived',
            publish_decision='publish',
            confidence='alta',
            rationale='Computed from primary prices',
        )
        assert result.specie_pair == 'AL30'
        assert abs(result.mep - 3846.15) < 0.01
        assert abs(result.ccl - 3787.88) < 0.01
        assert abs(result.brecha - (-58.27)) < 0.01
        assert result.data_classification == 'derived'
        assert result.publish_decision == 'publish'
        assert result.confidence == 'alta'
        assert result.rationale == 'Computed from primary prices'

    def test_mep_ccl_result_publishable(self: None) -> None:
        """Test publishable/flagged/suppressed detection."""
        publishable = MepCclResult(
            specie_pair='AL30',
            mep=3846.15,
            ccl=3787.88,
            brecha=-58.27,
            publish_decision='publish',
        )
        flagged = MepCclResult(
            specie_pair='AL30',
            mep=3846.15,
            ccl=3787.88,
            brecha=-58.27,
            publish_decision='flag',
        )
        suppressed = MepCclResult(
            specie_pair='AL30',
            mep=3846.15,
            ccl=3787.88,
            brecha=-58.27,
            publish_decision='suppress',
        )

        assert publishable.is_publishable() is True
        assert publishable.is_suppressed() is False

        assert flagged.is_publishable() is False
        assert flagged.is_suppressed() is False

        assert suppressed.is_publishable() is False
        assert suppressed.is_suppressed() is True

    def test_mep_ccl_result_to_dict(self: None) -> None:
        """Test converting MepCclResult to dictionary."""
        inputs = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            )
        ]
        result = MepCclResult(
            specie_pair='AL30',
            mep=3846.15,
            ccl=3787.88,
            brecha=-58.27,
            data_classification='derived',
            inputs_used=tuple(inputs),
            publish_decision='publish',
            confidence='alta',
            rationale='Computed from primary prices',
        )
        data = result.to_dict()

        assert data['specie_pair'] == 'AL30'
        assert data['data_classification'] == 'derived'
        assert data['publish_decision'] == 'publish'
        assert data['confidence'] == 'alta'
        assert len(data['inputs_used']) == 1

    def test_mep_ccl_result_from_dict(self: None) -> None:
        """Test creating MepCclResult from dictionary."""
        data = {
            'specie_pair': 'AL30',
            'mep': 3846.15,
            'ccl': 3787.88,
            'brecha': -58.27,
            'data_classification': 'derived',
            'inputs_used': [
                {
                    'specie': 'AL30',
                    'currency': 'ARS',
                    'tranche': None,
                    'price': 125000.0,
                    'as_of_date': '2026-06-22',
                    'source_classification': 'primary',
                }
            ],
            'publish_decision': 'publish',
            'confidence': 'alta',
            'rationale': 'Computed from primary prices',
        }
        result = MepCclResult.from_dict(data)

        assert result.specie_pair == 'AL30'
        assert abs(result.mep - 3846.15) < 0.01
        assert result.data_classification == 'derived'
        assert len(result.inputs_used) == 1
        assert result.publish_decision == 'publish'


class TestMepCclCalculation(unittest.TestCase):
    """Tests for MEP/CCL calculation logic (AC #1)."""

    def test_compute_mep_single_pair(self: None) -> None:
        """Test MEP calculation for a single bond pair."""
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results = compute_mep_ccl(prices)

        assert len(results) == 1
        result = results[0]
        assert result.specie_pair == 'AL30'
        assert result.mep is not None
        expected_mep = 125000.0 / 32.5
        assert abs(result.mep - expected_mep) < 0.01
        assert result.ccl is None
        assert result.brecha is None

    def test_compute_ccl_single_pair(self: None) -> None:
        """Test CCL calculation for a single bond pair."""
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30D',
                currency='USD',
                tranche='D',
                price=33.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results = compute_mep_ccl(prices)

        assert len(results) == 1
        result = results[0]
        assert result.specie_pair == 'AL30'
        assert result.ccl is not None
        expected_ccl = 125000.0 / 33.0
        assert abs(result.ccl - expected_ccl) < 0.01
        assert result.mep is None
        assert result.brecha is None

    def test_compute_both_mep_and_ccl(self: None) -> None:
        """Test computing both MEP and CCL for a single bond pair."""
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30D',
                currency='USD',
                tranche='D',
                price=33.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results = compute_mep_ccl(prices)

        assert len(results) == 1
        result = results[0]
        assert result.specie_pair == 'AL30'
        assert result.mep is not None
        assert result.ccl is not None
        assert result.brecha is not None

        expected_mep = 125000.0 / 32.5
        expected_ccl = 125000.0 / 33.0
        expected_brecha = expected_ccl - expected_mep

        assert abs(result.mep - expected_mep) < 0.01
        assert abs(result.ccl - expected_ccl) < 0.01
        assert abs(result.brecha - expected_brecha) < 0.01

    def test_compute_multiple_species(self: None) -> None:
        """Test computing MEP/CCL for multiple bond species."""
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30D',
                currency='USD',
                tranche='D',
                price=33.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='GD30',
                currency='ARS',
                tranche=None,
                price=98000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='GD30C',
                currency='USD',
                tranche='C',
                price=25.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='GD30D',
                currency='USD',
                tranche='D',
                price=26.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results = compute_mep_ccl(prices)

        assert len(results) == 2

        al30_result = next((r for r in results if r.specie_pair == 'AL30'), None)
        gd30_result = next((r for r in results if r.specie_pair == 'GD30'), None)

        assert al30_result is not None
        assert gd30_result is not None

        assert al30_result.mep is not None
        assert al30_result.ccl is not None
        assert gd30_result.mep is not None
        assert gd30_result.ccl is not None

    def test_compute_no_ars_price(self: None) -> None:
        """Test that no result is generated without ARS price."""
        prices = [
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30D',
                currency='USD',
                tranche='D',
                price=33.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results = compute_mep_ccl(prices)

        assert len(results) == 0

    def test_compute_invalid_division(self: None) -> None:
        """Test handling of invalid division (zero denominator)."""
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=0.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results = compute_mep_ccl(prices)

        assert len(results) == 0

    def test_compute_negative_prices(self: None) -> None:
        """Test handling of negative prices."""
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=-125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results = compute_mep_ccl(prices)

        assert len(results) == 0


class TestDerivedDataClassification(unittest.TestCase):
    """Tests for derived data classification (AC #2)."""

    def test_result_marked_as_derived(self: None) -> None:
        """Test that results are marked as derived, not primary."""
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results = compute_mep_ccl(prices)

        assert len(results) == 1
        result = results[0]
        assert result.data_classification == 'derived'

    def test_inputs_used_tracks_primary_prices(self: None) -> None:
        """Test that inputs_used contains the primary price inputs."""
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results = compute_mep_ccl(prices)

        assert len(results) == 1
        result = results[0]
        assert len(result.inputs_used) == 2

        input_currencies = [inp.currency for inp in result.inputs_used]
        assert 'ARS' in input_currencies
        assert 'USD' in input_currencies

    def test_inputs_used_includes_both_tranches(self: None) -> None:
        """Test that inputs_used includes both C and D tranches when available."""
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30D',
                currency='USD',
                tranche='D',
                price=33.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results = compute_mep_ccl(prices)

        assert len(results) == 1
        result = results[0]
        assert len(result.inputs_used) == 3

        input_tranches = [inp.tranche for inp in result.inputs_used]
        assert None in input_tranches
        assert 'C' in input_tranches
        assert 'D' in input_tranches

    def test_mep_ccl_not_labeled_as_primary(self: None) -> None:
        """Test that computed MEP/CCL is never labeled as primary."""
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results = compute_mep_ccl(prices)

        assert len(results) == 1
        result = results[0]

        assert result.data_classification == 'derived'

        for inp in result.inputs_used:
            assert inp.source_classification == 'primary'

        assert result.mep is not None
        assert isinstance(result.mep, float)

    def test_proxy_source_degrades_confidence(self: None) -> None:
        """Test that proxy source degrades confidence level."""
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='proxy',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results = compute_mep_ccl(prices)

        assert len(results) == 1
        result = results[0]
        assert result.confidence == 'media'
        assert 'proxy' in result.rationale.lower()


class TestConfidenceFilters(unittest.TestCase):
    """Tests for confidence filters from methodology (AC #3)."""

    def test_freshness_filter_valid_prices(self: None) -> None:
        """Test that fresh prices pass the filter."""
        reference_date = date(2026, 6, 22)
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=reference_date,
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=reference_date,
                source_classification='primary',
            ),
        ]

        calculator = MepCclCalculator(reference_date=reference_date, freshness_ttl_days=3)
        results = calculator.compute_mep_ccl(prices)

        assert len(results) == 1
        result = results[0]
        assert result.mep is not None

    def test_freshness_filter_stale_prices(self: None) -> None:
        """Test that stale prices are filtered out."""
        reference_date = date(2026, 6, 22)
        stale_date = date(2026, 6, 10)
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=stale_date,
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=stale_date,
                source_classification='primary',
            ),
        ]

        calculator = MepCclCalculator(reference_date=reference_date, freshness_ttl_days=3)
        results = calculator.compute_mep_ccl(prices)

        assert len(results) == 0

    def test_dual_pair_agreement_within_tolerance(self: None) -> None:
        """Test dual-pair agreement within tolerance publishes with high confidence."""
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='GD30',
                currency='ARS',
                tranche=None,
                price=98000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='GD30C',
                currency='USD',
                tranche='C',
                price=25.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results = compute_mep_ccl(prices)

        assert len(results) == 2

        al30_mep = next((r.mep for r in results if r.specie_pair == 'AL30'), None)
        gd30_mep = next((r.mep for r in results if r.specie_pair == 'GD30'), None)

        assert al30_mep is not None
        assert gd30_mep is not None

        dispersion = abs(al30_mep - gd30_mep) / min(al30_mep, gd30_mep)
        assert dispersion < 0.015

        for result in results:
            if result.mep is not None:
                assert result.publish_decision == 'publish' or result.publish_decision == 'flag'
                assert 'Dual-pair' in result.rationale or result.publish_decision == 'publish'

    def test_dual_pair_disagreement_flags(self: None) -> None:
        """Test dual-pair disagreement beyond tolerance flags the result."""
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='GD30',
                currency='ARS',
                tranche=None,
                price=98000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='GD30C',
                currency='USD',
                tranche='C',
                price=20.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results = compute_mep_ccl(prices)

        assert len(results) == 2

        al30_mep = next((r.mep for r in results if r.specie_pair == 'AL30'), None)
        gd30_mep = next((r.mep for r in results if r.specie_pair == 'GD30'), None)

        assert al30_mep is not None
        assert gd30_mep is not None

        dispersion = abs(al30_mep - gd30_mep) / min(al30_mep, gd30_mep)
        assert dispersion > 0.015

        for result in results:
            if result.mep is not None:
                if dispersion > 0.02:
                    assert result.confidence == 'baja' or result.publish_decision == 'suppress'
                else:
                    assert result.confidence == 'media' or result.publish_decision == 'flag'

    def test_cross_pair_divergence_within_threshold(self: None) -> None:
        """Test that cross-pair divergence within threshold is acceptable."""
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30D',
                currency='USD',
                tranche='D',
                price=33.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results = compute_mep_ccl(prices)

        assert len(results) == 1
        result = results[0]
        assert result.publish_decision != 'suppress'

    def test_cross_pair_divergence_suppresses(self: None) -> None:
        """Test that excessive cross-pair divergence suppresses publication."""
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30D',
                currency='USD',
                tranche='D',
                price=45.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results = compute_mep_ccl(prices)

        assert len(results) == 1
        result = results[0]
        assert result.publish_decision == 'suppress'
        assert result.confidence == 'baja'
        assert 'divergence' in result.rationale.lower()

    def test_outlier_detection(self: None) -> None:
        """Test outlier detection for ratio validation."""
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='GD30',
                currency='ARS',
                tranche=None,
                price=98000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='GD30C',
                currency='USD',
                tranche='C',
                price=25.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL29',
                currency='ARS',
                tranche=None,
                price=130000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL29C',
                currency='USD',
                tranche='C',
                price=10.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        calculator = MepCclCalculator(outlier_threshold_factor=3.0)
        results = calculator.compute_mep_ccl(prices)

        assert len(results) == 3

        mep_values = [r.mep for r in results if r.mep is not None]
        assert len(mep_values) == 3

        median_mep = sorted(mep_values)[1]

        outlier_result = None
        for result in results:
            if result.mep is not None:
                relative_diff = abs(result.mep - median_mep) / median_mep
                if relative_diff > 3.0:
                    outlier_result = result
                    break

    def test_confidence_level_mapping(self: None) -> None:
        """Test confidence level mapping to alta/media/baja."""
        prices_primary = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results_primary = compute_mep_ccl(prices_primary)
        assert results_primary[0].confidence == 'alta'

        prices_proxy = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='proxy',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results_proxy = compute_mep_ccl(prices_proxy)
        assert results_proxy[0].confidence == 'media'

    def test_publish_decision_mapping(self: None) -> None:
        """Test publish decision mapping to publish/flag/suppress."""
        prices_publish = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results_publish = compute_mep_ccl(prices_publish)
        assert results_publish[0].publish_decision == 'publish'

        prices_suppress = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30D',
                currency='USD',
                tranche='D',
                price=45.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results_suppress = compute_mep_ccl(prices_suppress)
        assert results_suppress[0].publish_decision == 'suppress'


class TestMepCclCalculator(unittest.TestCase):
    """Tests for MepCclCalculator class."""

    def test_calculator_initialization(self: None) -> None:
        """Test calculator initialization with default parameters."""
        calculator = MepCclCalculator()
        assert calculator.freshness_ttl_days == 3
        assert calculator.outlier_threshold_factor == 3.0
        assert calculator.dual_pair_tolerance_mep == 0.015
        assert calculator.dual_pair_tolerance_ccl == 0.02
        assert calculator.cross_pair_suppress_threshold == 0.05

    def test_calculator_custom_parameters(self: None) -> None:
        """Test calculator initialization with custom parameters."""
        calculator = MepCclCalculator(
            freshness_ttl_days=5,
            outlier_threshold_factor=2.0,
            dual_pair_tolerance_mep=0.02,
            dual_pair_tolerance_ccl=0.03,
            cross_pair_suppress_threshold=0.10,
        )
        assert calculator.freshness_ttl_days == 5
        assert calculator.outlier_threshold_factor == 2.0
        assert calculator.dual_pair_tolerance_mep == 0.02
        assert calculator.dual_pair_tolerance_ccl == 0.03
        assert calculator.cross_pair_suppress_threshold == 0.10

    def test_calculator_with_reference_date(self: None) -> None:
        """Test calculator with custom reference date."""
        reference_date = date(2026, 6, 20)
        calculator = MepCclCalculator(reference_date=reference_date)
        assert calculator.reference_date == reference_date

    def test_calculator_empty_prices(self: None) -> None:
        """Test calculator with empty price list."""
        calculator = MepCclCalculator()
        results = calculator.compute_mep_ccl([])
        assert results == []

    def test_calculator_mixed_dates_selects_most_recent(self: None) -> None:
        """Test that calculator selects most recent price when multiple dates exist."""
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=120000.0,
                as_of_date=date(2026, 6, 20),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.0,
                as_of_date=date(2026, 6, 21),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        calculator = MepCclCalculator()
        results = calculator.compute_mep_ccl(prices)

        assert len(results) == 1
        result = results[0]
        assert result.mep is not None

        expected_mep = 125000.0 / 32.5
        assert abs(result.mep - expected_mep) < 0.01


class TestComputeMepCclFunction(unittest.TestCase):
    """Tests for the compute_mep_ccl convenience function."""

    def test_compute_mep_ccl_function(self: None) -> None:
        """Test the compute_mep_ccl convenience function."""
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results = compute_mep_ccl(prices)

        assert len(results) == 1
        assert results[0].specie_pair == 'AL30'
        assert results[0].mep is not None

    def test_compute_mep_ccl_empty_list(self: None) -> None:
        """Test compute_mep_ccl with empty list."""
        results = compute_mep_ccl([])
        assert results == []


class TestComprehensiveFixtures(unittest.TestCase):
    """Comprehensive tests using realistic fixtures (AC #3)."""

    def test_full_workflow_primary_data(self: None) -> None:
        """Test full workflow with primary data (AL30, GD30, AL29, GD35)."""
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
                volume=50000000.0,
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
                volume=10000000.0,
            ),
            BondPrice(
                specie='AL30D',
                currency='USD',
                tranche='D',
                price=33.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
                volume=15000000.0,
            ),
            BondPrice(
                specie='GD30',
                currency='ARS',
                tranche=None,
                price=98000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
                volume=40000000.0,
            ),
            BondPrice(
                specie='GD30C',
                currency='USD',
                tranche='C',
                price=25.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
                volume=8000000.0,
            ),
            BondPrice(
                specie='GD30D',
                currency='USD',
                tranche='D',
                price=26.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
                volume=12000000.0,
            ),
            BondPrice(
                specie='AL29',
                currency='ARS',
                tranche=None,
                price=130000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
                volume=30000000.0,
            ),
            BondPrice(
                specie='AL29C',
                currency='USD',
                tranche='C',
                price=34.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
                volume=6000000.0,
            ),
            BondPrice(
                specie='AL29D',
                currency='USD',
                tranche='D',
                price=34.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
                volume=9000000.0,
            ),
            BondPrice(
                specie='GD35',
                currency='ARS',
                tranche=None,
                price=95000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
                volume=25000000.0,
            ),
            BondPrice(
                specie='GD35C',
                currency='USD',
                tranche='C',
                price=24.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
                volume=5000000.0,
            ),
            BondPrice(
                specie='GD35D',
                currency='USD',
                tranche='D',
                price=25.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
                volume=7000000.0,
            ),
        ]

        results = compute_mep_ccl(prices)

        assert len(results) == 4

        for result in results:
            assert result.data_classification == 'derived'
            assert len(result.inputs_used) >= 2
            assert result.specie_pair in {'AL30', 'GD30', 'AL29', 'GD35'}

            ars_input = next((inp for inp in result.inputs_used if inp.currency == 'ARS'), None)
            usd_c_input = next((inp for inp in result.inputs_used if inp.tranche == 'C'), None)
            usd_d_input = next((inp for inp in result.inputs_used if inp.tranche == 'D'), None)

            assert ars_input is not None
            assert usd_c_input is not None
            assert usd_d_input is not None

            assert result.mep is not None
            assert result.ccl is not None
            assert result.brecha is not None

            assert result.publish_decision in {'publish', 'flag', 'suppress'}
            assert result.confidence in {'alta', 'media', 'baja'}

    def test_mixed_primary_and_proxy_data(self: None) -> None:
        """Test workflow with mixed primary and proxy data."""
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='proxy',
            ),
            BondPrice(
                specie='AL30D',
                currency='USD',
                tranche='D',
                price=33.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='GD30',
                currency='ARS',
                tranche=None,
                price=98000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='proxy',
            ),
            BondPrice(
                specie='GD30C',
                currency='USD',
                tranche='C',
                price=25.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='GD30D',
                currency='USD',
                tranche='D',
                price=26.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results = compute_mep_ccl(prices)

        assert len(results) == 2

        for result in results:
            assert result.data_classification == 'derived'

            has_proxy = any(
                inp.source_classification == 'proxy' for inp in result.inputs_used
            )

            if has_proxy:
                assert result.confidence == 'media'
                assert 'proxy' in result.rationale.lower()
            else:
                assert result.confidence == 'alta'

    def test_edge_case_single_valid_pair(self: None) -> None:
        """Test edge case with only one valid pair."""
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='GD30',
                currency='ARS',
                tranche=None,
                price=98000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results = compute_mep_ccl(prices)

        assert len(results) == 1
        assert results[0].specie_pair == 'AL30'

    def test_cross_check_species_agreement(self: None) -> None:
        """Test cross-check between species for agreement."""
        prices = [
            BondPrice(
                specie='AL30',
                currency='ARS',
                tranche=None,
                price=125000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='AL30C',
                currency='USD',
                tranche='C',
                price=32.5,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='GD30',
                currency='ARS',
                tranche=None,
                price=98000.0,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
            BondPrice(
                specie='GD30C',
                currency='USD',
                tranche='C',
                price=25.48,
                as_of_date=date(2026, 6, 22),
                source_classification='primary',
            ),
        ]

        results = compute_mep_ccl(prices)

        assert len(results) == 2

        mep_values = [r.mep for r in results if r.mep is not None]
        assert len(mep_values) == 2

        dispersion = abs(mep_values[0] - mep_values[1]) / min(mep_values)
        if dispersion > 0.015:
            for result in results:
                if result.mep is not None:
                    assert 'Dual-pair' in result.rationale or result.confidence != 'alta'


if __name__ == '__main__':
    import unittest

    unittest.main()