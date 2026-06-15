from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.config import FreshnessSpec, SeriesConfig, SourceConfig
from finance_news.config.loader import (
    ConfigValidationError,
    load_config,
    parse_series_configs,
    parse_source_configs,
)


class ConfigSchemaTests(unittest.TestCase):
    """Test AC #1: Schema includes source_id, connector, frequency, freshness TTL, priority."""

    def test_source_config_all_required_fields(self) -> None:
        """Test SourceConfig with all required fields present and valid."""
        freshness = FreshnessSpec(ttl_seconds=86400, freshness_tolerance_seconds=86400)
        config = SourceConfig(
            source_id="bcra",
            connector="finance_news.connectors.bcra:BCRAConnector",
            base_url="https://api.bcra.gob.ar",
            frequency="daily",
            freshness=freshness,
            priority="alta",
            category="primary",
            enabled=True,
        )

        self.assertEqual(config.source_id, "bcra")
        self.assertEqual(config.connector, "finance_news.connectors.bcra:BCRAConnector")
        self.assertEqual(config.base_url, "https://api.bcra.gob.ar")
        self.assertEqual(config.frequency, "daily")
        self.assertEqual(config.priority, "alta")
        self.assertEqual(config.category, "primary")
        self.assertTrue(config.enabled)
        self.assertEqual(config.freshness.ttl_seconds, 86400)
        self.assertEqual(config.freshness.freshness_tolerance_seconds, 86400)

    def test_freshness_spec_fields(self) -> None:
        """Test FreshnessSpec has ttl_seconds and freshness_tolerance_seconds."""
        spec = FreshnessSpec(ttl_seconds=3600, freshness_tolerance_seconds=7200)
        self.assertEqual(spec.ttl_seconds, 3600)
        self.assertEqual(spec.freshness_tolerance_seconds, 7200)

    def test_source_config_serialization_round_trip(self) -> None:
        """Test SourceConfig to_dict/from_dict round trip."""
        original = SourceConfig(
            source_id="bcra",
            connector="finance_news.connectors.bcra:BCRAConnector",
            base_url="https://api.bcra.gob.ar",
            frequency="daily",
            freshness=FreshnessSpec(ttl_seconds=86400, freshness_tolerance_seconds=86400),
            priority="alta",
            category="primary",
            enabled=True,
        )

        data = original.to_dict()
        restored = SourceConfig.from_dict(data)

        self.assertEqual(restored, original)

    def test_freshness_spec_serialization_round_trip(self) -> None:
        """Test FreshnessSpec to_dict/from_dict round trip."""
        original = FreshnessSpec(ttl_seconds=86400, freshness_tolerance_seconds=86400)
        data = original.to_dict()
        restored = FreshnessSpec.from_dict(data)

        self.assertEqual(restored, original)


class ConfigCategoryTests(unittest.TestCase):
    """Test AC #2: Separates primary, proxy, and manual sources."""

    def test_source_config_categories_primary(self) -> None:
        """Test SourceConfig with category='primary'."""
        config = SourceConfig(
            source_id="bcra",
            connector="finance_news.connectors.bcra:BCRAConnector",
            base_url="https://api.bcra.gob.ar",
            frequency="daily",
            freshness=FreshnessSpec(ttl_seconds=86400, freshness_tolerance_seconds=86400),
            priority="alta",
            category="primary",
        )
        self.assertEqual(config.category, "primary")

    def test_source_config_categories_proxy(self) -> None:
        """Test SourceConfig with category='proxy'."""
        config = SourceConfig(
            source_id="bloomberg",
            connector="finance_news.connectors.bloomberg:BloombergConnector",
            base_url="https://www.bloomberg.com/markets",
            frequency="daily",
            freshness=FreshnessSpec(ttl_seconds=3600, freshness_tolerance_seconds=7200),
            priority="media",
            category="proxy",
        )
        self.assertEqual(config.category, "proxy")

    def test_source_config_categories_manual(self) -> None:
        """Test SourceConfig with category='manual'."""
        config = SourceConfig(
            source_id="manual_source",
            connector="finance_news.connectors.manual:ManualConnector",
            base_url="https://example.com",
            frequency="weekly",
            freshness=FreshnessSpec(ttl_seconds=604800, freshness_tolerance_seconds=1209600),
            priority="baja",
            category="manual",
        )
        self.assertEqual(config.category, "manual")


