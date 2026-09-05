/**
 * DealFlow360 — Role-Aware Navigation & Future Module Definitions
 * Provides role presentation formatting, sidebar menu configuration, and placeholder handling.
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

    // Fallback: title case
    return roleName
      .toLowerCase()
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  // Master definitions of all navigation items with SVG icons
  const NAV_ITEMS_DEF = {
    // Shared / Core
    dashboard: {
      id: 'dashboard',
      label: 'Dashboard',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>`,
      active: true,
      status: 'active'
    },
    quotations: {
      id: 'quotations',
      label: 'Quotations',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>`,
      active: false,
      status: 'Coming Soon',
      description: 'Quotation intelligence and automated CPQ pricing will be available in Phase 2.'
    },
    pipeline: {
      id: 'pipeline',
      label: 'Pipeline',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>`,
      active: false,
      status: 'Coming Soon',
      description: 'Deal pipeline visibility and stage tracking will be available in an upcoming module.'
    },
    approvals: {
      id: 'approvals',
      label: 'Approvals',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
      active: false,
      status: 'Coming Soon',
      description: 'Multi-tier commercial discount and margin approval workflows are in development.'
    },
    customers: {
      id: 'customers',
      label: 'Customers',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
      active: false,
      status: 'Coming Soon',
      description: 'Customer Master, credit limits, and account intelligence are scheduled for upcoming release.'
    },
    inventory: {
      id: 'inventory',
      label: 'Inventory',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>`,
      active: false,
      status: 'Coming Soon',
      description: 'Multi-warehouse stock allocation and availability reservations will be released in an upcoming module.'
    },
    billing: {
      id: 'billing',
      label: 'Billing',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>`,
      active: false,
      status: 'Coming Soon',
      description: 'Commercial deal invoicing and payment tracking will be available in future phases.'
    },
    dealHealth: {
      id: 'dealHealth',
      label: 'Deal Health',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>`,
      active: false,
      status: 'Coming Soon',
      description: 'Commercial margin risk and deal velocity health scoring are coming soon.'
    },
    reports: {
      id: 'reports',
      label: 'Reports',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`,
      active: false,
      status: 'Coming Soon',
      description: 'Enterprise executive reporting and export analytics will be available in future phases.'
    },
    settings: {
      id: 'settings',
      label: 'Settings',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`,
      active: false,
      status: 'Coming Soon',
      description: 'System administration, RBAC policies, and audit logs are coming soon.'
    },

    // Customer Specific Portal Items
    customerOverview: {
      id: 'customerOverview',
      label: 'Overview',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>`,
      active: true,
      status: 'active'
    },
    customerQuotes: {
      id: 'customerQuotes',
      label: 'My Quotations',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`,
      active: false,
      status: 'Coming Soon',
      description: 'Self-service quotation review and acceptance will be available in the Customer Portal module.'
    },
    customerNegotiations: {
      id: 'customerNegotiations',
      label: 'Negotiations',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`,
      active: false,
      status: 'Coming Soon',
      description: 'Direct quote feedback and counter-proposal negotiations will be available in future releases.'
    },
    customerOrders: {
      id: 'customerOrders',
      label: 'Orders',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/></svg>`,
      active: false,
      status: 'Coming Soon',
      description: 'Order fulfillment status and dispatch tracking will be available in upcoming customer features.'
    },
    customerAccount: {
      id: 'customerAccount',
      label: 'Account',
      icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`,
      active: false,
      status: 'Coming Soon',
      description: 'Customer company profile and billing contact settings are coming soon.'
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
      'approvals',
      'customers',
      'inventory',
      'billing',
      'dealHealth',
      'reports',
      'settings'
    ],
    SALES_REP: [
      'dashboard',
      'quotations',
      'pipeline',
      'customers',
      'dealHealth'
    ],
    SALES_MANAGER: [
      'dashboard',
      'quotations',
      'pipeline',
      'approvals',
      'customers',
      'dealHealth',
      'reports'
    ],
    FINANCE_OPERATIONS: [
      'dashboard',
      'approvals',
      'customers',
      'inventory',
      'billing',
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

    /**
     * Get array of nav item objects for a given role name.
     * @param {string} roleName
     * @returns {Array<object>}
     */
    getNavItemsForRole(roleName) {
      const normalizedRole = (roleName || 'ADMIN').toUpperCase();
      const itemKeys = ROLE_NAV_MAPPINGS[normalizedRole] || ROLE_NAV_MAPPINGS.ADMIN;
      return itemKeys.map(key => NAV_ITEMS_DEF[key]).filter(Boolean);
    },

    /**
     * Render the sidebar navigation DOM for the current role.
     * @param {string} roleName
     * @param {HTMLElement} containerEl
     */
    renderSidebar(roleName, containerEl) {
      if (!containerEl) return;
      const items = this.getNavItemsForRole(roleName);
      const isCustomer = (roleName || '').toUpperCase() === 'CUSTOMER';

      const sectionTitle = isCustomer ? 'Customer Portal' : 'Main Navigation';

      let html = `<div class="nav-section-title">${sectionTitle}</div>`;

      items.forEach(item => {
        const isActive = item.active;
        const disabledClass = isActive ? 'active' : 'disabled';
        const badgeHtml = item.status && item.status !== 'active' 
          ? `<span class="nav-pill-badge">${item.status}</span>` 
          : '';

        html += `
          <a class="nav-item ${disabledClass}" 
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
      });

      containerEl.innerHTML = html;

      // Attach click handlers to notify user of Coming Soon items
      containerEl.querySelectorAll('.nav-item').forEach(el => {
        el.addEventListener('click', (e) => {
          e.preventDefault();
          const navId = el.getAttribute('data-nav-id');
          const navItem = NAV_ITEMS_DEF[navId];
          if (navItem && !navItem.active) {
            if (global.DealFlowUI && global.DealFlowUI.showComingSoonModal) {
              global.DealFlowUI.showComingSoonModal(navItem.label, navItem.description);
            } else {
              alert(`${navItem.label}: ${navItem.description}`);
            }
          }
        });
      });
    }
  };

  global.DealFlowNav = Navigation;
})(typeof window !== 'undefined' ? window : this);
