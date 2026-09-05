/**
 * DealFlow360 — Billing Engine API Client
 * Connects to /api/v1/orders/{order_id}/billing and /api/v1/billing/generate-due endpoints.
 */
(function (global) {
  'use strict';

  const BillingAPI = {
    /**
     * List billing invoices for sales order.
     * GET /api/v1/orders/{order_id}/billing
     */
    async getOrderBilling(orderId) {
      return global.DealFlowAPI.get(`/api/v1/orders/${orderId}/billing`, true);
    },

    /**
     * Initialize one-time & recurring billing for sales order.
     * POST /api/v1/orders/{order_id}/billing/initialize
     */
    async initializeOrderBilling(orderId) {
      return global.DealFlowAPI.post(`/api/v1/orders/${orderId}/billing/initialize`, {}, true);
    },

    /**
     * Idempotently generate recurring invoices due as of date.
     * POST /api/v1/billing/generate-due?as_of=...
     */
    async generateDueInvoices(asOfDate = null) {
      const qs = asOfDate ? `?as_of=${encodeURIComponent(asOfDate)}` : '';
      return global.DealFlowAPI.post(`/api/v1/billing/generate-due${qs}`, {}, true);
    }
  };

  global.BillingAPI = BillingAPI;
})(typeof window !== 'undefined' ? window : this);
