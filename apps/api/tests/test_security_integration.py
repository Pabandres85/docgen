from fastapi.testclient import TestClient

from app.core.settings import settings
from app.main import create_app


def test_rate_limit_blocks_after_threshold():
    original_enabled = settings.rate_limit_enabled
    original_requests = settings.rate_limit_requests
    original_window = settings.rate_limit_window_seconds
    try:
        settings.rate_limit_enabled = True
        settings.rate_limit_requests = 2
        settings.rate_limit_window_seconds = 60

        app = create_app()
        with TestClient(app) as client:
            assert client.get("/health").status_code == 200
            assert client.get("/batches/unknown").status_code in {404, 429}
            assert client.get("/batches/unknown").status_code in {404, 429}
            limited = client.get("/batches/unknown")
            assert limited.status_code == 429
    finally:
        settings.rate_limit_enabled = original_enabled
        settings.rate_limit_requests = original_requests
        settings.rate_limit_window_seconds = original_window


def test_security_headers_present(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
