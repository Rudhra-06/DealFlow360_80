/**
 * DealFlow360 — Billing Plans API Client
 */
(function (global) {
  'use strict';

  const BillingPlansAPI = {
    async list(params = {}) {
      const query = new URLSearchParams();
      if (params.billing_type) query.append('billing_type', params.billing_type);
      if (params.is_active !== undefined && params.is_active !== '') query.append('is_active', params.is_active);
      if (params.limit !== undefined) query.append('limit', params.limit);
      if (params.offset !== undefined) query.append('offset', params.offset);

      const qs = query.toString() ? `?${query.toString()}` : '';
      return global.DealFlowAPI.get(`/api/v1/billing-plans${qs}`, true);
    },

    async get(id) {
      return global.DealFlowAPI.get(`/api/v1/billing-plans/${id}`, true);
    },

    async create(payload) {
      return global.DealFlowAPI.post('/api/v1/billing-plans', payload, true);
    },

    async update(id, payload) {
      return global.DealFlowAPI.request(`/api/v1/billing-plans/${id}`, {
        method: 'PATCH',
        body: payload
      }, true);
    }
  };

  global.BillingPlansAPI = BillingPlansAPI;
})(typeof window !== 'undefined' ? window : this);
