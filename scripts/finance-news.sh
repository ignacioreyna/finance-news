#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHONPATH="$ROOT_DIR/src" python3 -m finance_news.cli "$@"