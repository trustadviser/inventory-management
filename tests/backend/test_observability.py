"""Tests for API health, request correlation, and Prometheus metrics."""


def test_generated_request_id_is_returned(client):
    response = client.get("/api/inventory")

    assert response.status_code == 200
    assert response.headers["x-request-id"]


def test_caller_request_id_is_preserved(client):
    response = client.get("/health/live", headers={"X-Request-ID": "trace-123"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["x-request-id"] == "trace-123"


def test_readiness_reports_loaded_data(client):
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_metrics_expose_templated_route_and_latency(client):
    client.get("/api/inventory/1")
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "inventory_http_requests_total" in response.text
    assert 'route="/api/inventory/{item_id}"' in response.text
    assert "inventory_http_request_duration_seconds_bucket" in response.text
