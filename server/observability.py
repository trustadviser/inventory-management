"""Dependency-free HTTP telemetry for the inventory API.

The application is intentionally small, so keeping the metrics implementation local
avoids requiring a monitoring backend just to run it.  The exposed format is the
Prometheus text format and can be scraped by any compatible collector.
"""

import json
import logging
import os
import threading
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response

REQUEST_ID_HEADER = "X-Request-ID"
LATENCY_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)


class JsonFormatter(logging.Formatter):
    """Render log records as machine-readable JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in ("request_id", "method", "path", "status_code", "duration_ms"):
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Configure application logging from ``LOG_LEVEL`` and ``LOG_FORMAT``."""

    level = os.getenv("LOG_LEVEL", "INFO").upper()
    handler = logging.StreamHandler()
    if os.getenv("LOG_FORMAT", "json").lower() == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))

    logger = logging.getLogger("inventory.api")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False


class MetricsRegistry:
    """Thread-safe, bounded-cardinality HTTP metric store."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._requests: Counter[tuple[str, str, int]] = Counter()
        self._durations: Counter[tuple[str, str, float]] = Counter()
        self._duration_sums: Counter[tuple[str, str]] = Counter()

    def observe(self, method: str, route: str, status: int, duration: float) -> None:
        with self._lock:
            self._requests[(method, route, status)] += 1
            self._duration_sums[(method, route)] += duration
            for bucket in LATENCY_BUCKETS:
                if duration <= bucket:
                    self._durations[(method, route, bucket)] += 1

    def render(self) -> str:
        with self._lock:
            requests = self._requests.copy()
            durations = self._durations.copy()
            sums = self._duration_sums.copy()

        lines = [
            "# HELP inventory_http_requests_total Total HTTP requests.",
            "# TYPE inventory_http_requests_total counter",
        ]
        for (method, route, status), count in sorted(requests.items()):
            labels = f'method="{method}",route="{route}",status="{status}"'
            lines.append(f"inventory_http_requests_total{{{labels}}} {count}")

        lines.extend([
            "# HELP inventory_http_request_duration_seconds HTTP request latency.",
            "# TYPE inventory_http_request_duration_seconds histogram",
        ])
        for method, route in sorted(sums):
            labels = f'method="{method}",route="{route}"'
            for bucket in LATENCY_BUCKETS:
                count = durations[(method, route, bucket)]
                lines.append(
                    f'inventory_http_request_duration_seconds_bucket{{{labels},le="{bucket:g}"}} {count}'
                )
            count = sum(value for (m, r, _), value in requests.items() if (m, r) == (method, route))
            lines.append(f'inventory_http_request_duration_seconds_bucket{{{labels},le="+Inf"}} {count}')
            lines.append(f"inventory_http_request_duration_seconds_sum{{{labels}}} {sums[(method, route)]:.9f}")
            lines.append(f"inventory_http_request_duration_seconds_count{{{labels}}} {count}")
        return "\n".join(lines) + "\n"


metrics = MetricsRegistry()


def _route_name(request: Request) -> str:
    route = request.scope.get("route")
    return getattr(route, "path", None) or "unmatched"


def install_observability(app: FastAPI, readiness_check: Callable[[], bool]) -> None:
    """Install health endpoints, metrics, request correlation, and access logs."""

    configure_logging()
    logger = logging.getLogger("inventory.api")

    @app.middleware("http")
    async def observe_request(request: Request, call_next):
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = time.perf_counter() - started
            route = _route_name(request)
            if request.url.path != "/metrics":
                metrics.observe(request.method, route, status_code, duration)
            logger.info(
                "request_completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": route,
                    "status_code": status_code,
                    "duration_ms": round(duration * 1000, 3),
                },
            )
            # Starlette responses have mutable headers even after call_next returns.
            if "response" in locals():
                response.headers[REQUEST_ID_HEADER] = request_id

    @app.get("/health/live", tags=["observability"], include_in_schema=False)
    def liveness():
        return {"status": "ok"}

    @app.get("/health/ready", tags=["observability"], include_in_schema=False)
    def readiness(response: Response):
        ready = readiness_check()
        if not ready:
            response.status_code = 503
        return {"status": "ready" if ready else "not_ready"}

    @app.get("/health", tags=["observability"], include_in_schema=False)
    def health():
        return {"status": "ok"}

    @app.get("/metrics", tags=["observability"], include_in_schema=False)
    def prometheus_metrics():
        return Response(metrics.render(), media_type="text/plain; version=0.0.4; charset=utf-8")
