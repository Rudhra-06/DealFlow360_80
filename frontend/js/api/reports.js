/**
 * DealFlow360 — Reports & Export API Client
 * Connects to /api/v1/reports endpoints. Handles binary file downloads for PDF & XLSX.
 */
(function (global) {
  'use strict';

  function buildQuery(params = {}) {
    const qs = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== null && value !== undefined && value !== '') {
        qs.append(key, value);
      }
    }
    const str = qs.toString();
    return str ? '?' + str : '';
  }

  const ReportsAPI = {
    REPORT_TYPES: {
      EXECUTIVE_SUMMARY: 'EXECUTIVE_SUMMARY',
      QUOTATION_FUNNEL: 'QUOTATION_FUNNEL',
      SALES_PERFORMANCE: 'SALES_PERFORMANCE',
      CUSTOMER_360: 'CUSTOMER_360',
      PRODUCT_PERFORMANCE: 'PRODUCT_PERFORMANCE',
      APPROVAL_ANALYTICS: 'APPROVAL_ANALYTICS',
      NEGOTIATION_ANALYTICS: 'NEGOTIATION_ANALYTICS',
      DEAL_HEALTH: 'DEAL_HEALTH',
      FULFILLMENT: 'FULFILLMENT',
      BACKORDERS: 'BACKORDERS',
      BILLING: 'BILLING',
      RECEIVABLES: 'RECEIVABLES',
      SUBSCRIPTIONS: 'SUBSCRIPTIONS',
      QUOTATION: 'QUOTATION',
      INVOICE: 'INVOICE'
    },

    REPORT_LABELS: {
      EXECUTIVE_SUMMARY: 'Executive Summary',
      QUOTATION_FUNNEL: 'Quotation Funnel',
      SALES_PERFORMANCE: 'Sales Performance',
      CUSTOMER_360: 'Customer 360 Full Dossier',
      PRODUCT_PERFORMANCE: 'Product & Category Performance',
      APPROVAL_ANALYTICS: 'Approval & Governance Analytics',
      NEGOTIATION_ANALYTICS: 'Negotiation & Counteroffer Analytics',
      DEAL_HEALTH: 'Deal Health & Risk Signals',
      FULFILLMENT: 'Operations & Warehouse Fulfillment',
      BACKORDERS: 'Backorder Analysis',
      BILLING: 'Billing & Invoicing Summary',
      RECEIVABLES: 'Receivables Aging Report',
      SUBSCRIPTIONS: 'Recurring Revenue & Subscriptions',
      QUOTATION: 'Commercial Quotation Document',
      INVOICE: 'Customer Invoice Document'
    },

    /**
     * Export report in PDF or XLSX.
     * Receives binary file and triggers browser download.
     * @param {Object} payload { report_type, format, start_date, end_date, customer_id, sales_rep_id, currency, filters }
     * @returns {Promise<{ filename: string, size: number }>}
     */
    async exportReport(payload) {
      const baseUrl = (global.DealFlowConfig && global.DealFlowConfig.API_BASE_URL) || 'http://127.0.0.1:8000';
      const url = `${baseUrl.replace(/\/$/, '')}/api/v1/reports/export`;

      const token = global.DealFlowAuth ? global.DealFlowAuth.getAccessToken() : null;
      const headers = {
        'Content-Type': 'application/json'
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        let errMessage = 'Report generation failed.';
        try {
          const errData = await response.json();
          if (errData && errData.detail) {
            errMessage = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
          }
        } catch (_) {}

        if (response.status === 403) {
          errMessage = "You don't have permission to export this report.";
        } else if (response.status === 422) {
          errMessage = `Validation error: ${errMessage}`;
        }
        throw new Error(errMessage);
      }

      // Extract filename from Content-Disposition header
      let filename = `dealflow360_${payload.report_type.toLowerCase()}.${payload.format.toLowerCase()}`;
      const disposition = response.headers.get('Content-Disposition') || response.headers.get('content-disposition');
      if (disposition) {
        const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (match && match[1]) {
          filename = match[1].replace(/['"]/g, '');
        }
      }

      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);

      return { filename, size: blob.size };
    },

    /**
     * Get recent export audit log.
     * @param {Object} params { limit, offset }
     */
    async getExportHistory(params = {}) {
      return await global.DealFlowAPI.get(`/api/v1/reports/exports${buildQuery(params)}`, true);
    }
  };

  global.ReportsAPI = ReportsAPI;
})(typeof window !== 'undefined' ? window : this);
