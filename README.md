# DealFlow360

## Intelligent B2B Sales, Quotation and Deal Management Platform

DealFlow360 is a B2B sales and deal management platform designed to manage the complete lifecycle of a business deal, starting from quotation creation and continuing through approval, fulfillment, billing, customer negotiation and reporting.

The main idea behind the system is to connect the different stages of a deal instead of treating them as independent modules. A change made during quotation or negotiation can affect pricing, margins, risk, approvals, inventory and billing.

The overall workflow is:

**Quotation → Approval → Fulfillment → Billing → Negotiation → Reporting**

---

# 1. Problem Statement

B2B sales operations involve multiple teams such as sales, finance, warehouse and customers. Different decisions made during a deal can affect several other parts of the business process.

For example, increasing a discount can:

* Reduce the deal margin
* Increase the risk associated with the deal
* Trigger an approval requirement
* Affect the final invoice
* Change the overall health of the deal

Similarly, adding another product can affect inventory allocation, pricing, margin and possible upsell recommendations.

In many systems, these operations are handled through separate screens or modules. This can make it difficult to maintain consistency between different stages of the deal.

DealFlow360 addresses this by providing a unified workflow in which important business actions are evaluated against the current state of the deal.

---

# 2. Proposed Solution

DealFlow360 provides a centralized platform for managing B2B sales operations.

The main modules of the system include:

* Authentication and Role-Based Access Control
* Customer Management
* Product and Price List Management
* Discount Management
* Margin Calculation
* Deal Risk Scoring
* Approval Workflows
* Warehouse Allocation
* Fulfillment Management
* One-Time and Recurring Billing
* Customer Negotiation Portal
* Deal Health Monitoring
* Discount Anomaly Detection
* Sales Reporting
* AI-Assisted Upsell and Cross-Sell Recommendations
* Audit Logging

The system focuses on connecting these modules through business rules rather than implementing them as independent CRUD operations.

---

# 3. System Architecture

```text
                           USER
                             |
                             v
                    HTML / CSS / JS
                       FRONTEND
                             |
                         REST API
                             |
                             v
                         FASTAPI
                             |
                +------------+------------+
                |            |            |
             Pydantic     JWT / RBAC     APIs
                |            |            |
                +------------+------------+
                             |
                       SERVICE LAYER
                             |
                     REPOSITORY LAYER
                             |
                        SQLAlchemy
                             |
                    +--------+--------+
                    |                 |
                    v                 v
               PostgreSQL         ChromaDB
                    |                 |
                ERP / CRM          AI / RAG
                   DATA           KNOWLEDGE
```

## Architecture Layers

### API Layer

The API layer handles:

* HTTP requests and responses
* Request validation
* API contracts
* Authentication and authorization
* Communication with the frontend

FastAPI is used to implement the REST APIs.

### Service Layer

The service layer contains the main business logic of the application.

Examples include:

* Pricing calculations
* Discount validation
* Margin calculation
* Risk scoring
* Approval decisions
* Warehouse allocation
* Billing logic
* Negotiation validation

Keeping these rules in the service layer prevents business logic from being tightly coupled to the frontend.

### Repository Layer

The repository layer handles database operations and provides an abstraction between the business logic and the database.

### Data Layer

PostgreSQL is used as the main transactional database.

ChromaDB is used separately for AI-related functionality such as semantic retrieval and recommendation support.

---

# 4. Technology Stack

## Frontend

* HTML5
* CSS3
* JavaScript
* REST API integration

## Backend

* Python
* FastAPI
* Pydantic
* SQLAlchemy
* asyncpg

## Database

* PostgreSQL

PostgreSQL stores the main application data, including:

* Customers
* Products
* Price Lists
* Quotations
* Orders
* Approvals
* Warehouses
* Inventory
* Fulfillment
* Invoices
* Subscriptions
* Payments
* Deal information

## Authentication and Security

* JWT Authentication
* Role-Based Access Control
* Restricted Customer Portal
* API-level authorization

## AI Layer

* ChromaDB
* RAG-based retrieval
* AI-assisted recommendations

AI is used only where it provides useful assistance. Important transactional decisions such as discount validation, approval requirements and billing calculations are handled through deterministic backend rules.

---

# 5. End-to-End Workflow