class ConfigValidationTests(unittest.TestCase):
    """Test AC #3: Schema validation tests."""

    def test_parse_valid_config(self) -> None:
        """Test parsing a valid configuration file."""
        config_toml = """
version = "1.0"

[sources]

[sources.bcra]
connector = "finance_news.connectors.bcra:BCRAConnector"
base_url = "https://api.bcra.gob.ar"
frequency = "daily"
freshness = { ttl_seconds = 86400, freshness_tolerance_seconds = 86400 }
priority = "alta"
category = "primary"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_toml)
            f.flush()
            config_path = Path(f.name)

        try:
            sources = parse_source_configs(config_path)
            self.assertIn("bcra", sources)
            self.assertEqual(sources["bcra"].source_id, "bcra")
        finally:
            config_path.unlink()

    def test_missing_required_field_raises_error(self) -> None:
        """Test that missing required fields raise ConfigValidationError."""
        config_toml = """
version = "1.0"

[sources]

[sources.bcra]
connector = "finance_news.connectors.bcra:BCRAConnector"
base_url = "https://api.bcra.gob.ar"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_toml)
            f.flush()
            config_path = Path(f.name)

        try:
            with self.assertRaises(ConfigValidationError) as cm:
                parse_source_configs(config_path)
            self.assertIn("Missing required fields", str(cm.exception))
        finally:
            config_path.unlink()

    def test_invalid_frequency_raises_error(self) -> None:
        """Test that invalid frequency raises ConfigValidationError."""
        config_toml = """
version = "1.0"

[sources]

[sources.bcra]
connector = "finance_news.connectors.bcra:BCRAConnector"
base_url = "https://api.bcra.gob.ar"
frequency = "invalid"
freshness = { ttl_seconds = 86400, freshness_tolerance_seconds = 86400 }
priority = "alta"
category = "primary"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_toml)
            f.flush()
            config_path = Path(f.name)

        try:
            with self.assertRaises(ConfigValidationError) as cm:
                parse_source_configs(config_path)
            self.assertIn("Invalid frequency", str(cm.exception))
        finally:
            config_path.unlink()

    def test_invalid_priority_raises_error(self) -> None:
        """Test that invalid priority raises ConfigValidationError."""
        config_toml = """
version = "1.0"

[sources]

[sources.bcra]
connector = "finance_news.connectors.bcra:BCRAConnector"
base_url = "https://api.bcra.gob.ar"
frequency = "daily"
freshness = { ttl_seconds = 86400, freshness_tolerance_seconds = 86400 }
priority = "invalid"
category = "primary"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_toml)
            f.flush()
            config_path = Path(f.name)

        try:
            with self.assertRaises(ConfigValidationError) as cm:
                parse_source_configs(config_path)
            self.assertIn("Invalid priority", str(cm.exception))
        finally:
            config_path.unlink()

    def test_invalid_category_raises_error(self) -> None:
        """Test that invalid category raises ConfigValidationError."""
        config_toml = """
version = "1.0"

[sources]

[sources.bcra]
connector = "finance_news.connectors.bcra:BCRAConnector"
base_url = "https://api.bcra.gob.ar"
frequency = "daily"
freshness = { ttl_seconds = 86400, freshness_tolerance_seconds = 86400 }
priority = "alta"
category = "invalid"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_toml)
            f.flush()
            config_path = Path(f.name)

        try:
            with self.assertRaises(ConfigValidationError) as cm:
                parse_source_configs(config_path)
            self.assertIn("Invalid category", str(cm.exception))
        finally:
            config_path.unlink()

    def test_nested_freshness_validation(self) -> None:
        """Test that nested freshness fields are validated."""
        # Missing freshness_tolerance_seconds
        config_toml = """
version = "1.0"

[sources]

