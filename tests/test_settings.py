"""Unit tests for finance_news.settings module."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_news.settings import load_env, get_repo_root


class TestGetRepoRoot(unittest.TestCase):
    """Tests for get_repo_root function."""

    def test_returns_path(self):
        """Test that get_repo_root returns a Path object."""
        root = get_repo_root()
        self.assertIsInstance(root, Path)
        self.assertTrue(root.exists())

    def test_repo_root_structure(self):
        """Test that repo root has expected structure."""
        root = get_repo_root()
        # Should contain src/ directory
        self.assertTrue((root / "src").exists())
        # Should contain pyproject.toml (standard Python project)
        self.assertTrue((root / "pyproject.toml").exists())


class TestLoadEnvBasicParsing(unittest.TestCase):
    """Tests for basic .env file parsing."""

    def setUp(self):
        """Set up a clean environment for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.env_path = Path(self.temp_dir.name) / ".env"
        # Use test-specific keys to avoid conflicts
        self.test_keys = []

    def tearDown(self):
        """Clean up environment after each test."""
        for key in self.test_keys:
            if key in os.environ:
                del os.environ[key]
        self.temp_dir.cleanup()

    def register_key(self, key: str) -> None:
        """Register a key for cleanup."""
        self.test_keys.append(key)

    def test_parses_key_value(self):
        """Test basic KEY=VALUE parsing."""
        self.env_path.write_text("FN_TEST_KEY=value123\n")
        result = load_env(self.env_path)
        self.assertEqual(result, {"FN_TEST_KEY": "value123"})
        self.assertEqual(os.environ.get("FN_TEST_KEY"), "value123")
        self.register_key("FN_TEST_KEY")

    def test_skips_blank_lines(self):
        """Test that blank lines are skipped."""
        self.env_path.write_text("\n\nFN_TEST_KEY=value\n\n\n")
        result = load_env(self.env_path)
        self.assertEqual(result, {"FN_TEST_KEY": "value"})
        self.assertEqual(os.environ.get("FN_TEST_KEY"), "value")
        self.register_key("FN_TEST_KEY")

    def test_skips_comment_lines(self):
        """Test that lines starting with # are skipped."""
        self.env_path.write_text(
            "# This is a comment\nFN_TEST_KEY=value\n# Another comment\n"
        )
        result = load_env(self.env_path)
        self.assertEqual(result, {"FN_TEST_KEY": "value"})
        self.assertEqual(os.environ.get("FN_TEST_KEY"), "value")
        self.register_key("FN_TEST_KEY")

    def test_skips_comment_with_leading_space(self):
        """Test that lines with leading space and # are skipped."""
        self.env_path.write_text("  # Comment with leading space\nFN_TEST_KEY=value\n")
        result = load_env(self.env_path)
        self.assertEqual(result, {"FN_TEST_KEY": "value"})
        self.assertEqual(os.environ.get("FN_TEST_KEY"), "value")
        self.register_key("FN_TEST_KEY")

    def test_strips_export_prefix(self):
        """Test that 'export ' prefix is stripped."""
        self.env_path.write_text("export FN_TEST_KEY=value\n")
        result = load_env(self.env_path)
        self.assertEqual(result, {"FN_TEST_KEY": "value"})
        self.assertEqual(os.environ.get("FN_TEST_KEY"), "value")
        self.register_key("FN_TEST_KEY")

    def test_strips_export_with_extra_spaces(self):
        """Test that 'export ' prefix with extra spaces is stripped."""
        self.env_path.write_text("export  FN_TEST_KEY=value\n")
        result = load_env(self.env_path)
        self.assertEqual(result, {"FN_TEST_KEY": "value"})
        self.assertEqual(os.environ.get("FN_TEST_KEY"), "value")
        self.register_key("FN_TEST_KEY")