```text
                 +----------------------+
                 | Sales Representative |
                 +----------+-----------+
                            |
                            v
                    Create Quotation
                            |
             +--------------+--------------+
             |              |              |
             v              v              v
         Products       Discounts      Upsell /
                                      Cross-Sell
             |              |              |
             +--------------+--------------+
                            |
                            v
                    Margin and Risk
                       Analysis
                            |
                     +------+------+
                     |             |
                     v             v
                 Safe Deal      Risky Deal
                     |             |
                     |             v
                     |       Approval Workflow
                     |       Manager / Finance
                     |             |
                     +------+------+
                            |
                            v
                    Order Confirmed
                            |
                            v
                  Warehouse Allocation
                            |
                            v
                      Fulfillment
                            |
                +-----------+-----------+
                |                       |
                v                       v
          One-Time Product        Subscription
                |                       |
                v                       v
             Invoice             Billing Schedule
                |                       |
                +-----------+-----------+
                            |
                            v
                     Customer Portal
                            |
                            v
                       Negotiation
                            |
                     Terms Changed?
                            |
                            v
                       Re-Approval
                            |
                            v
                         Confirm
                            |
                            v
                     Deal Analytics
```

---

# 6. Real-Time Business Intelligence

In DealFlow360, real-time processing means that the system recalculates relevant business information whenever the current transaction changes.

This does not require WebSockets for every operation. REST APIs are sufficient for the main transaction workflow.

For example, consider a quotation containing:

```text
Laptop
Selling Price: ₹50,000
Cost: ₹40,000
```

The initial margin is:

```text
₹50,000 - ₹40,000 = ₹10,000
```

If the sales representative adds an upsell product, the system can recalculate:

* Total Revenue
* Total Cost
* Total Discount
* Total Margin
* Margin Percentage
* Risk Score
* Approval Requirement
* Upsell Recommendations

The frontend receives the updated information through the REST API and updates the quotation view.

---

# 7. Discount Governance

DealFlow360 uses configurable discount policies to control discounts.

For example:

```text
Customer Tier: Gold

Hardware Maximum Discount: 15%
Service Maximum Discount: 10%
```

If a quotation contains:

```text
Laptop  → 12%
Service → 18%
```

the service discount exceeds the permitted threshold.

The system identifies the violation and can send the quotation through the appropriate approval workflow.

The basic process is:

```text
Discount Request
       |
       v
Policy Evaluation
       |
       v
Threshold Check
       |
   +---+---+
   |       |
   v       v
Allowed  Exceeded
   |       |
   v       v
Continue Approval
```

The rules are implemented in the backend so that they can be reused by different parts of the application.

---

# 8. Deal Risk Engine

DealFlow360 uses a risk score to evaluate the overall condition of a quotation.

Instead of considering only one violation, the system can combine multiple risk factors.

For example:

```text
Product A → Risk +2
Product B → Risk +3
Product C → Risk +2
--------------------
Total Risk → 7
```

Possible factors include:

* Discount over the permitted limit
* Product or category risk
* Customer tier
* Overall discount
* Margin reduction
* Multiple simultaneous policy violations

The final risk score can be used to determine whether additional approval is required.

For example:

```text
Risk Score
     |
     v
Risk Classification
     |
     +------ Low ------> Continue
     |
     +---- Medium -----> Manager Review
     |
     +------ High -----> Manager / Finance Approval
```

---

# 9. Warehouse Allocation

After an order is confirmed, the system checks current inventory and determines how the order can be fulfilled.

For example:

```text
Order Requirement: 100 units

Warehouse A → 40
Warehouse B → 50
Warehouse C → 30
```

The system can generate an allocation such as:

```text
Warehouse A → 40
Warehouse B → 50
Warehouse C → 10
```

The allocation can also consider shipping costs to reduce unnecessary shipments.

The automatically generated allocation can be manually modified by an authorized user when required.

---

# 10. Hybrid Billing

DealFlow360 supports orders containing both one-time products and recurring services.

For example:

```text
Laptop
₹80,000
One-Time
```

and:

```text
Premium Support
₹2,000 / month
Recurring
```

The system maintains these as separate billing types:

```text
ONE-TIME
₹80,000
```

and:

```text
RECURRING
₹2,000 / month
```

This allows the platform to support:

* One-time invoices
* Recurring billing
* Billing schedules
* Subscription changes
* Mid-cycle changes
* Proration

---

# 11. Customer Negotiation Portal

DealFlow360 provides a separate customer-facing portal instead of exposing the internal sales dashboard to customers.

The customer can view their quotation and submit a counteroffer.

