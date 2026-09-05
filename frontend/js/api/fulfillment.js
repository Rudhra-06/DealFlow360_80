/**
 * DealFlow360 — Fulfillment & Multi-Warehouse Allocation API Client
 * Connects to /api/v1/{order_id}/fulfillment and /api/v1/{order_id}/backorders endpoints.
 */
(function (global) {
  'use strict';

  const FulfillmentAPI = {
    /**
     * Preview system fulfillment allocation recommendation.
     * GET /api/v1/{order_id}/fulfillment/preview
     */
    async preview(orderId) {
      return global.DealFlowAPI.get(`/api/v1/${orderId}/fulfillment/preview`, true);
    },

    /**
     * Get active fulfillment plan for sales order.
     * GET /api/v1/{order_id}/fulfillment
     */
    async getPlan(orderId) {
      return global.DealFlowAPI.get(`/api/v1/${orderId}/fulfillment`, true);
    },

    /**
     * Accept or initialize system fulfillment plan recommendation.
     * POST /api/v1/{order_id}/fulfillment/accept
     */
    async accept(orderId) {
      return global.DealFlowAPI.post(`/api/v1/${orderId}/fulfillment/accept`, {}, true);
    },

    /**
     * Manually override warehouse fulfillment allocation split.
     * POST /api/v1/{order_id}/fulfillment/manual-override
     * Payload: { allocations: [ { order_line_id: int, warehouse_id: int, quantity: float } ] }
     */
    async manualOverride(orderId, allocations) {
      return global.DealFlowAPI.post(`/api/v1/${orderId}/fulfillment/manual-override`, {
        allocations: allocations
      }, true);
    },

    /**
     * List backorders for sales order.
     * GET /api/v1/{order_id}/backorders
     */
    async listBackorders(orderId) {
      return global.DealFlowAPI.get(`/api/v1/${orderId}/backorders`, true);
    },

    /**
     * Consolidate backorders with newly arrived warehouse inventory.
     * POST /api/v1/{order_id}/backorders/consolidate
     */
    async consolidateBackorders(orderId) {
      return global.DealFlowAPI.post(`/api/v1/${orderId}/backorders/consolidate`, {}, true);
    }
  };

  global.FulfillmentAPI = FulfillmentAPI;
})(typeof window !== 'undefined' ? window : this);
