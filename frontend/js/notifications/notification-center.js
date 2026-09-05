/**
 * DealFlow360 — Notification Center UI Component & Live Alert Controller
 * Manages top-bar bell trigger, unread counts, slide-out notification center drawer,
 * and real-time live event toast dispatches.
 */
(function (global) {
  'use strict';

  class NotificationCenter {
    constructor() {
      this.notifications = [];
      this.unreadCount = 0;
      this.isDrawerOpen = false;
      this.initialized = false;
    }

    init() {
      if (this.initialized) return;
      this.initialized = true;

      this.setupWebSocketListeners();
      this.fetchNotifications();
    }

    setupWebSocketListeners() {
      if (!global.DealFlowWS) return;

      // Listen for notification creation
      global.DealFlowWS.on('notification.created', (data) => {
        this.fetchNotifications();
        const notif = data.data || data;
        global.DealFlowUI?.toast(notif.title ? `${notif.title}: ${notif.message}` : 'New notification received', 'teal');
      });

      // Listen for live negotiation & quote events
      global.DealFlowWS.on('quote.sent', (data) => {
        global.DealFlowUI?.toast(`Quotation ${data.quote_number || ''} sent to customer for review.`, 'teal');
        this.fetchNotifications();
      });

      global.DealFlowWS.on('negotiation.requested', (data) => {
        global.DealFlowUI?.toast(`New negotiation request / counter-offer received!`, 'coral');
        this.fetchNotifications();
      });

      global.DealFlowWS.on('negotiation.accepted', (data) => {
        global.DealFlowUI?.toast(`Counter-offer accepted! Revised quotation generated.`, 'teal');
        this.fetchNotifications();
      });

      global.DealFlowWS.on('negotiation.rejected', (data) => {
        global.DealFlowUI?.toast(`Negotiation request was rejected.`, 'coral');
        this.fetchNotifications();
      });

      global.DealFlowWS.on('quote.customer_confirmed', (data) => {
        global.DealFlowUI?.toast(`🎉 Customer confirmed Quotation Version ${data.version_number || ''}!`, 'teal');
        this.fetchNotifications();
      });

      global.DealFlowWS.on('approval.required', (data) => {
        global.DealFlowUI?.toast(`Commercial approval required for quotation.`, 'coral');
        this.fetchNotifications();
      });

      // Phase 5 Operational & Revenue Events
      global.DealFlowWS.on('order.created', (data) => {
        global.DealFlowUI?.toast(`Sales Order ${data.order_number || ''} created from confirmed quotation.`, 'teal');
        this.fetchNotifications();
      });

      global.DealFlowWS.on('fulfillment.reserved', (data) => {
        global.DealFlowUI?.toast(`Inventory reserved across warehouses for Order ${data.order_number || ''}.`, 'teal');
        this.fetchNotifications();
      });

      global.DealFlowWS.on('fulfillment.backordered', (data) => {
        global.DealFlowUI?.toast(`Backorder recorded for Order ${data.order_number || ''}.`, 'coral');
        this.fetchNotifications();
      });

      global.DealFlowWS.on('backorder.stock_available', (data) => {
        global.DealFlowUI?.toast(`Backordered stock is now available for consolidation!`, 'teal');
        this.fetchNotifications();
      });

      global.DealFlowWS.on('shipment.shipped', (data) => {
        global.DealFlowUI?.toast(`Shipment ${data.shipment_number || ''} has been dispatched!`, 'teal');
        this.fetchNotifications();
      });

      global.DealFlowWS.on('shipment.delivered', (data) => {
        global.DealFlowUI?.toast(`Shipment ${data.shipment_number || ''} delivered to customer.`, 'teal');
        this.fetchNotifications();
      });

      global.DealFlowWS.on('invoice.issued', (data) => {
        global.DealFlowUI?.toast(`Invoice ${data.invoice_number || ''} has been issued.`, 'teal');
        this.fetchNotifications();
      });

      global.DealFlowWS.on('payment.received', (data) => {
        global.DealFlowUI?.toast(`Payment received and allocated!`, 'teal');
        this.fetchNotifications();
      });

      global.DealFlowWS.on('subscription.changed', (data) => {
        global.DealFlowUI?.toast(`Subscription quantity updated with mid-cycle proration.`, 'teal');
        this.fetchNotifications();
      });

      global.DealFlowWS.on('subscription.cancelled', (data) => {
        global.DealFlowUI?.toast(`Subscription cancellation processed.`, 'navy');
        this.fetchNotifications();
      });
    }

    async fetchNotifications() {
      try {
        if (!global.NotificationsAPI) return;
        const res = await global.NotificationsAPI.list({ limit: 30 });
        if (res.ok && res.data) {
          this.notifications = res.data;
          this.unreadCount = this.notifications.filter(n => !n.is_read).length;
          this.updateBellUI();
          if (this.isDrawerOpen) {
            this.renderDrawerContent();
          }
        }
      } catch (e) {
        console.warn('[NotificationCenter] Failed to fetch notifications:', e);
      }
    }

    updateBellUI() {
      const badgeEl = document.getElementById('header-notif-badge');
      if (badgeEl) {
        if (this.unreadCount > 0) {
          badgeEl.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
          badgeEl.style.display = 'inline-flex';
        } else {
          badgeEl.style.display = 'none';
        }
      }
    }

    toggleDrawer() {
      if (this.isDrawerOpen) {
        this.closeDrawer();
      } else {
        this.openDrawer();
      }
    }

    openDrawer() {
      this.isDrawerOpen = true;
      const backdrop = document.getElementById('dealflow-drawer-backdrop');
      const panel = document.getElementById('dealflow-drawer-panel');

      if (!panel || !backdrop) return;

      panel.innerHTML = `
        <div class="notification-drawer animate-fade-in">
          <div class="notif-drawer-header">
            <div style="display: flex; align-items: center; gap: 8px;">
              <h3 style="margin: 0; font-size: var(--font-size-md); color: var(--color-navy);">Notifications</h3>
              ${this.unreadCount > 0 ? `<span class="badge badge-coral" style="font-size: 0.65rem;">${this.unreadCount} Unread</span>` : ''}
            </div>

            <div style="display: flex; align-items: center; gap: 8px;">
              ${this.unreadCount > 0 ? `
                <button id="btn-mark-all-read" class="btn btn-secondary btn-sm" style="font-size: 0.7rem; padding: 2px 6px;">
                  Mark All Read
                </button>
              ` : ''}
              <button id="btn-close-notif-drawer" class="modal-close" style="font-size: 1.25rem;">&times;</button>
            </div>
          </div>

          <div id="notif-drawer-body" class="notif-drawer-body">
            <!-- Rendered by renderDrawerContent() -->
          </div>
        </div>
      `;

      this.renderDrawerContent();

      backdrop.classList.add('show');
      panel.classList.add('open');

      document.getElementById('btn-close-notif-drawer')?.addEventListener('click', () => this.closeDrawer());
      backdrop.addEventListener('click', () => this.closeDrawer(), { once: true });

      document.getElementById('btn-mark-all-read')?.addEventListener('click', async () => {
        try {
          await global.NotificationsAPI?.markAllRead();
          this.notifications.forEach(n => { n.is_read = true; });
          this.unreadCount = 0;
          this.updateBellUI();
          this.renderDrawerContent();
          global.DealFlowUI?.toast('All notifications marked as read', 'teal');
        } catch (e) {
          console.warn('Failed to mark all read:', e);
        }
      });
    }

    closeDrawer() {
      this.isDrawerOpen = false;
      const backdrop = document.getElementById('dealflow-drawer-backdrop');
      const panel = document.getElementById('dealflow-drawer-panel');
      if (backdrop) backdrop.classList.remove('show');
      if (panel) panel.classList.remove('open');
    }

    renderDrawerContent() {
      const bodyEl = document.getElementById('notif-drawer-body');
      if (!bodyEl) return;

      if (this.notifications.length === 0) {
        bodyEl.innerHTML = `
          <div style="text-align: center; padding: 50px 20px; color: var(--color-text-muted);">
            <div style="width: 44px; height: 44px; border-radius: 50%; background: var(--color-background); color: var(--color-text-secondary); display: flex; align-items: center; justify-content: center; margin: 0 auto 12px;">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
            </div>
            <div style="font-weight: 600; font-size: var(--font-size-sm); color: var(--color-navy); margin-bottom: 4px;">You're all caught up</div>
            <div style="font-size: var(--font-size-xs);">No notifications recorded for your account.</div>
          </div>
        `;
        return;
      }

      bodyEl.innerHTML = `
        <div class="notif-list">
          ${this.notifications.map(n => {
            const timeStr = new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' · ' + new Date(n.created_at).toLocaleDateString();
            const unreadClass = !n.is_read ? 'unread' : '';

            return `
              <div class="notif-card ${unreadClass}" data-notif-id="${n.id}" data-quote-id="${n.quotation_id || ''}">
                <div class="notif-card-top">
                  <span class="notif-card-title">${n.title}</span>
                  <span class="notif-card-time">${timeStr}</span>
                </div>
                <div class="notif-card-msg">${n.message}</div>
                ${!n.is_read ? `<span class="notif-unread-dot"></span>` : ''}
              </div>
            `;
          }).join('')}
        </div>
      `;

      bodyEl.querySelectorAll('.notif-card').forEach(card => {
        card.addEventListener('click', async () => {
          const notifId = parseInt(card.dataset.notifId, 10);
          const quoteId = parseInt(card.dataset.quoteId, 10);

          // Mark as read locally and remotely
          const notif = this.notifications.find(n => n.id === notifId);
          if (notif && !notif.is_read) {
            notif.is_read = true;
            this.unreadCount = Math.max(0, this.unreadCount - 1);
            this.updateBellUI();
            card.classList.remove('unread');
            card.querySelector('.notif-unread-dot')?.remove();
            global.NotificationsAPI?.markRead(notifId).catch(console.warn);
          }

          if (quoteId) {
            this.closeDrawer();
            const role = (global.DealFlowAuth?.getCurrentUser()?.role?.name || '').toUpperCase();
            if (role === 'CUSTOMER') {
              global.DealFlowApp?.switchView('portal-quotation', { quoteId });
            } else {
              global.DealFlowApp?.switchView('quotation-builder', { quoteId });
            }
          }
        });
      });
    }
  }

  global.DealFlowNotificationCenter = new NotificationCenter();
})(typeof window !== 'undefined' ? window : this);
