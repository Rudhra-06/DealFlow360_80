/**
 * DealFlow360 — Application Router & Workspace Controller
 * Handles route authentication, view mounting, live system health, and role-governed navigation.
 */
(function (global) {
  'use strict';

  let currentViewName = 'dashboard';

  const VIEW_TITLES = {
    'dashboard': { title: 'Dashboard', breadcrumb: 'DealFlow360 / Workspace Overview' },
    'quotations': { title: 'Sales Quotations', breadcrumb: 'DealFlow360 / Sales Workspace / Quotations' },
    'pipeline': { title: 'Pipeline Board', breadcrumb: 'DealFlow360 / Sales Workspace / Pipeline Board' },
    'quotation-builder': { title: 'Quotation Builder & Deal Intelligence', breadcrumb: 'DealFlow360 / Sales Workspace / Quotation Builder' },
    'negotiations': { title: 'Negotiation Inbox', breadcrumb: 'DealFlow360 / Sales Workspace / Negotiation Inbox' },
    'approvals': { title: 'Approval Queue', breadcrumb: 'DealFlow360 / Commercial Governance / Approval Queue' },
    'recommendation-rules': { title: 'Recommendation Rules', breadcrumb: 'DealFlow360 / Commercial Configuration / Recommendation Rules' },
    'customers': { title: 'Customers Master', breadcrumb: 'DealFlow360 / Master Data / Customers' },
    'products': { title: 'Products Catalog', breadcrumb: 'DealFlow360 / Master Data / Products' },
    'inventory': { title: 'Inventory Stock', breadcrumb: 'DealFlow360 / Master Data / Inventory' },
    'settings': { title: 'Settings & Configuration', breadcrumb: 'DealFlow360 / Commercial Configuration Hub' },
    'discount-policies': { title: 'Discount Policies', breadcrumb: 'DealFlow360 / Commercial Configuration / Discount Policies' },
    'approval-policies': { title: 'Approval Policies', breadcrumb: 'DealFlow360 / Commercial Configuration / Approval Policies' },
    'billing-plans': { title: 'Billing Plans', breadcrumb: 'DealFlow360 / Commercial Configuration / Billing Plans' },
    'portal': { title: 'Customer Portal', breadcrumb: 'DealFlow360 / Customer Workspace / My Quotations' },
    'portal-quotation': { title: 'Commercial Proposal', breadcrumb: 'DealFlow360 / Customer Workspace / Quotation Review' }
  };

  /**
   * Switch the active view in the main content container.
   * @param {string} viewName
   * @param {object|string|null} params
   */
  async function switchView(viewName, params = null) {
    currentViewName = viewName;
    const container = document.getElementById('main-view-container');
    if (!container) return;

    // Update Header Title & Breadcrumb
    const meta = VIEW_TITLES[viewName] || { title: 'Workspace', breadcrumb: 'DealFlow360' };
    const titleEl = document.getElementById('header-view-title');
    const breadcrumbEl = document.getElementById('header-view-breadcrumb');
    if (titleEl) titleEl.textContent = meta.title;
    if (breadcrumbEl) breadcrumbEl.textContent = meta.breadcrumb;

    // Update Sidebar active state
    if (global.DealFlowNav) {
      let navId = viewName;
      if (['discount-policies', 'approval-policies', 'billing-plans', 'recommendation-rules'].includes(viewName)) {
        navId = viewName === 'approval-policies' ? 'approvals' : (viewName === 'billing-plans' ? 'billing' : 'settings');
      } else if (viewName === 'quotation-builder') {
        navId = 'quotations';
      } else if (viewName === 'portal' || viewName === 'portal-quotation') {
        navId = 'customerQuotes';
      }
      global.DealFlowNav.setActiveNav(navId);
    }

    // Normalize params
    const initialSubTab = typeof params === 'string' ? params : null;
    const extraParams = typeof params === 'object' && params !== null ? params : {};

    // Mount View
    switch (viewName) {
      case 'dashboard':
        if (global.DashboardView) {
          await global.DashboardView.render(container, (targetView, subTab) => switchView(targetView, subTab));
        }
        break;

      case 'quotations':
        if (global.QuotationsView) {
          await global.QuotationsView.render(container, 'list');
        }
        break;

      case 'pipeline':
        if (global.QuotationsView) {
          await global.QuotationsView.render(container, 'pipeline');
        }
        break;

      case 'quotation-builder':
        if (global.QuotationBuilderView) {
          await global.QuotationBuilderView.render(container, extraParams);
        }
        break;

      case 'negotiations':
        if (global.NegotiationsView) {
          await global.NegotiationsView.render(container);
        }
        break;

      case 'portal':
        if (global.PortalView) {
          await global.PortalView.render(container, 'list');
        }
        break;

      case 'portal-quotation':
        if (global.PortalView) {
          const qId = extraParams.quoteId || extraParams.id || (typeof params === 'number' ? params : null);
          await global.PortalView.renderQuotationDetail(container, qId);
        }
        break;

      case 'approvals':
        if (global.ApprovalsView) {
          await global.ApprovalsView.render(container);
        }
        break;

      case 'recommendation-rules':
        if (global.RecommendationRulesView) {
          await global.RecommendationRulesView.render(container);
        }
        break;

      case 'customers':
        if (global.CustomersView) {
          await global.CustomersView.render(container, initialSubTab || 'customers');
        }
        break;

      case 'products':
        if (global.ProductsView) {
          await global.ProductsView.render(container, initialSubTab || 'products');
        }
        break;

      case 'inventory':
        if (global.InventoryView) {
          await global.InventoryView.render(container, initialSubTab || 'inventory');
        }
        break;

      case 'settings':
        if (global.SettingsView) {
          await global.SettingsView.render(container, (targetView, subTab) => switchView(targetView, subTab));
        }
        break;

      case 'discount-policies':
        if (global.DiscountPoliciesView) {
          await global.DiscountPoliciesView.render(container);
        }
        break;

      case 'approval-policies':
        if (global.ApprovalPoliciesView) {
          await global.ApprovalPoliciesView.render(container);
        }
        break;

      case 'billing-plans':
        if (global.BillingPlansView) {
          await global.BillingPlansView.render(container);
        }
        break;

      default:
        if (global.DashboardView) {
          await global.DashboardView.render(container, (targetView, subTab) => switchView(targetView, subTab));
        }
        break;
    }
  }

  /**
   * Main application bootstrap function.
   */
  async function initApp() {
    const pageLoader = document.getElementById('page-loader');
    const auth = global.DealFlowAuth;
    const api = global.DealFlowAPI;
    const nav = global.DealFlowNav;
    const ui = global.DealFlowUI;

    if (!auth || !api || !nav || !ui) {
      console.error('[DealFlow360] Required core modules missing');
      return;
    }

    let currentUser = null;

    try {
      // 1. Guard route: verify token and fetch safe current user profile from GET /api/v1/auth/me
      currentUser = await auth.requireAuth();
      if (!currentUser) return;
    } catch (err) {
      console.error('[DealFlow360] Auth initialization error:', err);
      auth.logout('Unable to verify session with backend.');
      return;
    }

    // 2. Extract user details
    const fullName = currentUser.full_name || 'Enterprise User';
    const email = currentUser.email || '';
    const roleName = (currentUser.role && currentUser.role.name) ? currentUser.role.name : 'ADMIN';
    const formattedRole = nav.formatRole(roleName);
    const userInitials = ui.getInitials(fullName);

    // 3. Update Header UI
    const headerUserNameEl = document.getElementById('header-user-name');
    const headerUserRoleEl = document.getElementById('header-user-role');
    const headerUserAvatarEl = document.getElementById('header-user-avatar');
    const dropdownUserNameEl = document.getElementById('dropdown-user-name');
    const dropdownUserEmailEl = document.getElementById('dropdown-user-email');
    const dropdownUserRoleBadgeEl = document.getElementById('dropdown-user-role-badge');

    if (headerUserNameEl) headerUserNameEl.textContent = fullName;
    if (headerUserRoleEl) headerUserRoleEl.textContent = formattedRole;
    if (headerUserAvatarEl) headerUserAvatarEl.textContent = userInitials;
    if (dropdownUserNameEl) dropdownUserNameEl.textContent = fullName;
    if (dropdownUserEmailEl) dropdownUserEmailEl.textContent = email;
    if (dropdownUserRoleBadgeEl) dropdownUserRoleBadgeEl.textContent = formattedRole;

    // 4. Render Role-Aware Sidebar Navigation with View Switcher callback
    const sidebarNavContainer = document.getElementById('sidebar-nav-container');
    if (sidebarNavContainer) {
      nav.renderSidebar(roleName, sidebarNavContainer, (navId, targetTab) => {
        if (navId === 'approvals') switchView('approvals');
        else if (navId === 'billing') switchView('billing-plans');
        else if (navId === 'pipeline') switchView('pipeline');
        else if (navId === 'quotations') switchView('quotations');
        else if (navId === 'negotiations') switchView('negotiations');
        else if (navId === 'customerQuotes' || navId === 'customerOverview' || navId === 'customerNegotiations') switchView('portal');
        else switchView(navId, targetTab);
      });
    }

    // 5. Initialize Real-Time WebSockets & Notification Center
    if (global.DealFlowWS) {
      global.DealFlowWS.connect();
    }
    if (global.DealFlowNotificationCenter) {
      global.DealFlowNotificationCenter.init();
    }

    // 6. Setup User Dropdown & Drawer Events
    const userTrigger = document.getElementById('user-menu-trigger');
    const userDropdown = document.getElementById('user-dropdown-menu');
    ui.initUserDropdown(userTrigger, userDropdown);

    const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
    const appSidebar = document.getElementById('app-sidebar');
    const sidebarBackdrop = document.getElementById('sidebar-backdrop');
    ui.initMobileSidebar(sidebarToggleBtn, appSidebar, sidebarBackdrop);

    document.getElementById('dropdown-view-profile')?.addEventListener('click', (e) => {
      e.preventDefault();
      userDropdown?.classList.remove('show');
      ui.showProfileModal(currentUser);
    });

    document.getElementById('dropdown-logout-btn')?.addEventListener('click', (e) => {
      e.preventDefault();
      auth.logout();
    });

    // 7. Mount Initial View (Customer Portal for CUSTOMER role, Dashboard for internal roles)
    if (roleName.toUpperCase() === 'CUSTOMER') {
      await switchView('portal');
    } else {
      await switchView('dashboard');
    }

    // 8. Load Live Backend & Database Health Status
    await checkSystemHealth(api);

    // 8. Dismiss Loading Overlay smoothly
    if (pageLoader) {
      pageLoader.classList.add('hidden');
      setTimeout(() => pageLoader.remove(), 350);
    }
  }

  /**
   * Fetch and display live health check indicators from FastAPI.
   * @param {object} api
   */
  async function checkSystemHealth(api) {
    const connectionIndicator = document.getElementById('header-connection-indicator');
    const dashApiBadge = document.getElementById('dash-api-badge');
    const dashApiVal = document.getElementById('dash-api-val');
    const dashDbBadge = document.getElementById('dash-db-badge');
    const dashDbVal = document.getElementById('dash-db-val');

    // Root / v1 API Health
    const apiHealth = await api.getHealth();
    if (apiHealth.ok && apiHealth.data && apiHealth.data.status === 'healthy') {
      if (connectionIndicator) {
        connectionIndicator.innerHTML = `<span class="status-dot status-dot-teal status-dot-pulse"></span><span>Connected</span>`;
      }
      if (dashApiBadge) {
        dashApiBadge.className = 'badge badge-teal';
        dashApiBadge.innerHTML = `<span class="status-dot status-dot-teal status-dot-pulse"></span>Online`;
      }
      if (dashApiVal) dashApiVal.textContent = 'Online';
    } else {
      if (connectionIndicator) {
        connectionIndicator.innerHTML = `<span class="status-dot status-dot-coral"></span><span>Disconnected</span>`;
      }
      if (dashApiBadge) {
        dashApiBadge.className = 'badge badge-coral';
        dashApiBadge.innerHTML = `<span class="status-dot status-dot-coral"></span>Unavailable`;
      }
      if (dashApiVal) dashApiVal.textContent = 'Offline';
    }

    // Database Health
    const dbHealth = await api.getDatabaseHealth();
    if (dbHealth.ok && dbHealth.data && dbHealth.data.database === 'connected') {
      if (dashDbBadge) {
        dashDbBadge.className = 'badge badge-teal';
        dashDbBadge.innerHTML = `<span class="status-dot status-dot-teal"></span>Connected`;
      }
      if (dashDbVal) dashDbVal.textContent = 'Connected';
    } else {
      if (dashDbBadge) {
        dashDbBadge.className = 'badge badge-coral';
        dashDbBadge.innerHTML = `<span class="status-dot status-dot-coral"></span>Disconnected`;
      }
      if (dashDbVal) dashDbVal.textContent = 'Unavailable';
    }
  }

  global.DealFlowApp = {
    init: initApp,
    switchView: switchView
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
  } else {
    initApp();
  }
})(typeof window !== 'undefined' ? window : this);
