"""Canonical role names for DealFlow360.

These constants prevent typos when configuring role-based access control.
The database `roles` table remains the single source of truth for user assignment.
"""


class RoleName:
    ADMIN = "ADMIN"
    SALES_REP = "SALES_REP"
    SALES_MANAGER = "SALES_MANAGER"
    FINANCE_OPERATIONS = "FINANCE_OPERATIONS"
    CUSTOMER = "CUSTOMER"
