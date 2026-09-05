/**
 * DealFlow360 — Frontend Configuration
 * Centralized configuration for API base URL and application settings.
 */
(function (global) {
  'use strict';

  const Config = {
    // Configurable API base URL (can be updated for different environments)
    API_BASE_URL: 'http://127.0.0.1:8000',
    
    // API Version prefix
    API_V1_PREFIX: '/api/v1',
    
    // Storage keys (centralized)
    STORAGE_TOKEN_KEY: 'dealflow360_access_token',
    STORAGE_USER_KEY: 'dealflow360_current_user',
    
    // Application info
    APP_NAME: 'DealFlow360',
    APP_TAGLINE: 'Enterprise B2B Deal Management and Commercial Operations Platform',
    PHASE: 'Phase 1'
  };

  global.DealFlowConfig = Config;
})(typeof window !== 'undefined' ? window : this);
