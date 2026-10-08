#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8080}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
fi

AWS_REGION="${AWS_REGION:-ap-south-1}"
DYNAMODB_ENABLED="${DYNAMODB_ENABLED:-false}"
DYNAMODB_TABLE="${DYNAMODB_TABLE:-environmental-recovery}"
ML_S3_BUCKET="${ML_S3_BUCKET:-environmental-recovery-ml-132218943520}"
REKOGNITION_MODEL_ARN="${REKOGNITION_MODEL_ARN:-arn:aws:rekognition:ap-south-1:132218943520:project/environmental-recovery-classifier/version/trashnet-v1/1791474803175}"
START_REKOGNITION_MODEL="${START_REKOGNITION_MODEL:-false}"

MODEL_STARTED=false
if [[ "$START_REKOGNITION_MODEL" == "true" && -n "$REKOGNITION_MODEL_ARN" ]]; then
  export AWS_REGION
  echo "Starting Rekognition model..."
  aws rekognition start-project-version \
    --project-version-arn "$REKOGNITION_MODEL_ARN" \
    --min-inference-units 1 \
    --region "$AWS_REGION" >/dev/null
  for _ in {1..18}; do
    STATUS="$(aws rekognition describe-project-versions \
      --project-arn "${REKOGNITION_MODEL_ARN%/version/*}" \
      --version-names trashnet-v1 \
      --region "$AWS_REGION" \
      --query 'ProjectVersionDescriptions[0].Status' --output text 2>/dev/null || true)"
    [[ "$STATUS" == "RUNNING" ]] && { MODEL_STARTED=true; break; }
    [[ "$STATUS" == "FAILED" || "$STATUS" == "STOPPED" ]] && { echo "Rekognition model failed to start: $STATUS" >&2; exit 1; }
    sleep 5
  done
  [[ "$MODEL_STARTED" == true ]] || { echo "Timed out waiting for Rekognition model." >&2; exit 1; }
fi

cleanup() {
  if [[ "$MODEL_STARTED" == true ]]; then
    echo "Stopping Rekognition model..."
    aws rekognition stop-project-version --project-version-arn "$REKOGNITION_MODEL_ARN" --region "$AWS_REGION" >/dev/null || true
  fi
}
trap cleanup EXIT

echo "Starting the recovery demo at http://localhost:${PORT}"
echo "Press Ctrl+C to stop."
cd "$ROOT_DIR"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
[[ -x "$PYTHON_BIN" ]] || PYTHON_BIN="python3"
export PORT AWS_REGION DYNAMODB_ENABLED DYNAMODB_TABLE ML_S3_BUCKET REKOGNITION_MODEL_ARN
"$PYTHON_BIN" -m src.api_server
