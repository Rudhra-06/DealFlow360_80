/**
 * DealFlow360 — Subscriptions API Client
 * Connects to /api/v1/subscriptions endpoints.
 */
(function (global) {
  'use strict';

  const SubscriptionsAPI = {
    /**
     * List active customer subscriptions with filters.
     * GET /api/v1/subscriptions
     */
    async list(params = {}) {
      const query = new URLSearchParams();
      if (params.status) query.append('status', params.status);
      if (params.customer_id) query.append('customer_id', params.customer_id);
      if (params.sales_order_id) query.append('sales_order_id', params.sales_order_id);
      if (params.limit) query.append('limit', params.limit);
      if (params.offset) query.append('offset', params.offset);

      const qs = query.toString();
      const endpoint = qs ? `/api/v1/subscriptions?${qs}` : '/api/v1/subscriptions';
      return global.DealFlowAPI.get(endpoint, true);
    },

    /**
     * Get subscription details by ID (including billing schedules).
     * GET /api/v1/subscriptions/{id}
     */
    async get(id) {
      return global.DealFlowAPI.get(`/api/v1/subscriptions/${id}`, true);
    },

    /**
     * Modify subscription quantity with mid-cycle proration calculation.
     * POST /api/v1/subscriptions/{id}/change-quantity
     */
    async changeQuantity(id, payload) {
      return global.DealFlowAPI.post(`/api/v1/subscriptions/${id}/change-quantity`, payload, true);
    },

    /**
     * Cancel subscription according to plan cancellation policy.
     * POST /api/v1/subscriptions/{id}/cancel
     */
    async cancel(id, payload) {
      return global.DealFlowAPI.post(`/api/v1/subscriptions/${id}/cancel`, payload, true);
    }
  };

  global.SubscriptionsAPI = SubscriptionsAPI;
})(typeof window !== 'undefined' ? window : this);
