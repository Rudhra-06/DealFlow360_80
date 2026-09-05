# DealFlow360 — Reviewer Demo Runbook

## Pre-Demo Preparation Commands

Execute in PowerShell inside `backend` directory:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m alembic upgrade head
python scripts/bootstrap_full_demo.py
python -m pytest -q
python -m uvicorn app.main:app --reload
```

---

## 5-Minute Golden Path Demo Sequence

1. **00:00 — Authenticate & Overview**
   - Login as `salesrep.demo@example.com` (`POST /api/v1/auth/login`).
   - Call `GET /api/v1/system/demo-readiness` to demonstrate 100% backend system readiness.

2. **00:45 — Quote Economics & Pricing**
   - Create quote for Omega Corporation (`DEMO-CUST-OMEGA`).
   - Add Enterprise Laptop Pro (qty 6) and 24/7 Enterprise Support Plan (qty 1).
   - Apply 15% discount. Show server-side pricing, margin calculation, and risk scoring.

3. **01:30 — Approval Workflow**
   - Submit quote (`POST /api/v1/quotations/{id}/submit`).
   - Quote moves to `PENDING_MANAGER_APPROVAL`.
   - Login as `manager.demo@example.com` and approve. Quote becomes `APPROVED`.
   - Send quote to customer (`SENT_TO_CUSTOMER`).

4. **02:30 — Customer Portal & Negotiation**
   - Login as `customer.demo@example.com`.
   - View customer-safe portal quote (`GET /api/v1/portal/quotations/{id}`). Demonstrate zero internal margin/risk data leak.
   - Submit counteroffer request for additional discount.
   - Login as Sales Rep and accept counteroffer. System creates Version 2, routes reapproval, and returns to `SENT_TO_CUSTOMER`.

5. **03:30 — Customer Confirmation & Multi-Warehouse Fulfillment**
   - Customer confirms Version 2 (`POST /api/v1/portal/quotations/{id}/confirm`).
   - Backend transaction creates `SalesOrder`, allocates stock across Main Warehouse (3 laptops) and East Depot (3 laptops), and locks stock.

6. **04:15 — Hybrid Billing, Payments & Deal Health**
   - Demonstrate generated `ONE_TIME` hardware invoice and `ACTIVE` subscription.
   - Record customer payment (`POST /api/v1/payments`).
   - Trigger Deal Health scan (`POST /api/v1/deal-health/run-scan`).
   - View consolidated Customer 360 profile (`GET /api/v1/analytics/customers/{id}/360`).
   - Export Customer 360 PDF report (`POST /api/v1/reports/export`).
