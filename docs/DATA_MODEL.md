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
7. **`discount_policies`**: Configurable commercial discount rules and precedence.
8. **`approval_policies`**: Configurable approval threshold triggers and approver roles.
9. **`billing_plans`**: Billing frequency and payment due day definitions (`ONE_TIME`, `RECURRING`).

