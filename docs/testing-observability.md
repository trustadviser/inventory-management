# Testing telemetry and observability

The observability feature can be verified with the automated backend tests, a
self-contained smoke test, or individual HTTP requests.

## Quick smoke test

From the repository root, run:

```bash
./scripts/test-observability.sh
```

The script starts the API on an unused test port, waits for it to become ready,
and verifies all of the following:

1. The readiness endpoint returns `{"status":"ready"}`.
2. A caller-provided `X-Request-ID` is returned unchanged.
3. The Prometheus endpoint contains a request counter and latency histogram.
4. Metrics use `/api/inventory/{item_id}` instead of the concrete item ID.
5. The structured access log includes the request ID, route, and status code.

The API process is stopped automatically, including when a check fails. Set
`PORT` to override the default test port (`18001`):

```bash
PORT=19001 ./scripts/test-observability.sh
```

## Backend test suite

Install the backend development dependencies and run the observability tests:

```bash
cd server
uv sync --dev
uv run pytest ../tests/backend/test_observability.py -q
```

Run the entire backend suite with:

```bash
cd server
uv run pytest ../tests/backend -q
```

## Manual verification

Start the backend in one terminal:

```bash
cd server
uv run python main.py
```

### Health probes

```bash
curl --fail --silent http://localhost:8001/health/live
curl --fail --silent http://localhost:8001/health/ready
```

Both requests should return HTTP 200. The liveness response is
`{"status":"ok"}` and the readiness response is `{"status":"ready"}`.

### Request correlation

```bash
curl --silent --dump-header - \
  -H 'X-Request-ID: manual-test-123' \
  http://localhost:8001/api/inventory/1 \
  --output /dev/null
```

The response headers should include:

```text
x-request-id: manual-test-123
```

The backend terminal should contain a JSON log entry with the same
`request_id`, along with `method`, templated `path`, `status_code`, and
`duration_ms` fields.

### Prometheus metrics

After making the inventory request above, run:

```bash
curl --fail --silent http://localhost:8001/metrics
```

The output should include entries similar to:

```text
inventory_http_requests_total{method="GET",route="/api/inventory/{item_id}",status="200"} 1
inventory_http_request_duration_seconds_bucket{method="GET",route="/api/inventory/{item_id}",le="0.005"} 1
inventory_http_request_duration_seconds_sum{method="GET",route="/api/inventory/{item_id}"} 0.001234567
inventory_http_request_duration_seconds_count{method="GET",route="/api/inventory/{item_id}"} 1
```

Counts and durations will vary. The important detail is that the label contains
the route template, not `/api/inventory/1`; this keeps metric cardinality
bounded.

### Logging configuration

JSON is the default log format. Human-readable output and a more verbose log
level can be tested with:

```bash
cd server
LOG_FORMAT=text LOG_LEVEL=DEBUG uv run python main.py
```

Then make any request and confirm the access log is plain text. Stop the server
with <kbd>Ctrl</kbd>+<kbd>C</kbd> when finished.
