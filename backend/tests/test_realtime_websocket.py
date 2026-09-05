import pytest
from app.core.roles import RoleName
from app.websocket.manager import ConnectionManager


@pytest.mark.asyncio
async def test_websocket_manager_sanitization():
    manager = ConnectionManager()

    internal_payload = {
        "event": "quote.updated",
        "quotation_id": 1,
        "timestamp": "2026-09-05T12:00:00Z",
        "data": {
            "net_total": 500.00,
            "unit_cost": 200.00,
            "total_cost": 200.00,
            "margin_amount": 300.00,
            "margin_pct": 60.00,
            "risk_score": 5.0,
        },
    }

    # Test CUSTOMER role payload sanitization
    cust_payload = manager._sanitize_payload(internal_payload, RoleName.CUSTOMER)
    assert "unit_cost" not in cust_payload["data"]
    assert "total_cost" not in cust_payload["data"]
    assert "margin_amount" not in cust_payload["data"]
    assert "margin_pct" not in cust_payload["data"]
    assert "risk_score" not in cust_payload["data"]
    assert cust_payload["data"]["net_total"] == 500.00

    # Test internal SALES_REP payload preservation
    rep_payload = manager._sanitize_payload(internal_payload, RoleName.SALES_REP)
    assert rep_payload["data"]["unit_cost"] == 200.00
    assert rep_payload["data"]["margin_pct"] == 60.00
