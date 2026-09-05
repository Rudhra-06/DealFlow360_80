import sys
from pathlib import Path
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app

client = TestClient(app)


def test_get_razorpay_config():
    response = client.get("/api/v1/payments/razorpay/config")
    assert response.status_code == 200
    data = response.json()
    assert data["key_id"] == "rzp_test_TYVhOpGcj7mkYU"
    assert "firebase" in data
    assert data["firebase"]["apiKey"] == "AIzaSyCQMQ9teEy9X_4Fe0JpPPKRCCysvY8v89w"
    assert data["firebase"]["projectId"] == "dealflow360-9bb5c"
