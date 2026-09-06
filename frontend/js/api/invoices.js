/**
 * DealFlow360 — Invoices API Client
 * Connects to /api/v1/invoices endpoints.
 */
(function (global) {
  'use strict';

  const InvoicesAPI = {
    /**
     * List customer invoices with filters.
     * GET /api/v1/invoices
     */
    async list(params = {}) {
      const query = new URLSearchParams();
      if (params.status) query.append('status', params.status);
      if (params.customer_id) query.append('customer_id', params.customer_id);
      if (params.sales_order_id) query.append('sales_order_id', params.sales_order_id);
      if (params.invoice_type) query.append('invoice_type', params.invoice_type);
      if (params.limit) query.append('limit', params.limit);
      if (params.offset) query.append('offset', params.offset);

      const qs = query.toString();
      const endpoint = qs ? `/api/v1/invoices?${qs}` : '/api/v1/invoices';
      return global.DealFlowAPI.get(endpoint, true);
    },

    /**
     * Get invoice details by ID.
     * GET /api/v1/invoices/{id}
     */
    async get(id) {
      return global.DealFlowAPI.get(`/api/v1/invoices/${id}`, true);
    },

    /**
     * Download Invoice PDF.
     * GET /api/v1/invoices/{id}/pdf
     */
    async downloadPdf(id) {
      return global.ReportsAPI.exportReport({
        report_type: 'INVOICE',
        format: 'PDF',
        invoice_id: id
      });
    }
  };

  global.InvoicesAPI = InvoicesAPI;
})(typeof window !== 'undefined' ? window : this);
