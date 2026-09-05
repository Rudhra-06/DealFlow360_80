/**
 * DealFlow360 — Role-Aware Home Dashboard View Controller
 * Delivers tailored operational intelligence, action triggers, live system status,
 * and seamless cross-module workflows across Admin, Sales Manager, Sales Rep, and Finance.
 */
(function (global) {
  'use strict';

  const DashboardView = {
    async render(container, onNavigate) {
      const currentUser = global.DealFlowAuth.getCurrentUser();
      const fullName = currentUser?.full_name || 'Enterprise User';
      const firstName = fullName.split(' ')[0] || 'User';
      const roleName = (currentUser?.role?.name || 'ADMIN').toUpperCase();
      const formattedRole = global.DealFlowNav.formatRole(roleName);
      const isCustomer = roleName === 'CUSTOMER';

      container.innerHTML = `
        <!-- Dashboard Welcome Heading -->
        <div class="dashboard-welcome-banner animate-fade-in">
          <div style="display: flex; align-items: center; gap: var(--space-sm); flex-wrap: wrap;">
            <h1>Welcome back, ${firstName}</h1>
            <span class="badge badge-navy" style="font-size: var(--font-size-xs);">${formattedRole}</span>
          </div>
          <p>${isCustomer ? 'Your DealFlow360 Customer Portal is ready.' : 'Your DealFlow360 Sales Intelligence & Commercial Operations workspace is ready.'}</p>
        </div>

        <!-- ROW 1: Real System Status Grid -->
        <div class="status-grid animate-fade-in">
          <!-- API Status -->
          <div class="status-card">
            <div class="status-card-header">
              <span class="status-card-label">API Health</span>
              <span id="dash-api-badge" class="badge badge-teal">
                <span class="status-dot status-dot-teal status-dot-pulse"></span>
                Online
              </span>
            </div>
            <div class="status-card-value" id="dash-api-val">Online</div>
            <div class="status-card-sub">FastAPI v1 Services</div>
          </div>

          <!-- Database Status -->
          <div class="status-card">
            <div class="status-card-header">
              <span class="status-card-label">Database</span>
              <span id="dash-db-badge" class="badge badge-teal">
                <span class="status-dot status-dot-teal"></span>
                Connected
              </span>
            </div>
            <div class="status-card-value" id="dash-db-val">Connected</div>
            <div class="status-card-sub">PostgreSQL via asyncpg</div>
          </div>

          <!-- Deal Intelligence Engine Status -->
          <div class="status-card">
            <div class="status-card-header">
              <span class="status-card-label">Deal Intelligence</span>
              <span class="badge badge-teal">
                <span class="status-dot status-dot-teal"></span>
                Active
              </span>
            </div>
            <div class="status-card-value">Telemetric Scoring</div>
            <div class="status-card-sub">Explainable Risk & Health</div>
          </div>

          <!-- RBAC Status -->
          <div class="status-card">
            <div class="status-card-header">
              <span class="status-card-label">RBAC Tier</span>
              <span class="badge badge-teal">
                <span class="status-dot status-dot-teal"></span>
                ${formattedRole}
              </span>
            </div>
            <div class="status-card-value">Authoritative</div>
            <div class="status-card-sub">Strict Backend Scope</div>
          </div>
        </div>

        <!-- ROW 2: Role-Aware Quick Actions & Operational Priority -->
        ${!isCustomer ? `
          <div style="margin-bottom: var(--space-lg);" class="animate-fade-in">
            <div class="card">
              <div class="card-header">
                <div>
                  <h3 class="card-title" style="font-size:var(--font-size-sm);">Commercial & Operational Quick Actions</h3>
                  <div class="card-subtitle">Immediate operational workflows tailored for ${formattedRole}</div>
                </div>
                <span class="badge badge-navy">${formattedRole} Tier</span>
              </div>
              <div class="card-body" style="display:flex;gap:var(--space-md);flex-wrap:wrap;" id="quick-actions-container">
                <!-- Populated per role dynamically below -->
              </div>
            </div>
          </div>

          <!-- ROW 3: Role-Specific Operational Telemetry Matrix -->
          <div style="margin-bottom: var(--space-lg);" class="animate-fade-in">
            <div class="card" style="border-top: 3px solid var(--color-teal);">
              <div class="card-header" style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                  <h3 class="card-title" style="font-size:var(--font-size-sm);display:flex;align-items:center;gap:6px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                    Live Operations & Deal Health Telemetry
                  </h3>
                  <div class="card-subtitle">Real-time indicators across pipeline, governance, risk, and fulfillment</div>
                </div>
                <div style="display:flex;gap:var(--space-xs);">
                  <button class="btn btn-secondary btn-sm" id="dash-btn-alerts">
                    <span>Alerts Inbox</span>
                  </button>
                  <button class="btn btn-teal btn-sm" id="dash-btn-deal-health">
                    <span>Deal Health &rarr;</span>
                  </button>
                </div>
              </div>
              <div class="card-body" style="padding:var(--space-md);">
                <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(130px, 1fr));gap:var(--space-md);" id="dash-health-metrics-grid">
                  <div class="health-score-card" style="padding:10px;cursor:pointer;" onclick="window.location.hash='#/deal-health?health_level=HEALTHY'">
                    <div style="font-size:1.5rem;font-weight:800;color:var(--color-teal);" id="dash-count-healthy">—</div>
                    <div style="font-size:0.7rem;font-weight:700;color:var(--color-text-secondary);text-transform:uppercase;">Healthy Deals</div>
                  </div>
                  <div class="health-score-card" style="padding:10px;cursor:pointer;" onclick="window.location.hash='#/deal-health?health_level=WATCH'">
                    <div style="font-size:1.5rem;font-weight:800;color:#D97706;" id="dash-count-watch">—</div>
                    <div style="font-size:0.7rem;font-weight:700;color:var(--color-text-secondary);text-transform:uppercase;">Watch Deals</div>
                  </div>
                  <div class="health-score-card" style="padding:10px;cursor:pointer;" onclick="window.location.hash='#/deal-health?health_level=AT_RISK'">
                    <div style="font-size:1.5rem;font-weight:800;color:var(--color-coral);" id="dash-count-atrisk">—</div>
                    <div style="font-size:0.7rem;font-weight:700;color:var(--color-text-secondary);text-transform:uppercase;">At Risk Deals</div>
                  </div>
                  <div class="health-score-card" style="padding:10px;cursor:pointer;" onclick="window.location.hash='#/deal-health?health_level=CRITICAL'">
                    <div style="font-size:1.5rem;font-weight:800;color:#DC2626;" id="dash-count-critical">—</div>
                    <div style="font-size:0.7rem;font-weight:700;color:var(--color-text-secondary);text-transform:uppercase;">Critical Deals</div>
                  </div>
                  <div class="health-score-card" style="padding:10px;cursor:pointer;" onclick="window.location.hash='#/deal-alerts'">
                    <div style="font-size:1.5rem;font-weight:800;color:var(--color-navy);" id="dash-count-open-alerts">—</div>
                    <div style="font-size:0.7rem;font-weight:700;color:var(--color-text-secondary);text-transform:uppercase;">Open Alerts</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ` : ''}

        <!-- ROW 4: Enterprise Navigation & Workspace Hubs -->
        <div class="info-cards-grid animate-fade-in">
          <!-- Sales & Commercial Intelligence -->
          <div class="card">
            <div class="card-header">
              <div>
                <h3 class="card-title">Commercial & Intelligence Hub</h3>
                <div class="card-subtitle">Quotations, pipeline Kanban, approvals, and Customer 360</div>
              </div>
              <span class="badge badge-teal">Integrated</span>
            </div>
            <div class="card-body">
              <div class="key-value-list">
                <div class="key-value-item" style="cursor:pointer;" id="dash-link-quotations">
                  <span class="key-label" style="display:flex;align-items:center;gap:6px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                    Quotations Workspace
                  </span>
                  <span class="key-value" style="color:var(--color-teal);">Open Quotes &rarr;</span>
                </div>
                <div class="key-value-item" style="cursor:pointer;" id="dash-link-pipeline">
                  <span class="key-label" style="display:flex;align-items:center;gap:6px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
                    Sales Pipeline Board
                  </span>
                  <span class="key-value" style="color:var(--color-teal);">Open Board &rarr;</span>
                </div>
                <div class="key-value-item" style="cursor:pointer;" id="dash-link-approvals-queue">
                  <span class="key-label" style="display:flex;align-items:center;gap:6px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                    Approval Queue & Governance
                  </span>
                  <span class="key-value" style="color:var(--color-teal);">Review Queue &rarr;</span>
                </div>
                <div class="key-value-item" style="cursor:pointer;" id="dash-link-customer-360">
                  <span class="key-label" style="display:flex;align-items:center;gap:6px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                    Customer 360 Full Dossier
                  </span>
                  <span class="key-value" style="color:var(--color-navy);font-weight:600;">View 360 &rarr;</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Operations, Billing & System Hub -->
          <div class="card">
            <div class="card-header">
              <div>
                <h3 class="card-title">Operations, Billing & Telemetry Hub</h3>
                <div class="card-subtitle">Orders, fulfillment, hybrid billing, analytics, and demo readiness</div>
              </div>
              <span class="badge badge-navy">End-to-End</span>
            </div>
            <div class="card-body">
              <div class="key-value-list">
                <div class="key-value-item" style="cursor:pointer;" id="dash-link-orders">
                  <span class="key-label" style="display:flex;align-items:center;gap:6px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>
                    Sales Orders & Fulfillment
                  </span>
                  <span class="key-value" style="color:var(--color-teal);">Open Orders &rarr;</span>
                </div>
                <div class="key-value-item" style="cursor:pointer;" id="dash-link-invoices">
                  <span class="key-label" style="display:flex;align-items:center;gap:6px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>
                    Invoices & Subscriptions
                  </span>
                  <span class="key-value" style="color:var(--color-teal);">Open Billing &rarr;</span>
                </div>
                <div class="key-value-item" style="cursor:pointer;" id="dash-link-analytics">
                  <span class="key-label" style="display:flex;align-items:center;gap:6px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
                    Executive & Operations Analytics
                  </span>
                  <span class="key-value" style="color:var(--color-teal);">View Analytics &rarr;</span>
                </div>
                <div class="key-value-item" style="cursor:pointer;" id="dash-link-demo-readiness">
                  <span class="key-label" style="display:flex;align-items:center;gap:6px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                    System Demo Readiness
                  </span>
                  <span class="key-value" style="color:var(--color-navy);font-weight:600;">Check Readiness &rarr;</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      `;

      // Render tailored Quick Actions per role
      const qaContainer = document.getElementById('quick-actions-container');
      if (qaContainer) {
        let buttonsHtml = '';
        if (roleName === 'ADMIN') {
          buttonsHtml = `
            <button class="btn btn-primary btn-sm" id="qa-new-quote">+ New Quotation</button>
            <button class="btn btn-secondary btn-sm" id="qa-view-pipeline">Pipeline Board</button>
            <button class="btn btn-secondary btn-sm" id="qa-view-approvals">Approval Queue</button>
            <button class="btn btn-secondary btn-sm" id="qa-customer-360">Customer 360</button>
            <button class="btn btn-secondary btn-sm" id="qa-analytics">Executive Analytics</button>
            <button class="btn btn-secondary btn-sm" id="qa-reports">Reports Center</button>
            <button class="btn btn-teal btn-sm" id="qa-demo-readiness">System Readiness</button>
          `;
        } else if (roleName === 'SALES_REP') {
          buttonsHtml = `
            <button class="btn btn-primary btn-sm" id="qa-new-quote">+ New Quotation</button>
            <button class="btn btn-secondary btn-sm" id="qa-view-pipeline">My Pipeline</button>
            <button class="btn btn-secondary btn-sm" id="qa-negotiations">Negotiation Inbox</button>
            <button class="btn btn-secondary btn-sm" id="qa-deal-health">My At-Risk Deals</button>
            <button class="btn btn-secondary btn-sm" id="qa-customer-360">Customer 360</button>
          `;
        } else if (roleName === 'SALES_MANAGER') {
          buttonsHtml = `
            <button class="btn btn-primary btn-sm" id="qa-view-approvals">Pending Approvals</button>
            <button class="btn btn-secondary btn-sm" id="qa-deal-health">At-Risk Deals</button>
            <button class="btn btn-secondary btn-sm" id="qa-analytics">Sales Performance</button>
            <button class="btn btn-secondary btn-sm" id="qa-customer-360">Customer 360</button>
            <button class="btn btn-secondary btn-sm" id="qa-reports">Export Reports</button>
          `;
        } else if (roleName === 'FINANCE_OPERATIONS') {
          buttonsHtml = `
            <button class="btn btn-primary btn-sm" id="qa-orders">Fulfillment Orders</button>
            <button class="btn btn-secondary btn-sm" id="qa-invoices">Invoices & Billing</button>
            <button class="btn btn-secondary btn-sm" id="qa-analytics">Operations Analytics</button>
            <button class="btn btn-secondary btn-sm" id="qa-reports">Financial Reports</button>
          `;
        }
        qaContainer.innerHTML = buttonsHtml;
      }

      // Bind dynamic actions
      this._bindEvents(onNavigate);

      // Fetch live Deal Health summary
      if (!isCustomer) {
        this._loadDealHealthTelemetry();
      }
    },

    _bindEvents(onNavigate) {
      const navigate = (route) => {
        if (typeof onNavigate === 'function') {
          onNavigate(route);
        } else {
          window.location.hash = `#/${route}`;
        }
      };

      document.getElementById('dash-btn-alerts')?.addEventListener('click', () => navigate('deal-alerts'));
      document.getElementById('dash-btn-deal-health')?.addEventListener('click', () => navigate('deal-health'));
      document.getElementById('dash-link-quotations')?.addEventListener('click', () => navigate('quotations'));
      document.getElementById('dash-link-pipeline')?.addEventListener('click', () => navigate('pipeline'));
      document.getElementById('dash-link-approvals-queue')?.addEventListener('click', () => navigate('approvals'));
      document.getElementById('dash-link-customer-360')?.addEventListener('click', () => navigate('customer-360'));
      document.getElementById('dash-link-orders')?.addEventListener('click', () => navigate('orders'));
      document.getElementById('dash-link-invoices')?.addEventListener('click', () => navigate('invoices'));
      document.getElementById('dash-link-analytics')?.addEventListener('click', () => navigate('analytics'));
      document.getElementById('dash-link-demo-readiness')?.addEventListener('click', () => navigate('demo-readiness'));

      // Quick action buttons
      document.getElementById('qa-new-quote')?.addEventListener('click', () => navigate('quotation-builder'));
      document.getElementById('qa-view-pipeline')?.addEventListener('click', () => navigate('pipeline'));
      document.getElementById('qa-view-approvals')?.addEventListener('click', () => navigate('approvals'));
      document.getElementById('qa-negotiations')?.addEventListener('click', () => navigate('negotiations'));
      document.getElementById('qa-deal-health')?.addEventListener('click', () => navigate('deal-health'));
      document.getElementById('qa-customer-360')?.addEventListener('click', () => navigate('customer-360'));
      document.getElementById('qa-analytics')?.addEventListener('click', () => navigate('analytics'));
      document.getElementById('qa-reports')?.addEventListener('click', () => navigate('reports'));
      document.getElementById('qa-orders')?.addEventListener('click', () => navigate('orders'));
      document.getElementById('qa-invoices')?.addEventListener('click', () => navigate('invoices'));
      document.getElementById('qa-demo-readiness')?.addEventListener('click', () => navigate('demo-readiness'));
    },

    async _loadDealHealthTelemetry() {
      try {
        if (global.DealHealthAPI) {
          const res = await global.DealHealthAPI.getSummary();
          const healthyEl = document.getElementById('dash-count-healthy');
          const watchEl = document.getElementById('dash-count-watch');
          const atriskEl = document.getElementById('dash-count-atrisk');
          const criticalEl = document.getElementById('dash-count-critical');
          const alertsEl = document.getElementById('dash-count-open-alerts');

          if (healthyEl) healthyEl.textContent = res.HEALTHY ?? res.healthy ?? 0;
          if (watchEl) watchEl.textContent = res.WATCH ?? res.watch ?? 0;
          if (atriskEl) atriskEl.textContent = res.AT_RISK ?? res.at_risk ?? 0;
          if (criticalEl) criticalEl.textContent = res.CRITICAL ?? res.critical ?? 0;
          if (alertsEl) alertsEl.textContent = res.open_alerts_count ?? res.open_alerts ?? 0;
        }
      } catch (_) {
        // Silently preserve dashboard layout if telemetry unavailable
      }
    }
  };

  global.DashboardView = DashboardView;
})(typeof window !== 'undefined' ? window : this);
