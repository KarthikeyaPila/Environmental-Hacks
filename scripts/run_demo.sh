#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8080}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Starting the recovery demo at http://localhost:${PORT}"
echo "Press Ctrl+C to stop."
python3 -m http.server "$PORT" --directory "$ROOT_DIR/demo"
