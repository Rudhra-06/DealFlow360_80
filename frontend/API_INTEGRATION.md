# DealFlow360 — Frontend API Integration Inventory

Comprehensive audit matrix mapping every frontend UI feature and component to its authoritative backend FastAPI endpoint, HTTP method, authorized roles, and source implementation file.

---

## 1. Authentication & Session Management (Phase 1)

| UI Feature | Method | Endpoint | Authorized Roles | Frontend File |
| :--- | :--- | :--- | :--- | :--- |
| User Login (JWT) | `POST` | `/api/v1/auth/login` | Public | `js/auth.js` |
| Authenticated User Profile | `GET` | `/api/v1/auth/me` | Authenticated | `js/auth.js`, `js/app.js` |
| Root API Health | `GET` | `/api/v1/health` | Public | `js/api.js` |
| Database Connection Health | `GET` | `/api/v1/health/db` | Public | `js/api.js` |

---

## 2. Master Data & Commercial Configuration (Phase 2)

| UI Feature | Method | Endpoint | Authorized Roles | Frontend File |
| :--- | :--- | :--- | :--- | :--- |
| Customer Directory | `GET` | `/api/v1/customers` | Internal | `js/api/customers.js` |
| Create / Update Customer | `POST`, `PATCH` | `/api/v1/customers`, `/api/v1/customers/{id}` | Admin, Manager | `js/api/customers.js` |
| Customer Tiers | `GET` | `/api/v1/customer-tiers` | Internal | `js/api/customers.js` |
| Product Catalog | `GET` | `/api/v1/products` | Internal | `js/api/products.js` |
| Create / Update Product | `POST`, `PATCH` | `/api/v1/products`, `/api/v1/products/{id}` | Admin, Manager | `js/api/products.js` |
| Product Categories | `GET` | `/api/v1/product-categories` | Internal | `js/api/productCategories.js` |
| Warehouses Master | `GET` | `/api/v1/warehouses` | Internal | `js/api/warehouses.js` |
| Inventory Stock Ledger | `GET` | `/api/v1/inventory` | Internal | `js/api/inventory.js` |
| Discount Policies | `GET`, `POST`, `PATCH`| `/api/v1/discount-policies` | Admin, Manager | `js/api/discountPolicies.js` |
| Approval Governance Policies | `GET`, `POST`, `PATCH`| `/api/v1/approval-policies` | Admin, Manager | `js/api/approvalPolicies.js` |
| Hybrid Billing Plans | `GET`, `POST`, `PATCH`| `/api/v1/billing-plans` | Admin, Manager, Finance | `js/api/billingPlans.js` |
| Recommendation Rules | `GET`, `POST`, `PATCH`| `/api/v1/recommendation-rules` | Admin, Manager | `js/api/recommendationRules.js` |

---

## 3. Quotation Intelligence & CPQ (Phase 3)

| UI Feature | Method | Endpoint | Authorized Roles | Frontend File |
| :--- | :--- | :--- | :--- | :--- |
| Quotations Pipeline / List | `GET` | `/api/v1/quotations` | Internal | `js/api/quotations.js` |
| Quotation Detail | `GET` | `/api/v1/quotations/{id}` | Internal | `js/api/quotations.js` |
| Create Draft Quotation | `POST` | `/api/v1/quotations` | Sales Rep, Manager, Admin | `js/api/quotations.js` |
| Update Quotation Lines & Terms| `PUT`, `PATCH`| `/api/v1/quotations/{id}` | Sales Rep, Manager, Admin | `js/api/quotations.js` |
| What-If Pricing Simulation | `POST` | `/api/v1/what-if/simulate` | Sales Rep, Manager, Admin | `js/api/quotations.js` |
| Upsell Recommendations | `GET` | `/api/v1/recommendations/quotes/{id}`| Sales Rep, Manager, Admin | `js/api/quotations.js` |
| Submit Quote for Approval | `POST` | `/api/v1/quotations/{id}/submit` | Sales Rep, Manager, Admin | `js/api/quotations.js` |
| Approval Queue | `GET` | `/api/v1/quote-approvals` | Manager, Finance, Admin | `js/api/quotations.js` |
| Approve / Reject Quote | `POST` | `/api/v1/quote-approvals/{id}/decision` | Manager, Finance, Admin | `js/api/quotations.js` |

---

## 4. Customer Portal, Negotiation & Real-Time (Phase 4)

