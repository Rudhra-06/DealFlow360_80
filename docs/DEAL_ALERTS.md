# Deal Alerts & Actions Specification

## Deal Alert Lifecycle
```
[ OPEN ] ---> (Acknowledge API) ---> [ ACKNOWLEDGED ] ---> (Resolve API) ---> [ RESOLVED ]
   |                                                                                |
   +--------------------------> (Dismiss API) -------------------------------> [ DISMISSED ]
```

## Deduplication Logic
When health scans evaluate quotations:
- The system queries active alerts matching `(quotation_id, alert_type)` with status `OPEN` or `ACKNOWLEDGED`.
- If an active alert is found, `last_triggered_at` is updated to current timestamp and `occurrence_count` is incremented.
- If no active alert exists, a new `DealAlert` is created with status `OPEN`.

## Action Types
- `NUDGE_SALES_REP`: Direct nudge to quotation owner.
- `NUDGE_APPROVER`: Nudge to pending approver role users.
- `ESCALATE_MANAGER`: Operational escalation to Sales Manager.
- `ESCALATE_FINANCE`: Operational escalation to Finance Operations.
- `FOLLOW_UP_CUSTOMER`: Follow-up reminder.
