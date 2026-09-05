/**
 * DealFlow360 — Internal Negotiation & Versioning API Client
 * Used by SALES_REP, SALES_MANAGER, and ADMIN to manage customer collaboration,
 * send approved quotes, review customer counter-offers, accept/reject terms, and inspect diffs.
 */
(function (global) {
  'use strict';

  const NegotiationAPI = {
    /**
     * Send approved quotation to customer portal.
     * POST /api/v1/quotations/{id}/send-to-customer
     */
    async sendToCustomer(id) {
      return global.DealFlowAPI.post(`/api/v1/quotations/${id}/send-to-customer`, {}, true);
    },

    /**
     * List internal quotation version snapshots.
     * GET /api/v1/quotations/{id}/versions
     */
    async listVersions(id) {
      return global.DealFlowAPI.get(`/api/v1/quotations/${id}/versions`, true);
    },

    /**
     * Get specific quotation version snapshot.
     * GET /api/v1/quotations/{id}/versions/{versionNumber}
     */
    async getVersion(id, versionNumber) {
      return global.DealFlowAPI.get(`/api/v1/quotations/${id}/versions/${versionNumber}`, true);
    },

    /**
     * Compare two internal quotation versions.
     * GET /api/v1/quotations/{id}/versions/compare?from_version=X&to_version=Y
     */
    async compareVersions(id, fromVersion, toVersion) {
      const query = new URLSearchParams({
        from_version: fromVersion,
        to_version: toVersion
      });
      return global.DealFlowAPI.get(`/api/v1/quotations/${id}/versions/compare?${query.toString()}`, true);
    },

    /**
     * Get negotiation inbox requests for a quotation.
     * GET /api/v1/quotations/{id}/negotiation-inbox
     */
    async getNegotiationInbox(id) {
      return global.DealFlowAPI.get(`/api/v1/quotations/${id}/negotiation-inbox`, true);
    },

    /**
     * Sales rep accepts customer counter-offer and triggers recalculation/reapproval.
     * POST /api/v1/quotations/{id}/negotiation-requests/{requestId}/accept
     */
    async acceptCounterOffer(id, requestId) {
      return global.DealFlowAPI.post(`/api/v1/quotations/${id}/negotiation-requests/${requestId}/accept`, {}, true);
    },

    /**
     * Sales rep rejects customer counter-offer with mandatory reason.
     * POST /api/v1/quotations/{id}/negotiation-requests/{requestId}/reject
     */
    async rejectCounterOffer(id, requestId, resolutionReason) {
      return global.DealFlowAPI.post(`/api/v1/quotations/${id}/negotiation-requests/${requestId}/reject`, {
        resolution_reason: resolutionReason,
        rejection_reason: resolutionReason
      }, true);
    },

    /**
     * Sales rep replies to customer comment/line question.
     * POST /api/v1/quotations/{id}/messages
     */
    async replyMessage(id, payload) {
      return global.DealFlowAPI.post(`/api/v1/quotations/${id}/messages`, payload, true);
    }
  };

  global.NegotiationAPI = NegotiationAPI;
})(typeof window !== 'undefined' ? window : this);
