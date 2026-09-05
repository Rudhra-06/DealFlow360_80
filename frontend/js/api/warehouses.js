/**
 * DealFlow360 — Warehouses API Client
 */
(function (global) {
  'use strict';

  const WarehousesAPI = {
    async list(params = {}) {
      const query = new URLSearchParams();
      if (params.is_active !== undefined && params.is_active !== '') query.append('is_active', params.is_active);
      if (params.limit !== undefined) query.append('limit', params.limit);
      if (params.offset !== undefined) query.append('offset', params.offset);

      const qs = query.toString() ? `?${query.toString()}` : '';
      return global.DealFlowAPI.get(`/api/v1/warehouses${qs}`, true);
    },

    async get(id) {
      return global.DealFlowAPI.get(`/api/v1/warehouses/${id}`, true);
    },

    async create(payload) {
      return global.DealFlowAPI.post('/api/v1/warehouses', payload, true);
    },

    async update(id, payload) {
      return global.DealFlowAPI.request(`/api/v1/warehouses/${id}`, {
        method: 'PATCH',
        body: payload
      }, true);
    }
  };

  global.WarehousesAPI = WarehousesAPI;
})(typeof window !== 'undefined' ? window : this);
