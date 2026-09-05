/**
 * DealFlow360 — Inventory API Client
 */
(function (global) {
  'use strict';

  const InventoryAPI = {
    async list(params = {}) {
      const query = new URLSearchParams();
      if (params.warehouse_id) query.append('warehouse_id', params.warehouse_id);
      if (params.product_id) query.append('product_id', params.product_id);
      if (params.limit !== undefined) query.append('limit', params.limit);
      if (params.offset !== undefined) query.append('offset', params.offset);

      const qs = query.toString() ? `?${query.toString()}` : '';
      return global.DealFlowAPI.get(`/api/v1/inventory${qs}`, true);
    },

    async get(id) {
      return global.DealFlowAPI.get(`/api/v1/inventory/${id}`, true);
    },

    async create(payload) {
      return global.DealFlowAPI.post('/api/v1/inventory', payload, true);
    },

    async update(id, payload) {
      return global.DealFlowAPI.request(`/api/v1/inventory/${id}`, {
        method: 'PATCH',
        body: payload
      }, true);
    }
  };

  global.InventoryAPI = InventoryAPI;
})(typeof window !== 'undefined' ? window : this);
