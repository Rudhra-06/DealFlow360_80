# Phase 3 — Part 1: Quotation Intelligence & Commercial Evaluation Engine

## Overview
Phase 3 Part 1 introduces the complete quotation transaction foundation, price/cost snapshot preservation, hybrid billing references, sequential discount mathematics, deterministic margin calculations, explainable risk scoring, normalized risk reason codes, audit trail logging, and REST APIs.

## Architecture & Calculation Engines

### 1. Pricing Engine (`app/engines/pricing.py`)
- Side-effect free, pure Decimal engine.
- Sequential discount formula:
  $$\text{effective\_discount\_pct} = 1 - (1 - \text{line\_discount\_pct}) \times (1 - \text{order\_discount\_pct})$$
- Line gross total: $\text{gross} = \text{quantity} \times \text{unit\_list\_price}$
- Net line total: $\text{net} = \text{gross} \times (1 - \frac{\text{line\_discount\_pct}}{100}) \times (1 - \frac{\text{order\_discount\_pct}}{100})$
- Discount amount: $\text{discount} = \text{gross} - \text{net}$

### 2. Margin Engine (`app/engines/margin.py`)
- Line cost: $\text{line\_cost} = \text{quantity} \times \text{unit\_cost}$
- Margin amount: $\text{margin\_amount} = \text{net\_line\_total} - \text{line\_cost}$
- Margin percentage: $\text{margin\_pct} = \frac{\text{margin\_amount}}{\text{net\_line\_total}} \times 100$
- Zero-revenue division protection handles 0 net revenue safely (-100.00% if cost > 0).

### 3. Explainable Risk Engine (`app/engines/risk.py`)
- Evaluates effective discount against policy standard & maximum snapshot thresholds.
- Risk Classification:
  - `GREEN`: Effective discount $\le$ standard policy discount limit.
  - `YELLOW`: Standard discount $<$ Effective discount $\le$ Maximum policy limit, OR missing policy.
  - `CORAL_RED`: Effective discount $>$ Maximum policy limit, OR line/quote negative margin.
- Weighted Blended Risk Score:
  $$\text{blended\_risk\_score} = \frac{\sum (\text{gross\_line\_total} \times \text{line\_overage\_pct})}{\sum \text{gross\_line\_total}}$$

## Snapshot Strategy
- Unit list price and unit cost are copied from Product master data onto `QuoteLine` at line creation time.
- Resolved policy standard and maximum discount percentages are snapshot on `QuoteLine`.
- Master data price changes after line creation do not modify historical quote totals.

## Status Editability & RBAC
- **Editable Statuses**: `DRAFT`, `RETURNED_FOR_REVISION`.
- **Non-Editable Statuses**: `PENDING_MANAGER_APPROVAL`, `PENDING_FINANCE_APPROVAL`, `APPROVED`, `REJECTED`, `CANCELLED`.
- **Ownership**: `SALES_REP` can create quotes and edit owned quotes. `ADMIN` can edit any quote. `CUSTOMER` role is forbidden from internal quotation endpoints.

## Phase 3 Part 2 Capabilities

### 1. Approval Engine & Automatic Routing (`app/engines/approval.py`)
- Evaluates quotation discount, margin, payment terms, blended risk score, and line-level max discount violations against active `ApprovalPolicy` records.
- Configurable triggers: `discount_above_pct`, `margin_below_pct`, `payment_terms_above_days`, `blended_risk_above`.
- Multi-Level Approval Chain: If Finance Operations approval is triggered, a 2-level chain (`SALES_MANAGER` $\rightarrow$ `FINANCE_OPERATIONS`) is automatically created.
- Approval Actions: `APPROVE`, `REJECT` (mandatory reason), `RETURN` for revision (mandatory reason).
- Resubmission rounds increment `approval_round` while preserving historical approval steps.

### 2. Recommendation Engine & Upsell (`app/engines/recommendation.py`)
- Co-purchase affinity rules (`ProductRecommendationRule`) for products present on quotation.
- Excludes products already on quotation or dismissed for quote (`QuoteRecommendationDismissal`).
- Server-Side Minimum Margin Filter: Rules with calculated margin $<$ `min_margin_pct` are filtered out.
- Deterministic Ranking: `is_promoted DESC`, `affinity_score DESC`, `priority ASC`, `incremental_margin_amount DESC`.
- Adding recommendation (`source_type = UPSELL`) recalculates quotation immediately.

### 3. What-If Simulator (`app/engines/what_if.py`)
- Non-persistent preview endpoint `POST /api/v1/quotations/{id}/what-if`.
- Computes hypothetical overrides (`order_discount_pct`, `payment_terms_days`, line overrides) in-memory using production engines.
- Returns before/after snapshots, deltas, and projected approval requirements with ZERO database commits or ORM mutations.