| UI Feature | Method | Endpoint | Authorized Roles | Frontend File |
| :--- | :--- | :--- | :--- | :--- |
| Send Quote to Customer | `POST` | `/api/v1/quotations/{id}/send-to-customer` | Sales Rep, Manager, Admin | `js/api/quotations.js` |
| Customer Portal Quotation List | `GET` | `/api/v1/portal/quotations` | Customer | `js/portal/portal-api.js` |
| Customer Portal Quote Detail | `GET` | `/api/v1/portal/quotations/{id}` | Customer | `js/portal/portal-api.js` |
| Quote Versions Timeline | `GET` | `/api/v1/quote-versions/quotations/{id}` | Internal, Customer | `js/portal/portal-api.js` |
| Version Comparison Diff | `GET` | `/api/v1/quote-versions/diff` | Internal, Customer | `js/portal/portal-api.js` |
| Customer Negotiation Request | `POST` | `/api/v1/quote-negotiations` | Customer | `js/portal/portal-api.js` |
| Negotiation Inbox | `GET` | `/api/v1/quote-negotiations` | Internal | `js/negotiation/negotiation-api.js` |
| Accept / Reject Counteroffer | `POST` | `/api/v1/quote-negotiations/{id}/decision` | Sales Rep, Manager, Admin | `js/negotiation/negotiation-api.js` |
| Customer Confirmation (Win) | `POST` | `/api/v1/portal/quotations/{id}/confirm` | Customer | `js/portal/portal-api.js` |
| Notification Stream | `GET` | `/api/v1/notifications` | Authenticated | `js/notifications/notifications-api.js` |
| Mark Notification Read | `PATCH`| `/api/v1/notifications/{id}/read` | Authenticated | `js/notifications/notifications-api.js` |
| WebSocket Telemetry Stream | `WS` | `/api/v1/ws?token={jwt}` | Authenticated | `js/realtime/websocket.js` |

---

## 5. Order Execution, Fulfillment & Hybrid Billing (Phase 5)

| UI Feature | Method | Endpoint | Authorized Roles | Frontend File |
| :--- | :--- | :--- | :--- | :--- |
| Sales Orders List | `GET` | `/api/v1/orders` | Internal | `js/api/orders.js` |
| Sales Order Detail | `GET` | `/api/v1/orders/{id}` | Internal | `js/api/orders.js` |
| Fulfillment Recommendation | `GET` | `/api/v1/fulfillment/recommendation/{order_id}` | Internal | `js/api/fulfillment.js` |
| Accept Warehouse Split | `POST` | `/api/v1/fulfillment/split/{order_id}` | Internal | `js/api/fulfillment.js` |
| Manual Warehouse Override | `POST` | `/api/v1/fulfillment/manual-override/{order_id}` | Dispatcher, Manager, Admin | `js/api/fulfillment.js` |
| Generate Shipments | `POST` | `/api/v1/shipments/generate/{order_id}` | Internal | `js/api/shipments.js` |
| Dispatch / Deliver Shipment | `PATCH`| `/api/v1/shipments/{id}/status` | Internal | `js/api/shipments.js` |
| Invoices List & Detail | `GET` | `/api/v1/invoices`, `/api/v1/invoices/{id}` | Internal | `js/api/invoices.js` |
| Record Payment Against Invoice| `POST` | `/api/v1/payments` | Finance, Admin | `js/api/payments.js` |
| Subscriptions Ledger | `GET` | `/api/v1/subscriptions` | Internal | `js/api/subscriptions.js` |
| Proration & Credit Notes | `GET`, `POST`| `/api/v1/credit-notes` | Finance, Admin | `js/api/creditNotes.js` |

---

## 6. Deal Health & Risk Intelligence (Phase 6 Part 1)

| UI Feature | Method | Endpoint | Authorized Roles | Frontend File |
| :--- | :--- | :--- | :--- | :--- |
| Deal Health Intelligence Board | `GET` | `/api/v1/deal-health` | Internal | `js/api/dealHealth.js` |
| Deal Health Summary Metrics | `GET` | `/api/v1/deal-health/summary` | Internal | `js/api/dealHealth.js` |
| Quotation Health Detail & Signals| `GET`| `/api/v1/deal-health/quotations/{id}` | Internal | `js/api/dealHealth.js` |
| Recalculate Deal Health | `POST` | `/api/v1/deal-health/quotations/{id}/evaluate` | Internal | `js/api/dealHealth.js` |
| Bulk Deal Health Scan | `POST` | `/api/v1/deal-health/scan` | Manager, Admin | `js/api/dealHealth.js` |
| Deal Alerts Inbox | `GET` | `/api/v1/deal-alerts` | Internal | `js/api/dealAlerts.js` |
| Acknowledge Deal Alert | `POST` | `/api/v1/deal-alerts/{id}/acknowledge` | Internal | `js/api/dealAlerts.js` |
| Resolve Deal Alert | `POST` | `/api/v1/deal-alerts/{id}/resolve` | Internal | `js/api/dealAlerts.js` |
| Dismiss Deal Alert | `POST` | `/api/v1/deal-alerts/{id}/dismiss` | Internal | `js/api/dealAlerts.js` |
| Nudge Sales Rep | `POST` | `/api/v1/deal-alerts/{id}/nudge` | Manager, Admin | `js/api/dealAlerts.js` |
| Escalate Deal Alert | `POST` | `/api/v1/deal-alerts/{id}/escalate` | Internal | `js/api/dealAlerts.js` |
| Deal Health Policy Config | `GET`, `PUT`| `/api/v1/deal-health-config` | Admin, Manager | `js/api/dealHealth.js` |

