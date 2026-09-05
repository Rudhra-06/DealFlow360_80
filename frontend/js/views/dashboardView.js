/**
 * DealFlow360 — Dashboard View Controller
 * Highlights active Phase 3 Sales Workspace, Master Data, and Commercial Governance.
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
            <div class="status-card-value">Phase 3 Live</div>
            <div class="status-card-sub">CPQ & Approvals Ready</div>
          </div>

          <!-- Account / RBAC Status -->
          <div class="status-card">
            <div class="status-card-header">
              <span class="status-card-label">RBAC Tier</span>
              <span class="badge badge-teal">
                <span class="status-dot status-dot-teal"></span>
                ${formattedRole}
              </span>
            </div>
            <div class="status-card-value">Authoritative</div>
            <div class="status-card-sub">Strict Backend Security</div>
          </div>
        </div>

        <!-- ROW 2: Role-Aware Quick Actions -->
        ${!isCustomer ? `
          <div style="margin-bottom: var(--space-lg);" class="animate-fade-in">
            <div class="card">
              <div class="card-header">
                <div>
                  <h3 class="card-title" style="font-size:var(--font-size-sm);">Commercial Quick Actions</h3>
                  <div class="card-subtitle">Fast access workflows tailored for ${formattedRole}</div>
                </div>
                <span class="badge badge-navy">${formattedRole} Tier</span>
              </div>
              <div class="card-body" style="display:flex;gap:var(--space-md);flex-wrap:wrap;" id="quick-actions-container">
                <!-- Populated per role -->
              </div>
            </div>
          </div>
        ` : ''}

        <!-- ROW 3: Phase 3 Sales Workspace & Master Data Overview -->
        <div class="info-cards-grid animate-fade-in">
          <!-- Sales Workspace Shortcuts -->
          <div class="card">
            <div class="card-header">
              <div>
                <h3 class="card-title">Sales Workspace & Deal CPQ</h3>
                <div class="card-subtitle">Live quotations, pipeline board, and governance queue</div>
              </div>
              <span class="badge badge-teal">Phase 3 Active</span>
            </div>
            <div class="card-body">
              <div class="key-value-list">
                <div class="key-value-item" style="cursor:pointer;" id="dash-link-quotations">
                  <span class="key-label" style="display:flex;align-items:center;gap:6px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                    Quotations Master List
                  </span>
                  <span class="key-value" style="color:var(--color-teal);">View Quotes &rarr;</span>
                </div>
                <div class="key-value-item" style="cursor:pointer;" id="dash-link-pipeline">
                  <span class="key-label" style="display:flex;align-items:center;gap:6px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
                    Sales Pipeline Board (Kanban)
                  </span>
                  <span class="key-value" style="color:var(--color-teal);">Open Pipeline &rarr;</span>
                </div>
                <div class="key-value-item" style="cursor:pointer;" id="dash-link-approvals-queue">
                  <span class="key-label" style="display:flex;align-items:center;gap:6px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                    Approval Queue & Triggers
                  </span>
                  <span class="key-value" style="color:var(--color-teal);">Review Queue &rarr;</span>
                </div>
                <div class="key-value-item" style="cursor:pointer;" id="dash-link-customers">
                  <span class="key-label" style="display:flex;align-items:center;gap:6px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
                    Customers & Accounts
                  </span>
                  <span class="key-value" style="color:var(--color-teal);">View Customers &rarr;</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Commercial Policies & Rules Shortcuts -->
          <div class="card">
            <div class="card-header">
              <div>
                <h3 class="card-title">Commercial Configuration</h3>
                <div class="card-subtitle">Discount bounds, approval rules, upsell rules, and billing schedules</div>
              </div>
              <span class="badge badge-navy">Rules Engine</span>
            </div>
            <div class="card-body">
              <div class="key-value-list">
                <div class="key-value-item" style="cursor:pointer;" id="dash-link-discounts">
                  <span class="key-label" style="display:flex;align-items:center;gap:6px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="9" y1="15" x2="15" y2="9"/></svg>
                    Discount Policies (6-Tier Precedence)
                  </span>
                  <span class="key-value" style="color:var(--color-teal);">Manage Rules &rarr;</span>
                </div>
                <div class="key-value-item" style="cursor:pointer;" id="dash-link-approvals-config">
                  <span class="key-label" style="display:flex;align-items:center;gap:6px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/></svg>
                    Approval Policies & Thresholds
                  </span>
                  <span class="key-value" style="color:var(--color-teal);">Configure Rules &rarr;</span>
                </div>
                <div class="key-value-item" style="cursor:pointer;" id="dash-link-rec-rules">
                  <span class="key-label" style="display:flex;align-items:center;gap:6px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                    Recommendation & Upsell Rules
                  </span>
                  <span class="key-value" style="color:var(--color-teal);">Configure Upsell &rarr;</span>
                </div>
                <div class="key-value-item" style="cursor:pointer;" id="dash-link-settings">
                  <span class="key-label" style="display:flex;align-items:center;gap:6px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
                    Configuration Overview Hub
                  </span>
                  <span class="key-value" style="color:var(--color-navy);font-weight:600;">Open Hub &rarr;</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      `;

      // Render role-aware quick action buttons
      const qaContainer = document.getElementById('quick-actions-container');
      if (qaContainer) {
        let buttonsHtml = '';
        if (roleName === 'ADMIN') {
          buttonsHtml = `
            <button class="btn btn-primary btn-sm" id="qa-new-quote">+ New Quotation</button>
            <button class="btn btn-secondary btn-sm" id="qa-view-pipeline">View Pipeline</button>
            <button class="btn btn-secondary btn-sm" id="qa-view-approvals">Approval Queue</button>
            <button class="btn btn-secondary btn-sm" id="qa-add-cust">+ Add Customer</button>
            <button class="btn btn-secondary btn-sm" id="qa-add-prod">+ Add Product</button>
          `;
        } else if (roleName === 'SALES_REP') {
          buttonsHtml = `
            <button class="btn btn-primary btn-sm" id="qa-new-quote">+ New Quotation</button>
            <button class="btn btn-secondary btn-sm" id="qa-view-pipeline">View Pipeline</button>
            <button class="btn btn-secondary btn-sm" id="qa-add-cust">+ Add Customer</button>
            <button class="btn btn-secondary btn-sm" id="qa-view-prods">Browse Products</button>
          `;
        } else if (roleName === 'SALES_MANAGER') {
          buttonsHtml = `
            <button class="btn btn-primary btn-sm" id="qa-view-approvals">Approval Queue</button>
            <button class="btn btn-secondary btn-sm" id="qa-new-quote">+ New Quotation</button>
            <button class="btn btn-secondary btn-sm" id="qa-view-pipeline">View Pipeline</button>
            <button class="btn btn-secondary btn-sm" id="qa-add-disc">+ Discount Policy</button>
          `;
        } else if (roleName === 'FINANCE_OPERATIONS') {
          buttonsHtml = `
            <button class="btn btn-primary btn-sm" id="qa-view-approvals">Approval Queue</button>
            <button class="btn btn-secondary btn-sm" id="qa-view-quotes">View Quotations</button>
            <button class="btn btn-secondary btn-sm" id="qa-add-prod">+ Add Product</button>
            <button class="btn btn-secondary btn-sm" id="qa-add-bill">+ Billing Plan</button>
          `;
        }

        qaContainer.innerHTML = buttonsHtml;

        document.getElementById('qa-new-quote')?.addEventListener('click', () => {
          if (typeof onNavigate === 'function') onNavigate('quotations');
        });
        document.getElementById('qa-view-pipeline')?.addEventListener('click', () => {
          if (typeof onNavigate === 'function') onNavigate('pipeline');
        });
        document.getElementById('qa-view-approvals')?.addEventListener('click', () => {
          if (typeof onNavigate === 'function') onNavigate('approvals');
        });
        document.getElementById('qa-view-quotes')?.addEventListener('click', () => {
          if (typeof onNavigate === 'function') onNavigate('quotations');
        });
        document.getElementById('qa-add-cust')?.addEventListener('click', () => {
          if (typeof onNavigate === 'function') onNavigate('customers');
        });
        document.getElementById('qa-add-prod')?.addEventListener('click', () => {
          if (typeof onNavigate === 'function') onNavigate('products');
        });
        document.getElementById('qa-add-disc')?.addEventListener('click', () => {
          if (typeof onNavigate === 'function') onNavigate('discount-policies');
        });
        document.getElementById('qa-add-bill')?.addEventListener('click', () => {
          if (typeof onNavigate === 'function') onNavigate('billing-plans');
        });
        document.getElementById('qa-view-prods')?.addEventListener('click', () => {
          if (typeof onNavigate === 'function') onNavigate('products');
        });
      }

      // Link clicks
      document.getElementById('dash-link-quotations')?.addEventListener('click', () => onNavigate('quotations'));
      document.getElementById('dash-link-pipeline')?.addEventListener('click', () => onNavigate('pipeline'));
      document.getElementById('dash-link-approvals-queue')?.addEventListener('click', () => onNavigate('approvals'));
      document.getElementById('dash-link-customers')?.addEventListener('click', () => onNavigate('customers', 'customers'));
      document.getElementById('dash-link-discounts')?.addEventListener('click', () => onNavigate('discount-policies'));
      document.getElementById('dash-link-approvals-config')?.addEventListener('click', () => onNavigate('approval-policies'));
      document.getElementById('dash-link-rec-rules')?.addEventListener('click', () => onNavigate('recommendation-rules'));
      document.getElementById('dash-link-settings')?.addEventListener('click', () => onNavigate('settings'));
    }
  };

  global.DashboardView = DashboardView;
})(typeof window !== 'undefined' ? window : this);
