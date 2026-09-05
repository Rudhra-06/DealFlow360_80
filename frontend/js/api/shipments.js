/**
 * DealFlow360 — Shipments API Client
 * Connects to /api/v1/{order_id}/shipments endpoints.
 */
(function (global) {
  'use strict';

  const ShipmentsAPI = {
    /**
     * List shipments for sales order.
     * GET /api/v1/{order_id}/shipments
     */
    async list(orderId) {
      return global.DealFlowAPI.get(`/api/v1/${orderId}/shipments`, true);
    },

    /**
     * Generate physical shipment records from fulfillment plan allocations.
     * POST /api/v1/{order_id}/shipments/generate
     */
    async generate(orderId) {
      return global.DealFlowAPI.post(`/api/v1/${orderId}/shipments/generate`, {}, true);
    },

    /**
     * Mark shipment shipped (decrements inventory on_hand and reserved stock).
     * POST /api/v1/{order_id}/shipments/{shipment_id}/ship
     */
    async ship(orderId, shipmentId) {
      return global.DealFlowAPI.post(`/api/v1/${orderId}/shipments/${shipmentId}/ship`, {}, true);
    },

    /**
     * Mark shipment delivered to customer.
     * POST /api/v1/{order_id}/shipments/{shipment_id}/deliver
     */
    async deliver(orderId, shipmentId) {
      return global.DealFlowAPI.post(`/api/v1/${orderId}/shipments/${shipmentId}/deliver`, {}, true);
    }
  };

  global.ShipmentsAPI = ShipmentsAPI;
})(typeof window !== 'undefined' ? window : this);
