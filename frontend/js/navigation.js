/**
 * DealFlow360 — Role-Aware Navigation & Sales Workspace Routing
 * Provides role presentation formatting, sidebar menu configuration, and view switching.
 */
(function (global) {
  'use strict';

  /**
   * Formats backend role constants (e.g. SALES_MANAGER) into user-friendly labels.
   * Note: This is for display presentation only; backend RBAC is authoritative.
   * @param {string} roleName
   * @returns {string}
   */
  function formatRole(roleName) {
    if (!roleName || typeof roleName !== 'string') return 'User';
    
    const roleMap = {
      'ADMIN': 'Admin',
      'SALES_REP': 'Sales Rep',
      'SALES_MANAGER': 'Sales Manager',
      'FINANCE_OPERATIONS': 'Finance / Operations',
      'CUSTOMER': 'Customer'
    };

    if (roleMap[roleName.toUpperCase()]) {
      return roleMap[roleName.toUpperCase()];
    }

    return roleName
      .toLowerCase()
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  // Master definitions of all navigation items with SVG icons
  const NAV_ITEMS_DEF = {
    // Core Overview
    dashboard: {
      id: 'dashboard',
      label: 'Dashboard',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>`,
      active: true,
      status: 'active',
      section: 'main'
    },

    // Sales Workspace (Phase 3 Active)
    quotations: {
      id: 'quotations',
      label: 'Quotations',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`,
      active: true,
      status: 'active',
      section: 'sales'
    },
    pipeline: {
      id: 'pipeline',
      label: 'Pipeline Board',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>`,
      active: true,
      status: 'active',
      section: 'sales'
    },
    approvals: {
      id: 'approvals',
      label: 'Approval Queue',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
      active: true,
      status: 'active',
      section: 'sales'
    },
    negotiations: {
      id: 'negotiations',
      label: 'Negotiation Inbox',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`,
      active: true,
      status: 'active',
      section: 'sales'
    },

    // Operations Workspace (Phase 5)
    orders: {
      id: 'orders',
      label: 'Sales Orders',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>`,
      active: true,
      status: 'active',
      section: 'operations'
    },

    // Billing & Revenue Workspace (Phase 5)
    invoices: {
      id: 'invoices',
      label: 'Invoices',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`,
      active: true,
      status: 'active',
      section: 'billing_section'
    },
    subscriptions: {
      id: 'subscriptions',
      label: 'Subscriptions',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>`,
      active: true,
      status: 'active',
      section: 'billing_section'
    },
    payments: {
      id: 'payments',
      label: 'Payments',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>`,
      active: true,
      status: 'active',
      section: 'billing_section'
    },

    // Master Data Workspace
    customers: {
      id: 'customers',
      label: 'Customers',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
      active: true,
      status: 'active',
      section: 'master'
    },
    products: {
      id: 'products',
      label: 'Products',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>`,
      active: true,
      status: 'active',
      section: 'master'
    },
    inventory: {
      id: 'inventory',
      label: 'Inventory',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`,
      active: true,
      status: 'active',
      section: 'master'
    },

    // Commercial Config & Hub
    settings: {
      id: 'settings',
      label: 'Commercial Config',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`,
      active: true,
      status: 'active',
      section: 'master'
    },
    billing: {
      id: 'billing',
      label: 'Billing Plans',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>`,
      active: true,
      status: 'Config',
      targetTab: 'billing-plans',
      section: 'master'
    },

    // Future Modules (Phase 6+)
    dealHealth: {
      id: 'dealHealth',
      label: 'Deal Health',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>`,
      active: false,
      status: 'Coming Soon',
      description: 'Commercial margin protection and deal health velocity scoring are scheduled for Phase 6 release.',
      section: 'future'
    },
    reports: {
      id: 'reports',
      label: 'Reports & Analytics',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`,
      active: false,
      status: 'Coming Soon',
      description: 'Executive reporting, ledger export, and revenue analytics will be available in Phase 6.',
      section: 'future'
    },

    // Customer Specific Portal Items
    customerOverview: {
      id: 'customerOverview',
      label: 'Portal Overview',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>`,
      active: true,
      status: 'active',
      section: 'customer'
    },
    customerQuotes: {
      id: 'customerQuotes',
      label: 'My Quotations',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`,
      active: true,
      status: 'active',
      section: 'customer'
    },
    customerNegotiations: {
      id: 'customerNegotiations',
      label: 'Negotiations & Messages',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`,
      active: true,
      status: 'active',
      section: 'customer'
    },
    customerOrders: {
      id: 'customerOrders',
      label: 'Orders',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/></svg>`,
      active: false,
      status: 'Coming Soon',
      description: 'Customer self-service shipment tracking will be available in upcoming portal enhancements.',
      section: 'customer'
    },
    customerAccount: {
      id: 'customerAccount',
      label: 'Account',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`,
      active: false,
      status: 'Coming Soon',
      description: 'Customer company profile and billing contact settings are coming soon.',
      section: 'customer'
    }
  };

  /**
   * Role-based menu configuration mapping
   */
  const ROLE_NAV_MAPPINGS = {
    ADMIN: [
      'dashboard',
      'quotations',
      'pipeline',
      'negotiations',
      'approvals',
      'orders',
      'invoices',
      'subscriptions',
      'payments',
      'customers',
      'products',
      'inventory',
      'settings',
      'billing',
      'dealHealth',
      'reports'
    ],
    FINANCE_OPERATIONS: [
      'dashboard',
      'orders',
      'invoices',
      'subscriptions',
      'payments',
      'quotations',
      'approvals',
      'products',
      'inventory',
      'billing',
      'settings',
      'dealHealth',
      'reports'
    ],
    SALES_REP: [
      'dashboard',
      'quotations',
      'pipeline',
      'negotiations',
      'orders',
      'invoices',
      'customers',
      'products',
      'inventory',
      'settings',
      'dealHealth'
    ],
    SALES_MANAGER: [
      'dashboard',
      'quotations',
      'pipeline',
      'negotiations',
      'approvals',
      'orders',
      'invoices',
      'subscriptions',
      'customers',
      'products',
      'inventory',
      'settings',
      'dealHealth',
      'reports'
    ],
    CUSTOMER: [
      'customerOverview',
      'customerQuotes',
      'customerNegotiations',
      'customerOrders',
      'customerAccount'
    ]
  };

  const Navigation = {
    formatRole,
    NAV_ITEMS_DEF,
    currentNavId: 'dashboard',

    getNavItemsForRole(roleName) {
      const normalizedRole = (roleName || 'ADMIN').toUpperCase();
      const itemKeys = ROLE_NAV_MAPPINGS[normalizedRole] || ROLE_NAV_MAPPINGS.ADMIN;
      return itemKeys.map(key => NAV_ITEMS_DEF[key]).filter(Boolean);
    },

    /**
     * Render the sidebar navigation DOM for the current role.
     */
    renderSidebar(roleName, containerEl, onNavigate) {
      if (!containerEl) return;
      const items = this.getNavItemsForRole(roleName);
      const isCustomer = (roleName || '').toUpperCase() === 'CUSTOMER';

      if (isCustomer) {
        let html = `<div class="nav-section-title">Customer Portal</div>`;
        items.forEach(item => {
          html += this._renderNavItemHtml(item);
        });
        containerEl.innerHTML = html;
      } else {
        // Group internal items into Workspace sections
        const salesItems = items.filter(i => i.section === 'sales' || i.id === 'dashboard');
        const opsItems = items.filter(i => i.section === 'operations');
        const billingItems = items.filter(i => i.section === 'billing_section');
        const masterItems = items.filter(i => i.section === 'master');
        const otherItems = items.filter(i => i.section === 'future');

        let html = `<div class="nav-section-title">Sales Workspace</div>`;
        salesItems.forEach(item => { html += this._renderNavItemHtml(item); });

        if (opsItems.length > 0) {
          html += `<div class="nav-section-title" style="margin-top: 14px;">Operations Hub</div>`;
          opsItems.forEach(item => { html += this._renderNavItemHtml(item); });
        }

        if (billingItems.length > 0) {
          html += `<div class="nav-section-title" style="margin-top: 14px;">Billing & Revenue</div>`;
          billingItems.forEach(item => { html += this._renderNavItemHtml(item); });
        }

        if (masterItems.length > 0) {
          html += `<div class="nav-section-title" style="margin-top: 14px;">Master Data & Config</div>`;
          masterItems.forEach(item => { html += this._renderNavItemHtml(item); });
        }

        if (otherItems.length > 0) {
          html += `<div class="nav-section-title" style="margin-top: 14px;">Upcoming Modules</div>`;
          otherItems.forEach(item => { html += this._renderNavItemHtml(item); });
        }

        containerEl.innerHTML = html;
      }

      // Attach click handlers
      containerEl.querySelectorAll('.nav-item').forEach(el => {
        el.addEventListener('click', (e) => {
          e.preventDefault();
          const navId = el.getAttribute('data-nav-id');
          const navItem = NAV_ITEMS_DEF[navId];

          if (!navItem) return;

          if (!navItem.active) {
            if (global.DealFlowUI && global.DealFlowUI.showComingSoonModal) {
              global.DealFlowUI.showComingSoonModal(navItem.label, navItem.description);
            }
            return;
          }

          this.setActiveNav(navId, containerEl);

          if (typeof onNavigate === 'function') {
            onNavigate(navId, navItem.targetTab || null);
          }
        });
      });
    },

    _renderNavItemHtml(item) {
      const isCurrent = this.currentNavId === item.id;
      const activeClass = isCurrent ? 'active' : '';
      const disabledClass = !item.active ? 'disabled' : '';
      const badgeHtml = item.status && item.status !== 'active' 
        ? `<span class="nav-pill-badge">${item.status}</span>` 
        : '';

      return `
        <a class="nav-item ${activeClass} ${disabledClass}" 
           data-nav-id="${item.id}"
           role="button"
           tabindex="0"
           title="${item.label}">
          <div class="nav-item-left">
            <span class="nav-item-icon">${item.icon}</span>
            <span class="nav-item-text">${item.label}</span>
          </div>
          ${badgeHtml}
        </a>
      `;
    },

    setActiveNav(navId, containerEl) {
      this.currentNavId = navId;
      if (!containerEl) containerEl = document.getElementById('sidebar-nav-container');
      if (containerEl) {
        containerEl.querySelectorAll('.nav-item').forEach(el => {
          if (el.getAttribute('data-nav-id') === navId) {
            el.classList.add('active');
          } else {
            el.classList.remove('active');
          }
        });
      }
    }
  };

  global.DealFlowNav = Navigation;
})(typeof window !== 'undefined' ? window : this);
