#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8080}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Starting the recovery demo at http://localhost:${PORT}"
echo "Press Ctrl+C to stop."
cd "$ROOT_DIR"
python3 -m src.api_server
