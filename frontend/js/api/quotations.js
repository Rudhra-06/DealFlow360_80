/**
 * DealFlow360 — Quotations & Commercial Deal Intelligence API Client
 * Connects directly to backend endpoints for Quotation management, line items,
 * recalculation, submission, approvals, recommendations, what-if, and audit trail.
 */
(function (global) {
  'use strict';

  const QuotationsAPI = {
    /**
     * List quotations with optional backend filters.
     * GET /api/v1/quotations
     */
    async list(params = {}) {
      const query = new URLSearchParams();
      if (params.status) query.append('status', params.status);
      if (params.customer_id) query.append('customer_id', params.customer_id);
      if (params.sales_rep_id) query.append('sales_rep_id', params.sales_rep_id);
      if (params.search) query.append('search', params.search);
      if (params.limit !== undefined) query.append('limit', params.limit);
      if (params.offset !== undefined) query.append('offset', params.offset);

      const qs = query.toString() ? `?${query.toString()}` : '';
      return global.DealFlowAPI.get(`/api/v1/quotations${qs}`, true);
    },

    /**
     * Get single quotation details with lines and risk reasons.
     * GET /api/v1/quotations/{id}
     */
    async get(id) {
      return global.DealFlowAPI.get(`/api/v1/quotations/${id}`, true);
    },

    /**
     * Create new quotation header.
     * POST /api/v1/quotations
     */
    async create(payload) {
      return global.DealFlowAPI.post('/api/v1/quotations', payload, true);
    },

    /**
     * Update quotation header (payment_terms_days, order_discount_pct).
     * PATCH /api/v1/quotations/{id}
     */
    async update(id, payload) {
      return global.DealFlowAPI.request(`/api/v1/quotations/${id}`, {
        method: 'PATCH',
        body: payload
      }, true);
    },

    /**
     * Add product line item to quotation.
     * POST /api/v1/quotations/{id}/lines
     */
    async addLine(quotationId, payload) {
      return global.DealFlowAPI.post(`/api/v1/quotations/${quotationId}/lines`, payload, true);
    },

    /**
     * Update quotation line item (quantity, line_discount_pct, billing_plan_id).
     * PATCH /api/v1/quotations/{id}/lines/{lineId}
     */
    async updateLine(quotationId, lineId, payload) {
      return global.DealFlowAPI.request(`/api/v1/quotations/${quotationId}/lines/${lineId}`, {
        method: 'PATCH',
        body: payload
      }, true);
    },

    /**
     * Remove quotation line item.
     * DELETE /api/v1/quotations/{id}/lines/{lineId}
     */
    async removeLine(quotationId, lineId) {
      return global.DealFlowAPI.request(`/api/v1/quotations/${quotationId}/lines/${lineId}`, {
        method: 'DELETE'
      }, true);
    },

    /**
     * Explicitly recalculate quotation commercial metrics.
     * POST /api/v1/quotations/{id}/recalculate
     */
    async recalculate(id) {
      return global.DealFlowAPI.post(`/api/v1/quotations/${id}/recalculate`, {}, true);
    },

    /**
     * Cancel a quotation.
     * POST /api/v1/quotations/{id}/cancel
     */
    async cancel(id) {
      return global.DealFlowAPI.post(`/api/v1/quotations/${id}/cancel`, {}, true);
    },

    /**
     * Submit quotation for automatic approval routing evaluation.
     * POST /api/v1/quotations/{id}/submit
     */
    async submit(id) {
      return global.DealFlowAPI.post(`/api/v1/quotations/${id}/submit`, {}, true);
    },

    /**
     * Get quotation audit trail events.
     * GET /api/v1/quotations/{id}/audit
     */
    async getAudit(id) {
      return global.DealFlowAPI.get(`/api/v1/quotations/${id}/audit`, true);
    },

    /**
     * Get quotation approval steps and triggers.
     * GET /api/v1/quotations/{id}/approvals
     */
    async getApprovals(id) {
      return global.DealFlowAPI.get(`/api/v1/quotations/${id}/approvals`, true);
    },

    /**
     * Approve an approval step.
     * POST /api/v1/quotations/{id}/approvals/{stepId}/approve
     */
    async approveStep(quotationId, stepId, reason = null) {
      const payload = reason ? { reason } : {};
      return global.DealFlowAPI.post(`/api/v1/quotations/${quotationId}/approvals/${stepId}/approve`, payload, true);
    },

    /**
     * Reject an approval step with mandatory reason.
     * POST /api/v1/quotations/{id}/approvals/{stepId}/reject
     */
    async rejectStep(quotationId, stepId, reason) {
      return global.DealFlowAPI.post(`/api/v1/quotations/${quotationId}/approvals/${stepId}/reject`, { reason }, true);
    },

    /**
     * Return quotation for revision with mandatory reason.
     * POST /api/v1/quotations/{id}/approvals/{stepId}/return
     */
    async returnStep(quotationId, stepId, reason) {
      return global.DealFlowAPI.post(`/api/v1/quotations/${quotationId}/approvals/${stepId}/return`, { reason }, true);
    },

    /**
     * Get ranked upsell/cross-sell recommendations for a quotation.
     * GET /api/v1/quotations/{id}/recommendations
     */
    async getRecommendations(id) {
      return global.DealFlowAPI.get(`/api/v1/quotations/${id}/recommendations`, true);
    },

    /**
     * Add upsell recommendation directly to quotation.
     * POST /api/v1/quotations/{id}/recommendations/{ruleId}/add
     */
    async addRecommendation(quotationId, ruleId) {
      return global.DealFlowAPI.post(`/api/v1/quotations/${quotationId}/recommendations/${ruleId}/add`, {}, true);
    },

    /**
     * Persistently dismiss an upsell recommendation for a quotation.
     * POST /api/v1/quotations/{id}/recommendations/{ruleId}/dismiss
     */
    async dismissRecommendation(quotationId, ruleId) {
      return global.DealFlowAPI.post(`/api/v1/quotations/${quotationId}/recommendations/${ruleId}/dismiss`, {}, true);
    },

    /**
     * Run non-persistent What-If hypothetical simulation.
     * POST /api/v1/quotations/{id}/what-if
     */
    async runWhatIf(id, payload) {
      return global.DealFlowAPI.post(`/api/v1/quotations/${id}/what-if`, payload, true);
    }
  };

  global.QuotationsAPI = QuotationsAPI;
})(typeof window !== 'undefined' ? window : this);
