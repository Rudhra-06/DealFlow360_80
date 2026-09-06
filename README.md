# DealFlow360 — Intelligent B2B Commercial Orchestration Platform

DealFlow360 is an end-to-end enterprise B2B commercial orchestration platform that manages the complete commercial lifecycle — from quotation creation and pricing governance to customer negotiation, approvals, fulfillment, invoicing, online payment, subscriptions, deal health, and reporting.

Instead of handling quotations, approvals, negotiations, inventory, billing, and recurring revenue in disconnected tools, DealFlow360 connects them into one governed workflow.

---

## End-to-End Business Flow

```text
Customer 360
    ↓
Quotation / CPQ
    ↓
Pricing + Margin + Risk Evaluation
    ↓
Approval Governance
    ↓
Customer Portal
    ↓
Negotiation + Quote Versioning
    ↓
Customer Confirmation
    ↓
Sales Order
    ↓
Multi-Warehouse Fulfillment
    ↓
Invoice
    ↓
Customer Razorpay Payment
    ↓
Subscription / Recurring Revenue
    ↓
Deal Health + Analytics + Reporting
```

---

# Key Features

## Customer 360

Sales Representatives can view a complete commercial profile before creating a new quotation.

Customer 360 consolidates:

- Customer profile
- Historical quotations
- Sales orders
- Invoice activity
- Payment activity
- Outstanding balances
- Active subscriptions
- Commercial activity
- Deal Health indicators

This gives the salesperson better context before making a commercial offer.

---

## CPQ — Configure, Price, Quote

Sales Representatives can create quotations using products from the DealFlow360 catalog.

Supported capabilities include:

- Customer selection
- Product selection
- Quantity configuration
- Discounts
- Payment terms
- One-time products
- Recurring products
- Quote versioning
- Automatic pricing
- Margin calculation
- Risk evaluation
- Approval requirement detection

All authoritative commercial calculations are performed in the backend.

---

## Pricing & Margin Intelligence

DealFlow360 automatically evaluates the financial impact of each quotation.

The backend calculates:

- List price
- Applicable volume or tier pricing
- Discount
- Net unit price
- Line total
- Quotation subtotal
- Net quotation value
- Gross margin
- Gross margin percentage

Business calculations are enforced server-side and are not dependent on frontend logic.

---

## What-If Commercial Simulation

Sales Representatives can simulate alternative discounts before changing the real quotation.

Example:

```text
Current Discount: 10%
Simulated Discount: 25%
```

The system can preview the effect on:

- Revenue
- Margin
- Margin percentage
- Commercial risk
- Approval requirements

What-If simulation does not modify the actual quotation.

---

## Risk & Approval Governance

DealFlow360 evaluates quotations against configured commercial rules.

A quotation may proceed automatically when it remains within policy.

```text
Discount within limit
+ Healthy margin
+ Acceptable risk
        ↓
Approved
```

If commercial rules are exceeded:

```text
High discount
or
Low margin
or
High risk
        ↓
Approval Required
```

Authorized reviewers can include:

- Sales Manager
- Finance Operations

The Sales Representative cannot approve their own policy exception.

The approval workflow supports:

- Approval reasons
- Discount threshold checks
- Margin checks
- Risk evaluation
- Approve / Reject actions
- Approval history
- Reapproval after material negotiated changes

---

## Customer Self-Service Portal

Customers have a separate workspace from internal DealFlow360 users.

The Customer Portal supports:

- Portal Overview
- My Quotations
- Quotation review
- Negotiations & Messages
- Term adjustment requests
- Quote confirmation
- Orders & History
- Account Profile
- My Invoices
- Invoice details
- Razorpay payment

Customers only see information belonging to their own organization.

Internal information such as product cost, internal margin, approval thresholds, risk rules, warehouse strategy, and internal Deal Health information is not exposed to customers.

---

## Quote Negotiation & Versioning

B2B quotations often change during negotiation.

DealFlow360 keeps the negotiation process inside the platform.

Example:

```text
QT-1001 — Version 1
        ↓
Customer requests revised terms
        ↓
Sales Representative revises quotation
        ↓
QT-1001 — Version 2
```

Earlier versions are preserved for auditability and traceability.

If a revised quotation exceeds commercial policies, DealFlow360 can trigger reapproval before the revised offer is sent back to the customer.

---

## Customer Confirmation & Sales Order Creation

Once the customer accepts the final quotation, the quotation becomes commercially confirmed.

```text
Quotation
CUSTOMER_CONFIRMED
        ↓
Sales Order
SO-XXXX
```

Quotation status and Sales Order operational status are maintained separately.

```text
Quotation
= What was commercially agreed

Sales Order
= How the confirmed agreement is operationally fulfilled
```

---

## Multi-Warehouse Fulfillment

After customer confirmation, DealFlow360 evaluates stock across available warehouses.

The fulfillment workflow supports:

- Inventory availability checks
- Recommended warehouse allocation
- Multi-warehouse order splitting
- Inventory reservation
- Backorder creation
- Manual warehouse override where permitted
- Shipment generation
- Physical stock updates

