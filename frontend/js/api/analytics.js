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
      return await global.DealFlowAPI.request(`/analytics/overview${buildQuery(params)}`, { method: 'GET' });
    },

    async getOverviewTrend(params = {}) {
      return await global.DealFlowAPI.request(`/analytics/overview/trend${buildQuery(params)}`, { method: 'GET' });
    },

    async getQuotationFunnel(params = {}) {
      return await global.DealFlowAPI.request(`/analytics/quotation-funnel${buildQuery(params)}`, { method: 'GET' });
    },

    async getSalesPerformance(params = {}) {
      return await global.DealFlowAPI.request(`/analytics/sales-performance${buildQuery(params)}`, { method: 'GET' });
    },

    async getDiscounts(params = {}) {
      return await global.DealFlowAPI.request(`/analytics/discounts${buildQuery(params)}`, { method: 'GET' });
    },

    async getMargins(params = {}) {
      return await global.DealFlowAPI.request(`/analytics/margins${buildQuery(params)}`, { method: 'GET' });
    },

    async getCustomer360(customerId) {
      return await global.DealFlowAPI.request(`/analytics/customers/${customerId}/360`, { method: 'GET' });
    },

    async getProducts(params = {}) {
      return await global.DealFlowAPI.request(`/analytics/products${buildQuery(params)}`, { method: 'GET' });
    },

    async getProductCategories(params = {}) {
      return await global.DealFlowAPI.request(`/analytics/product-categories${buildQuery(params)}`, { method: 'GET' });
    },

    async getRecommendations(params = {}) {
      return await global.DealFlowAPI.request(`/analytics/recommendations${buildQuery(params)}`, { method: 'GET' });
    },

    async getApprovals(params = {}) {
      return await global.DealFlowAPI.request(`/analytics/approvals${buildQuery(params)}`, { method: 'GET' });
    },

    async getNegotiations(params = {}) {
      return await global.DealFlowAPI.request(`/analytics/negotiations${buildQuery(params)}`, { method: 'GET' });
    },

    async getDealHealth(params = {}) {
      return await global.DealFlowAPI.request(`/analytics/deal-health${buildQuery(params)}`, { method: 'GET' });
    },

    async getDealHealthTrend(params = {}) {
      return await global.DealFlowAPI.request(`/analytics/deal-health/trend${buildQuery(params)}`, { method: 'GET' });
    },

    async getFulfillment(params = {}) {
      return await global.DealFlowAPI.request(`/analytics/fulfillment${buildQuery(params)}`, { method: 'GET' });
    },

    async getWarehouses(params = {}) {
      return await global.DealFlowAPI.request(`/analytics/warehouses${buildQuery(params)}`, { method: 'GET' });
    },

    async getBackorders(params = {}) {
      return await global.DealFlowAPI.request(`/analytics/backorders${buildQuery(params)}`, { method: 'GET' });
    },

    async getShipments(params = {}) {
      return await global.DealFlowAPI.request(`/analytics/shipments${buildQuery(params)}`, { method: 'GET' });
    },

    async getBilling(params = {}) {
      return await global.DealFlowAPI.request(`/analytics/billing${buildQuery(params)}`, { method: 'GET' });
    },

    async getReceivables(params = {}) {
      return await global.DealFlowAPI.request(`/analytics/receivables${buildQuery(params)}`, { method: 'GET' });
    },

    async getPayments(params = {}) {
      return await global.DealFlowAPI.request(`/analytics/payments${buildQuery(params)}`, { method: 'GET' });
    },

    async getSubscriptions(params = {}) {
      return await global.DealFlowAPI.request(`/analytics/subscriptions${buildQuery(params)}`, { method: 'GET' });
    },

    async getExecutiveSummaryText(params = {}) {
      return await global.DealFlowAPI.request(`/analytics/executive-summary-text${buildQuery(params)}`, { method: 'GET' });
    }
  };

  global.AnalyticsAPI = AnalyticsAPI;
})(typeof window !== 'undefined' ? window : this);
