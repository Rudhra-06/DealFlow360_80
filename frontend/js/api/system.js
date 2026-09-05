/**
 * DealFlow360 — System & Demo Readiness API Client
 * Connects to /api/v1/system endpoints.
 */
(function (global) {
  'use strict';

  const SystemAPI = {
    /**
     * Fetch backend system demo readiness check results.
     * GET /api/v1/system/demo-readiness
     */
    async getDemoReadiness() {
      return await global.DealFlowAPI.request('/system/demo-readiness', { method: 'GET' });
    },

    /**
     * Fetch application system info and feature flags.
     * GET /api/v1/system/info
     */
    async getSystemInfo() {
      return await global.DealFlowAPI.request('/system/info', { method: 'GET' });
    }
  };

  global.SystemAPI = SystemAPI;
})(typeof window !== 'undefined' ? window : this);
