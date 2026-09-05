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
    PHASE: 'Phase 1',

    // Razorpay Integration Configuration
    RAZORPAY_KEY_ID: 'rzp_test_TYVhOpGcj7mkYU',

    // Firebase Web App & Analytics Configuration
    FIREBASE_CONFIG: {
      apiKey: "AIzaSyCQMQ9teEy9X_4Fe0JpPPKRCCysvY8v89w",
      authDomain: "dealflow360-9bb5c.firebaseapp.com",
      projectId: "dealflow360-9bb5c",
      storageBucket: "dealflow360-9bb5c.firebasestorage.app",
      messagingSenderId: "510730462531",
      appId: "1:510730462531:web:28f1ca48cf4c5445c8bbf6",
      measurementId: "G-N8TXSVSW0K"
    }
  };

  global.DealFlowConfig = Config;
})(typeof window !== 'undefined' ? window : this);
