"""Tests for configuration and route integration.

This module tests the Settings configuration and route endpoints
with mocked dependencies. NO live API calls are made.
"""

import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.main import app


class TestSettings:
    """Tests for Settings configuration."""

    def test_s2_enabled_with_api_key(self):
        """Test s2_enabled property returns True when API key is set."""
        settings = Settings(semantic_scholar_api_key="test-key-123")
        assert settings.s2_enabled is True

    def test_s2_enabled_without_api_key(self):
        """Test s2_enabled property returns False when API key is None."""
        settings = Settings(semantic_scholar_api_key=None)
        assert settings.s2_enabled is False

    def test_s2_enabled_with_empty_api_key(self):
        """Test s2_enabled property returns False when API key is empty string."""
        settings = Settings(semantic_scholar_api_key="")
        assert settings.s2_enabled is False

    def test_allowed_origins_parsing(self):
        """Test allowed_origins property parses comma-separated string."""
        settings = Settings(allowed_origins_raw="http://localhost:3000,http://localhost:3001")
        assert settings.allowed_origins == ["http://localhost:3000", "http://localhost:3001"]

    def test_allowed_origins_with_whitespace(self):
        """Test allowed_origins property handles whitespace correctly."""
        settings = Settings(allowed_origins_raw=" http://localhost:3000 , http://localhost:3001 ")
        assert settings.allowed_origins == ["http://localhost:3000", "http://localhost:3001"]

    def test_allowed_origins_empty(self):
        """Test allowed_origins property handles empty string."""
        settings = Settings(allowed_origins_raw="")
        assert settings.allowed_origins == []

    def test_default_values(self):
        """Test default configuration values."""
        # Use _env_file=None to prevent loading .env file
        settings = Settings(_env_file=None)
        assert settings.arxiv_delay_seconds == 5
        assert settings.s2_requests_per_second == 1
        assert settings.deepl_api_key is None


class TestQueryRoute:
    """Tests for /api/query endpoint."""

    def test_start_query_creates_session(self):
        """Test that POST /api/query creates a new session."""
        client = TestClient(app)
        
        with patch('backend.api.routes.query.create_session') as mock_create:
            with patch('backend.api.routes.query.run_pipeline') as mock_run:
                response = client.post(
                    "/api/query",
                    json={"query": "CRISPR gene editing"}
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert "session_id" in data
                assert data["status"] == "processing"
                assert "websocket_url" in data
                
                # Verify session was created and pipeline started
                mock_create.assert_called_once()
                mock_run.assert_called_once()

    def test_start_query_validation_error(self):
        """Test that POST /api/query validates request payload."""
        client = TestClient(app)
        
        # Missing required 'query' field
        response = client.post("/api/query", json={})
        
        assert response.status_code == 422  # Validation error


class TestPipelineRoute:
    """Tests for /api/pipeline endpoint."""

    def test_get_pipeline_status_success(self):
        """Test GET /api/pipeline/{session_id} returns session data."""
        client = TestClient(app)
        
        mock_session = {
            "session_id": "test-123",
            "stage": "extraction",
            "progress": 50,
            "papers_found": 10,
            "papers_analyzed": 5,
            "themes_identified": 3,
            "results": None,
            "error": None,
            "message": "Processing papers...",
        }
        
        with patch('backend.api.routes.pipeline.get_session') as mock_get:
            mock_get.return_value = mock_session
            
            response = client.get("/api/pipeline/test-123")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["session_id"] == "test-123"
            assert data["stage"] == "extraction"
            assert data["progress"] == 50
            assert data["papers_found"] == 10

    def test_get_pipeline_status_not_found(self):
        """Test GET /api/pipeline/{session_id} handles missing session."""
        client = TestClient(app)
        
        with patch('backend.api.routes.pipeline.get_session') as mock_get:
            mock_get.return_value = None
            
            response = client.get("/api/pipeline/nonexistent")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["error"] == "Session not found"
            assert data["stage"] == "error"

    def test_get_pipeline_status_with_results(self):
        """Test GET /api/pipeline/{session_id} returns results when complete."""
        client = TestClient(app)
        
        mock_session = {
            "session_id": "test-456",
            "stage": "complete",
            "progress": 100,
            "papers_found": 30,
            "papers_analyzed": 30,
            "themes_identified": 5,
            "results": {
                "summary": "Analysis complete",
                "graph": {"nodes": [], "edges": []},
                "timeline": {"years": []},
            },
            "error": None,
            "message": "Analysis complete",
        }
        
        with patch('backend.api.routes.pipeline.get_session') as mock_get:
            mock_get.return_value = mock_session
            
            response = client.get("/api/pipeline/test-456")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["stage"] == "complete"
            assert data["progress"] == 100
            assert data["results"] is not None
            assert "summary" in data["results"]

    def test_get_pipeline_status_with_error(self):
        """Test GET /api/pipeline/{session_id} returns error state."""
        client = TestClient(app)
        
        mock_session = {
            "session_id": "test-789",
            "stage": "error",
            "progress": 0,
            "papers_found": 0,
            "papers_analyzed": 0,
            "themes_identified": 0,
            "results": None,
            "error": "API rate limit exceeded",
            "message": "Pipeline failed",
        }
        
        with patch('backend.api.routes.pipeline.get_session') as mock_get:
            mock_get.return_value = mock_session
            
            response = client.get("/api/pipeline/test-789")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["stage"] == "error"
            assert data["error"] == "API rate limit exceeded"


# Made with Bob