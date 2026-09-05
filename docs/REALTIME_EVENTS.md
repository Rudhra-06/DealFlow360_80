# Real-Time Event & Push Notification Catalog

## Overview

DealFlow360 provides a dual-layer real-time communication infrastructure:
1. **WebSocket Connection Manager (`app.websocket.manager`)**: Low-latency WebSocket connections for active browser sessions.
2. **Firebase Cloud Messaging Push Service (`app.integrations.firebase`)**: Fail-safe mobile/desktop push notification delivery for off-line users.

---

## 1. WebSocket Infrastructure

### Endpoint
- **URL**: `ws://<host>:<port>/api/v1/ws?token=<JWT_BEARER_TOKEN>`
- **Authentication**: JWT token query parameter.
- **Heartbeat & Subscriptions**:
  - `{"action": "ping"}` -> Returns `{"event": "pong"}`
  - `{"action": "subscribe", "quotation_id": 123}` -> Returns `{"event": "subscription.success", "quotation_id": 123, "status": "subscribed"}`

### Role-Based Payload Sanitization
For connections associated with users possessing `RoleName.CUSTOMER`, sensitive internal financial fields (`unit_cost`, `total_cost`, `margin_amount`, `margin_pct`, `risk_score`, `risk_reasons`) are automatically stripped before WebSocket frame transmission.

---

## 2. Event Catalog

### 2.1 Quotation Released / Sent to Customer
- **Event Name**: `quote.sent` / `QUOTE_SENT`
- **Recipients**: Active customer portal users mapped to `customer_id`.
- **Payload**:
  ```json
  {
    "event": "quote.sent",
    "quotation_id": 42,
    "timestamp": "2026-09-05T19:40:00Z",
    "data": {
      "quotation_id": 42,
      "quote_number": "Q-20260905-ABCD"
    }
  }
  ```

### 2.2 Customer Posted Negotiation Message / Question
- **Event Name**: `negotiation.message_created` / `CUSTOMER_COMMENT`
- **Recipients**: Quotation owner (`sales_rep_id`).
- **Payload**:
  ```json
  {
    "event": "negotiation.message_created",
    "quotation_id": 42,
    "timestamp": "2026-09-05T19:41:00Z",
    "data": {
      "message_id": 105,
      "author_id": 201,
      "message": "Can we get a 5% discount on order?"
    }
  }
  ```

### 2.3 Sales Rep Internal Reply
- **Event Name**: `negotiation.message_created` / `CUSTOMER_COMMENT`
- **Recipients**: Active customer portal users.
- **Payload**:
  ```json
  {
    "event": "negotiation.message_created",
    "quotation_id": 42,
    "timestamp": "2026-09-05T19:42:00Z",
    "data": {
      "message_id": 106,
      "author_id": 15,
      "message": "Sales Rep replied to your query."
    }
  }
  ```

### 2.4 Customer Submitted Counter-Offer
- **Event Name**: `negotiation.counter_offer_submitted` / `CUSTOMER_COUNTER_OFFER`
- **Recipients**: Quotation owner (`sales_rep_id`).

### 2.5 Customer Confirmed Quotation
- **Event Name**: `quote.accepted` / `CUSTOMER_ACCEPTED`
- **Recipients**: Quotation owner (`sales_rep_id`).
- **Payload**:
  ```json
  {
    "event": "quote.accepted",
    "quotation_id": 42,
    "timestamp": "2026-09-05T19:45:00Z",
    "data": {
      "quotation_id": 42,
      "quote_number": "Q-20260905-ABCD",
      "confirmed_version_id": 12,
      "confirmed_at": "2026-09-05T19:45:00Z"
    }
  }
  ```
