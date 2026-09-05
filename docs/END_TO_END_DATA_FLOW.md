# DealFlow360 — End-to-End Data Flow

```
   1. QUOTATION DRAFT ───► 2. PRICING & MARGIN ───► 3. APPROVAL ROUTING
          │                                                  │
          ▼                                                  ▼
   6. CUSTOMER CONFIRMATION ◄── 5. PORTAL COUNTER ◄─── 4. SENT TO CUSTOMER
          │
          ▼
   7. SALES ORDER CREATION ───► 8. FULFILLMENT & STOCK ───► 9. SHIPMENT
          │                         RESERVATION
          ▼
  10. HYBRID BILLING ─────────► 11. INVOICE & SUBSCRIPTION ─► 12. PAYMENTS
          │
          ▼
  13. DEAL HEALTH ENGINE ────► 14. CUSTOMER 360 & ANALYTICS ─► 15. PDF/XLSX EXPORT
```

## Step-by-Step Data Flow
1. **Sales Rep builds Quotation**: Items, quantities, and requested discounts entered.
2. **Deterministic Economics**: Pricing, margin, blended risk score, and recommendations computed.
3. **Multi-Level Approval**: High discounts route to `PENDING_MANAGER_APPROVAL` and `PENDING_FINANCE_APPROVAL`.
4. **Customer Portal Sharing**: Approved quote moves to `SENT_TO_CUSTOMER` (Version 1).
5. **Customer Counteroffer**: Customer submits negotiation request; Sales Rep accepts, triggering Version 2 reapproval.
6. **Customer Confirmation**: Customer confirms exact approved version (`CUSTOMER_CONFIRMED`).
7. **Order Conversion**: `SalesOrder` generated linking directly to confirmed quote version.
8. **Multi-Warehouse Fulfillment**: Stock reserved across warehouses by priority and shipping cost. Unfilled items create `Backorder` records.
9. **Shipment Execution**: Shipments created and processed, physically decrementing `quantity_on_hand` and `quantity_reserved`.
10. **Hybrid Billing**: Hardware lines produce one-time `Invoice`; service lines create recurring `Subscription` and `BillingSchedule`.
11. **Payments & Receivables**: Customer payments recorded and allocated against invoices; balance due updated.
12. **Deal Health & Intelligence**: Deal Health Engine evaluates activity, baseline discount anomalies, and overdue invoices, firing deduplicated alerts and nudges.
13. **Executive Analytics & Reporting**: Customer 360 and Executive Overview aggregate PostgreSQL facts and export PDF/XLSX reports.
