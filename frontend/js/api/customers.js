/**
 * DealFlow360 — Customers API Client
 */
(function (global) {
  'use strict';

  const CustomersAPI = {
    async list(params = {}) {
      const query = new URLSearchParams();
      if (params.tier_id) query.append('tier_id', params.tier_id);
      if (params.is_active !== undefined && params.is_active !== '') query.append('is_active', params.is_active);
      if (params.search) query.append('search', params.search);
      if (params.limit !== undefined) query.append('limit', params.limit);
      if (params.offset !== undefined) query.append('offset', params.offset);

      const qs = query.toString() ? `?${query.toString()}` : '';
      return global.DealFlowAPI.get(`/api/v1/customers${qs}`, true);
    },

    async get(id) {
      return global.DealFlowAPI.get(`/api/v1/customers/${id}`, true);
    },

    async create(payload) {
      return global.DealFlowAPI.post('/api/v1/customers', payload, true);
    },

    async update(id, payload) {
      return global.DealFlowAPI.request(`/api/v1/customers/${id}`, {
        method: 'PATCH',
        body: payload
      }, true);
    }
  };

  global.CustomersAPI = CustomersAPI;
})(typeof window !== 'undefined' ? window : this);
