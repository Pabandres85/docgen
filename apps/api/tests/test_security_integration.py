from fastapi.testclient import TestClient

from app.core.settings import settings
from app.core.rate_limit import RateLimitConfig, RateLimitMiddleware
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


def test_cleanup_removes_inactive_keys_after_expiration():
    middleware = RateLimitMiddleware(app=lambda scope, receive, send: None, config=RateLimitConfig(max_requests=10, window_seconds=60))
    now = 1000.0
    middleware._hits["1.1.1.1"].extend([900.0, 910.0])
    middleware._hits["2.2.2.2"].extend([995.0])
    middleware._last_cleanup = now - 301.0

    with middleware._lock:
        middleware._cleanup_stale_keys(now - middleware.config.window_seconds)
        middleware._last_cleanup = now

    assert "1.1.1.1" not in middleware._hits
    assert "2.2.2.2" in middleware._hits