Inventory is reserved only after commercial confirmation.

---

## Backorder Management

When stock is not sufficient to completely fulfill an order, DealFlow360 can create a backorder rather than failing the entire order.

Example:

```text
Customer Order: 20 units

Warehouse A: 5 available
Warehouse B: 3 available

Immediate Fulfillment: 8
Backorder: 12
```

---

## Invoicing & Billing

Sales Orders can generate customer invoices using real transactional data.

Invoice information includes:

- Invoice number
- Customer
- Related Sales Order
- Invoice date
- Due date
- Currency
- Total amount
- Paid amount
- Outstanding balance
- Payment status

Typical invoice statuses:

```text
UNPAID
PARTIALLY_PAID
PAID
```

---

## Customer Razorpay Payment

Online payments are initiated by the Customer from the Customer Portal.

```text
Customer
    ↓
My Invoices
    ↓
Open Invoice
    ↓
Pay with Razorpay
    ↓
Backend creates Razorpay Order
    ↓
Razorpay Checkout
    ↓
Customer completes payment
    ↓
Backend verifies payment signature
    ↓
Payment stored in PostgreSQL
    ↓
Invoice balance updated
```

Finance users can monitor payments and record supported manual or offline payments where required.

Payment verification and invoice updates are performed by the backend.

---

## Subscription Management

Recurring products create subscriptions linked to billing plans.

DealFlow360 supports:

- Monthly billing
- Annual billing
- Active subscriptions
- Quantity changes
- Next billing date tracking
- Recurring revenue tracking
- Mid-cycle proration
- Subscription cancellation
- Credit adjustments where applicable

---

## Mid-Cycle Proration

When subscription quantities change during an active billing period, DealFlow360 calculates the appropriate remaining-period charge.

```text
Prorated Amount
=
Remaining Days / Total Billing Period Days
× Quantity Difference
× Unit Price
```

Example:

```text
Existing Seats: 5
New Seats: 10
Change occurs halfway through the month
```

The customer is charged only for the additional usage during the remaining billing period.

---

## Deal Health

DealFlow360 evaluates commercial and operational signals throughout the lifecycle.

Deal Health can identify:

- Quotes waiting too long for approval
- Long-running negotiations
- High-risk commercial terms
- Unusual discounts
- Fulfillment delays
- Backorders
- Payment delays
- Overdue invoices

Deals may be classified as:

```text
Healthy
Watch
At Risk
Critical
```

---

## Analytics & Reporting

DealFlow360 provides reporting based on real transactional data.

Supported reporting includes:

- Quotation PDFs
- Customer Activity Reports
- Billing reports
- Commercial analytics
- Deal Health reports
- PDF export
- XLSX export

Entity-specific reports are generated using the actual selected quotation or customer rather than generic placeholder values.

---

# User Roles

DealFlow360 uses role-based access control.

| Role | Responsibility |
|---|---|
| `ADMIN` | System configuration, policies, products, warehouses, governance |
| `SALES_MANAGER` | Commercial approvals, risk review, pipeline oversight |
| `SALES_REP` | Customer 360, quotation creation, negotiation, deal management |
| `FINANCE_OPERATIONS` | Invoices, payments, subscriptions, financial operations |
| `CUSTOMER` | Review offers, negotiate, confirm deals, view invoices, make payments |

Permissions are validated by the backend and are not dependent only on frontend visibility.

---

# Technical Stack

## Backend

- Python 3.11+
- FastAPI
- Pydantic
- SQLAlchemy 2.x Async
- asyncpg
- PostgreSQL
- Alembic
- AsyncSession architecture

## Frontend

- HTML
- CSS
- Vanilla JavaScript
- Fetch API
- Role-based navigation
- Responsive DealFlow360 UI

## Authentication & Security

- JWT authentication
- bcrypt password hashing
- Database-backed RBAC
- Customer ownership validation
- Server-side business rule enforcement
- Razorpay payment signature verification

## Payments

- Razorpay Checkout
- Backend Razorpay order creation
- HMAC SHA256 signature verification
- PostgreSQL payment persistence

## Reporting

- ReportLab for PDF generation
- openpyxl for XLSX generation

## Real-Time & Notifications

- FastAPI WebSockets
- Database-backed notification persistence
- Firebase integration for supported analytics and notification capabilities

---

# Backend Architecture

DealFlow360 follows a layered backend architecture.

```text
Frontend
    ↓
FastAPI Route
    ↓
Schema / Validation
    ↓
Service Layer
    ↓
Business Engine
    ↓
Repository
    ↓
SQLAlchemy AsyncSession
    ↓
asyncpg
    ↓
PostgreSQL
```

Core business engines include:

- Pricing Engine
- Margin Engine
- Risk Engine
- Approval Governance Engine
- Recommendation Engine
- Fulfillment Engine
- Billing Engine
- Subscription / Proration Engine
- Deal Health Engine

PostgreSQL is the primary source of truth for commercial application data.

---

# Database Environments

Application and automated test data are isolated.

