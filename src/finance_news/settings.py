"""Stdlib-only .env file loader for finance-news.

This module provides a minimal, dependency-free .env file loader that mirrors
the common subset of python-dotenv functionality. It loads environment variables
from a .env file into os.environ, making them available to connectors and other
code that reads API keys from the environment.

Key behaviors:
- .env file is optional: if missing, returns empty dict silently
- By default, does NOT override existing os.environ values (real shell env wins)
- Supports KEY=VALUE syntax, export prefix, quotes, and simple variable expansion
- Skips invalid key names rather than raising
"""

from __future__ import annotations

import os
import re
from pathlib import Path


def get_repo_root() -> Path:
    """Return the finance-news repository root directory.

    The repo root is the parent of the src/ directory. Since this module is at
    src/finance_news/settings.py, the path is:
        settings.py -> finance_news -> src -> repo_root

    Returns:
        Path to the repository root directory.
    """
    return Path(__file__).resolve().parents[2]


def load_env(
    path: str | os.PathLike[str] | None = None,
    *,
    override: bool = False,
) -> dict[str, str]:
    """Load environment variables from a .env file into os.environ.

    Args:
        path: Path to the .env file. If None, uses .env at repo root.
        override: If True, override existing os.environ values. If False,
            only set keys that don't already exist in os.environ.

    Returns:
        Dict of key-value pairs that were actually loaded/set into os.environ.
        Empty dict if file doesn't exist or contains no valid entries.
    """
    if path is None:
        path = get_repo_root() / ".env"

    env_path = Path(path)
    if not env_path.exists():
        return {}

    result: dict[str, str] = {}
    # Track values parsed from this file for variable expansion
    local_values: dict[str, str] = {}

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()

            # Skip blank lines
            if not stripped:
                continue

            # Skip comment lines (first non-space char is #)
            if stripped[0] == "#":
                continue

            # Strip optional 'export' prefix
            if stripped.startswith("export "):
                stripped = stripped[7:].lstrip()

            # Split on first '='
            if "=" not in stripped:
                continue

            key, value = stripped.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Validate key name (skip invalid rather than raise)
            if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
                continue

            # Strip surrounding matching quotes
            quote_char = None
            if len(value) >= 2:
                if value.startswith('"') and value.endswith('"'):
                    quote_char = '"'
                elif value.startswith("'") and value.endswith("'"):
                    quote_char = "'"

            if quote_char:
                # Quoted: keep inner content verbatim, no comment stripping
                value = value[1:-1]
            else:
                # Unquoted: strip trailing inline comment
                if " #" in value:
                    value = value.split(" #", 1)[0].rstrip()

            # Expand variable references ($VAR and ${VAR})
            # Use a simple best-effort approach, not full shell expansion
            value = _expand_variables(value, local_values, os.environ)

            # Store in local values for reference by later lines
            local_values[key] = value

            # Only set in os.environ if override=True or key not already present
            if override or key not in os.environ:
                os.environ[key] = value
                result[key] = value

    return result


def _expand_variables(
    value: str,
    local_values: dict[str, str],
    environ: dict[str, str] | os._Environ[str],
) -> str:
    """Expand $VAR and ${VAR} references in value.

    Looks up variables first in local_values (parsed earlier in this file),
    then in environ (already-set environment).

    Args:
        value: String that may contain variable references.
        local_values: Dict of values parsed from the .env file so far.
        environ: Current os.environ dict.

    Returns:
        String with variable references expanded (where found).
    """
    # Try ${VAR} syntax first
    def replace_braced(match: re.Match[str]) -> str:
        var_name = match.group(1)
        if var_name in local_values:
            return local_values[var_name]
        return environ.get(var_name, match.group(0))

    value = re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", replace_braced, value)

    # Then try $VAR syntax (but not $$ which is escaped)
    def replace_simple(match: re.Match[str]) -> str:
        var_name = match.group(1)
        if var_name in local_values:
            return local_values[var_name]
        return environ.get(var_name, match.group(0))

    value = re.sub(r"(?<!\$)\$([A-Za-z_][A-Za-z0-9_]*)", replace_simple, value)

    # Replace $$ with $
    value = value.replace("$$", "$")

    return value