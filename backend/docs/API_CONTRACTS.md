# DealFlow360 REST API Contracts

This document specifies the REST API endpoints, request/response formats, query filters, and error codes for master-data operations.

---

## Global API Standards

- **Base URL**: `/api/v1`
- **Authentication**: `Authorization: Bearer <JWT>` required for all master data endpoints.
- **Monetary Serialization**: Formatted as Decimal strings (e.g., `"50000.00"`).
- **Quantity Serialization**: Formatted as Decimal strings (e.g., `"100.000"`).

---

## Endpoints Summary

### 1. Customer Tiers
- `GET /api/v1/customer-tiers?is_active=true&limit=100&offset=0`
- `GET /api/v1/customer-tiers/{tier_id}`
- `POST /api/v1/customer-tiers`
- `PATCH /api/v1/customer-tiers/{tier_id}`

### 2. Customers
- `GET /api/v1/customers?tier_id=1&is_active=true&search=acme&limit=100&offset=0`
- `GET /api/v1/customers/{customer_id}`
- `POST /api/v1/customers`
- `PATCH /api/v1/customers/{customer_id}`

### 3. Product Categories
- `GET /api/v1/product-categories?is_active=true&limit=100&offset=0`
- `GET /api/v1/product-categories/{category_id}`
- `POST /api/v1/product-categories`
- `PATCH /api/v1/product-categories/{category_id}`

### 4. Products
- `GET /api/v1/products?category_id=2&is_active=true&search=SKU-001&limit=100&offset=0`
- `GET /api/v1/products/{product_id}`
- `POST /api/v1/products`
- `PATCH /api/v1/products/{product_id}`

### 5. Warehouses
- `GET /api/v1/warehouses?is_active=true&limit=100&offset=0`
- `GET /api/v1/warehouses/{warehouse_id}`
- `POST /api/v1/warehouses`
- `PATCH /api/v1/warehouses/{warehouse_id}`

### 6. Inventory
- `GET /api/v1/inventory?warehouse_id=1&product_id=5&limit=100&offset=0`
- `GET /api/v1/inventory/{inventory_id}`
- `POST /api/v1/inventory`
- `PATCH /api/v1/inventory/{inventory_id}`

### 7. Discount Policies
- `GET /api/v1/discount-policies?customer_tier_id=1&product_id=5&is_active=true&effective_only=true&limit=100&offset=0`
- `GET /api/v1/discount-policies/resolve?customer_tier_id=1&product_id=5`
- `GET /api/v1/discount-policies/{policy_id}`
- `POST /api/v1/discount-policies`
- `PATCH /api/v1/discount-policies/{policy_id}`

### 8. Approval Policies
- `GET /api/v1/approval-policies?customer_tier_id=1&approval_role=SALES_MANAGER&is_active=true&effective_only=true&limit=100&offset=0`
- `GET /api/v1/approval-policies/{policy_id}`
- `POST /api/v1/approval-policies`
- `PATCH /api/v1/approval-policies/{policy_id}`

### 9. Billing Plans
- `GET /api/v1/billing-plans?billing_type=RECURRING&is_active=true&limit=100&offset=0`
- `GET /api/v1/billing-plans/{plan_id}`
- `POST /api/v1/billing-plans`
- `PATCH /api/v1/billing-plans/{plan_id}`

---

## Example Payload & Response Formats

### Customer Response (`CustomerRead`)
```json
{
  "id": 10,
  "customer_code": "CUST-0001",
  "name": "Acme Global Enterprise",
  "email": "procurement@acmeglobal.com",
  "phone": "+1-555-0199",
  "tier_id": 2,
  "billing_address": "100 Corporate Way, NY",
  "shipping_address": "200 Logistics Blvd, NJ",
  "default_payment_terms_days": 30,
  "credit_limit": "50000.00",
  "currency": "USD",
  "is_active": true,
  "created_at": "2026-09-05T15:00:00Z",
  "updated_at": "2026-09-05T15:00:00Z",
  "tier": {
    "id": 2,
    "name": "GOLD",
    "description": "Gold Tier Partner",
    "is_active": true,
    "created_at": "2026-09-05T14:00:00Z",
    "updated_at": "2026-09-05T14:00:00Z"
  }
}
```

### Discount Policy Resolution Response (`DiscountPolicyResolutionRead`)
```json
{
  "applicable_policy": {
    "id": 5,
    "name": "Gold Tier Hardware Discount",
    "customer_tier_id": 2,
    "product_category_id": null,
    "product_id": 10,
    "standard_discount_pct": "10.00",
    "max_discount_pct": "20.00",
    "priority": 50,
    "effective_from": "2026-09-05T00:00:00Z",
    "effective_to": null,
    "is_active": true,
    "created_at": "2026-09-05T16:00:00Z",
    "updated_at": "2026-09-05T16:00:00Z"
  },
  "specificity_level": "tier+product"
}
```

---

## Standard Error Responses

- **400 Bad Request**: Invalid/inactive entity reference, quantity validation failure, or policy parameter conflict.
- **401 Unauthorized**: Missing, expired, or invalid Bearer JWT token.
- **403 Forbidden**: Authenticated user role lacks required permissions (or `CUSTOMER` role).
- **404 Not Found**: Resource primary key does not exist.
- **409 Conflict**: Duplicate unique constraint (code, SKU, email, billing plan code) or ambiguous overlapping policy.
