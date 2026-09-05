# DealFlow360 — Phase 5 Order-to-Cash Backend Architecture

## Overview
Phase 5 converts a commercially approved and `CUSTOMER_CONFIRMED` quotation into an operational sales order and completes the full Order-to-Cash transaction lifecycle:
1. **Confirmed Quotation → Sales Order Conversion** with version traceability (`confirmed_version_id`).
2. **Intelligent Multi-Warehouse Fulfillment & Reservation**: Optimization engine allocating stock across multiple warehouses based on priority, shipping weight, and base costs.
3. **Manual Fulfillment Overrides & Backorder Handling**: Operational flexibility to override allocations and generate tracked backorder items.
4. **Shipment Execution & Physical Inventory Consumption**: Multi-line shipment dispatch updating inventory `on_hand_qty` and `reserved_qty`.
5. **Hybrid Billing Engine**: Simultaneous support for one-time order line invoices and recurring subscription schedules.
6. **Subscription Management & Mid-Cycle Proration Engine**: Exact day-granularity proration calculations on quantity upgrades/downgrades and plan cancellations.
7. **Credit Notes & Payments**: Credit note issuance, application to outstanding balances, and atomic payment recording with overpayment prevention.

---

## Data Models & Schema

### Sales Orders & Lines
- `sales_orders`: `id`, `order_number`, `quotation_id`, `confirmed_version_id`, `customer_id`, `sales_rep_id`, `currency`, `total_gross_amount`, `total_discount_amount`, `total_net_amount`, `status`, `created_at`, `updated_at`.
- `sales_order_lines`: `id`, `sales_order_id`, `quotation_line_id`, `product_id`, `billing_plan_id`, `ordered_qty`, `unit_list_price`, `unit_cost`, `line_discount_pct`, `gross_line_total`, `discount_amount`, `net_line_total`, `shipped_qty`, `status`.

### Fulfillment & Inventory
- `fulfillment_plans`: `id`, `sales_order_id`, `is_manually_overridden`, `override_reason`, `estimated_shipping_cost`, `created_at`.
- `fulfillment_allocations`: `id`, `fulfillment_plan_id`, `sales_order_line_id`, `warehouse_id`, `allocated_qty`, `created_at`.
- `backorders`: `id`, `sales_order_id`, `sales_order_line_id`, `product_id`, `backorder_qty`, `status`, `created_at`.

### Shipments
- `shipments`: `id`, `shipment_number`, `sales_order_id`, `warehouse_id`, `carrier`, `tracking_number`, `shipped_at`, `status`, `created_by_user_id`.
- `shipment_lines`: `id`, `shipment_id`, `sales_order_line_id`, `shipped_qty`.

### Billing, Subscriptions & Credit Notes
- `invoices`: `id`, `invoice_number`, `sales_order_id`, `customer_id`, `invoice_type` (`ONE_TIME`/`RECURRING`), `currency`, `subtotal`, `total_amount`, `paid_amount`, `credited_amount`, `balance_due`, `due_date`, `status`, `paid_at`.
- `subscriptions`: `id`, `subscription_number`, `sales_order_id`, `customer_id`, `product_id`, `billing_plan_id`, `quantity`, `unit_price`, `monthly_recurring_revenue`, `billing_frequency`, `billing_timing`, `current_period_start`, `current_period_end`, `status`.
- `credit_notes`: `id`, `credit_note_number`, `customer_id`, `sales_order_id`, `invoice_id`, `currency`, `total_amount`, `remaining_amount`, `reason`, `status`.
- `payments`: `id`, `payment_number`, `customer_id`, `currency`, `amount`, `payment_method`, `reference`, `received_at`, `recorded_by_user_id`, `status`.
- `payment_allocations`: `id`, `payment_id`, `invoice_id`, `amount`.

---

## Calculation Engines

### 1. Multi-Warehouse Fulfillment Engine (`app/engines/fulfillment.py`)
Computes optimal stock allocation per order line across active warehouses:
```
score = (warehouse.priority * 1000) + (warehouse.shipping_cost_weight * 100) + base_shipping_cost
```
Reserves stock in priority order until full `ordered_qty` is satisfied. Generates backorders for unfulfilled quantities.

### 2. Subscription Proration Engine (`app/engines/proration.py`)
Calculates mid-cycle subscription quantity modifications using exact calendar day math:
```
daily_rate = (unit_recurring_price * delta_qty) / total_days_in_period
prorated_amount = RoundHalfUp(daily_rate * remaining_days_in_period, 2)
```

---

## API Endpoints Summary

| Method | Endpoint | Description | Roles |
|---|---|---|---|
| `GET` | `/api/v1/orders` | List sales orders | All internal roles |
| `GET` | `/api/v1/orders/{order_id}` | Get sales order details | All internal roles |
| `POST` | `/api/v1/orders/{order_id}/fulfillment-plan` | Generate optimal fulfillment plan | Ops/Admin |
| `POST` | `/api/v1/orders/{order_id}/fulfillment-plan/override` | Apply manual warehouse override | Ops/Admin |
| `POST` | `/api/v1/shipments` | Create and execute shipment | Ops/Admin |
| `GET` | `/api/v1/shipments` | List shipments | All internal roles |
| `GET` | `/api/v1/invoices` | List invoices | All internal roles |
| `POST` | `/api/v1/billing/generate-due` | Process recurring billing run | Ops/Admin |
| `GET` | `/api/v1/subscriptions` | List subscriptions | All internal roles |
| `POST` | `/api/v1/subscriptions/{id}/change-quantity` | Prorate subscription quantity change | Ops/Admin |
| `POST` | `/api/v1/subscriptions/{id}/cancel` | Cancel subscription | Ops/Admin |
| `GET` | `/api/v1/credit-notes` | List credit notes | All internal roles |
| `POST` | `/api/v1/credit-notes/{id}/apply` | Apply credit note to invoice | Ops/Admin |
| `POST` | `/api/v1/payments` | Record payment & allocate | Ops/Admin |
| `GET` | `/api/v1/payments` | List payments | All internal roles |