The workflow is:

```text
Sales Representative
        |
        v
Create Quote
        |
        v
Customer Portal
        |
        v
Customer Counteroffer
        |
        v
Business Rule Validation
        |
        v
Threshold Exceeded?
        |
       YES
        |
        v
Approval Workflow
        |
        v
Manager / Finance
        |
        v
Confirm Deal
```

If the customer changes important commercial terms, the system evaluates the updated deal again.

This helps maintain access boundaries while still allowing customers to participate in negotiations.

---

# 12. Deal Health and Analytics

The analytics section provides an overview of the current sales pipeline.

Important metrics include:

* Active deals
* At-risk deals
* Pending approvals
* Stalled quotations
* Discount anomalies
* Delivery delays
* Sales performance
* Deal margins

Example dashboard:

```text
+------------------+
|   ACTIVE DEALS   |
|       127        |
+------------------+

+------------------+
|     AT RISK      |
|        18        |
+------------------+

+------------------+
| PENDING APPROVAL |
|        12        |
+------------------+
```

The dashboard values are calculated from transactional data stored in PostgreSQL rather than being hardcoded demonstration values.

---

# 13. AI-Assisted Upsell and Cross-Sell

AI is used selectively in DealFlow360 for recommendation-related functionality.

The recommendation process can use historical purchases and product relationships.

```text
Historical Purchases
        |
        v
Product Relationships
        |
        v
Recommendation Engine
        |
        v
Margin Validation
        |
        v
Upsell / Cross-Sell Suggestion
```

For example:

```text
Customer adds Laptop
        |
        v
Frequently associated product:
Premium Support
        |
        v
Check margin and business rules
        |
        v
Recommend Premium Support
```

The recommendation system assists the salesperson but does not make critical business decisions automatically.

This separation allows:

**AI → Recommendations**

**Business Rules → Transaction Decisions**

---

# 14. Authentication and Role-Based Access Control

DealFlow360 uses JWT-based authentication and role-based authorization.

Different users have different responsibilities within the workflow.

## Sales Representative

Can:

* Create quotations
* Modify quotations
* Add products
* Request discounts
* Submit quotations for approval

## Manager

Can:

* Review risky deals
* Review quotations
* Approve or reject requests

## Finance

Can:

* Review financial impact
* Review discount exceptions
* Approve financial exceptions

## Customer

Can:

* View their own quotations
* Submit counteroffers
* Review negotiated terms
* Confirm final terms

Access is enforced at the API level so that users cannot access functionality outside their assigned role.

---

# 15. API Design

DealFlow360 follows REST API principles.

An example endpoint is:

```http
POST /api/v1/quotes/{quote_id}/recalculate
```

The endpoint can return the main quotation intelligence in a single response:

```json
{
  "subtotal": 120000,
  "discount": 18000,
  "total": 102000,
  "cost": 76000,
  "margin": 26000,
  "margin_percentage": 25.49,
  "risk_score": 7.2,
  "approval_required": true,
  "approval_level": "manager",
  "upsell_suggestions": [
    {
      "product_id": 42,
      "name": "Premium Support",
      "margin_delta": 4500
    }
  ]
}
```

This reduces unnecessary API requests because related calculations can be returned together.

---

# 16. Backend Optimization

The backend is designed to handle increasing amounts of transactional data.

## Database Indexing

Frequently searched fields can be indexed, such as:

```text
customer_id
quote_id
status
created_at
warehouse_id
product_id
sales_rep_id
```

## Pagination

Large datasets are returned using pagination.

Example:

```http
GET /api/v1/quotes?page=1&limit=20
```

This prevents the application from loading all records at once.

## Database Aggregation

Dashboard statistics can use PostgreSQL aggregation functions such as:

```text
COUNT()
SUM()
AVG()
GROUP BY()
```

This allows calculations to be performed closer to the database instead of loading unnecessary records into application memory.

## Transactions

Important operations can be handled within database transactions.

For example:

```text
Confirm Order
      |
      v
Reserve Stock
      |
      v
Create Fulfillment
      |
      v
Create Billing
```

If a critical step fails, the transaction can be rolled back to prevent an incomplete business state.

---

# 17. Project Structure

```text
DealFlow360/
|
├── frontend/
│   ├── index.html
│   ├── css/
│   ├── js/
│   └── assets/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── core/
│   │   └── main.py
│   │
│   ├── tests/
│   ├── seed/
│   └── requirements.txt
│
├── database/
│   ├── migrations/
│   └── seed_data/
│
├── docs/
│   └── architecture/
│
├── .env.example
├── .gitignore
└── README.md
```

