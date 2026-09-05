/**
 * DealFlow360 — Discount Policies API Client
 */
(function (global) {
  'use strict';

  const DiscountPoliciesAPI = {
    async list(params = {}) {
      const query = new URLSearchParams();
      if (params.customer_tier_id) query.append('customer_tier_id', params.customer_tier_id);
      if (params.product_category_id) query.append('product_category_id', params.product_category_id);
      if (params.product_id) query.append('product_id', params.product_id);
      if (params.is_active !== undefined && params.is_active !== '') query.append('is_active', params.is_active);
      if (params.effective_only !== undefined) query.append('effective_only', params.effective_only);
      if (params.limit !== undefined) query.append('limit', params.limit);
      if (params.offset !== undefined) query.append('offset', params.offset);

      const qs = query.toString() ? `?${query.toString()}` : '';
      return global.DealFlowAPI.get(`/api/v1/discount-policies${qs}`, true);
    },

    async get(id) {
      return global.DealFlowAPI.get(`/api/v1/discount-policies/${id}`, true);
    },

    async create(payload) {
      return global.DealFlowAPI.post('/api/v1/discount-policies', payload, true);
    },

    async update(id, payload) {
      return global.DealFlowAPI.request(`/api/v1/discount-policies/${id}`, {
        method: 'PATCH',
        body: payload
      }, true);
    },

    async resolve(params = {}) {
      const query = new URLSearchParams();
      if (params.customer_tier_id) query.append('customer_tier_id', params.customer_tier_id);
      if (params.product_id) query.append('product_id', params.product_id);
      if (params.as_of) query.append('as_of', params.as_of);

      const qs = query.toString() ? `?${query.toString()}` : '';
      return global.DealFlowAPI.get(`/api/v1/discount-policies/resolve${qs}`, true);
    }
  };

  global.DiscountPoliciesAPI = DiscountPoliciesAPI;
})(typeof window !== 'undefined' ? window : this);
