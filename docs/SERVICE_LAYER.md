# DealFlow360 — Service Layer Architecture

This document defines the Service Layer design, business workflow orchestration, password security rules, and transaction ownership boundaries for DealFlow360 (Phase 1 — Part 7).

---

## 1. Architectural Layers & Workflow Flow

```text
                                  APPLICATION RUNTIME
   Future API Route ──► UserService ──► UserRepository ──► AsyncSession ──► PostgreSQL
```

```text
                               PASSWORD SECURITY FLOW
   Plain Password ──► UserService ──► hash_password() ──► hashed_password ──► UserRepository ──► PostgreSQL
```

---

## 2. Core Concepts & Definitions

### WHAT IS A SERVICE?
A Service (`UserService`, `RoleService`) is a business orchestration class residing between the API presentation layer and data repositories. It enforces business rules (email normalization, duplicate validation, entity existence checks, security transformations) and manages database transaction boundaries (`commit()` / `rollback()`).

### SERVICE VS REPOSITORY
- **Repository** (`UserRepository`, `RoleRepository`): Handles low-level database operations (queries, filtering, `db.add()`, `await db.flush()`). Repositories **never** call `commit()`.
- **Service** (`UserService`, `RoleService`): Coordinates multi-step business logic and owns transaction commits.

### WHY SERVICES CONTROL TRANSACTIONS
In B2B sales operations, business actions span multiple entities (e.g. confirming a quote creates an order, reserves warehouse inventory, schedules billing, and posts audit logs). If repository calls committed independently, a failure mid-way would leave partial, corrupt data in PostgreSQL. Controlling transactions in the Service Layer allows calling multiple repositories and committing everything together atomically (`await db.commit()`) or rolling back cleanly (`await db.rollback()`).

### WHERE PASSWORD HASHING OCCURS
Password hashing occurs strictly inside the Service Layer (`UserService.create_user`) using the [`app.core.security`](file:///c:/Users/Nami..%21%21/DealFlow360_80/backend/app/core/security.py) utility before creating persistence data objects.

### WHY REPOSITORIES RECEIVE `hashed_password`
`UserRepository.create_user()` expects `UserCreateInternal` containing `hashed_password`. This guarantees that repositories and SQL database queries operate exclusively on secure, already-hashed password digests. Plain text passwords never touch the repository layer.

---

## 3. Step-by-Step User Creation Workflow

```text
1. API Route passes email, full_name, plain_password, role_id to UserService.create_user()
                                      │
                                      ▼
2. UserService normalizes email (whitespace stripped, lowercased)
                                      │
                                      ▼
3. UserRepository.get_by_email(normalized_email) checks for duplicate
   └── If found: raises UserAlreadyExistsError (Domain Exception)
                                      │
                                      ▼
4. RoleRepository.get_by_id(role_id) verifies role existence
   └── If missing: raises RoleNotFoundError (Domain Exception)
                                      │
                                      ▼
5. hash_password(plain_password) generates bcrypt salted digest ($2b$...)
                                      │
                                      ▼
6. UserCreateInternal schema built with hashed_password
                                      │
                                      ▼
7. UserRepository.create_user(user_in) executes db.add(user) and await db.flush()
                                      │
                                      ▼
8. UserService executes await db.commit() and await db.refresh(user)
                                      │
                                      ▼
9. Returns created User ORM instance (API layer converts to UserRead, omitting hash)
```

---

## 4. Email Normalization Policy

To prevent case-variant duplicate accounts (e.g. `User@Example.com` vs `user@example.com`), all input email strings are normalized before querying or persisting:
```python
normalized_email = email.strip().lower()
```

---

## 5. Domain Exception Hierarchy

Service layer exceptions are pure Python domain errors inheriting from `ServiceError` (defined in [`app.services.exceptions`](file:///c:/Users/Nami..%21%21/DealFlow360_80/backend/app/services/exceptions.py)). They contain zero HTTP or FastAPI dependencies, allowing services to be tested and executed independently of web frameworks.
