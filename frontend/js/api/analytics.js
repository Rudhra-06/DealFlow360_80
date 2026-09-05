/**
 * DealFlow360 — Analytics & Customer 360 API Client
 * Connects to /api/v1/analytics endpoints.
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

  const AnalyticsAPI = {
    async getOverview(params = {}) {
      return await global.DealFlowAPI.get(`/api/v1/analytics/overview${buildQuery(params)}`, true);
    },

    async getOverviewTrend(params = {}) {
      return await global.DealFlowAPI.get(`/api/v1/analytics/overview/trend${buildQuery(params)}`, true);
    },

    async getQuotationFunnel(params = {}) {
      return await global.DealFlowAPI.get(`/api/v1/analytics/quotation-funnel${buildQuery(params)}`, true);
    },

    async getSalesPerformance(params = {}) {
      return await global.DealFlowAPI.get(`/api/v1/analytics/sales-performance${buildQuery(params)}`, true);
    },

    async getDiscounts(params = {}) {
      return await global.DealFlowAPI.get(`/api/v1/analytics/discounts${buildQuery(params)}`, true);
    },

    async getMargins(params = {}) {
      return await global.DealFlowAPI.get(`/api/v1/analytics/margins${buildQuery(params)}`, true);
    },

    async getCustomer360(customerId) {
      return await global.DealFlowAPI.get(`/api/v1/analytics/customers/${customerId}/360`, true);
    },

    async getProducts(params = {}) {
      return await global.DealFlowAPI.get(`/api/v1/analytics/products${buildQuery(params)}`, true);
    },

    async getProductCategories(params = {}) {
      return await global.DealFlowAPI.get(`/api/v1/analytics/product-categories${buildQuery(params)}`, true);
    },

    async getRecommendations(params = {}) {
      return await global.DealFlowAPI.get(`/api/v1/analytics/recommendations${buildQuery(params)}`, true);
    },

    async getApprovals(params = {}) {
      return await global.DealFlowAPI.get(`/api/v1/analytics/approvals${buildQuery(params)}`, true);
    },

    async getNegotiations(params = {}) {
      return await global.DealFlowAPI.get(`/api/v1/analytics/negotiations${buildQuery(params)}`, true);
    },

    async getDealHealth(params = {}) {
      return await global.DealFlowAPI.get(`/api/v1/analytics/deal-health${buildQuery(params)}`, true);
    },

    async getDealHealthTrend(params = {}) {
      return await global.DealFlowAPI.get(`/api/v1/analytics/deal-health/trend${buildQuery(params)}`, true);
    },

    async getFulfillment(params = {}) {
      return await global.DealFlowAPI.get(`/api/v1/analytics/fulfillment${buildQuery(params)}`, true);
    },

    async getWarehouses(params = {}) {
      return await global.DealFlowAPI.get(`/api/v1/analytics/warehouses${buildQuery(params)}`, true);
    },

    async getBackorders(params = {}) {
      return await global.DealFlowAPI.get(`/api/v1/analytics/backorders${buildQuery(params)}`, true);
    },

    async getShipments(params = {}) {
      return await global.DealFlowAPI.get(`/api/v1/analytics/shipments${buildQuery(params)}`, true);
    },

    async getBilling(params = {}) {
      return await global.DealFlowAPI.get(`/api/v1/analytics/billing${buildQuery(params)}`, true);
    },

    async getReceivables(params = {}) {
      return await global.DealFlowAPI.get(`/api/v1/analytics/receivables${buildQuery(params)}`, true);
    },

    async getPayments(params = {}) {
      return await global.DealFlowAPI.get(`/api/v1/analytics/payments${buildQuery(params)}`, true);
    },

    async getSubscriptions(params = {}) {
      return await global.DealFlowAPI.get(`/api/v1/analytics/subscriptions${buildQuery(params)}`, true);
    },

    async getExecutiveSummaryText(params = {}) {
      return await global.DealFlowAPI.get(`/api/v1/analytics/executive-summary-text${buildQuery(params)}`, true);
    }
  };

  global.AnalyticsAPI = AnalyticsAPI;
})(typeof window !== 'undefined' ? window : this);
