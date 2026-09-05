# DealFlow360 — Repository Layer Architecture

This document defines the Repository Layer design, patterns, and transaction strategies for DealFlow360 (Phase 1 — Part 6).

---

## 1. Architecture Flow

```text
  FastAPI Route (API Layer)
           │
           ▼
  Service Layer (Business Rules & Transaction Boundary)
           │
           ▼
  Repository Layer (Persistence & Query Abstraction)
           │
           ▼
  AsyncSession (SQLAlchemy 2.x ORM)
           │
           ▼
  asyncpg (Database Driver)
           │
           ▼
  PostgreSQL (Transactional Database)
```

---

## 2. What is a Repository & Why We Use It

A **Repository** is an abstraction layer that handles database access and persistence operations for domain entities. It encapsulates all low-level SQLAlchemy queries, `select()` statements, filters, and joining/loading logic behind clean async methods (`get_by_id`, `get_by_email`, `list_roles`, `create_user`).

### Key Benefits:
- **Separation of Concerns**: Prevents database query logic from bleeding into API routes or business services.
- **Testability**: Allows domain services to be tested by mocking repository interfaces or running isolated transaction tests.
- **Maintainability**: Centralizes database access patterns. If a model query or index changes, only the repository needs modification.

---

## 3. Difference Between Repository and Service

| Aspect | Repository Layer | Service Layer |
| :--- | :--- | :--- |
| **Primary Focus** | Persistence & Database Retrieval | Business Logic & Workflow Coordination |
| **Questions Answered** | *"How do I fetch this user by email?"* | *"Can this user approve a quotation?"* |
| **Transaction Ownership** | Performs `add()` / `flush()`, does **not** commit | Controls `commit()` and `rollback()` boundaries |
| **Business Rules** | **NONE**. Strictly persistence operations. | Enforces policies, risk scores, and authorizations |

### Example Comparison:
- **`UserRepository.get_by_email()`**: Constructs `select(User).where(User.email == email)` and returns the `User` ORM instance. It does **not** verify passwords or generate JWT tokens.
- **`AuthenticationService.login()`**: Calls `UserRepository.get_by_email()`, verifies the hashed password, checks `is_active`, and generates a JWT access token.

---

## 4. What Should NEVER Go Into a Repository

1. **Business Authorization & Rules**: Never check permissions like "Sales Representative cannot give 30% discount" in a repository.
2. **Password Verification & Hashing**: Password hashing and comparisons belong in security/service modules.
3. **HTTP Status Codes or Exceptions**: Do not raise `HTTPException(404)` or return FastAPI response objects from repositories. Return Python domain models or `None`.
4. **Arbitrary Auto-Commits**: Do not call `db.commit()` inside every repository helper method.

---

## 5. Repository Implementations

### `BaseRepository[ModelType]` (`app/repositories/base.py`)
A lightweight, generic base repository providing standard CRUD helper primitives:
- `get_by_id(db, id)`: Fetches a single record by primary key.
- `list(db, limit, offset)`: Retrieves records with pagination support.
- `add(db, obj)`: Adds an ORM instance to the session and calls `flush()`.
- `delete(db, obj)`: Removes an ORM instance from the session and calls `flush()`.

### `RoleRepository` (`app/repositories/role.py`)
Provides focused operations for the `Role` entity:
- `get_by_name(db, name)`: Retrieves a role by classification (`ADMIN`, `SALES_REP`, `SALES_MANAGER`, `FINANCE_OPERATIONS`, `CUSTOMER`).
- `list_roles(db)`: Returns all roles ordered by ID.
- `create_role(db, role_create)`: Instantiates and flushes a new `Role` record.

### `UserRepository` (`app/repositories/user.py`)
Provides focused operations for the `User` entity:
- `get_by_id(db, user_id, load_role=False)`: Retrieves a user by primary key with optional eager loading of `Role`.
- `get_by_email(db, email, load_role=False)`: Retrieves a user by unique email with optional eager loading of `Role`.
- `list_users(db, load_role=False, limit, offset)`: Returns paginated user lists.
- `get_users_by_role(db, role_id, load_role=False)`: Fetches all users assigned to a specific role.
- `create_user(db, user_create)`: Instantiates and flushes a new `User` record from `UserCreateInternal`.

---

## 6. Transaction Ownership Strategy

In DealFlow360, complex business workflows require multi-step atomic operations. For example, confirming a deal involves:
1. Updating Quotation status $\rightarrow$ `QuotationRepository`
2. Reserving stock in warehouse $\rightarrow$ `InventoryRepository`
3. Generating initial invoice $\rightarrow$ `InvoiceRepository`

If step 3 fails, steps 1 and 2 must roll back.

### Strategy:
- **Repository**: Adds models to the session (`db.add()`), calls `await db.flush()` to populate primary key IDs and server default timestamps, but **does not commit**.
- **Service Layer**: Manages the `AsyncSession` context, calling `await db.commit()` at the end of successful workflows, or `await db.rollback()` on exceptions.

---

## 7. Async Relationship Loading & `selectinload`

In SQLAlchemy 2.x async mode, accessing unloaded relationships lazily outside an active session thread raises `MissingGreenlet` or awaitable attribute errors.

### Loading Strategies:
- **Lazy Loading**: Defers loading related entities until accessed. Avoided in async mode unless explicitly managed.
- **Eager Loading (`selectinload`)**: Emits a secondary `SELECT` statement in the same async task to populate relationship attributes (`User.role`).

`UserRepository` methods accept `load_role: bool = False` to eagerly load `selectinload(User.role)` only when requested by the caller, preventing unnecessary database join overhead when role information is not required.
