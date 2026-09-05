# DealFlow360 — Commercial Policy & Billing Configuration Guide

This document defines the commercial policy structures, threshold boundaries, billing plan configurations, precedence resolution, and RBAC security rules implemented in Phase 2 — Part 2.

---

## 1. Core Design Principle: Configuration vs. Business Engine Execution

> [!IMPORTANT]
> **Configuration Only — Not Engine Execution**
> 
> Commercial policy rules and approval thresholds are **NEVER hardcoded in application logic**.
> They are stored as version-controlled, queryable database configuration records (`DiscountPolicy`, `ApprovalPolicy`, `BillingPlan`).
> 
> In Phase 2, we build the database models, validation rules, precedence algorithms, and REST management APIs. Future engines (Quotation, Risk, Approval, Billing) introduced in Phase 3+ will consume these configuration records during deal evaluation.

---

## 2. Discount Policy (`DiscountPolicy`)

### A. Purpose & Structure
Configures commercial discount boundaries (standard reference discount % and maximum allowable discount %).

### B. Fields & Constraints
- `name`: Human-readable description (e.g. `"Gold Tier Standard Hardware Discount"`).
- `customer_tier_id`: Optional FK to `CustomerTier`. Null means applicable across all tiers.
- `product_category_id`: Optional FK to `ProductCategory`.
- `product_id`: Optional FK to `Product`.
- `standard_discount_pct`: Decimal(5,2), 0.00 to 100.00. Standard reference commercial discount.
- `max_discount_pct`: Decimal(5,2), 0.00 to 100.00. Maximum allowable discount limit. Must be `>= standard_discount_pct`.
- `priority`: Integer (lower number = higher priority, default `100`).
- `effective_from` & `effective_to`: Timezone-aware DateTime validity window.
- `is_active`: Administrative toggle boolean.

> [!CAUTION]
> **Scope Mutual Exclusion**
> A `DiscountPolicy` CANNOT specify both `product_id` AND `product_category_id` simultaneously. A product already belongs to a category; allowing both creates ambiguous scope semantics.

### C. Specificity Precedence Resolution
When `DiscountPolicyService.get_applicable_policy(customer_tier_id, product_id, as_of)` is invoked, candidate policies are ranked deterministically by specificity:

1. **`tier+product`** (Level 1): Matches both `customer_tier_id` and `product_id`.
2. **`product`** (Level 2): Matches `product_id` (any tier).
3. **`tier+category`** (Level 3): Matches `customer_tier_id` and product's `category_id`.
4. **`category`** (Level 4): Matches product's `category_id` (any tier).
5. **`tier`** (Level 5): Matches `customer_tier_id` (any product/category).
6. **`global`** (Level 6): Global default policy (all fields null).

If multiple policies match at the same specificity level, the policy with the **lowest `priority` value** (e.g., `10` beats `100`) wins.

---

## 3. Approval Policy (`ApprovalPolicy`)

### A. Purpose & Structure
Configures commercial conditions that trigger mandatory operational approvals in future deal workflows.

### B. Fields & Constraints
- `name`: Human-readable approval rule name (e.g. `"High Discount Finance Approval"`).
- `customer_tier_id`: Optional FK to `CustomerTier`.
- `discount_above_pct`: Optional Decimal(5,2). Triggers approval if quote discount exceeds this %.
- `margin_below_pct`: Optional Decimal(5,2) (allows negative values down to -100.00%). Triggers approval if profit margin falls below this %.
- `payment_terms_above_days`: Optional Integer (>= 0). Triggers approval if payment terms exceed N days.
- `approval_role`: Required operational approver role (`SALES_MANAGER` or `FINANCE_OPERATIONS`).
- `priority`: Integer (lower number = higher priority, default `100`).
- `effective_from` & `effective_to`: Validity timestamps.

> [!NOTE]
> **Multiple Simultaneous Approval Triggers Allowed**
> Unlike `DiscountPolicy` (which resolves to a single winning policy), multiple `ApprovalPolicy` rules can legitimately apply simultaneously to a deal (e.g. high discount AND low margin both triggering independent approval stages).

---

## 4. Billing Plan (`BillingPlan`)

### A. Purpose & Structure
Configures payment schedules and recurring billing frequencies for products and quotations.

### B. Fields & Constraints
- `code`: Normalized uppercase string identifier (e.g. `ONE_TIME`, `MONTHLY`, `QUARTERLY`, `ANNUAL`).
- `name`: Display name (e.g. `"Quarterly Recurring Billing"`).
- `billing_type`: `'ONE_TIME'` or `'RECURRING'`.
- `billing_interval_months`: Integer >= 1 for `RECURRING` plans; MUST be `null` for `ONE_TIME` plans.
- `payment_due_days`: Integer >= 0 (default `30` days).

---

## 5. Security & RBAC Matrix

| Resource | HTTP Method | Route | Allowed Roles |
|---|---|---|---|
| Discount Policy | `GET` | `/api/v1/discount-policies` | `ADMIN`, `SALES_REP`, `SALES_MANAGER`, `FINANCE_OPERATIONS` |
| Discount Policy | `POST`, `PATCH` | `/api/v1/discount-policies` | `ADMIN`, `SALES_MANAGER` |
| Approval Policy | `GET` | `/api/v1/approval-policies` | `ADMIN`, `SALES_REP`, `SALES_MANAGER`, `FINANCE_OPERATIONS` |
| Approval Policy | `POST`, `PATCH` | `/api/v1/approval-policies` | `ADMIN`, `SALES_MANAGER`, `FINANCE_OPERATIONS` |
| Billing Plan | `GET` | `/api/v1/billing-plans` | `ADMIN`, `SALES_REP`, `SALES_MANAGER`, `FINANCE_OPERATIONS` |
| Billing Plan | `POST`, `PATCH` | `/api/v1/billing-plans` | `ADMIN`, `FINANCE_OPERATIONS` |
| Any Resource | Any | Any | External `CUSTOMER` role $\rightarrow$ `HTTP 403 Forbidden` |
