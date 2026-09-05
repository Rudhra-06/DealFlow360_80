# DealFlow360 — Frontend (Phase 2: Master Data & Commercial Configuration)

DealFlow360 is an Enterprise B2B Deal Management and Commercial Operations Platform.

This directory contains the **Phase 2 Frontend Application** built with Vanilla JavaScript, HTML5, and CSS3, integrating with the FastAPI backend.

---

## 🎨 Locked Brand Identity & Design System

The visual design preserves the locked DealFlow360 enterprise color palette:

- **Deep Navy (`#172A46`)**: Sidebar, main headings, typography, dark container surfaces.
- **Teal (`#19B5A5`)**: Primary CTAs, active indicators, successful system health states, links.
- **Coral (`#F28C6B`)**: Warning indicators, errors, system disconnection alerts.
- **Off-white (`#F7F8FA`)**: Application background workspace.
- **White (`#FFFFFF`)**: Card surfaces, forms, panels.
- **Primary Text (`#172033`)**: High-contrast body copy and important values.

---

## 📁 Directory Structure

```
frontend/
├── index.html                  # Authenticated workspace shell & dynamic view container
├── login.html                  # Split-screen enterprise login page
├── README.md                   # Frontend architecture & guide
│
├── css/
│   ├── variables.css           # Design tokens & locked brand color palette
│   ├── base.css                # Base resets, typography, and utility classes
│   ├── components.css          # Tables, cards, form grids, drawers, modals, toasts, tabs
│   ├── layout.css              # Login split-screen & app shell layout
│   └── responsive.css          # Tablet and mobile responsive rules
│
└── js/
    ├── config.js               # Centralized API_BASE_URL & storage configuration
    ├── api.js                  # Centralized Fetch API client & health check callers
    ├── auth.js                 # Token storage, auth guard, login & logout services
    ├── navigation.js           # Role-aware navigation definitions & role formatter
    ├── ui.js                   # Modals, drawers, toasts, password toggles, and drawer controls
    │
    ├── api/                    # Modular API Service Clients
    │   ├── customerTiers.js    # Customer Tiers API (/api/v1/customer-tiers)
    │   ├── customers.js        # Customers API (/api/v1/customers)
    │   ├── productCategories.js# Product Categories API (/api/v1/product-categories)
    │   ├── products.js         # Products API (/api/v1/products)
    │   ├── warehouses.js       # Warehouses API (/api/v1/warehouses)
    │   ├── inventory.js        # Inventory API (/api/v1/inventory)
    │   ├── discountPolicies.js # Discount Policies API (/api/v1/discount-policies)
    │   ├── approvalPolicies.js # Approval Policies API (/api/v1/approval-policies)
    │   └── billingPlans.js     # Billing Plans API (/api/v1/billing-plans)
    │
    ├── views/                  # Phase 2 View Controllers
    │   ├── dashboardView.js    # Upgraded Phase 2 dashboard with role actions
    │   ├── customersView.js    # Customers & Customer Tiers management & detail drawer
    │   ├── productsView.js     # Products Catalog & Categories with stock availability tab
    │   ├── inventoryView.js    # Inventory stock overview & Warehouse facilities
    │   ├── discountPoliciesView.js # Discount policies & live Policy Resolver tool
    │   ├── approvalPoliciesView.js # Commercial approval triggers and roles
    │   ├── billingPlansView.js # Commercial billing contract schedules
    │   └── settingsView.js     # Master & Commercial Configuration Hub
    │
    └── app.js                  # Application Router & Lifecycle Controller
```

---

## 🛠️ Integrated Master Data & Commercial Configuration Modules

### 1. Master Data
- **Customers**: List, search by name/code, filter by tier and status, Add/Edit modal, and Slide-out Details Drawer with commercial profiles.
- **Customer Tiers**: Master classification levels (`GOLD`, `SILVER`, `BRONZE`) with active/inactive management.
- **Products Catalog**: SKU catalog items with List/Cost prices, Currency, Unit of Measure, and Category associations. Detail drawer includes live warehouse stock view.
- **Product Categories**: Logical item groupings.
- **Warehouses**: Multi-location storage facilities and addresses.
- **Inventory**: Stock balances (`on_hand_qty`, `reserved_qty`, `available_qty`, `reorder_level`) with stock health badges. (`reserved_qty` is strictly protected and read-only).

### 2. Commercial Configuration
- **Discount Policies**: Tier, category, or product SKU scoped standard & maximum discount rules with 6-tier precedence support. Includes **"Test Policy Resolution" tool** directly querying `GET /api/v1/discount-policies/resolve`.
- **Approval Policies**: Multi-trigger threshold rules (`Discount > X%`, `Margin < Y%`, `Payment Terms > Z days`) mapped to `SALES_MANAGER` or `FINANCE_OPERATIONS`.
- **Billing Plans**: Standard contract payment schedules (`ONE_TIME` vs `RECURRING`) with interval month management.

---

## 🔐 Role-Based Access Control (RBAC) UX Alignment

- **ADMIN**: Full create/edit/view access across all master data and commercial policies.
- **SALES_REP**: Can create/edit Customers; view-only access to Products, Inventory, and Policies.
- **SALES_MANAGER**: Can create/edit Customers, Customer Tiers, Discount Policies, and Approval Policies.
- **FINANCE_OPERATIONS**: Can create/edit Products, Categories, Warehouses, Inventory, Approval Policies, and Billing Plans.
- **CUSTOMER**: Restricted to separate Customer Portal shell (zero internal API exposure).
- *Authoritative security is enforced on the FastAPI backend on every request.*
