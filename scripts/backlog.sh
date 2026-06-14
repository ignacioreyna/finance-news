#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NODE_BIN="/Users/ignacioreyna/.nvm/versions/node/v22.22.0/bin"
BACKLOG_BIN="$ROOT_DIR/.tools/backlog-md/node_modules/.bin/backlog"

if [[ ! -x "$BACKLOG_BIN" ]]; then
  echo "Backlog.md is not installed locally. Run:" >&2
  echo "  $NODE_BIN/npm install --prefix .tools/backlog-md backlog.md" >&2
  exit 1
fi

PATH="$NODE_BIN:$PATH" "$BACKLOG_BIN" "$@"