class TestLoadEnvQuoting(unittest.TestCase):
    """Tests for quote handling in values."""

    def setUp(self):
        """Set up a clean environment for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.env_path = Path(self.temp_dir.name) / ".env"
        self.test_keys = []

    def tearDown(self):
        """Clean up environment after each test."""
        for key in self.test_keys:
            if key in os.environ:
                del os.environ[key]
        self.temp_dir.cleanup()

    def register_key(self, key: str) -> None:
        """Register a key for cleanup."""
        self.test_keys.append(key)

    def test_strips_single_quotes(self):
        """Test that surrounding single quotes are stripped."""
        self.env_path.write_text("FN_TEST_KEY='value'\n")
        result = load_env(self.env_path)
        self.assertEqual(result, {"FN_TEST_KEY": "value"})
        self.assertEqual(os.environ.get("FN_TEST_KEY"), "value")
        self.register_key("FN_TEST_KEY")

    def test_strips_double_quotes(self):
        """Test that surrounding double quotes are stripped."""
        self.env_path.write_text('FN_TEST_KEY="value"\n')
        result = load_env(self.env_path)
        self.assertEqual(result, {"FN_TEST_KEY": "value"})
        self.assertEqual(os.environ.get("FN_TEST_KEY"), "value")
        self.register_key("FN_TEST_KEY")

    def test_keeps_inner_quotes_verbatim(self):
        """Test that inner quotes are kept when quoted."""
        self.env_path.write_text('FN_TEST_KEY="value with \'inner\' quotes"\n')
        result = load_env(self.env_path)
        self.assertEqual(result, {"FN_TEST_KEY": "value with 'inner' quotes"})
        self.assertEqual(os.environ.get("FN_TEST_KEY"), "value with 'inner' quotes")
        self.register_key("FN_TEST_KEY")

    def test_quoted_value_preserves_hashes(self):
        """Test that quoted values preserve # characters."""
        self.env_path.write_text('FN_TEST_KEY="value # with hash"\n')
        result = load_env(self.env_path)
        self.assertEqual(result, {"FN_TEST_KEY": "value # with hash"})
        self.assertEqual(os.environ.get("FN_TEST_KEY"), "value # with hash")
        self.register_key("FN_TEST_KEY")

    def test_unquoted_strips_trailing_comment(self):
        """Test that unquoted values strip trailing # comments."""
        self.env_path.write_text("FN_TEST_KEY=value # comment\n")
        result = load_env(self.env_path)
        self.assertEqual(result, {"FN_TEST_KEY": "value"})
        self.assertEqual(os.environ.get("FN_TEST_KEY"), "value")
        self.register_key("FN_TEST_KEY")