```text
Application / Demo Database:
dealflow360

Automated Test Database:
dealflow360_test
```

Do not run demo bootstrap scripts against the test database.

---

# Quick Start

## 1. Enter Backend Directory

```bash
cd backend
```

---

## 2. Create and Activate Virtual Environment

### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Run Database Migrations

```bash
python -m alembic upgrade head
```

Verify migration state:

```bash
python -m alembic current
python -m alembic heads
```

The project should maintain a single Alembic migration head.

---

## 5. Bootstrap Demo Data

```bash
python scripts/bootstrap_full_demo.py
```

The demo database includes realistic B2B data across:

- Customer tiers
- Customers
- Product categories
- Products
- Warehouses
- Inventory
- Discount policies
- Approval policies
- Billing plans
- Quotations
- Quote lines
- Sales orders
- Invoices
- Payments
- Subscriptions

Do not repeatedly run bootstrap or seed scripts against an already prepared demo database unless required.

---

# Start Backend

```bash
python -m uvicorn app.main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

Health Check:

```text
http://127.0.0.1:8000/health
```

Swagger / OpenAPI:

```text
http://127.0.0.1:8000/docs
```

---

# Start Frontend

From the frontend directory:

```bash
cd frontend
python -m http.server 5500
```

Open:

```text
http://127.0.0.1:5500/login.html
```

If another local development server is used, open the frontend URL configured for that environment.

---

# Run Automated Tests

From the backend directory:

```bash
python -m compileall app scripts
python -m pytest -q
```

Use the actual final pytest result when presenting the final test count.

---

# Demo Credentials

Default Demo Password:

```text
DealFlow360Demo123!
```

## System Administrator

```text
admin.demo@example.com
```

## Sales Manager

```text
manager.demo@example.com
```

## Finance Operations

```text
finance.demo@example.com
```

## Sales Representative

```text
salesrep.demo@example.com
```

## Customer Contact

```text
customer.demo@example.com
```

---

# Recommended Demo Flow

```text
1. Admin
   Show commercial policies and governance rules

2. Sales Representative
   Open Customer 360
   Create quotation
   Add products
   Apply discount
   Show pricing, margin, risk and What-If
   Submit quotation

3. Sales Manager
   Review commercial exception
   Approve quotation

4. Sales Representative
   Send approved quotation to customer

5. Customer
   Review quotation
   Request commercial adjustment

6. Sales Representative
   Revise quotation
   Create a new quote version
   Trigger reapproval if required

7. Customer
   Confirm final quotation

8. System
   Create Sales Order

9. Fulfillment
   Check warehouse availability
   Reserve inventory
   Generate shipment or backorder

10. Finance
    Generate and review invoice

11. Customer
    Open My Invoices
    Pay using Razorpay

12. Finance
    Monitor payment status

13. Subscription
    Show recurring billing and proration

14. Management
    Show Deal Health, Customer 360 and reports
```

---

# Recommended Demo Scenario

Customer:

```text
Omega Corporation
```

Products:

```text
Enterprise Laptop Pro
USB-C Docking Station
24/7 Enterprise Support Plan
```

This scenario can demonstrate:

- One-time revenue
- Recurring revenue
- Pricing
- Margin
- Commercial risk
- Approval governance
- Customer negotiation
- Quote versioning
- Multi-warehouse fulfillment
- Invoicing
- Razorpay payment
- Subscription management

---

# Core Business Concepts

```text
Quotation
= What the seller is offering to the customer

Approval
= Internal permission to offer exceptional commercial terms

Customer Confirmation
= Customer officially accepts the commercial offer

Sales Order
= Operational record used to fulfill the confirmed agreement

Invoice
= Amount the customer is required to pay

Payment
= Amount received from the customer

Subscription
= Recurring commercial relationship after the initial sale
```

---

# Project Documentation

Additional documentation is available under the `docs/` directory:

```text
docs/FINAL_ARCHITECTURE.md
docs/END_TO_END_DATA_FLOW.md
docs/CORE_BUSINESS_RULES.md
docs/DEMO_RUNBOOK.md
docs/REVIEWER_FAQ.md
docs/CUSTOMER_360.md
docs/PHASE_6_PART1_DEAL_HEALTH.md
docs/PHASE_6_PART2_ANALYTICS.md
```

---

# Why DealFlow360?

Traditional B2B commercial processes often depend on disconnected spreadsheets, email approvals, CRM systems, warehouse tools, billing platforms, and separate customer communication channels.

DealFlow360 connects the complete commercial lifecycle:

```text
Quote
→ Approve
→ Negotiate
→ Confirm
→ Fulfill
→ Invoice
→ Pay
→ Subscribe
→ Monitor
```

This provides:

- Stronger commercial governance
- Better pricing visibility
- Improved margin protection
- Full negotiation traceability
- Reduced manual handoffs
- Improved inventory coordination
- Customer self-service
- Integrated billing and payments
- Recurring revenue management
- Better management visibility

---

## DealFlow360

**From the first pricing decision to final payment and recurring customer value — one connected B2B commercial workflow.**
