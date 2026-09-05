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
      return await global.DealFlowAPI.get('/api/v1/system/demo-readiness', true);
    },

    /**
     * Fetch application system info and feature flags.
     * GET /api/v1/system/info
     */
    async getSystemInfo() {
      return await global.DealFlowAPI.get('/api/v1/system/info', true);
    }
  };

  global.SystemAPI = SystemAPI;
})(typeof window !== 'undefined' ? window : this);
