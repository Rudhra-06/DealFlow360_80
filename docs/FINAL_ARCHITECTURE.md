# DealFlow360 — Final Backend Architecture

```
                               ┌────────────────────────┐
                               │  FastAPI REST / WS API │
                               └───────────┬────────────┘
                                           │
                        ┌──────────────────┴──────────────────┐
                        │    Schemas, Pydantic & RBAC Gate   │
                        └──────────────────┬──────────────────┘
                                           │
                 ┌─────────────────────────┴─────────────────────────┐
                 │                  Service Layer                    │
                 │  (Transactions, Permissions, Event Dispatch)     │
                 └─────────────────────────┬─────────────────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         │                                 │                                 │
┌────────┴────────┐               ┌────────┴────────┐               ┌────────┴────────┐
│ Business Engines│               │ Analytics Engine│               │ Export Renderers│
│  - Pricing      │               │  - Executive    │               │  - ReportLab PDF│
│  - Margin/Risk  │               │  - Customer 360 │               │  - openpyxl XLSX│
│  - Approval     │               │  - Receivables  │               └─────────────────┘
│  - Fulfillment  │               │  - MRR          │
│  - Proration    │               └─────────────────┘
│  - Deal Health  │
└────────┬────────┘
         │
┌────────┴────────┐
│  Repositories   │
│ (Query/Add/Flush│
│   No Commits)   │
└────────┬────────┘
         │
┌────────┴────────┐
│ AsyncSession /  │
│  SQLAlchemy ORM │
└────────┬────────┘
         │
┌────────┴────────┐
│   PostgreSQL    │
│ (Truth Source)  │
└─────────────────┘
```

## Architectural Design Principles
1. **Unidirectional Control Flow**: `Route -> Schema -> Service -> Engine/Repository -> AsyncSession -> PostgreSQL`.
2. **Transaction Ownership**: Services own database transactions (`commit`/`rollback`). Repositories and calculation engines NEVER execute commits or rollbacks.
3. **Pure Calculation Engines**: Business engines (Pricing, Risk, Fulfillment, Proration, Deal Health) are deterministic and side-effect free.
4. **Data Isolation**: Internal commercial metrics (margin, risk, cost) are stripped from customer portal responses.
