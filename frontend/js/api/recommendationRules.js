/**
 * DealFlow360 — Recommendation Rules API Client
 * Manages product affinity, cross-sell pairings, and upsell configuration rules.
 */
(function (global) {
  'use strict';

  const RecommendationRulesAPI = {
    async list(params = {}) {
      const query = new URLSearchParams();
      if (params.source_product_id) query.append('source_product_id', params.source_product_id);
      if (params.suggested_product_id) query.append('suggested_product_id', params.suggested_product_id);
      if (params.is_active !== undefined && params.is_active !== '') query.append('is_active', params.is_active);
      if (params.is_promoted !== undefined && params.is_promoted !== '') query.append('is_promoted', params.is_promoted);
      if (params.limit !== undefined) query.append('limit', params.limit);
      if (params.offset !== undefined) query.append('offset', params.offset);

      const qs = query.toString() ? `?${query.toString()}` : '';
      return global.DealFlowAPI.get(`/api/v1/recommendation-rules${qs}`, true);
    },

    async get(id) {
      return global.DealFlowAPI.get(`/api/v1/recommendation-rules/${id}`, true);
    },

    async create(payload) {
      return global.DealFlowAPI.post('/api/v1/recommendation-rules', payload, true);
    },

    async update(id, payload) {
      return global.DealFlowAPI.request(`/api/v1/recommendation-rules/${id}`, {
        method: 'PATCH',
        body: payload
      }, true);
    }
  };

  global.RecommendationRulesAPI = RecommendationRulesAPI;
})(typeof window !== 'undefined' ? window : this);