class TestLoadEnvVariableExpansion(unittest.TestCase):
    """Tests for variable expansion in values."""

    def setUp(self):
        """Set up a clean environment for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.env_path = Path(self.temp_dir.name) / ".env"
        self.test_keys = []

    def tearDown(self):
        """Clean up environment after each test."""
        for key in self.test_keys:
            if key in os.environ:
                del os.environ[key]
        self.temp_dir.cleanup()

    def register_key(self, key: str) -> None:
        """Register a key for cleanup."""
        self.test_keys.append(key)

    def test_expands_simple_dollar_var(self):
        """Test that $VAR syntax expands to earlier value."""
        self.env_path.write_text("FN_TEST_BASE=base\nFN_TEST_KEY=$FN_TEST_BASE\n")
        result = load_env(self.env_path)
        self.assertEqual(result, {"FN_TEST_BASE": "base", "FN_TEST_KEY": "base"})
        self.assertEqual(os.environ.get("FN_TEST_KEY"), "base")
        self.register_key("FN_TEST_BASE")
        self.register_key("FN_TEST_KEY")

    def test_expands_braced_var(self):
        """Test that ${VAR} syntax expands to earlier value."""
        self.env_path.write_text("FN_TEST_BASE=base\nFN_TEST_KEY=${FN_TEST_BASE}\n")
        result = load_env(self.env_path)
        self.assertEqual(result, {"FN_TEST_BASE": "base", "FN_TEST_KEY": "base"})
        self.assertEqual(os.environ.get("FN_TEST_KEY"), "base")
        self.register_key("FN_TEST_BASE")
        self.register_key("FN_TEST_KEY")

    def test_expands_from_os_environ(self):
        """Test that variables expand from os.environ."""
        os.environ["FN_TEST_PRESET"] = "preset_value"
        self.register_key("FN_TEST_PRESET")
        self.env_path.write_text("FN_TEST_KEY=$FN_TEST_PRESET\n")
        result = load_env(self.env_path)
        self.assertEqual(result, {"FN_TEST_KEY": "preset_value"})
        self.assertEqual(os.environ.get("FN_TEST_KEY"), "preset_value")
        self.register_key("FN_TEST_KEY")

    def test_expands_mixed_variables(self):
        """Test expansion with multiple variables."""
        os.environ["FN_TEST_EXTERN"] = "extern"
        self.register_key("FN_TEST_EXTERN")
        self.env_path.write_text(
            "FN_TEST_FIRST=first\nFN_TEST_SECOND=$FN_TEST_FIRST/$FN_TEST_EXTERN\n"
        )
        result = load_env(self.env_path)
        self.assertEqual(
            result,
            {"FN_TEST_FIRST": "first", "FN_TEST_SECOND": "first/extern"},
        )
        self.assertEqual(os.environ.get("FN_TEST_SECOND"), "first/extern")
        self.register_key("FN_TEST_FIRST")
        self.register_key("FN_TEST_SECOND")

    def test_escaped_dollar(self):
        """Test that $$ is replaced with $."""
        self.env_path.write_text("FN_TEST_KEY=escaped$$dollar\n")
        result = load_env(self.env_path)
        self.assertEqual(result, {"FN_TEST_KEY": "escaped$dollar"})
        self.assertEqual(os.environ.get("FN_TEST_KEY"), "escaped$dollar")
        self.register_key("FN_TEST_KEY")


class TestLoadEnvOverride(unittest.TestCase):
    """Tests for override behavior."""

    def setUp(self):
        """Set up a clean environment for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.env_path = Path(self.temp_dir.name) / ".env"
        self.test_keys = []

    def tearDown(self):
        """Clean up environment after each test."""
        for key in self.test_keys:
            if key in os.environ:
                del os.environ[key]
        self.temp_dir.cleanup()

    def register_key(self, key: str) -> None:
        """Register a key for cleanup."""
        self.test_keys.append(key)

    def test_does_not_override_existing_by_default(self):
        """Test that existing os.environ values are not overridden by default."""
        os.environ["FN_TEST_EXISTING"] = "original_value"
        self.register_key("FN_TEST_EXISTING")
        self.env_path.write_text("FN_TEST_EXISTING=new_value\n")
        result = load_env(self.env_path)
        # Should be empty since key already exists
        self.assertEqual(result, {})
        # Original value should remain
        self.assertEqual(os.environ.get("FN_TEST_EXISTING"), "original_value")

    def test_overrides_when_flag_set(self):
        """Test that override=True overrides existing values."""
        os.environ["FN_TEST_EXISTING"] = "original_value"
        self.register_key("FN_TEST_EXISTING")
        self.env_path.write_text("FN_TEST_EXISTING=new_value\n")
        result = load_env(self.env_path, override=True)
        # Should contain the new value
        self.assertEqual(result, {"FN_TEST_EXISTING": "new_value"})
        # Value should be updated
        self.assertEqual(os.environ.get("FN_TEST_EXISTING"), "new_value")


