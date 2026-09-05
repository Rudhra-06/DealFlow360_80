# DealFlow360 — Repository Layer Architecture

This document defines the Repository Layer design, database access abstraction, and session management boundaries for DealFlow360.

---

## 1. Architectural Role & Responsibilities

The Repository Layer (`BaseRepository`, `RoleRepository`, `UserRepository`) abstracts database operations away from business services:
- **Queries & Filtering**: Encapsulates SQLAlchemy `select()` statements.
- **Session Management**: Adds new ORM instances to `AsyncSession` and executes `await db.flush()`.
- **Transaction Rule**: Repositories **NEVER** call `commit()`. Transaction ownership belongs strictly to the Service Layer.

---

## 2. Key Repository Components

### BaseRepository (`backend/app/repositories/base.py`)
Provides `AsyncSession` reference and `flush()` implementation.

### RoleRepository (`backend/app/repositories/role.py`)
- `get_by_id(role_id: int)`
- `get_by_name(name: str)`
- `list_roles(skip: int, limit: int)`
- `create_role(role_in: RoleCreateInternal)`

### UserRepository (`backend/app/repositories/user.py`)
- `get_by_id(user_id: int)`
- `get_by_email(email: str)`
- `list_users(skip: int, limit: int)`
- `create_user(user_in: UserCreateInternal)`
