/**
 * DealFlow360 — Customer Portal API Client
 * Connects directly to safe /api/v1/portal/ endpoints with strict RBAC boundary (CUSTOMER role only).
 * Zero internal data leakage (no unit costs, line margins, risk scores, or internal approval policies).
 */
(function (global) {
  'use strict';

  const PortalAPI = {
    /**
     * List quotations assigned to the authenticated customer.
     * GET /api/v1/portal/quotations
     */
    async listQuotations(params = {}) {
      const query = new URLSearchParams();
      if (params.status) query.append('status', params.status);
      const qs = query.toString() ? `?${query.toString()}` : '';
      return global.DealFlowAPI.get(`/api/v1/portal/quotations${qs}`, true);
    },

    /**
     * Get safe details of single quotation.
     * GET /api/v1/portal/quotations/{id}
     */
    async getQuotation(id) {
      return global.DealFlowAPI.get(`/api/v1/portal/quotations/${id}`, true);
    },

    /**
     * Customer confirms quotation terms for the current version.
     * POST /api/v1/portal/quotations/{id}/confirm
     */
    async confirmQuotation(id) {
      return global.DealFlowAPI.post(`/api/v1/portal/quotations/${id}/confirm`, {}, true);
    },

    /**
     * List historical version snapshots of quotation.
     * GET /api/v1/portal/quotations/{id}/versions
     */
    async listVersions(id) {
      return global.DealFlowAPI.get(`/api/v1/portal/quotations/${id}/versions`, true);
    },

    /**
     * Compare two versions of quotation for customer review.
     * GET /api/v1/portal/quotations/{id}/versions/compare?from_version=X&to_version=Y
     */
    async compareVersions(id, fromVersion, toVersion) {
      const query = new URLSearchParams({
        from_version: fromVersion,
        to_version: toVersion
      });
      return global.DealFlowAPI.get(`/api/v1/portal/quotations/${id}/versions/compare?${query.toString()}`, true);
    },

    /**
     * Post a customer comment or line question.
     * POST /api/v1/portal/quotations/{id}/messages
     */
    async postMessage(id, payload) {
      return global.DealFlowAPI.post(`/api/v1/portal/quotations/${id}/messages`, payload, true);
    },

    /**
     * Submit a customer counter-offer / change request.
     * POST /api/v1/portal/quotations/{id}/counter-offer
     */
    async submitCounterOffer(id, payload) {
      return global.DealFlowAPI.post(`/api/v1/portal/quotations/${id}/counter-offer`, payload, true);
    },

    /**
     * List invoices assigned to the authenticated customer.
     * GET /api/v1/portal/invoices
     */
    async listInvoices(params = {}) {
      const query = new URLSearchParams();
      if (params.status) query.append('status', params.status);
      const qs = query.toString() ? `?${query.toString()}` : '';
      return global.DealFlowAPI.get(`/api/v1/portal/invoices${qs}`, true);
    },

    /**
     * Get safe details of single invoice.
     * GET /api/v1/portal/invoices/{id}
     */
    async getInvoice(id) {
      return global.DealFlowAPI.get(`/api/v1/portal/invoices/${id}`, true);
    },

    /**
     * Export PDF document for customer invoice.
     * GET /api/v1/portal/invoices/{id}/pdf
     */
    async exportInvoicePdf(id) {
      const endpoint = `/api/v1/portal/invoices/${id}/pdf`;
      const token = global.DealFlowAuth ? global.DealFlowAuth.getToken() : null;
      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`${global.DealFlowAPI.BASE_URL}${endpoint}`, { headers });
      if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to export PDF`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Invoice_${id}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    }
  };

  global.PortalAPI = PortalAPI;
})(typeof window !== 'undefined' ? window : this);
