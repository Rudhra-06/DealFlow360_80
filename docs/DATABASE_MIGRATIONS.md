# DealFlow360 — Database Migrations Guide

This document defines the database migration architecture, concepts, and standard development workflow for DealFlow360 using Alembic and SQLAlchemy 2.x.

---

## 1. Why We Use Alembic

In modern production backend applications, database schema changes (creating tables, adding columns, modifying constraints, building indexes) cannot be executed manually or blindly via `Base.metadata.create_all()`.

Alembic provides **version-controlled database schema management**. It tracks every schema change in executable Python migration scripts (revisions), allowing developers to:
- Apply database migrations reproducibly across local, staging, and production environments.
- Safely roll back schema changes if needed (`downgrade()`).
- Audit the history of schema changes alongside git history.

---

## 2. Core Alembic & SQLAlchemy Concepts

### WHAT IS A MIGRATION
A migration is a single, version-controlled step in the lifecycle of a database schema. It consists of instructions to transition a database schema from revision $N$ to revision $N+1$.

### WHAT IS A REVISION
A revision is a unique identifier (hash or prefixed slug, e.g. `001_initial_baseline`) assigned to a specific migration script. Each migration references its `revision` ID and its parent `down_revision` ID, forming a strict chain of schema history.

### WHAT IS `upgrade()`
`upgrade()` is the Python function inside a migration file containing DDL instructions to apply new changes to the database schema (e.g. `op.create_table()`, `op.add_column()`).

### WHAT IS `downgrade()`
`downgrade()` is the Python function containing instructions to revert the changes performed by `upgrade()` (e.g. `op.drop_table()`, `op.drop_column()`).

### WHAT IS `Base.metadata`
`Base.metadata` is SQLAlchemy's internal registry (`DeclarativeBase`) that collects table objects, column definitions, data types, and constraints defined in Python ORM model classes.

### WHAT IS `target_metadata`
`target_metadata` is the variable inside `backend/alembic/env.py` set to `Base.metadata`. It instructs Alembic which SQLAlchemy metadata registry to inspect when auto-generating migrations.

### WHAT IS AUTOGENERATE (`--autogenerate`)
Autogenerate is Alembic's feature that compares `target_metadata` (the state of models in Python code) against the active database schema (the current state of tables in PostgreSQL). Alembic calculates the difference and automatically drafts the `upgrade()` and `downgrade()` code in a new revision script.

### WHAT IS `alembic_version`
`alembic_version` is an internal table created and managed by Alembic inside PostgreSQL. It contains a single row storing the `version_num` (the `revision` ID) of the migration currently applied to that database instance. It is **not** a DealFlow360 business table.

---

## 3. Standard Migration Development Workflow

Follow this strict step-by-step workflow whenever modifying database schemas:

1. **Developer modifies or creates a SQLAlchemy model** in `backend/app/models/` (inheriting from `Base`).
2. **Developer generates migration file** from `backend/`:
   ```bash
   alembic revision --autogenerate -m "describe schema change"
   ```
3. **Developer opens the generated migration file** inside `backend/alembic/versions/`.
4. **Developer manually reviews `upgrade()` and `downgrade()`** to verify accuracy, check column types, nullable flags, foreign keys, and indexes.
5. **Developer runs backend test suite** to ensure no application imports or model mappings are broken:
   ```bash
   pytest
   ```
6. **Developer applies migration to PostgreSQL**:
   ```bash
   alembic upgrade head
   ```
7. **Developer verifies database schema** (e.g. using `alembic current` or psql client).
8. **Only then continue** with service / repository implementation.

---

## 4. Useful Developer Commands

All commands are executed from the `backend/` directory:

| Command | Description |
| :--- | :--- |
| `alembic revision --autogenerate -m "desc"` | Auto-detect schema changes & generate new migration file |
| `alembic upgrade head` | Apply all pending migrations to bring DB up to date |
| `alembic current` | Display the current database revision ID |
| `alembic history` | Display list of all migration revisions in chronological order |
| `alembic downgrade -1` | Rollback the most recently applied migration step |

---

## 5. Team Safety & Concurrency Rules

> [!CAUTION]
> **Strict Team Rule — Prevents Migration Conflicts**
> 
> Only the currently active backend developer should create or apply schema-changing migrations at a given time.
> 
> **Rudhrashini and Namisha must NOT independently create different migrations from different database states simultaneously.** Creating concurrent migrations on separate Git branches generates split revision trees (multiple head revisions), causing Alembic migration branch conflicts.
> 
> Always pull the latest `main` branch, ensure your local database is updated to `head`, and coordinate schema changes before running `alembic revision --autogenerate`.

---

## 6. First-Time Local Database Setup

Follow these steps to set up and verify a local PostgreSQL development database for DealFlow360:

1. **Start PostgreSQL Server**: Ensure your local PostgreSQL database service is running locally (default port `5432`).
2. **Create Development Database**: Create the `dealflow360` database using your PostgreSQL admin client or shell:
   ```bash
   createdb -U postgres dealflow360
   ```
3. **Configure Local Environment**: Copy `backend/.env.example` to `backend/.env` and update credentials:
   ```ini
   POSTGRES_SERVER=localhost
   POSTGRES_PORT=5432
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_local_password
   POSTGRES_DB=dealflow360
   ```
4. **Verify Database Connectivity**: Start the FastAPI server and query the database health endpoint:
   ```bash
   curl http://127.0.0.1:8000/api/v1/health/db
   ```
   Expected response: `{"status":"healthy","database":"connected"}`
5. **Apply Latest Schema Migrations**: From the `backend/` directory, run:
   ```bash
   alembic upgrade head
   ```
6. **Verify Current Revision**: Confirm the migration state matches `001_initial_baseline`:
   ```bash
   alembic current
   ```
7. **Start Feature Development**: Begin writing business logic or models.

