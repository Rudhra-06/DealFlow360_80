import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from app.db.session import get_db

client = TestClient(app)


def test_root_health_endpoint():
    """Verify that root GET /health returns HTTP 200 and expected payload."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "DealFlow360 API"
    }


def test_v1_health_endpoint():
    """Verify that API v1 GET /api/v1/health returns HTTP 200 and expected payload."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "DealFlow360 API"
    }


def test_db_health_endpoint_success():
    """Verify GET /api/v1/health/db returns HTTP 200 when DB query succeeds."""
    async def mock_get_db_success():
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_result
        yield mock_session

    app.dependency_overrides[get_db] = mock_get_db_success
    try:
        response = client.get("/api/v1/health/db")
        assert response.status_code == 200
        assert response.json() == {
            "status": "healthy",
            "database": "connected"
        }
    finally:
        app.dependency_overrides.clear()


def test_db_health_endpoint_failure_safe_response():
    """Verify GET /api/v1/health/db returns HTTP 503 and hides credentials on failure."""
    async def mock_get_db_failure():
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Internal db password=secret123 connection failed")
        yield mock_session

    app.dependency_overrides[get_db] = mock_get_db_failure
    try:
        response = client.get("/api/v1/health/db")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "disconnected"
        assert data["detail"] == "Database connection unavailable"
        # Ensure no sensitive keywords like password or secret are in response
        response_str = str(data).lower()
        assert "password" not in response_str
        assert "secret" not in response_str
    finally:
        app.dependency_overrides.clear()
