/**
 * DealFlow360 — Deal Alerts API Client
 * Connects to /api/v1/deal-alerts endpoints.
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

  const DealAlertsAPI = {
    /**
     * List deal alerts with optional filters.
     * GET /api/v1/deal-alerts
     */
    async list(params = {}) {
      return global.DealFlowAPI.get(`/api/v1/deal-alerts${buildQuery(params)}`, true);
    },

    /**
     * Get detail of single deal alert.
     * GET /api/v1/deal-alerts/{id}
     */
    async get(id) {
      return global.DealFlowAPI.get(`/api/v1/deal-alerts/${id}`, true);
    },

    /**
     * Acknowledge deal alert.
     * POST /api/v1/deal-alerts/{id}/acknowledge
     */
    async acknowledge(id) {
      return global.DealFlowAPI.post(`/api/v1/deal-alerts/${id}/acknowledge`, {}, true);
    },

    /**
     * Resolve deal alert.
     * POST /api/v1/deal-alerts/{id}/resolve
     */
    async resolve(id, resolutionNote) {
      return global.DealFlowAPI.post(`/api/v1/deal-alerts/${id}/resolve`, {
        resolution_note: resolutionNote
      }, true);
    },

    /**
     * Dismiss deal alert.
     * POST /api/v1/deal-alerts/{id}/dismiss
     */
    async dismiss(id, reason = null) {
      return global.DealFlowAPI.post(`/api/v1/deal-alerts/${id}/dismiss`, {
        reason: reason
      }, true);
    },

    /**
     * Trigger nudge for deal alert.
     * POST /api/v1/deal-alerts/{id}/nudge
     */
    async nudge(id, payload = {}) {
      return global.DealFlowAPI.post(`/api/v1/deal-alerts/${id}/nudge`, payload, true);
    },

    /**
     * Escalate deal alert to management.
     * POST /api/v1/deal-alerts/{id}/escalate
     */
    async escalate(id, payload = {}) {
      return global.DealFlowAPI.post(`/api/v1/deal-alerts/${id}/escalate`, payload, true);
    }
  };

  global.DealAlertsAPI = DealAlertsAPI;
})(typeof window !== 'undefined' ? window : this);
