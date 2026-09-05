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
The `CUSTOMER` role is registered in `Role.name`. However, because the `Customer` business model does not exist yet in Phase 1, no foreign key (`customer_id`) is defined on `User` at this stage. A dedicated relationship (`User` $\leftrightarrow$ `Customer`) will be introduced in subsequent customer portal phases.
