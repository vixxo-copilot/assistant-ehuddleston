#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source <(grep -v '^\s*#' "$ENV_FILE" | grep -v '^\s*$' | sed 's/\r$//')
  set +a
fi

cd "$SCRIPT_DIR"
if [[ ! -d node_modules/@modelcontextprotocol/sdk ]]; then
  npm install --no-fund --no-audit
fi

export HUBSPOT_PAGES_PYTHON="${HUBSPOT_PAGES_PYTHON:-python3}"
exec node "$SCRIPT_DIR/hubspot-pages-mcp.mjs"
