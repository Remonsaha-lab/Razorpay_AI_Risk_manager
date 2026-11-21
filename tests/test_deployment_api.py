"""Integration tests for deployment endpoints, health checks, and CORS configuration."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client):
    """Test that GET / returns 200 OK and service metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "DisputeGuard API"
    assert "version" in data
    assert data["health"] == "/health"


def test_health_endpoint(client):
    """Test that GET /health returns 200 OK and status healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "DisputeGuard"


def test_cors_vercel_production(client):
    """Test CORS preflight for production Vercel domain."""
    origin = "https://disputeguard.vercel.app"
    response = client.options(
        "/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_vercel_preview_branches(client):
    """Test CORS preflight for dynamic Vercel preview deployment URLs."""
    preview_origins = [
        "https://disputeguard-git-main-user.vercel.app",
        "https://disputeguard-pr-12.vercel.app",
        "https://disputeguard-preview-abc123.vercel.app",
    ]
    for origin in preview_origins:
        response = client.options(
            "/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200, f"Failed for {origin}"
        assert response.headers.get("access-control-allow-origin") == origin


def test_cors_localhost(client):
    """Test CORS preflight for local development origins."""
    for origin in ["http://localhost:3000", "http://127.0.0.1:3000"]:
        response = client.options(
            "/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == origin


def test_cors_unauthorized_origin(client):
    """Test that unauthorized origin is rejected by CORS."""
    response = client.options(
        "/health",
        headers={
            "Origin": "https://unauthorized-malicious-site.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    # CORSMiddleware rejects unapproved origins on preflight by returning 400 or omitting allow-origin header
    assert response.headers.get("access-control-allow-origin") is None