---

## 7. Analytics, Customer 360 & Reports (Phase 6 Part 2)

| UI Feature | Method | Endpoint | Authorized Roles | Frontend File |
| :--- | :--- | :--- | :--- | :--- |
| Executive Overview KPIs | `GET` | `/api/v1/analytics/overview` | Internal | `js/api/analytics.js` |
| Overview Trend (Day/Week/Month)| `GET`| `/api/v1/analytics/overview/trend` | Internal | `js/api/analytics.js` |
| Quotation Conversion Funnel | `GET` | `/api/v1/analytics/quotation-funnel` | Internal | `js/api/analytics.js` |
| Sales Rep Performance Matrix | `GET` | `/api/v1/analytics/sales-performance` | Internal | `js/api/analytics.js` |
| Discount Governance Analytics | `GET` | `/api/v1/analytics/discounts` | Internal | `js/api/analytics.js` |
| Margin & Profitability Telemetry| `GET` | `/api/v1/analytics/margins` | Internal | `js/api/analytics.js` |
| Customer 360 Full Dossier | `GET` | `/api/v1/analytics/customers/{id}/360`| Internal | `js/api/analytics.js` |
| Product Performance & Velocity | `GET` | `/api/v1/analytics/products` | Internal | `js/api/analytics.js` |
| Product Category Aggregates | `GET` | `/api/v1/analytics/product-categories`| Internal | `js/api/analytics.js` |
| Upsell Rule Recommendations | `GET` | `/api/v1/analytics/recommendations` | Internal | `js/api/analytics.js` |
| Approval SLA & Turnaround | `GET` | `/api/v1/analytics/approvals` | Internal | `js/api/analytics.js` |
| Counteroffer & Negotiation | `GET` | `/api/v1/analytics/negotiations` | Internal | `js/api/analytics.js` |
| Deal Health Analytics & Trend | `GET` | `/api/v1/analytics/deal-health`, `/trend` | Internal | `js/api/analytics.js` |
| Fulfillment Split Telemetry | `GET` | `/api/v1/analytics/fulfillment` | Internal | `js/api/analytics.js` |
| Warehouse Node Performance | `GET` | `/api/v1/analytics/warehouses` | Internal | `js/api/analytics.js` |
| Backorder Deficit Analytics | `GET` | `/api/v1/analytics/backorders` | Internal | `js/api/analytics.js` |
| Shipment Logistics Analytics | `GET` | `/api/v1/analytics/shipments` | Internal | `js/api/analytics.js` |
| Billing & Invoicing Totals | `GET` | `/api/v1/analytics/billing` | Internal | `js/api/analytics.js` |
| Multi-Currency Receivables Aging| `GET`| `/api/v1/analytics/receivables` | Internal | `js/api/analytics.js` |
| Payment Stream Analytics | `GET` | `/api/v1/analytics/payments` | Internal | `js/api/analytics.js` |
| Subscription MRR & ARR | `GET` | `/api/v1/analytics/subscriptions` | Internal | `js/api/analytics.js` |
| Executive Narrative Summary Text| `GET`| `/api/v1/analytics/executive-summary-text`| Internal | `js/api/analytics.js` |
| Generate Report (PDF / XLSX) | `POST` | `/api/v1/reports/export` | Internal | `js/api/reports.js` |
| Report Export Audit History | `GET` | `/api/v1/reports/exports` | Internal | `js/api/reports.js` |

---

## 8. System & Demo Readiness (Phase 6 Part 3)

| UI Feature | Method | Endpoint | Authorized Roles | Frontend File |
| :--- | :--- | :--- | :--- | :--- |
| Demo Readiness Verification | `GET` | `/api/v1/system/demo-readiness` | Internal | `js/api/system.js` |
| System Info & Feature Flags | `GET` | `/api/v1/system/info` | Internal | `js/api/system.js` |
