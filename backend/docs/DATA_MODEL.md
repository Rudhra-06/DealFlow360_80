# DealFlow360 Data Model Specification

This document details the database schema and entity relationship structures for DealFlow360.

---

## Entity Relationship Diagram

```mermaid
erDiagram
    Role ||--o{ User : "has assigned"
    CustomerTier ||--o{ Customer : "classifies"
    ProductCategory ||--o{ Product : "groups"
    Product ||--o{ Inventory : "stocked in"
    Warehouse ||--o{ Inventory : "contains stock"

    Role {
        int id PK
        string name UK
        string description
    }

    User {
        int id PK
        string email UK
        string full_name
        string hashed_password
        int role_id FK
        boolean is_active
    }

    CustomerTier {
        int id PK
        string name UK
        string description
        boolean is_active
    }

    Customer {
        int id PK
        string customer_code UK
        string name
        string email UK
        string phone
        int tier_id FK
        int default_payment_terms_days
        decimal credit_limit
        string currency
        boolean is_active
    }

    ProductCategory {
        int id PK
        string name UK
        string description
        boolean is_active
    }

    Product {
        int id PK
        string sku UK
        string name
        string description
        int category_id FK
        decimal list_price
        decimal cost_price
        string currency
        string unit_of_measure
        boolean is_active
    }

    Warehouse {
        int id PK
        string code UK
        string name
        string location
        string address
        boolean is_active
    }

    Inventory {
        int id PK
        int warehouse_id FK
        int product_id FK
        decimal on_hand_qty
        decimal reserved_qty
        decimal reorder_level
    }
```

---

## Current Database Migrations

1. `001_initial_schema_baseline`: Baseline setup.
2. `002_create_roles_and_users`: Identity & Authorization tables (`roles`, `users`).
3. `003_create_core_master_data`: Core Master Data tables (`customer_tiers`, `customers`, `product_categories`, `products`, `warehouses`, `inventory`). Current migration head.
