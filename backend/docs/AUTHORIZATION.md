# DealFlow360 Authorization Architecture

This document describes the core authorization architecture for the DealFlow360 B2B Sales Operations Platform.

---

## 1. What is Authorization?

Authorization is the security process that determines whether an authenticated entity has permission to perform a specific action or access a specific resource. While **Authentication** verifies identity, **Authorization** enforces operational scope and access boundaries.

---

## 2. Authentication vs Authorization

| Aspect | Authentication | Authorization |
| :--- | :--- | :--- |
| **Question** | "Who are you?" | "What are you allowed to do?" |
| **Responsibility** | Credentials, Passwords, JWT Tokens | Roles, Policy Rules, Permissions |
| **Handling Unit** | `POST /api/v1/auth/login`, `get_current_user` | `require_roles(...)` |
| **Failure HTTP Status** | `401 Unauthorized` | `403 Forbidden` |

---

## 3. What is RBAC?

**Role-Based Access Control (RBAC)** is an authorization mechanism where access permissions are grouped into **Roles** (such as `SALES_REP` or `SALES_MANAGER`), and users are assigned specific roles. System endpoints evaluate the current user's role against allowed roles to grant or deny access.

---

## 4. Architectural Flow

```
HTTP Request
      ↓
Authorization: Bearer <JWT>
      ↓
get_current_user (Authentication Layer)
      ↓
Validate & Decode JWT sub
      ↓
Fetch fresh User + Role from PostgreSQL
      ↓
Current User (Authenticated)
      ↓
require_roles(*allowed_roles) (Authorization Layer)
      ↓
User Role permitted?
   ↙            ↘
 YES            NO
  ↓              ↓
Return User   HTTP 403 Forbidden ("Insufficient permissions")
  ↓
Endpoint Logic
```

---

## 5. What does `require_roles` Do?

`require_roles(*allowed_roles)` is a FastAPI dependency factory defined in `app/api/dependencies/rbac.py`.

Key operational traits:
1. **Depends on `get_current_user`**: Reuses existing authentication state without duplicating token decoding or user lookup.
2. **Evaluates `user.role`**: Reads the user's role loaded freshly from PostgreSQL.
3. **Multi-Role Support (OR Logic)**: Passes if the user's role matches **any** of the allowed roles.
4. **Returns `User`**: If authorized, yields the authenticated `User` object for downstream endpoint auditing.
5. **Raises 403**: If the user lacks an allowed role or if the user's role relationship is missing, raises `HTTP 403 Forbidden` with detail `"Insufficient permissions"`.

---

## 6. Why Role Comes From PostgreSQL & Why Role is NOT in JWT

- **Role Source of Truth**: The `roles` table in PostgreSQL is the sole source of truth.
- **Why NOT in JWT**: Storing role claims inside a stateless JWT creates a security vulnerability: if an Administrator updates a user's role (e.g. demoting a `SALES_MANAGER` to `SALES_REP`), a JWT containing the old role claim would remain valid until token expiration.
- **Real-Time Revocation/Promotion**: By resolving `User.role` from PostgreSQL on every request inside `get_current_user`, role changes take effect immediately without requiring user re-authentication or token revocation.

---

## 7. 401 vs 403 HTTP Response Semantics

- **HTTP 401 Unauthorized**: Returned when authentication cannot be established.
  - Examples: Missing Bearer token, expired JWT, malformed JWT, non-existent user.
- **HTTP 403 Forbidden**: Returned when authentication succeeds, but authorization fails.
  - Examples: Authenticated `SALES_REP` attempting a `SALES_MANAGER` action, inactive user.

---

## 8. Why ADMIN Access is Explicit (Least Privilege)

DealFlow360 does **NOT** implement an implicit "ADMIN always wins" bypass in `require_roles`. 

- **Explicit Security Policy**: Every protected route must explicitly specify all allowed roles, e.g. `require_roles(RoleName.ADMIN, RoleName.SALES_MANAGER)`.
- **Least Privilege & Visibility**: Explicit declaration makes authorization policies readable, auditable, and prevents accidental bypasses in sensitive operations.

---

## 9. Why Frontend Role Hiding is NOT Security

- **Frontend Role Hiding (UX)**: Hiding or disabling UI buttons for unauthorized roles improves user experience by preventing invalid actions.
- **Backend Enforcement (Security)**: Any client can forge HTTP requests bypassing the UI completely. The backend `require_roles` dependency is the **only authoritative security boundary**.

---

## 10. Canonical DealFlow360 Roles

DealFlow360 defines five standard development roles:

1. **`ADMIN`**: Platform administrator managing users and system configuration.
2. **`SALES_REP`**: Operational sales representative creating and managing deal pipelines/quotations.
3. **`SALES_MANAGER`**: Sales manager reviewing, approving, and overseeing team sales operations.
4. **`FINANCE_OPERATIONS`**: Finance team member handling billing, payments, and margin approvals.
5. **`CUSTOMER`**: External B2B customer interacting with customer-facing portals.
