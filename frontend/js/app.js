/**
 * DealFlow360 — Dashboard & Application Controller
 * Bootstraps authenticated workspace, loads live system health, renders role-aware UI.
 */
(function (global) {
  'use strict';

  /**
   * Main dashboard initialization function.
   */
  async function initDashboard() {
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
      if (!currentUser) return; // redirect already initiated in requireAuth
    } catch (err) {
      console.error('[DealFlow360] Auth initialization error:', err);
      auth.logout('Unable to verify session with backend.');
      return;
    }

    // 2. Extract and format user details
    const fullName = currentUser.full_name || 'Enterprise User';
    const firstName = fullName.split(' ')[0] || 'User';
    const email = currentUser.email || '';
    const roleName = (currentUser.role && currentUser.role.name) ? currentUser.role.name : 'ADMIN';
    const formattedRole = nav.formatRole(roleName);
    const userInitials = ui.getInitials(fullName);
    const isCustomer = roleName.toUpperCase() === 'CUSTOMER';

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

    // 4. Update Dashboard Greeting & User Info Cards
    const welcomeGreetingEl = document.getElementById('welcome-greeting');
    const welcomeRoleBadgeEl = document.getElementById('welcome-role-badge');
    if (welcomeGreetingEl) welcomeGreetingEl.textContent = `Welcome back, ${firstName}`;
    if (welcomeRoleBadgeEl) welcomeRoleBadgeEl.textContent = formattedRole;

    // Account Info Card
    const accountCardNameEl = document.getElementById('account-card-name');
    const accountCardEmailEl = document.getElementById('account-card-email');
    const accountCardRoleEl = document.getElementById('account-card-role');
    const accountCardStatusEl = document.getElementById('account-card-status');
    const accountCardCreatedEl = document.getElementById('account-card-created');

    if (accountCardNameEl) accountCardNameEl.textContent = fullName;
    if (accountCardEmailEl) accountCardEmailEl.textContent = email;
    if (accountCardRoleEl) accountCardRoleEl.textContent = formattedRole;
    if (accountCardStatusEl) {
      accountCardStatusEl.innerHTML = currentUser.is_active
        ? `<span class="badge badge-teal"><span class="status-dot status-dot-teal"></span>Active</span>`
        : `<span class="badge badge-coral"><span class="status-dot status-dot-coral"></span>Inactive</span>`;
    }
    if (accountCardCreatedEl && currentUser.created_at) {
      accountCardCreatedEl.textContent = new Date(currentUser.created_at).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    }

    // 5. Render Role-Aware Sidebar Navigation
    const sidebarNavContainer = document.getElementById('sidebar-nav-container');
    if (sidebarNavContainer) {
      nav.renderSidebar(roleName, sidebarNavContainer);
    }

    // Adapt workspace subtitle if customer role
    const workspaceSubtitleEl = document.getElementById('workspace-subtitle');
    if (workspaceSubtitleEl && isCustomer) {
      workspaceSubtitleEl.textContent = 'Your DealFlow360 Customer Portal is ready.';
    }

    // 6. Setup Interactive UI Events
    // User dropdown
    const userTrigger = document.getElementById('user-menu-trigger');
    const userDropdown = document.getElementById('user-dropdown-menu');
    ui.initUserDropdown(userTrigger, userDropdown);

    // Mobile sidebar toggle
    const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
    const appSidebar = document.getElementById('app-sidebar');
    const sidebarBackdrop = document.getElementById('sidebar-backdrop');
    ui.initMobileSidebar(sidebarToggleBtn, appSidebar, sidebarBackdrop);

    // Profile modal trigger
    document.getElementById('dropdown-view-profile')?.addEventListener('click', (e) => {
      e.preventDefault();
      userDropdown?.classList.remove('show');
      ui.showProfileModal(currentUser);
    });

    // Logout trigger
    document.getElementById('dropdown-logout-btn')?.addEventListener('click', (e) => {
      e.preventDefault();
      auth.logout();
    });

    // 7. Load Live Backend & Database Health Status
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
    const apiStatusBadge = document.getElementById('status-api-badge');
    const apiStatusVal = document.getElementById('status-api-val');
    const dbStatusBadge = document.getElementById('status-db-badge');
    const dbStatusVal = document.getElementById('status-db-val');
    const connectionIndicator = document.getElementById('header-connection-indicator');

    // Root / v1 API Health
    const apiHealth = await api.getHealth();
    if (apiHealth.ok && apiHealth.data && apiHealth.data.status === 'healthy') {
      if (apiStatusBadge) {
        apiStatusBadge.className = 'badge badge-teal';
        apiStatusBadge.innerHTML = `<span class="status-dot status-dot-teal status-dot-pulse"></span>Online`;
      }
      if (apiStatusVal) apiStatusVal.textContent = 'Online';
      if (connectionIndicator) {
        connectionIndicator.innerHTML = `<span class="status-dot status-dot-teal status-dot-pulse"></span><span>Connected</span>`;
      }
    } else {
      if (apiStatusBadge) {
        apiStatusBadge.className = 'badge badge-coral';
        apiStatusBadge.innerHTML = `<span class="status-dot status-dot-coral"></span>Unavailable`;
      }
      if (apiStatusVal) apiStatusVal.textContent = 'Offline';
      if (connectionIndicator) {
        connectionIndicator.innerHTML = `<span class="status-dot status-dot-coral"></span><span>Disconnected</span>`;
      }
    }

    // PostgreSQL Database Health
    const dbHealth = await api.getDatabaseHealth();
    if (dbHealth.ok && dbHealth.data && dbHealth.data.database === 'connected') {
      if (dbStatusBadge) {
        dbStatusBadge.className = 'badge badge-teal';
        dbStatusBadge.innerHTML = `<span class="status-dot status-dot-teal"></span>Connected`;
      }
      if (dbStatusVal) dbStatusVal.textContent = 'Connected';
    } else {
      if (dbStatusBadge) {
        dbStatusBadge.className = 'badge badge-coral';
        dbStatusBadge.innerHTML = `<span class="status-dot status-dot-coral"></span>Disconnected`;
      }
      if (dbStatusVal) dbStatusVal.textContent = 'Unavailable';
    }
  }

  // Execute on DOM Ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboard);
  } else {
    initDashboard();
  }
})(typeof window !== 'undefined' ? window : this);