---

# 18. Core Modules

```text
01. Authentication and RBAC
02. Customers
03. Products and Price Lists
04. Discount Governance
05. Quotations
06. Upsell and Cross-Sell
07. Approval Workflow
08. Warehouse and Fulfillment
09. Subscriptions and Billing
10. Customer Portal
11. Deal Health and Anomaly Detection
12. Reporting
13. Audit Logs
```

---

# 19. End-to-End Demo Flows

The project is designed to demonstrate complete business workflows rather than isolated features.

## Flow 1: Risky Quote to Fulfillment

```text
Login
  |
  v
Configure Customer / Product
  |
  v
Create Quotation
  |
  v
Apply Discount
  |
  v
Risk Engine
  |
  v
Approval Required
  |
  v
Manager Approval
  |
  v
Add Upsell
  |
  v
Margin Recalculation
  |
  v
Confirm Order
  |
  v
Warehouse Allocation
  |
  v
Fulfillment
  |
  v
Hybrid Billing
```

## Flow 2: Customer Negotiation

```text
Create Quotation
       |
       v
Customer Portal
       |
       v
Customer Counteroffer
       |
       v
Discount / Terms Changed
       |
       v
Business Rule Evaluation
       |
       v
Approval Reopened
       |
       v
Manager / Finance Approval
       |
       v
Customer Confirmation
       |
       v
Invoice / Payment Update
```

These flows demonstrate how a change in one stage can affect the rest of the deal lifecycle.

---

# 20. Key Differentiating Features

## 20.1 Business Logic Instead of Only CRUD

The project focuses on implementing actual business rules rather than only creating forms for storing data.

## 20.2 Connected Deal Intelligence

Changes to products, discounts or negotiation terms can trigger recalculation of relevant deal information.

## 20.3 Rule-Based Approval

Approval requirements are determined based on the current state of the quotation and its risk.

## 20.4 Inventory-Aware Fulfillment

Warehouse allocation uses current inventory information rather than using a fixed allocation.

## 20.5 Hybrid Billing

The same order can contain both one-time products and recurring services.

## 20.6 Separate Customer Portal

Customers access only their own quotations and negotiation information.

## 20.7 Controlled Use of AI

AI is used for recommendations and knowledge retrieval, while critical transaction decisions remain deterministic and auditable.

---

# 21. Design Principle

The central design principle of DealFlow360 is:

> **A B2B deal is not just a form. It is a chain of connected business decisions.**

For example, when a discount changes:

```text
Discount
   |
   v
Risk
   |
   v
Approval
   |
   v
Deal Health
```

When a product is added:

```text
Product
   |
   v
Price
   |
   v
Cost
   |
   v
Margin
   |
   v
Risk
   |
   v
Upsell Intelligence
```

When inventory changes:

```text
Current Stock
   |
   v
Warehouse Allocation
   |
   v
Fulfillment
```

When a customer negotiates:

```text
Counteroffer
   |
   v
Policy Evaluation
   |
   v
Risk
   |
   v
Approval
   |
   v
Final Deal
```

This interconnected workflow is the main concept behind DealFlow360.

---

# 22. Future Enhancements

Possible future improvements include:

* AI-based sales assistant
* Predictive deal-risk forecasting
* Improved product recommendation models
* Automated email notifications
* Advanced sales forecasting
* Event-driven architecture
* WebSocket-based collaboration
* External payment gateway integration
* Advanced shipment optimization
* Customer behavior analytics

These features can be considered after the core workflow has been implemented.

---

# 23. Team

DealFlow360 is being developed as part of the Odoo Hackathon 2026.

### Team Members

**Rudhrashini Murugan**
Backend and Business Logic

**Namisha**
Backend, Data and Workflow

**Sri Divya Dharshini**
Frontend and User Experience

---

# 24. Project Philosophy

DealFlow360 is based on a simple idea:

**A B2B deal is a chain of business decisions rather than a single form.**

The system is designed to connect those decisions, apply business rules at the appropriate stages, and provide relevant information to different stakeholders throughout the deal lifecycle.

The main objective is not to build a large number of independent features, but to demonstrate how different enterprise operations can work together as one connected workflow.

---

# DealFlow360

**From quotation to closed deal, one connected workflow.**
