# DealFlow360 Core Master Data Architecture

This document describes the design principles, schema structures, domain validations, decimal precision rules, and RBAC policies for the DealFlow360 Core Business Master Data Platform.

---

## 1. Master Data Entities

The master-data platform manages 6 foundational entities:

1. **`CustomerTier`**: Commercial tier classification (`STANDARD`, `SILVER`, `GOLD`, `PLATINUM`).
2. **`Customer`**: B2B enterprise customer profile containing commercial attributes (`customer_code`, `credit_limit`, `default_payment_terms_days`, `currency`, `tier_id`).
3. **`ProductCategory`**: Product catalog grouping.
4. **`Product`**: Sellable inventory items with pricing and unit specs (`sku`, `list_price`, `cost_price`, `currency`, `unit_of_measure`, `category_id`).
5. **`Warehouse`**: Physical or virtual fulfillment facility (`code`, `name`, `location`, `address`).
6. **`Inventory`**: Stock state junction linking `Warehouse` and `Product` (`on_hand_qty`, `reserved_qty`, `reorder_level`).

---

## 2. Key Domain Validations & Design Decisions

### Decimal Monetary & Quantity Types
- **Monetary Amounts** (`credit_limit`, `list_price`, `cost_price`): Stored as PostgreSQL `Numeric(14, 2)` and Python `Decimal`. Python floats are strictly prohibited to avoid floating-point rounding errors in commercial quote/risk engines.
- **Stock Quantities** (`on_hand_qty`, `reserved_qty`, `reorder_level`): Stored as PostgreSQL `Numeric(14, 3)` and Python `Decimal` to support non-integer units of measure (e.g. KG, Liters).

### Derived Available Quantity
`available_qty = on_hand_qty - reserved_qty` is dynamically calculated in Pydantic schema responses (`InventoryRead`). Storing `available_qty` as a third mutable database column is intentionally avoided to prevent state drift.

### Protected `reserved_qty`
Generic stock update APIs (`PATCH /api/v1/inventory/{id}`) permit updating `on_hand_qty` and `reorder_level` only. Direct client manipulation of `reserved_qty` is rejected; reservation state will be exclusively owned by the Phase 5 Fulfillment Engine.

### Soft Deletion via `is_active`
Physical database record deletion (`DELETE`) is disabled across all master data tables. Inactivating a record via `PATCH is_active=false` preserves historical referential integrity for future quotations, orders, and audit logs.

### Active Reference Protection
Services enforce that new child entities can only be associated with **active** parent resources:
- Creating a `Customer` requires an active `CustomerTier`.
- Creating a `Product` requires an active `ProductCategory`.
- Creating an `Inventory` mapping requires an active `Warehouse` and active `Product`.

---

## 3. RBAC Matrix

| Endpoint | Internal Read Roles | Write / Update Roles | Customer Role |
| :--- | :--- | :--- | :--- |
| `/api/v1/customer-tiers` | `ADMIN`, `SALES_REP`, `SALES_MANAGER`, `FINANCE_OPERATIONS` | `ADMIN`, `SALES_MANAGER` | `403 Forbidden` |
| `/api/v1/customers` | `ADMIN`, `SALES_REP`, `SALES_MANAGER`, `FINANCE_OPERATIONS` | `ADMIN`, `SALES_REP`, `SALES_MANAGER` | `403 Forbidden` |
| `/api/v1/product-categories` | `ADMIN`, `SALES_REP`, `SALES_MANAGER`, `FINANCE_OPERATIONS` | `ADMIN`, `FINANCE_OPERATIONS` | `403 Forbidden` |
| `/api/v1/products` | `ADMIN`, `SALES_REP`, `SALES_MANAGER`, `FINANCE_OPERATIONS` | `ADMIN`, `FINANCE_OPERATIONS` | `403 Forbidden` |
| `/api/v1/warehouses` | `ADMIN`, `SALES_REP`, `SALES_MANAGER`, `FINANCE_OPERATIONS` | `ADMIN`, `FINANCE_OPERATIONS` | `403 Forbidden` |
| `/api/v1/inventory` | `ADMIN`, `SALES_REP`, `SALES_MANAGER`, `FINANCE_OPERATIONS` | `ADMIN`, `FINANCE_OPERATIONS` | `403 Forbidden` |
