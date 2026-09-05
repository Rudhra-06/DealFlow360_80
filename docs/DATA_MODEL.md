# DealFlow360 — Data Model Architecture

This document defines the entity-relationship architecture, database schemas, and constraints for DealFlow360 (Phase 1 — Part 5).

---

## 1. Entity-Relationship Overview

```text
+-----------------------+           1 : N           +-----------------------+
|         ROLE          | ────────────────────────< |         USER          |
+-----------------------+                           +-----------------------+
| id (PK)               |                           | id (PK)               |
| name (Unique, Index)  |                           | email (Unique, Index) |
| description           |                           | full_name             |
| created_at            |                           | hashed_password       |
+-----------------------+                           | role_id (FK -> roles) |
                                                    | is_active             |
                                                    | created_at            |
                                                    | updated_at            |
                                                    +-----------------------+
```

---

## 2. Model Definitions

### ROLE Entity (`roles` table)

**Purpose**: Identifies user identity classifications across DealFlow360 business workflows (`ADMIN`, `SALES_REP`, `SALES_MANAGER`, `FINANCE_OPERATIONS`, `CUSTOMER`).

| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | Primary Key, Autoincrement | Unique role surrogate key |
| `name` | String(50) | Required, Unique, Indexed | Role classification identifier |
| `description` | Text | Nullable | Human-readable role description |
| `created_at` | DateTime (TZ) | Required, Server Default `now()` | Record creation timestamp |

**Relationships**:
- `users`: One-to-Many relationship (`Role` $\rightarrow$ `User`). One Role can be assigned to multiple User accounts.

---

### USER Entity (`users` table)

**Purpose**: Represents authenticated application user accounts in the platform.

| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | Primary Key, Autoincrement | Unique user surrogate key |
| `email` | String(255) | Required, Unique, Indexed | User login email address |
| `full_name` | String(255) | Required | Display name of the user |
| `hashed_password` | String(255) | Required | Secure password hash store (Never exposed via API) |
| `role_id` | Integer | Required, FK (`roles.id`), Indexed | Assigned role foreign key |
| `is_active` | Boolean | Required, Default `True` | Account active flag |
| `created_at` | DateTime (TZ) | Required, Server Default `now()` | Account creation timestamp |
| `updated_at` | DateTime (TZ) | Required, On Update `now()` | Account modification timestamp |

**Relationships**:
- `role`: Many-to-One relationship (`User` $\rightarrow$ `Role`). Each User is linked to exactly one Role via `role_id`.

---

## 3. Security & Design Decisions

### Password Security Strategy
- **Field Name**: `hashed_password` (never named `password`).
- **API Isolation**: The Pydantic response schema `UserRead` explicitly omits `hashed_password`. Password hashes are strictly internal database fields.
- **Workflow Isolation**: Actual password hashing (e.g. bcrypt/argon2) will be implemented in future authentication modules. Plain-text passwords are never accepted into database storage.

### Customer Portal Association (Future Scope)
## 4. Phase 2 Data Models

### ER Diagram Architecture

```text
CustomerTier
   │
   ├──< Customer
   │
   ├──< DiscountPolicy
   │
   └──< ApprovalPolicy


ProductCategory
   │
   ├──< Product
   └──< DiscountPolicy


Product
   │
   ├──< Inventory
   └──< DiscountPolicy


BillingPlan
   (Future reference by Quote / QuoteLine)


Warehouse
   └──< Inventory
```

---

### Phase 2 Tables Overview

1. **`customer_tiers`**: Customer tier levels (`GOLD`, `SILVER`, `BRONZE`).
2. **`customers`**: Customer accounts with credit limits, currency, and payment terms.
3. **`product_categories`**: Catalog product categories.
4. **`products`**: Product catalog items with SKU, list price, cost price, and category FK.
5. **`warehouses`**: Storage locations.
6. **`inventory`**: Stock levels per warehouse/product (`on_hand_qty`, `reserved_qty`).
## 5. Phase 3 Data Models

### ER Diagram Architecture

```text
Quotation
   ├──< QuoteLine (FK -> Product, FK -> BillingPlan, FK -> DiscountPolicy)
   ├──< QuoteRiskReason
   └──< QuoteAuditEvent (FK -> User actor)
```

### Phase 3 Tables Overview
1. **`quotations`**: Quotation header records (`quote_number`, `customer_id`, `sales_rep_id`, `status`, `currency`, `order_discount_pct`, financial totals, `blended_risk_score`, `risk_level`).
2. **`quotation_lines`**: Quotation line items (`product_id`, `quantity`, `unit_list_price` snapshot, `unit_cost` snapshot, line discount %, effective discount %, totals, margin %, `resolved_discount_policy_id`, policy snapshots, risk level).
3. **`quote_risk_reasons`**: Transactional explainable risk reasons (`code`, `severity`, `message`, `actual_value`, `threshold_value`).
4. **`quote_audit_events`**: Transaction audit trail (`event_type`, `actor_user_id`, `from_status`, `to_status`, `reason`, `event_metadata`).


