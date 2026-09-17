#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${PORT:-18001}"
BASE_URL="http://127.0.0.1:${PORT}"
LOG_FILE="$(mktemp)"
HEADERS_FILE="$(mktemp)"
BODY_FILE="$(mktemp)"

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]]; then
    kill "${SERVER_PID}" 2>/dev/null || true
    wait "${SERVER_PID}" 2>/dev/null || true
  fi
  rm -f "${LOG_FILE}" "${HEADERS_FILE}" "${BODY_FILE}"
}
trap cleanup EXIT

cd "${ROOT_DIR}/server"
python -m uvicorn main:app --host 127.0.0.1 --port "${PORT}" >"${LOG_FILE}" 2>&1 &
SERVER_PID=$!

for _ in {1..50}; do
  if curl --fail --silent "${BASE_URL}/health/ready" >"${BODY_FILE}"; then
    break
  fi
  if ! kill -0 "${SERVER_PID}" 2>/dev/null; then
    echo "API failed to start:" >&2
    cat "${LOG_FILE}" >&2
    exit 1
  fi
  sleep 0.1
done

python - "${BODY_FILE}" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as response:
    assert json.load(response) == {"status": "ready"}
PY
echo "PASS: readiness endpoint"

curl --fail --silent --dump-header "${HEADERS_FILE}" \
  -H "X-Request-ID: observability-smoke-test" \
  "${BASE_URL}/api/inventory/1" --output /dev/null
tr -d '\r' <"${HEADERS_FILE}" | grep -qi '^x-request-id: observability-smoke-test$'
echo "PASS: request ID propagation"

curl --fail --silent "${BASE_URL}/metrics" >"${BODY_FILE}"
grep -q '^# TYPE inventory_http_requests_total counter$' "${BODY_FILE}"
grep -Fq 'route="/api/inventory/{item_id}"' "${BODY_FILE}"
grep -q '^# TYPE inventory_http_request_duration_seconds histogram$' "${BODY_FILE}"
if grep -Fq 'route="/api/inventory/1"' "${BODY_FILE}"; then
  echo "Metrics contain a concrete resource ID instead of a route template" >&2
  exit 1
fi
echo "PASS: bounded-cardinality Prometheus metrics"

grep -q '"request_id": "observability-smoke-test"' "${LOG_FILE}"
grep -q '"path": "/api/inventory/{item_id}"' "${LOG_FILE}"
grep -q '"status_code": 200' "${LOG_FILE}"
echo "PASS: structured correlated access log"

echo "All observability smoke tests passed."