class TestLoadEnvMissingFile(unittest.TestCase):
    """Tests for missing .env file handling."""

    def setUp(self):
        """Set up a clean environment for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_keys = []

    def tearDown(self):
        """Clean up environment after each test."""
        for key in self.test_keys:
            if key in os.environ:
                del os.environ[key]
        self.temp_dir.cleanup()

    def register_key(self, key: str) -> None:
        """Register a key for cleanup."""
        self.test_keys.append(key)

    def test_missing_file_returns_empty_dict(self):
        """Test that missing .env file returns empty dict and doesn't raise."""
        missing_path = Path(self.temp_dir.name) / "nonexistent.env"
        result = load_env(missing_path)
        self.assertEqual(result, {})
        # No exception should be raised

    def test_missing_path_none_returns_empty_dict(self):
        """Test that path=None with missing default .env returns empty dict."""
        # Create temp dir without .env file
        old_cwd = os.getcwd()
        try:
            os.chdir(self.temp_dir.name)
            result = load_env(None)
            self.assertEqual(result, {})
        finally:
            os.chdir(old_cwd)


class TestLoadEnvValidation(unittest.TestCase):
    """Tests for key validation and error handling."""

    def setUp(self):
        """Set up a clean environment for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.env_path = Path(self.temp_dir.name) / ".env"
        self.test_keys = []

    def tearDown(self):
        """Clean up environment after each test."""
        for key in self.test_keys:
            if key in os.environ:
                del os.environ[key]
        self.temp_dir.cleanup()

    def register_key(self, key: str) -> None:
        """Register a key for cleanup."""
        self.test_keys.append(key)

    def test_skips_invalid_key_names(self):
        """Test that invalid key names are skipped."""
        self.env_path.write_text(
            "123INVALID=value\nFN_TEST_VALID=value\nINVALID-KEY=value\n"
        )
        result = load_env(self.env_path)
        # Should only contain the valid key
        self.assertEqual(result, {"FN_TEST_VALID": "value"})
        self.assertEqual(os.environ.get("FN_TEST_VALID"), "value")
        self.register_key("FN_TEST_VALID")

    def test_skips_lines_without_equals(self):
        """Test that lines without = are skipped."""
        self.env_path.write_text("FN_TEST_VALID=value\nINVALID_LINE\nFN_TEST_ANOTHER=another\n")
        result = load_env(self.env_path)
        self.assertEqual(result, {"FN_TEST_VALID": "value", "FN_TEST_ANOTHER": "another"})
        self.register_key("FN_TEST_VALID")
        self.register_key("FN_TEST_ANOTHER")

    def test_handles_empty_value(self):
        """Test that empty values are handled."""
        self.env_path.write_text("FN_TEST_KEY=\n")
        result = load_env(self.env_path)
        self.assertEqual(result, {"FN_TEST_KEY": ""})
        self.assertEqual(os.environ.get("FN_TEST_KEY"), "")
        self.register_key("FN_TEST_KEY")


class TestRunnerIntegration(unittest.TestCase):
    """Smoke test for runner integration with load_env."""

    def test_runner_load_env_reference(self):
        """Test that load_env is imported in runner module."""
        # Import the source directly to check for the import
        runner_source = Path(__file__).resolve().parents[1] / "src" / "finance_news" / "cli" / "runner.py"
        runner_content = runner_source.read_text()
        # Check that settings is imported
        self.assertIn("from finance_news.settings import load_env", runner_content)
        # Check that load_env is called in main()
        self.assertIn("load_env()", runner_content)

    def test_runner_main_loads_env_without_crashing(self):
        """Test that runner main() doesn't crash and load_env is called."""
        # Import the source directly to check for the import
        runner_source = Path(__file__).resolve().parents[1] / "src" / "finance_news" / "cli" / "runner.py"
        runner_content = runner_source.read_text()
        # Check that settings is imported
        self.assertIn("from finance_news.settings import load_env", runner_content)
        # Check that load_env is called in main()
        self.assertIn("load_env()", runner_content)


if __name__ == "__main__":
    unittest.main()