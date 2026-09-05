# Phase 4 — Customer Portal, Versioning, Negotiation & Real-Time Collaboration Architecture

## Executive Overview

Phase 4 completes the DealFlow360 customer-facing quotation portal, immutable versioning engine, negotiation inbox, automatic reapproval routing, and post-commit real-time event distribution network.

---

## 1. Secure Customer Portal Foundation

### 1.1 Customer User Mapping (`CustomerPortalAccess`)
- **Entity**: `CustomerPortalAccess`
- **Fields**: `id`, `user_id` (Unique FK), `customer_id` (FK), `is_active`, `created_at`, `updated_at`.
- **Security Rule**: Customers only possess visibility into quotations matching their active mapped `customer_id`.

### 1.2 Customer-Facing Safe Representation (`PortalQuotationResponse`)
- **Field Stripping**: `unit_cost`, `total_cost`, `margin_amount`, `margin_pct`, `blended_risk_score`, `risk_level`, and `risk_reasons` are stripped from all customer-facing DTOs.
- **Allowed Portal Statuses**: `SENT_TO_CUSTOMER`, `UNDER_NEGOTIATION`, `UNDER_CUSTOMER_REVIEW`, `CUSTOMER_ACCEPTED`, `REJECTED`, `EXPIRED`.

---

## 2. Immutable Quotation Versioning & Diffing

### 2.1 Version Snapshots (`QuoteVersion` & `QuoteVersionLine`)
- **Trigger Points**: Created upon initial release (`send-to-customer`), internal revisions, and accepted customer counter-offers.
- **Concurrency Locking**: `QuoteVersionRepository.get_next_version_number_with_lock` acquires a database row lock (`SELECT FOR UPDATE`) on `Quotations` to compute `MAX(version_number) + 1` safely.

### 2.2 Version Diff Engine (`VersionDiffEngine`)
- Side-effect-free compare engine calculating header attribute differences (`payment_terms_days`, `order_discount_pct`, `net_total`, etc.), added lines, removed lines, and line-level quantity/discount modifications.

---

## 3. Two-Way Negotiation & Stale Version Guard

### 3.1 Line Questions & Customer Counter-Offers
- Customers submit comments (`COMMENT`, `LINE_QUESTION`) and structured counter-offers (`COUNTER_OFFER`, `CHANGE_REQUEST`).
- **Stale Version Guard**: `submit_counter_offer` and `accept_negotiation_request` enforce `base_quote_version_id == quote.current_version.id`, returning `HTTP 409 Conflict` if the quote has evolved.

### 3.2 Atomic Negotiation Acceptance & Reapproval Routing
- Accepting a counteroffer automatically updates quotation header/lines, recalculates pricing, margin, and risk scores, creates a new `QuoteVersion` snapshot, and checks `ApprovalEngine` policies.
- If policy thresholds are triggered, status transitions to `REAPPROVAL_REQUIRED` / `PENDING_MANAGER_APPROVAL` with `approval_context="NEGOTIATION"`.
- Upon final step approval, status transitions back to `SENT_TO_CUSTOMER` (returning negotiated terms to the customer for confirmation).

---

## 4. Customer Confirmation & Approved Version Guarantee

- **Endpoint**: `POST /portal/quotations/{id}/confirm`
- **State Guarantee**: Quote transitions to `CUSTOMER_ACCEPTED`. `confirmed_quote_version_id`, `customer_confirmed_at`, and `customer_confirmed_by_user_id` are permanently locked.

---

## 5. Real-Time Collaboration & Post-Commit Event Dispatch

### 5.1 Post-Commit Event Dispatcher (`NotificationService`)
- Dispatch executes **strictly post-commit** (`after db.commit()`).
- WebSocket broadcast via `ConnectionManager`.
- FCM Push notification dispatch via `FirebasePushService`.
- Delivery errors are logged without invalidating database transactions.
