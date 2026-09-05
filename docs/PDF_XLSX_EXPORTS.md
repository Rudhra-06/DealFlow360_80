# Report Exports (PDF & XLSX)

## Overview
Phase 6 Part 2 provides a report export engine capable of rendering any backend report into PDF or XLSX formats.

## Supported Formats
- **PDF**: Generated via ReportLab (`application/pdf`). Contains styled headers, KPI tables, and footers.
- **XLSX**: Generated via openpyxl (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`). Contains Summary and Detail worksheets with frozen header rows.

## Formula Injection Protection
All text values exported to XLSX are sanitized. If a string starts with `=`, `+`, `-`, or `@`, it is prefixed with a single quote (`'`) to prevent spreadsheet formula injection vulnerabilities.

## Audit Logging
All export requests are logged in the `report_export_audits` database table (`user_id`, `report_type`, `format`, `status`, `filename`, `generated_at`). History is queryable at `GET /api/v1/reports/exports`.
