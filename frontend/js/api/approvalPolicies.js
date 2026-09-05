/**
 * DealFlow360 — Approval Policies API Client
 */
(function (global) {
  'use strict';

  const ApprovalPoliciesAPI = {
    async list(params = {}) {
      const query = new URLSearchParams();
      if (params.customer_tier_id) query.append('customer_tier_id', params.customer_tier_id);
      if (params.approval_role) query.append('approval_role', params.approval_role);
      if (params.is_active !== undefined && params.is_active !== '') query.append('is_active', params.is_active);
      if (params.effective_only !== undefined) query.append('effective_only', params.effective_only);
      if (params.limit !== undefined) query.append('limit', params.limit);
      if (params.offset !== undefined) query.append('offset', params.offset);

      const qs = query.toString() ? `?${query.toString()}` : '';
      return global.DealFlowAPI.get(`/api/v1/approval-policies${qs}`, true);
    },

    async get(id) {
      return global.DealFlowAPI.get(`/api/v1/approval-policies/${id}`, true);
    },

    async create(payload) {
      return global.DealFlowAPI.post('/api/v1/approval-policies', payload, true);
    },

    async update(id, payload) {
      return global.DealFlowAPI.request(`/api/v1/approval-policies/${id}`, {
        method: 'PATCH',
        body: payload
      }, true);
    }
  };

  global.ApprovalPoliciesAPI = ApprovalPoliciesAPI;
})(typeof window !== 'undefined' ? window : this);
