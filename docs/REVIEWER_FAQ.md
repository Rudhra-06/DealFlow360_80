# DealFlow360 — Reviewer FAQ & Technical Architecture QA

### Q1: How does DealFlow360 ensure business calculations are authoritative?
All pricing, margin, risk, approval thresholds, fulfillment stock allocations, billing proration, and deal health scores are computed deterministically on the FastAPI server using `Decimal` arithmetic. The frontend never calculates authoritative financial or business values.

### Q2: How is customer data isolation enforced?
`CUSTOMER` role tokens receive HTTP 403 Forbidden across all internal routes (`/analytics/*`, `/reports/*`, `/deal-health*`, `/deal-alerts*`). Furthermore, internal fields (`margin_pct`, `blended_risk_score`, `unit_cost`) are completely stripped from all customer portal schemas.

### Q3: How does stock reservation work during negotiation versus confirmation?
Stock is NOT reserved while a quote is in draft, approval, or negotiation. Stock reservation occurs transactionally only AFTER explicit customer confirmation (`CUSTOMER_CONFIRMED`).

### Q4: How are multi-currency amounts handled in reporting?
Because DealFlow360 does not maintain an FX conversion engine, monetary metrics are NEVER added together across different currencies. Analytics endpoints return dictionaries mapping currency codes to sums (e.g. `{"USD": 10000.00, "EUR": 5000.00}`).

### Q5: How is report export safety ensured?
XLSX exports sanitize all string fields to prevent spreadsheet formula injection (`=`, `+`, `-`, `@` strings are prefixed with `'`). PDF reports are rendered using ReportLab. All exports record an audit log in `report_export_audits`.
