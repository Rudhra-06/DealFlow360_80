/**
 * DealFlow360 — Orders API Client
 * Connects to /api/v1/orders endpoints.
 */
(function (global) {
  'use strict';

  const OrdersAPI = {
    /**
     * List sales orders with role-aware filtering.
     * GET /api/v1/orders
     */
    async list(params = {}) {
      const query = new URLSearchParams();
      if (params.status) query.append('status', params.status);
      if (params.customer_id) query.append('customer_id', params.customer_id);
      if (params.search) query.append('search', params.search);
      if (params.limit) query.append('limit', params.limit);
      if (params.offset) query.append('offset', params.offset);

      const qs = query.toString();
      const endpoint = qs ? `/api/v1/orders?${qs}` : '/api/v1/orders';
      return global.DealFlowAPI.get(endpoint, true);
    },

    /**
     * Get detailed sales order by ID.
     * GET /api/v1/orders/{id}
     */
    async get(id) {
      return global.DealFlowAPI.get(`/api/v1/orders/${id}`, true);
    },

    /**
     * Get sales order associated with quotation ID.
     * GET /api/v1/orders/by-quotation/{quotation_id}
     */
    async getByQuotation(quotationId) {
      return global.DealFlowAPI.get(`/api/v1/orders/by-quotation/${quotationId}`, true);
    },

    /**
     * Get audit timeline events for sales order.
     * GET /api/v1/orders/{id}/audit
     */
    async getAudit(id) {
      return global.DealFlowAPI.get(`/api/v1/orders/${id}/audit`, true);
    }
  };

  global.OrdersAPI = OrdersAPI;
})(typeof window !== 'undefined' ? window : this);
