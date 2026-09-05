/**
 * DealFlow360 — Payments API Client
 * Connects to /api/v1/payments endpoints.
 */
(function (global) {
  'use strict';

  const PaymentsAPI = {
    /**
     * List recorded payments with filters.
     * GET /api/v1/payments
     */
    async list(params = {}) {
      const query = new URLSearchParams();
      if (params.customer_id) query.append('customer_id', params.customer_id);
      if (params.status) query.append('status', params.status);
      if (params.limit) query.append('limit', params.limit);
      if (params.offset) query.append('offset', params.offset);

      const qs = query.toString();
      const endpoint = qs ? `/api/v1/payments?${qs}` : '/api/v1/payments';
      return global.DealFlowAPI.get(endpoint, true);
    },

    /**
     * Get payment details by ID.
     * GET /api/v1/payments/{id}
     */
    async get(id) {
      return global.DealFlowAPI.get(`/api/v1/payments/${id}`, true);
    },

    /**
     * Record customer payment and allocate across invoices.
     * POST /api/v1/payments
     * Payload: { customer_id, amount, currency, payment_method, reference, allocations: [ { invoice_id, amount } ] }
     */
    async record(payload) {
      return global.DealFlowAPI.post('/api/v1/payments', payload, true);
    }
  };

  global.PaymentsAPI = PaymentsAPI;
})(typeof window !== 'undefined' ? window : this);
