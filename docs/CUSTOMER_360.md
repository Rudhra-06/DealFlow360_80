# Customer 360 Architecture & API Reference

## Overview
The Customer 360 endpoint (`GET /api/v1/analytics/customers/{customer_id}/360`) consolidates all commercial, operational, health, and financial data for a single customer into a single response.

## Data Structure
1. **Profile**: Master customer data, tier, assigned sales rep, creation date.
2. **Commercial Summary**: Quotation counts, confirmation rate, average discount, average margin, confirmed value by currency.
3. **Deal Health**: Latest health score, health level, open alerts, top signals, last activity timestamp.
4. **Orders & Fulfillment**: Order count, open orders, in-fulfillment count, backordered count, latest order number.
5. **Billing & Receivables**: Invoice counts, outstanding balance by currency, overdue invoices, credit notes.
6. **Subscriptions**: Active subscriptions, MRR by currency, next billing date.
7. **Activity Timeline**: Unified 20 most recent timeline events (quote created, order created, invoice issued, etc.).

## Security
- `CUSTOMER` role: HTTP 403 Forbidden.
- `SALES_REP` role: Restricted to assigned customers only. HTTP 403 Forbidden if attempting to access unassigned customer profile.
- `SALES_MANAGER` & `ADMIN`: Access across all customer profiles.
