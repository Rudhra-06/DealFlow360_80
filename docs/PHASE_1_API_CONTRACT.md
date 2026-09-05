# DealFlow360 — Phase 1 API Contract & Handoff Guide

This document defines the formal HTTP API contract for Phase 1 of DealFlow360.

---

## Base URL
- **Local Development**: `http://127.0.0.1:8000`
- **API v1 Prefix**: `/api/v1`
- **Interactive OpenAPI Documentation**: `http://127.0.0.1:8000/docs`

---

## Endpoints

### 1. Root Health Check
- **Method**: `GET`
- **Path**: `/health`
- **Auth Required**: None
- **Response `200 OK`**:
  ```json
  {
    "status": "healthy",
    "service": "DealFlow360 API"
  }
  ```

---

### 2. API v1 Health Check
- **Method**: `GET`
- **Path**: `/api/v1/health`
- **Auth Required**: None
- **Response `200 OK`**:
  ```json
  {
    "status": "healthy",
    "service": "DealFlow360 API"
  }
  ```

---

### 3. Database Connectivity Health Check
- **Method**: `GET`
- **Path**: `/api/v1/health/db`
- **Auth Required**: None
- **Response `200 OK`**:
  ```json
  {
    "status": "healthy",
    "database": "connected"
  }
  ```
- **Response `503 Service Unavailable`** (Database disconnected):
  ```json
  {
    "status": "unhealthy",
    "database": "disconnected",
    "detail": "Database connection unavailable"
  }
  ```

---

### 4. User Login (Issue JWT Access Token)
- **Method**: `POST`
- **Path**: `/api/v1/auth/login`
- **Auth Required**: None
- **Request Body**: `application/json`
  ```json
  {
    "email": "user@example.com",
    "password": "YourSecurePassword123!"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```
- **Response `401 Unauthorized`** (Invalid credentials):
  ```json
  {
    "detail": "Invalid email or password"
  }
  ```
- **Response `403 Forbidden`** (Inactive user account):
  ```json
  {
    "detail": "User account is inactive"
  }
  ```
- **Response `422 Unprocessable Entity`** (Validation error):
  ```json
  {
    "detail": [
      {
        "loc": ["body", "email"],
        "msg": "value is not a valid email address",
        "type": "value_error.email"
      }
    ]
  }
  ```

---

### 5. Get Current Authenticated User Profile
- **Method**: `GET`
- **Path**: `/api/v1/auth/me`
- **Auth Required**: Bearer JWT Token
- **Headers**:
  ```http
  Authorization: Bearer <access_token>
  ```
- **Response `200 OK`**:
  ```json
  {
    "id": 1,
    "email": "admin.demo@example.com",
    "full_name": "Demo Admin User",
    "is_active": true,
    "role_id": 1,
    "created_at": "2026-09-05T14:00:00Z",
    "updated_at": "2026-09-05T14:00:00Z",
    "role": {
      "id": 1,
      "name": "ADMIN",
      "description": "System Administrator with full management access.",
      "created_at": "2026-09-05T14:00:00Z",
      "updated_at": "2026-09-05T14:00:00Z"
    }
  }
  ```
  *(Note: `hashed_password` is securely omitted from output schema)*
- **Response `401 Unauthorized`** (Missing token, invalid token, or expired token):
  ```json
  {
    "detail": "Access token has expired"
  }
  ```
- **Response `403 Forbidden`** (User account inactive):
  ```json
  {
    "detail": "User account is inactive"
  }
  ```

---

## Frontend Integration Notes

1. **Authentication Flow**:
   - The frontend submits credentials (`email`, `password`) to `POST /api/v1/auth/login`.
   - Upon receiving `{ "access_token": "...", "token_type": "bearer" }`, store `access_token` securely (e.g. in memory or secure HTTP cookie).
   - Attach `Authorization: Bearer <access_token>` header to all subsequent API requests.

2. **User Identity & UI Role Customization**:
   - Call `GET /api/v1/auth/me` upon application load.
   - Use returned `role.name` (`ADMIN`, `SALES_REP`, `SALES_MANAGER`, `FINANCE_OPERATIONS`, `CUSTOMER`) to customize navigation items and UI component visibility.
   - **Note**: Frontend role checks are for UX enhancement only; backend RBAC dependencies strictly enforce security on every endpoint.
