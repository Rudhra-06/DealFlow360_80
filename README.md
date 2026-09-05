# DealFlow360 — Intelligent Commercial Orchestration Engine

DealFlow360 is an enterprise commercial orchestration backend built with FastAPI, Async SQLAlchemy, and PostgreSQL. It manages the complete Order-to-Cash commercial lifecycle: quote building, pricing/margin/risk calculation, multi-level approvals, customer portal negotiation, multi-warehouse stock reservation & fulfillment, hybrid one-time & subscription billing, deal health anomaly detection, and executive analytics/reporting (PDF/XLSX).

---

## Technical Stack & Architecture
- **Framework**: FastAPI (Async Python 3.11+)
- **Database**: PostgreSQL (AsyncSession via SQLAlchemy + asyncpg)
- **Migrations**: Alembic (Single linear revision chain)
- **Security**: PyJWT, bcrypt password hashing, Database-backed RBAC (`ADMIN`, `SALES_MANAGER`, `SALES_REP`, `FINANCE_OPERATIONS`, `CUSTOMER`)
- **Export Engines**: ReportLab (PDF), openpyxl (XLSX with formula injection protection)
- **Real-time**: WebSockets & Database Notification persistence

---

## Quick Start & Verification

### 1. Database Setup & Migration
```powershell
cd backend
python -m alembic upgrade head
python -m alembic current
python -m alembic heads
```

### 2. Run Test Suite
```powershell
python -m compileall app scripts
python -m pytest -q
```

### 3. Bootstrap Demo Data
```powershell
python scripts/bootstrap_full_demo.py
```

### 4. Check Demo Readiness & Start Backend
```powershell
python -m uvicorn app.main:app --reload
```
Open interactive OpenAPI documentation at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

## Reviewer Demo Credentials
Default demo password: `DealFlow360Demo123!` (or set `DEMO_USER_PASSWORD` environment variable).

- **Admin**: `admin.demo@example.com`
- **Sales Manager**: `manager.demo@example.com`
- **Finance Operations**: `finance.demo@example.com`
- **Sales Rep**: `salesrep.demo@example.com`
- **Customer Contact**: `customer.demo@example.com`

---

## Complete Project Documentation
- [`docs/FINAL_ARCHITECTURE.md`](file:///c:/Users/Nami..%21%21/DealFlow360_80/docs/FINAL_ARCHITECTURE.md)
- [`docs/END_TO_END_DATA_FLOW.md`](file:///c:/Users/Nami..%21%21/DealFlow360_80/docs/END_TO_END_DATA_FLOW.md)
- [`docs/CORE_BUSINESS_RULES.md`](file:///c:/Users/Nami..%21%21/DealFlow360_80/docs/CORE_BUSINESS_RULES.md)
- [`docs/DEMO_RUNBOOK.md`](file:///c:/Users/Nami..%21%21/DealFlow360_80/docs/DEMO_RUNBOOK.md)
- [`docs/REVIEWER_FAQ.md`](file:///c:/Users/Nami..%21%21/DealFlow360_80/docs/REVIEWER_FAQ.md)
- [`docs/CUSTOMER_360.md`](file:///c:/Users/Nami..%21%21/DealFlow360_80/docs/CUSTOMER_360.md)
- [`docs/PHASE_6_PART1_DEAL_HEALTH.md`](file:///c:/Users/Nami..%21%21/DealFlow360_80/docs/PHASE_6_PART1_DEAL_HEALTH.md)
- [`docs/PHASE_6_PART2_ANALYTICS.md`](file:///c:/Users/Nami..%21%21/DealFlow360_80/docs/PHASE_6_PART2_ANALYTICS.md)
