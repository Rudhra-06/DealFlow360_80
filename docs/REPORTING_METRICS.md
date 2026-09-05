# Reporting Metrics & Formulas

## Key Metrics Dictionary

### 1. Confirmation Rate
- **Formula**: `(Confirmed Quotations / Sent Quotations) * 100`
- **Zero Denominator**: Returns `null`.

### 2. Weighted Margin Percentage
- **Formula**: `(Sum(Margin Amount) / Sum(Net Total)) * 100`
- **Difference from Simple Average**: Weights deal margins by commercial net value.

### 3. Receivables Aging Buckets
- **Buckets**:
  - `CURRENT`: `due_date >= as_of`
  - `1-30 DAYS`: `1 <= days_overdue <= 30`
  - `31-60 DAYS`: `31 <= days_overdue <= 60`
  - `61-90 DAYS`: `61 <= days_overdue <= 90`
  - `90+ DAYS`: `days_overdue > 90`

### 4. Monthly Recurring Revenue (MRR)
- **Formula**: Sum of `monthly_recurring_revenue` for active & pending cancellation subscriptions grouped by currency.

### 5. Multi-Currency Grouping
- All monetary metrics return dictionary mapping currency code to amount (`{"USD": 100.0, "EUR": 50.0}`). Cross-currency summation is strictly forbidden.
