# DealHealthEngine Reference & Formulas

## Scoring Formula
```
Health Score = Max(0.00, Min(100.00, 100.00 - Sum(Signal Penalties)))
```

### Signal Evaluation Rules & Formulas

1. **Stalled Quotation**:
   - `elapsed_days = (as_of - last_meaningful_activity_at) / 86400.0`
   - Trigger condition: `elapsed_days > config.stalled_quote_days`
   - Penalty: `config.weight_stalled_quote` (default 20.00)

2. **Discount Anomaly**:
   - `sales_rep_historical_avg = Sum(rep_discounts_90d) / len(rep_discounts_90d)`
   - Minimum sample size requirement: `len(rep_discounts_90d) >= 3`
   - `delta_pp = weighted_effective_discount_pct - sales_rep_historical_avg`
   - Trigger condition: `delta_pp >= config.discount_anomaly_threshold_pct`
   - Penalty: `config.weight_discount_anomaly` (default 15.00)

3. **Approval Delay**:
   - `elapsed_hours = (as_of - pending_step_updated_at) / 3600.0`
   - Trigger condition: `elapsed_hours > config.approval_delay_hours`
   - Penalty: `config.weight_approval_delay` (default 10.00)

4. **Negotiation Stall**:
   - `elapsed_days = (as_of - last_negotiation_activity_at) / 86400.0`
   - Trigger condition: `elapsed_days > config.negotiation_stall_days`
   - Penalty: `config.weight_negotiation_stall` (default 15.00)

5. **Delivery Slippage**:
   - `elapsed_days = (as_of - sales_order_created_at) / 86400.0`
   - Trigger condition: `elapsed_days > config.delivery_slippage_days`
   - Penalty: `config.weight_delivery_slippage` (default 20.00)

6. **Backorder Delay**:
   - `age_days = (as_of - oldest_open_backorder_created_at) / 86400.0`
   - Trigger condition: `age_days > config.backorder_age_days`
   - Penalty: `config.weight_backorder` (default 10.00)

7. **Invoice Overdue**:
   - `overdue_days = (as_of - invoice_due_date).days`
   - Trigger condition: `balance_due > 0` AND `overdue_days >= config.invoice_overdue_days`
   - Penalty: `config.weight_invoice_overdue` (default 10.00)
