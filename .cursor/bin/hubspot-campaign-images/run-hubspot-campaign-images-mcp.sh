#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

cd "${SCRIPT_DIR}"
if [[ ! -d node_modules/@modelcontextprotocol/sdk ]]; then
  npm install --no-fund --no-audit --silent 2>/dev/null || npm install --no-fund --no-audit
fi

if command -v python3 >/dev/null 2>&1; then
  export HUBSPOT_CAMPAIGN_IMAGES_PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
  export HUBSPOT_CAMPAIGN_IMAGES_PYTHON="python"
elif command -v py >/dev/null 2>&1; then
  export HUBSPOT_CAMPAIGN_IMAGES_PYTHON="py -3"
else
  echo "hubspot-campaign-images-mcp: Python 3 required" >&2
  exit 1
fi

exec node "${SCRIPT_DIR}/hubspot-campaign-images-mcp.mjs"
