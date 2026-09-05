# DealFlow360 — Phase 2 Backend Architecture Reference

This document summarizes the master-data and commercial configuration architecture established in Phase 2.

---

## 1. Phase 2 Component Scope

```text
               ┌──────────────────────────────────────────────┐
               │              PHASE 2 BACKEND                 │
               └──────────────────────┬───────────────────────┘
                                      │
         ┌────────────────────────────┴───────────────────────────┐
         ▼                                                        ▼
 ┌─────────────────────────────┐                         ┌─────────────────────────────┐
 │    CORE MASTER DATA         │                         │   COMMERCIAL CONFIGURATION  │
 ├─────────────────────────────┤                         ├─────────────────────────────┤
 │ • CustomerTier              │                         │ • DiscountPolicy            │
 │ • Customer                  │                         │ • ApprovalPolicy            │
 │ • ProductCategory           │                         │ • BillingPlan               │
 │ • Product                   │                         └─────────────────────────────┘
 │ • Warehouse                 │
 │ • Inventory                 │
 └─────────────────────────────┘
```

---

## 2. Master Data Entities
1. **`CustomerTier`**: Customer classification levels (`GOLD`, `SILVER`, `BRONZE`).
2. **`Customer`**: Account entity linking to `CustomerTier`, with credit limits, currency, and default payment terms.
3. **`ProductCategory`**: Logical product groupings.
4. **`Product`**: Commercial catalog items with SKU, list price, cost price, and category association.
5. **`Warehouse`**: Physical storage locations.
6. **`Inventory`**: Stock balances per warehouse/product pair with `on_hand_qty` and `reserved_qty`.

---

## 3. Commercial Configuration Entities
1. **`DiscountPolicy`**: Tier/category/product-scoped standard & max discount limits.
2. **`ApprovalPolicy`**: Configurable discount, margin, and payment term threshold triggers mapped to required approver roles (`SALES_MANAGER`, `FINANCE_OPERATIONS`).
3. **`BillingPlan`**: Payment term & frequency definitions (`ONE_TIME`, `RECURRING`).

---

## 4. Layered Architectural Pattern

```text
HTTP Request
     │
     ▼
FastAPI Router (`app/api/v1/*.py`)
     │
     ├── Pydantic Schemas (`app/schemas/*.py`) — Input Validation
     │
     ▼
Service Layer (`app/services/*.py`) — Business Logic & Transaction Ownership
     │
     ▼
Repository Layer (`app/repositories/*.py`) — Queries & Flushing (No Commits)
     │
     ▼
AsyncSession (SQLAlchemy 2.x + asyncpg)
     │
     ▼
PostgreSQL Database
```

---

## 5. Security & Isolation Guarantee
- All write operations require valid Bearer JWT authentication and Role-Based Access Control (`require_roles`).
- Automated tests run inside outer connection SAVEPOINT transactions, leaving **zero persistent test records** in PostgreSQL upon test teardown.
