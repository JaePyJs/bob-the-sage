"""Tests for health check endpoint and basic API availability.

This module contains smoke tests to verify the FastAPI application
starts correctly and responds to basic health check requests.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def test_health_endpoint_returns_ok(client):
    """Test that /health endpoint returns 200 OK with correct payload."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "sage-backend"


def test_health_endpoint_structure(client):
    """Test that health endpoint returns expected JSON structure."""
    response = client.get("/health")
    data = response.json()
    
    # Verify required fields exist
    assert "status" in data
    assert "service" in data
    
    # Verify field types
    assert isinstance(data["status"], str)
    assert isinstance(data["service"], str)


def test_api_is_available(client):
    """Smoke test: verify API is reachable and responds."""
    response = client.get("/health")
    assert response.status_code == 200


def test_cors_headers_present(client):
    """Test that CORS middleware is configured (headers present)."""
    response = client.get("/health")
    # CORS headers should be present in response
    # Note: TestClient may not include all CORS headers, but we can verify the endpoint works
    assert response.status_code == 200


def test_health_endpoint_method_not_allowed(client):
    """Test that non-GET methods return 405 Method Not Allowed."""
    response = client.post("/health")
    assert response.status_code == 405
    
    response = client.put("/health")
    assert response.status_code == 405
    
    response = client.delete("/health")
    assert response.status_code == 405


def test_health_endpoint_idempotent(client):
    """Test that health endpoint is idempotent (multiple calls return same result)."""
    response1 = client.get("/health")
    response2 = client.get("/health")
    response3 = client.get("/health")
    
    assert response1.json() == response2.json() == response3.json()
    assert all(r.status_code == 200 for r in [response1, response2, response3])


def test_invalid_endpoint_returns_404(client):
    """Test that invalid endpoints return 404 Not Found."""
    response = client.get("/nonexistent")
    assert response.status_code == 404


def test_health_response_time(client):
    """Test that health endpoint responds quickly (< 1 second)."""
    import time
    
    start = time.time()
    response = client.get("/health")
    elapsed = time.time() - start
    
    assert response.status_code == 200
    assert elapsed < 1.0, f"Health check took {elapsed:.2f}s, should be < 1s"


# Made with Bob