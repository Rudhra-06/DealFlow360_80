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

### E. HTTP Transport Layer (Phase 1 — Part 9)
Phase 1 Part 9 exposes `AuthenticationService` and JWT validation through HTTP endpoints (`POST /api/v1/auth/login`, `GET /api/v1/auth/me`) and the `get_current_user` FastAPI dependency.

---

## 4. HTTP API Endpoints & Security Dependency

### A. Login Endpoint (`POST /api/v1/auth/login`)
- **Request Body**: `LoginRequest` (`email: EmailStr`, `password: str`)
- **Response**: `TokenResponse` (`access_token: str`, `token_type: "bearer"`)
- **Status Codes**:
  - `200 OK`: Valid credentials, returns access token.
  - `401 Unauthorized`: Invalid credentials (wrong password or unknown email). Detail: `"Invalid email or password"`.
  - `403 Forbidden`: Inactive user account. Detail: `"User account is inactive"`.
  - `422 Unprocessable Entity`: Validation failure (malformed email or empty body).

### B. Bearer Security Dependency (`get_current_user`)
Located in [`backend/app/api/dependencies/auth.py`](file:///c:/Users/Nami..%21%21/DealFlow360_80/backend/app/api/dependencies/auth.py):
1. Extracts Bearer token from `Authorization: Bearer <token>` header via `HTTPBearer(auto_error=True)`.
2. Decodes JWT token using `decode_access_token(token)`.
3. Converts `sub` claim to integer user ID (`int(payload["sub"])`).
4. Re-validates active user and loads role from PostgreSQL using `UserRepository.get_by_id(db, user_id, load_role=True)`.
5. Ensures fresh user entity and role verification on every request.

### C. Current User Endpoint (`GET /api/v1/auth/me`)
- **Headers**: `Authorization: Bearer <token>`
- **Response**: `UserRead` (`id`, `email`, `full_name`, `is_active`, `role_id`, `role`)
- **Security**: Password hash (`hashed_password`) is **never** exposed in responses.
- **Status Codes**:
  - `200 OK`: Returns authenticated user details with loaded role.
  - `401 Unauthorized`: Missing token, invalid signature/format, expired token, or user missing.
  - `403 Forbidden`: User account is deactivated.

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
