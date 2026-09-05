/**
 * DealFlow360 — Notifications API Client
 */
(function (global) {
  'use strict';

  const NotificationsAPI = {
    /**
     * List notifications for authenticated user.
     * GET /api/v1/notifications
     */
    async list(params = {}) {
      const query = new URLSearchParams();
      if (params.unread_only !== undefined) query.append('unread_only', params.unread_only);
      if (params.limit !== undefined) query.append('limit', params.limit);
      if (params.offset !== undefined) query.append('offset', params.offset);

      const qs = query.toString() ? `?${query.toString()}` : '';
      return global.DealFlowAPI.get(`/api/v1/notifications${qs}`, true);
    },

    /**
     * Mark single notification as read.
     * PUT /api/v1/notifications/{id}/read
     */
    async markRead(id) {
      return global.DealFlowAPI.request(`/api/v1/notifications/${id}/read`, {
        method: 'PUT'
      }, true);
    },

    /**
     * Mark all notifications as read.
     * PUT /api/v1/notifications/read-all
     */
    async markAllRead() {
      return global.DealFlowAPI.request('/api/v1/notifications/read-all', {
        method: 'PUT'
      }, true);
    }
  };

  global.NotificationsAPI = NotificationsAPI;
})(typeof window !== 'undefined' ? window : this);
