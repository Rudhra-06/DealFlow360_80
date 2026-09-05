/**
 * DealFlow360 — Centralized API Client Layer
 * Handles HTTP requests, headers, Bearer tokens, JSON serialization, and error normalization.
 */
(function (global) {
  'use strict';

  const config = global.DealFlowConfig || {
    API_BASE_URL: 'http://127.0.0.1:8000'
  };

  /**
   * Custom API Error class with HTTP status code and user-friendly message.
   */
  class ApiError extends Error {
    constructor(message, status = 0, detail = null) {
      super(message);
      this.name = 'ApiError';
      this.status = status;
      this.detail = detail;
      this.ok = false;
      this.data = null;
    }
  }

  const API = {
    /**
     * Core request dispatcher.
     * @param {string} path - URL path (e.g., '/api/v1/auth/me')
     * @param {object} options - Fetch options (method, body, headers, etc.)
     * @param {boolean} requiresAuth - Whether to attach Bearer token
     * @returns {Promise<any>}
     */
    async request(path, options = {}, requiresAuth = false) {
      const baseUrl = (global.DealFlowConfig && global.DealFlowConfig.API_BASE_URL) || config.API_BASE_URL;
      const url = `${baseUrl.replace(/\/$/, '')}/${path.replace(/^\//, '')}`;

      const headers = {
        'Accept': 'application/json',
        ...(options.headers || {})
      };

      if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(options.body);
      }

      if (requiresAuth && global.DealFlowAuth) {
        const token = global.DealFlowAuth.getAccessToken();
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
      }

      let response;
      try {
        response = await fetch(url, {
          ...options,
          headers
        });
      } catch (networkError) {
        // Network failure (CORS, offline, server not running)
        throw new ApiError(
          'Unable to connect to DealFlow360. Please verify the backend service is running and try again.',
          0,
          networkError.message
        );
      }

      // Parse JSON response body if present
      let data = null;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        try {
          data = await response.json();
        } catch (e) {
          data = null;
        }
      }

      if (!response.ok) {
        let userMessage = 'An unexpected error occurred.';

        if (response.status === 401) {
          userMessage = (data && data.detail) ? data.detail : 'Invalid email or password.';
        } else if (response.status === 403) {
          userMessage = (data && data.detail) ? data.detail : 'Your account is currently inactive.';
        } else if (response.status === 422) {
          userMessage = 'Please check your inputs and try again.';
          if (data && Array.isArray(data.detail) && data.detail.length > 0) {
            userMessage = data.detail.map(d => d.msg || 'Invalid input').join(', ');
          }
        } else if (response.status === 503) {
          userMessage = (data && data.detail) ? data.detail : 'Service is temporarily unavailable.';
        } else if (response.status >= 500) {
          userMessage = 'DealFlow360 server encountered an issue. Please try again later.';
        } else if (data && data.detail && typeof data.detail === 'string') {
          userMessage = data.detail;
        }

        throw new ApiError(userMessage, response.status, data);
      }

      if (data !== null && typeof data === 'object') {
        try {
          if (!('ok' in data)) {
            Object.defineProperty(data, 'ok', { value: true, enumerable: false, writable: true, configurable: true });
          }
          if (!('data' in data)) {
            Object.defineProperty(data, 'data', { value: data, enumerable: false, writable: true, configurable: true });
          }
        } catch (e) {
          // ignore if non-extensible
        }
      } else if (data === null) {
        data = { ok: true, data: null };
      }

      return data;
    },

    /**
     * Helper for GET requests.
     */
    async get(path, requiresAuth = true) {
      return this.request(path, { method: 'GET' }, requiresAuth);
    },

    /**
     * Helper for POST requests.
     */
    async post(path, body = {}, requiresAuth = true) {
      return this.request(path, { method: 'POST', body }, requiresAuth);
    },

    /**
     * Check root API health.
     * GET /health or GET /api/v1/health
     */
    async getHealth() {
      try {
        const res = await this.get('/api/v1/health', false);
        return { ok: true, data: res };
      } catch (err) {
        return { ok: false, error: err.message, status: err.status };
      }
    },

    /**
     * Check PostgreSQL database connectivity health.
     * GET /api/v1/health/db
     */
    async getDatabaseHealth() {
      try {
        const res = await this.get('/api/v1/health/db', false);
        return { ok: true, data: res };
      } catch (err) {
        return { ok: false, error: err.message, status: err.status };
      }
    }
  };

  global.DealFlowAPI = API;
  global.ApiError = ApiError;
})(typeof window !== 'undefined' ? window : this);
