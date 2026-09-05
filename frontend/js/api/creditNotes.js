/**
 * DealFlow360 — Credit Notes API Client
 * Connects to /api/v1/credit-notes endpoints.
 */
(function (global) {
  'use strict';

  const CreditNotesAPI = {
    /**
     * List credit notes with filters.
     * GET /api/v1/credit-notes
     */
    async list(params = {}) {
      const query = new URLSearchParams();
      if (params.status) query.append('status', params.status);
      if (params.customer_id) query.append('customer_id', params.customer_id);
      if (params.sales_order_id) query.append('sales_order_id', params.sales_order_id);
      if (params.limit) query.append('limit', params.limit);
      if (params.offset) query.append('offset', params.offset);

      const qs = query.toString();
      const endpoint = qs ? `/api/v1/credit-notes?${qs}` : '/api/v1/credit-notes';
      return global.DealFlowAPI.get(endpoint, true);
    },

    /**
     * Get credit note by ID.
     * GET /api/v1/credit-notes/{id}
     */
    async get(id) {
      return global.DealFlowAPI.get(`/api/v1/credit-notes/${id}`, true);
    },

    /**
     * Apply credit note amount to outstanding invoice balance.
     * POST /api/v1/credit-notes/{id}/apply
     */
    async apply(id, invoiceId) {
      return global.DealFlowAPI.post(`/api/v1/credit-notes/${id}/apply`, {
        invoice_id: invoiceId
      }, true);
    }
  };

  global.CreditNotesAPI = CreditNotesAPI;
})(typeof window !== 'undefined' ? window : this);
