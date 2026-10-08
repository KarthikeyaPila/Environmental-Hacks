#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8080}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Starting the recovery demo at http://localhost:${PORT}"
echo "Press Ctrl+C to stop."
cd "$ROOT_DIR"
PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" -m src.api_server