[sources.bcra]
connector = "finance_news.connectors.bcra:BCRAConnector"
base_url = "https://api.bcra.gob.ar"
frequency = "daily"
freshness = { ttl_seconds = 86400 }
priority = "alta"
category = "primary"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_toml)
            f.flush()
            config_path = Path(f.name)

        try:
            with self.assertRaises(ConfigValidationError) as cm:
                parse_source_configs(config_path)
            self.assertIn("freshness_tolerance_seconds", str(cm.exception))
        finally:
            config_path.unlink()

    def test_freshness_positive_integer_validation(self) -> None:
        """Test that freshness TTL must be positive integer."""
        config_toml = """
version = "1.0"

[sources]

[sources.bcra]
connector = "finance_news.connectors.bcra:BCRAConnector"
base_url = "https://api.bcra.gob.ar"
frequency = "daily"
freshness = { ttl_seconds = -100, freshness_tolerance_seconds = 86400 }
priority = "alta"
category = "primary"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_toml)
            f.flush()
            config_path = Path(f.name)

        try:
            with self.assertRaises(ConfigValidationError) as cm:
                parse_source_configs(config_path)
            self.assertIn("must be positive", str(cm.exception))
        finally:
            config_path.unlink()

    def test_disabled_source_excluded_from_active(self) -> None:
        """Test that disabled sources can be parsed and excluded when needed."""
        config_toml = """
version = "1.0"

[sources]

[sources.bcra]
connector = "finance_news.connectors.bcra:BCRAConnector"
base_url = "https://api.bcra.gob.ar"
frequency = "daily"
freshness = { ttl_seconds = 86400, freshness_tolerance_seconds = 86400 }
priority = "alta"
category = "primary"
enabled = false
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_toml)
            f.flush()
            config_path = Path(f.name)

        try:
            sources = parse_source_configs(config_path)
            self.assertIn("bcra", sources)
            self.assertFalse(sources["bcra"].enabled)

            # Filter for active sources
            active_sources = {k: v for k, v in sources.items() if v.enabled}
            self.assertEqual(len(active_sources), 0)
        finally:
            config_path.unlink()

    def test_series_config_parsing(self) -> None:
        """Test parsing series configurations."""
        config_toml = """
version = "1.0"

[sources]

[sources.bcra]
connector = "finance_news.connectors.bcra:BCRAConnector"
base_url = "https://api.bcra.gob.ar"
frequency = "daily"
freshness = { ttl_seconds = 86400, freshness_tolerance_seconds = 86400 }
priority = "alta"
category = "primary"

[series]

[series.bcra_reservas]
source_id = "bcra"
path = "/estadisticas/v2/reservas"
filters = { currency = "usd" }
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_toml)
            f.flush()
            config_path = Path(f.name)

        try:
            series = parse_series_configs(config_path)
            self.assertIn("bcra_reservas", series)
            self.assertEqual(series["bcra_reservas"].source_id, "bcra")
            self.assertEqual(series["bcra_reservas"].path, "/estadisticas/v2/reservas")
            self.assertEqual(series["bcra_reservas"].filters, {"currency": "usd"})
        finally:
            config_path.unlink()

    def test_invalid_toml_raises_error(self) -> None:
        """Test that invalid TOML raises ConfigValidationError."""
        config_toml = """
version = "1.0"

[sources]

[sources.bcra]
connector = "finance_news.connectors.bcra:BCRAConnector"
base_url = "https://api.bcra.gob.ar"
frequency = "daily"
freshness = { ttl_seconds = 86400, freshness_tolerance_seconds = 86400 }
priority = "alta"
category = "primary"
  bad_toml = [unclosed
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_toml)
            f.flush()
            config_path = Path(f.name)

        try:
            with self.assertRaises(ConfigValidationError) as cm:
                parse_source_configs(config_path)
            self.assertIn("Invalid TOML", str(cm.exception))
        finally:
            config_path.unlink()

    def test_file_not_found_raises_error(self) -> None:
        """Test that missing file raises ConfigValidationError."""
        config_path = Path("/nonexistent/config.toml")

        with self.assertRaises(ConfigValidationError) as cm:
            parse_source_configs(config_path)
        self.assertIn("not found", str(cm.exception))


if __name__ == "__main__":
    unittest.main()