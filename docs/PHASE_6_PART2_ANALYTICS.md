# DealFlow360 — Phase 6 Part 2 Analytics Overview

## Overview
Phase 6 Part 2 converts transactional facts and health intelligence into an executive reporting suite and Customer 360 platform.

## Core Analytics Endpoints
- `GET /api/v1/analytics/overview` — High-level operational & financial overview (currency-grouped)
- `GET /api/v1/analytics/overview/trend` — Time-series trends (DAY, WEEK, MONTH)
- `GET /api/v1/analytics/quotation-funnel` — Quotation stage breakdown & confirmation rates
- `GET /api/v1/analytics/sales-performance` — Metrics per Sales Rep
- `GET /api/v1/analytics/discounts` — Discount distribution by Rep, Tier, Category
- `GET /api/v1/analytics/margins` — Simple average & value-weighted margins
- `GET /api/v1/analytics/customers/{customer_id}/360` — Consolidated Customer 360 profile
- `GET /api/v1/analytics/products` — Product sales, volumes, and margins
- `GET /api/v1/analytics/product-categories` — Product category breakdown
- `GET /api/v1/analytics/approvals` — Approval turnaround times & cycle metrics
- `GET /api/v1/analytics/negotiations` — Counteroffer acceptance & duration
- `GET /api/v1/analytics/deal-health` — Current deal health distribution & alerts
- `GET /api/v1/analytics/fulfillment` — Order split rates & fulfillment performance
- `GET /api/v1/analytics/receivables` — Outstanding aging buckets (CURRENT, 1-30, 31-60, 61-90, 90+ days)
- `GET /api/v1/analytics/billing` — Billing totals & invoice status counts
- `GET /api/v1/analytics/payments` — Payment totals & methods
- `GET /api/v1/analytics/subscriptions` — MRR and active subscription counts
- `POST /api/v1/reports/export` — PDF and XLSX export generation
- `GET /api/v1/reports/exports` — Report export audit history

## Architecture & Guarantees
- **No Fake Data**: 0 values returned when datasets are empty.
- **Multi-Currency Safety**: Monetary amounts are grouped by currency (`{"USD": 10000.00, "EUR": 5000.00}`). No cross-currency aggregation.
- **Customer Security Isolation**: `CUSTOMER` role yields 403 Forbidden. `SALES_REP` restricted to owned records.
