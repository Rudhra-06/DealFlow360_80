# DealFlow360 — Core Business Rules

## 1. Commercial & Pricing Rules
- **Discount Limits**: Discount limits resolved hierarchically: Customer Tier -> Product -> Commercial Discount Policy.
- **Approval Triggers**: Quote discount > policy limit routes to `SALES_MANAGER` approval. High-risk score / margin policy violations route to `FINANCE_OPERATIONS`.
- **Customer Confirmation**: Terminal commercial state (`CUSTOMER_CONFIRMED`). Quote cannot be edited post-confirmation.

## 2. Fulfillment & Stock Reservation Rules
- **Reservation Timing**: Stock is reserved strictly AFTER customer confirmation, never during negotiation.
- **Warehouse Allocation Priority**: Allocated by warehouse `priority` ascending, then lowest base shipping cost.
- **Stock Decrement**: `quantity_on_hand` and `quantity_reserved` are physically decremented when shipment status becomes `SHIPPED`.

## 3. Billing & Payment Rules
- **Hybrid Invoicing**: Physical items generate `ONE_TIME` invoices; recurring services generate `ACTIVE` subscriptions.
- **Proration**: Mid-cycle subscription changes calculate exact day-count proration quantized to 2 decimal places.
- **Overpayment Protection**: Payment amount cannot exceed total invoice balance due. Payment currency must match invoice currency.

## 4. Deal Health & Anomaly Rules
- **Discount Anomaly**: Triggered if current quote discount is >= `config.discount_anomaly_threshold_pct` percentage points above the Sales Rep's 90-day historical average (minimum sample size = 3).
- **Alert Deduplication**: Alerts indexed by `(quotation_id, alert_type)` where status is `OPEN` or `ACKNOWLEDGED`. Subsequent scans update `occurrence_count` and `last_triggered_at` rather than spawning duplicate rows.

## 5. Security & Isolation Rules
- **Customer Role Scoping**: `CUSTOMER` users receive HTTP 403 Forbidden across all internal endpoints (`/analytics/*`, `/reports/*`, `/deal-health*`, `/deal-alerts*`).
- **Data Leak Prevention**: Internal fields (`margin_pct`, `blended_risk_score`, `unit_cost`) are omitted from all customer portal schemas.
