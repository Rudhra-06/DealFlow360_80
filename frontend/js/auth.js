/**
 * DealFlow360 — Centralized Authentication Service
 * Manages JWT tokens, safe user profile state, login, and logout.
 */
(function (global) {
  'use strict';

  const config = global.DealFlowConfig || {
    API_BASE_URL: 'http://127.0.0.1:8000',
    STORAGE_TOKEN_KEY: 'dealflow360_access_token',
    STORAGE_USER_KEY: 'dealflow360_current_user'
  };

  const Auth = {
    /**
     * Retrieve the stored JWT access token.
     * @returns {string|null}
     */
    getAccessToken() {
      try {
        return localStorage.getItem(config.STORAGE_TOKEN_KEY);
      } catch (e) {
        return null;
      }
    },

    /**
     * Store the JWT access token.
     * @param {string} token
     */
    setAccessToken(token) {
      if (token && typeof token === 'string') {
        localStorage.setItem(config.STORAGE_TOKEN_KEY, token);
      }
    },

    /**
     * Remove the stored JWT access token.
     */
    clearAccessToken() {
      localStorage.removeItem(config.STORAGE_TOKEN_KEY);
    },

    /**
     * Retrieve the cached current user profile.
     * @returns {object|null}
     */
    getCurrentUser() {
      try {
        const raw = localStorage.getItem(config.STORAGE_USER_KEY);
        return raw ? JSON.parse(raw) : null;
      } catch (e) {
        return null;
      }
    },

    /**
     * Store the safe current user profile.
     * (Never stores passwords or secrets)
     * @param {object} user
     */
    setCurrentUser(user) {
      if (user && typeof user === 'object') {
        // Strip out any sensitive fields if present defensively
        const safeUser = {
          id: user.id,
          email: user.email,
          full_name: user.full_name,
          is_active: user.is_active,
          role_id: user.role_id,
          role: user.role ? {
            id: user.role.id,
            name: user.role.name,
            description: user.role.description
          } : null,
          created_at: user.created_at,
          updated_at: user.updated_at
        };
        localStorage.setItem(config.STORAGE_USER_KEY, JSON.stringify(safeUser));
      }
    },

    /**
     * Remove the cached current user profile.
     */
    clearCurrentUser() {
      localStorage.removeItem(config.STORAGE_USER_KEY);
    },

    /**
     * Quick check if a token exists in storage.
     * Note: Authorization must still be verified with backend.
     * @returns {boolean}
     */
    hasToken() {
      return Boolean(this.getAccessToken());
    },

    /**
     * Authenticate user with credentials, store token, and fetch profile.
     * @param {string} email
     * @param {string} password
     * @returns {Promise<object>} User profile
     */
    async login(email, password) {
      const api = global.DealFlowAPI;
      if (!api) {
        throw new Error('API service layer not loaded');
      }

      // 1. Post credentials to /api/v1/auth/login
      const tokenData = await api.post('/api/v1/auth/login', {
        email: email.trim(),
        password: password
      }, false);

      if (!tokenData || !tokenData.access_token) {
        throw new Error('Invalid response from authentication server');
      }

      // 2. Store access token centrally
      this.setAccessToken(tokenData.access_token);

      // 3. Request current user profile from GET /api/v1/auth/me
      const userProfile = await api.get('/api/v1/auth/me', true);

      // 4. Cache safe user profile
      this.setCurrentUser(userProfile);

      return userProfile;
    },

    /**
     * Validate active token against backend and return fresh user profile.
     * @returns {Promise<object>}
     */
    async fetchCurrentUser() {
      const api = global.DealFlowAPI;
      if (!api) {
        throw new Error('API service layer not loaded');
      }

      const userProfile = await api.get('/api/v1/auth/me', true);
      this.setCurrentUser(userProfile);
      return userProfile;
    },

    /**
     * Clear all authentication data and redirect to login page.
     * @param {string|null} message Optional reason to pass in query string
     */
    logout(message = null) {
      this.clearAccessToken();
      this.clearCurrentUser();
      
      let redirectUrl = 'login.html';
      if (message) {
        redirectUrl += `?reason=${encodeURIComponent(message)}`;
      }
      window.location.href = redirectUrl;
    },

    /**
     * Handle expired or invalidated session.
     */
    handleSessionExpired() {
      this.clearAccessToken();
      this.clearCurrentUser();
      window.location.href = 'login.html?reason=session_expired';
    },

    /**
     * Handle inactive user account.
     */
    handleInactiveAccount() {
      this.clearAccessToken();
      this.clearCurrentUser();
      window.location.href = 'login.html?reason=account_inactive';
    },

    /**
     * Route guard for protected pages (e.g. index.html).
     * If unauthenticated, immediately redirects to login.html.
     * If token exists, verifies with /api/v1/auth/me.
     * @returns {Promise<object>} Verified user
     */
    async requireAuth() {
      const token = this.getAccessToken();
      if (!token) {
        this.logout();
        return null;
      }

      try {
        const user = await this.fetchCurrentUser();
        if (!user.is_active) {
          this.handleInactiveAccount();
          return null;
        }
        return user;
      } catch (err) {
        if (err.status === 401) {
          this.handleSessionExpired();
        } else if (err.status === 403) {
          this.handleInactiveAccount();
        } else {
          // In case of temporary network error during health check, allow retry or handle
          console.warn('[DealFlow360 Auth] Verification error:', err.message);
          throw err;
        }
        return null;
      }
    }
  };

  global.DealFlowAuth = Auth;
})(typeof window !== 'undefined' ? window : this);
