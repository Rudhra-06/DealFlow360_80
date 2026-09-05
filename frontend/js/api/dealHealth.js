/**
 * DealFlow360 — Deal Health API Client
 * Connects to /api/v1/deal-health and /api/v1/deal-health-config endpoints.
 */
(function (global) {
  'use strict';

  function buildQuery(params = {}) {
    const qs = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== null && value !== undefined && value !== '') {
        qs.append(key, value);
      }
    }
    const str = qs.toString();
    return str ? '?' + str : '';
  }

  const DealHealthAPI = {
    /**
     * Get active Deal Health policy configuration.
     * GET /api/v1/deal-health-config
     */
    async getConfig() {
      return global.DealFlowAPI.get('/api/v1/deal-health-config', true);
    },

    /**
     * Update active Deal Health policy configuration.
     * PATCH /api/v1/deal-health-config/{id}
     */
    async updateConfig(id, payload) {
      return global.DealFlowAPI.request(`/api/v1/deal-health-config/${id}`, {
        method: 'PATCH',
        body: payload
      }, true);
    },

    /**
     * List deal health summaries with optional filters.
     * GET /api/v1/deal-health
     */
    async list(params = {}) {
      return global.DealFlowAPI.get(`/api/v1/deal-health${buildQuery(params)}`, true);
    },

    /**
     * Get latest deal health snapshot for quotation.
     * GET /api/v1/deal-health/quotations/{quotation_id}
     */
    async getQuotationHealth(quotationId) {
      return global.DealFlowAPI.get(`/api/v1/deal-health/quotations/${quotationId}`, true);
    },

    /**
     * Recalculate deal health snapshot for quotation.
     * POST /api/v1/deal-health/quotations/{quotation_id}/evaluate
     */
    async evaluateQuotationHealth(quotationId) {
      return global.DealFlowAPI.post(`/api/v1/deal-health/quotations/${quotationId}/evaluate`, {}, true);
    },

    /**
     * Get historical health snapshots for quotation.
     * GET /api/v1/deal-health/quotations/{quotation_id}/history
     */
    async getHistory(quotationId, limit = 50) {
      return global.DealFlowAPI.get(`/api/v1/deal-health/quotations/${quotationId}/history?limit=${limit}`, true);
    },

    /**
     * Trigger bulk deal health scan.
     * POST /api/v1/deal-health/run-scan
     */
    async runScan(payload = {}) {
      return global.DealFlowAPI.post('/api/v1/deal-health/run-scan', payload, true);
    }
  };

  global.DealHealthAPI = DealHealthAPI;
})(typeof window !== 'undefined' ? window : this);
