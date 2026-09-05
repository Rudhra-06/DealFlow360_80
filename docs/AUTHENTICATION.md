# DealFlow360 — Authentication Architecture & JWT Infrastructure

This document defines the authentication architecture, security strategy, and JWT infrastructure for DealFlow360 (Phase 1 — Part 8).

---

## 1. Authentication Flow Diagram

```text
  User Credentials (email, plain_password)
                     │
                     ▼
  AuthenticationService.authenticate_user()
                     │
                     ├─► Email Normalization (strip & lowercase)
                     │
                     ▼
  UserRepository.get_by_email() ──► PostgreSQL
                     │
                     ▼
  User ORM Entity Found?
                     ├─► NO ──► raise InvalidCredentialsError ("Invalid email or password.")
                     │
                     ▼
  verify_password(plain_password, user.hashed_password)
                     ├─► NO ──► raise InvalidCredentialsError ("Invalid email or password.")
                     │
                     ▼
  user.is_active == True?
                     ├─► NO ──► raise InactiveUserError ("User account is inactive.")
                     │
                     ▼
  Authenticated User ORM Instance
                     │
                     ▼
  create_access_token(subject=user.id)
                     │
                     ▼
  Signed JWT Access Token String
```

---

## 2. Security Strategy & Design Decisions

### A. User Enumeration Protection
`AuthenticationService.authenticate_user()` raises the **exact same exception class** (`InvalidCredentialsError`) with identical error details (`"Invalid email or password."`) whether:
1. The requested email does not exist in PostgreSQL.
2. The provided password fails bcrypt verification.

This prevents malicious actors from probing the platform to discover registered email addresses.

### B. Why `Role` is NOT Embedded in JWT Claims
- **JWT Claims**: `sub` (User ID), `type` ("access"), `iat` (issued-at), `exp` (expiration).
- **Rationale**: If a user's role is updated in PostgreSQL by an administrator (e.g. `SALES_REP` $\rightarrow$ `SALES_MANAGER`), embedding the role in the JWT payload would leave stale permissions active until the token expires. By storing only `sub` (User ID) in the token, future `get_current_user` middleware fetches fresh user and role data from PostgreSQL on each request.

### C. JWT Integrity vs. Encryption
> [!IMPORTANT]
> **JWT is Signed, NOT Encrypted**
> 
> A standard JWT payload is `base64url`-encoded text. Anyone holding a JWT can decode and view its claims (`sub`, `iat`, `exp`).
> 
> The security of a JWT relies on its **cryptographic signature** generated using `JWT_SECRET_KEY` and algorithm `HS256`. If an attacker tampers with the payload, signature verification fails upon decoding. Sensitive data (passwords, social security numbers, private customer data) must **never** be placed inside JWT claims.

### D. Why `authenticate_user()` Does Not Commit Transactions
Authentication is a read-and-verify operation. Unlike `UserService.create_user()` which mutates database state, `authenticate_user()` queries PostgreSQL and evaluates password hashes in CPU memory. It does not perform DML statements (`INSERT`, `UPDATE`, `DELETE`) and therefore does not invoke `db.commit()`.

### E. Why HTTP Login Endpoints Are Deferred
Phase 1 Part 8 focuses strictly on building and verifying domain security primitives and `AuthenticationService` below the API layer. HTTP transport logic (`POST /api/v1/auth/login`, `OAuth2PasswordRequestForm`, `Depends(get_current_user)`) will be introduced in subsequent API integration phases.

---

## 3. Core Modules & Exception Hierarchy

### Core Security & JWT Helpers
- [`backend/app/core/security.py`](file:///d:/Hackathons/Odoo/DealFlow360/DealFlow360_80/backend/app/core/security.py): `hash_password(plain)`, `verify_password(plain, hash)`
- [`backend/app/core/jwt.py`](file:///d:/Hackathons/Odoo/DealFlow360/DealFlow360_80/backend/app/core/jwt.py): `create_access_token(subject, expires_delta)`, `decode_access_token(token)`

### Exception Hierarchy ([`backend/app/services/exceptions.py`](file:///d:/Hackathons/Odoo/DealFlow360/DealFlow360_80/backend/app/services/exceptions.py))
```text
ServiceError
 ├── UserAlreadyExistsError
 ├── RoleNotFoundError
 ├── AuthenticationError
 │    ├── InvalidCredentialsError
 │    └── InactiveUserError
 └── TokenError
      └── InvalidTokenError
           └── ExpiredTokenError
```
