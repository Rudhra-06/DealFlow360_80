# DealFlow360 — Phase 1 Backend Architecture Reference

This document provides the canonical architectural reference for Phase 1 of DealFlow360.

---

## 1. Application Layers & Control Flow

```text
Request (HTTP / Client)
       │
       ▼
 FastAPI Route Layer (`app/api/v1/*.py`)
       │
       ├── Pydantic Schemas (`app/schemas/*.py`) — Data Validation
       │
       ▼
 Service Layer (`app/services/*.py`) — Business Logic & Transaction Control
       │
       ▼
 Repository Layer (`app/repositories/*.py`) — Database Queries & Flushing
       │
       ▼
 AsyncSession (SQLAlchemy 2.x Async Engine + asyncpg)
       │
       ▼
 PostgreSQL Database
```

---

## 2. Component Layer Responsibilities

### A. Route Layer (`app/api/v1/`)
- Accepts HTTP requests, parses headers/parameters/bodies against Pydantic schemas.
- Injects FastAPI dependencies (`Depends(get_db)`, `Depends(get_current_user)`, `Depends(require_roles)`).
- Delegates domain operations to Service classes.
- Maps domain exception types (`InvalidCredentialsError`, `UserAlreadyExistsError`, `RoleNotFoundError`, etc.) to explicit HTTP status codes (400, 401, 403, 404, 409).
- Returns validated Pydantic response models.

### B. Security & Authentication Dependencies (`app/api/dependencies/`)
- `get_current_user`: Extracts Bearer token from `Authorization: Bearer <token>`, decodes JWT via `decode_access_token`, converts `sub` to integer user ID, re-verifies user existence and loads role from PostgreSQL using `UserRepository.get_by_id(db, user_id, load_role=True)`.
- `require_roles(*allowed_roles)`: Enforces RBAC permissions based on the active user's database-persisted role (`user.role.name`).

### C. Service Layer (`app/services/`)
- Encapsulates business logic, email normalization, password hashing, and transaction boundaries.
- **Transaction Ownership**: Service methods execute database operations and invoke `await db.commit()` / `await db.rollback()`.
- Prevents invalid business state transitions and raises domain-specific `ServiceError` subclasses.

### D. Repository Layer (`app/repositories/`)
- Performs raw data access and SQLAlchemy ORM query construction.
- **No Commit Rule**: Repositories invoke `await db.flush()` to generate primary key IDs or check database constraints within an open transaction, but **NEVER** call `db.commit()`.

### E. Persistence Layer (`app/models/`, `app/db/`)
- SQLAlchemy 2.x Mapped models (`Role`, `User`).
- Async engine (`create_async_engine`) using `asyncpg` database driver.
- Schema migrations managed exclusively by Alembic.

---

## 3. Security Architecture & JWT Infrastructure

### A. Password Security
- Passwords are processed using `bcrypt` via `app.core.security`.
- Plain-text passwords exist only transiently in memory during user creation or login authentication.
- `hashed_password` is stored in PostgreSQL and **never** returned in API responses or written to log outputs.

### B. Authentication Flow (`POST /api/v1/auth/login`)
1. Accepts `LoginRequest` (`email`, `password`).
2. Normalizes email (`strip().lower()`).
3. Fetches user from PostgreSQL via `UserRepository.get_by_email()`.
4. Verifies password against `user.hashed_password` using `verify_password()`.
5. Verifies `user.is_active is True`.
6. Generates signed JWT access token containing claims: `sub` (User ID), `type` ("access"), `iat` (timestamp), `exp` (timestamp).
7. Returns `TokenResponse` (`access_token`, `token_type="bearer"`).

> [!IMPORTANT]
> **Anti-User Enumeration Protection**
> Both missing email and invalid password raise identical `InvalidCredentialsError` mapped to `HTTP 401 Unauthorized` with detail `"Invalid email or password"`.

### C. Why `Role` is NOT Embedded in JWT Claims
- **Freshness & Revocation**: If an administrator changes a user's role in PostgreSQL (or deactivates the account), embedding role/active status inside JWT claims would cause stale permissions to persist until token expiration.
- **Design Decision**: The JWT payload contains only `sub` (User ID). `get_current_user` queries PostgreSQL on every request to ensure role permissions and active status are always up to date.

---

## 4. Test Architecture & Database Isolation

- **Runner**: `pytest` + `pytest-asyncio` / `anyio`.
- **Database Isolation Strategy**: Tests execute inside an outer connection transaction with `join_transaction_mode="create_savepoint"`.
- **Zero Pollution**: Service layer `db.commit()` calls operate on nested `SAVEPOINT`s. Upon test teardown, the outer transaction rolls back completely, leaving zero persistent test records in PostgreSQL.
- **Self-Contained**: Automated tests do **not** depend on `seed_roles.py` or `bootstrap_demo_users.py`.

---

## 5. Team & Database Workflow

- **Tracked in Git**: Code, SQLAlchemy models, Alembic migrations (`alembic/`), `requirements.txt`, `.env.example`, tests, documentation.
- **Local to Developer**: `backend/.env`, `venv/`, PostgreSQL database credentials, `JWT_SECRET_KEY`, `DEMO_USER_PASSWORD`.
- **Alembic**: Synchronizes database table structure (`python -m alembic upgrade head`).
- **Bootstrap Script**: Optionally seeds reference roles and local demo user accounts (`python scripts/bootstrap_demo_users.py`).
