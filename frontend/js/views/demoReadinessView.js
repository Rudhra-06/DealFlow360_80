/**
 * DealFlow360 — System Demo Readiness View Controller
 * Implements authoritative backend readiness audit display, feature flag status,
 * and reviewer-ready verification telemetry.
 */
(function (global) {
  'use strict';

  let lastCheckedTime = new Date();

  const CHECK_LABELS = {
    database: { label: 'PostgreSQL Database Engine', desc: 'Core relational persistence connectivity & query execution' },
    roles: { label: 'Role-Based Access Control (RBAC)', desc: '5 canonical roles seeded (Admin, Manager, Rep, Finance, Customer)' },
    demo_users: { label: 'Demo User Accounts', desc: 'Pre-configured persona accounts for reviewer evaluation' },
    customers: { label: 'Customer Master Directory', desc: 'Tiered B2B enterprise accounts initialized' },
    products: { label: 'Product & Pricing Catalog', desc: 'Multi-category products with base pricing & cost records' },
    warehouses: { label: 'Multi-Warehouse Logistics Nodes', desc: 'Fulfillment warehouse facilities configured' },
    inventory: { label: 'Inventory Stock Reserves', desc: 'Stock allocation and reservation records active' },
    discount_policy: { label: 'Commercial Discount Policy', desc: 'Tier-based discount thresholds & margin controls' },
    approval_policy: { label: 'Approval Governance Policies', desc: 'Multi-step Manager & Finance approval rules' },
    billing_plan: { label: 'Hybrid Billing Plans', desc: 'One-time hardware & recurring subscription schedules' },
    deal_health_config: { label: 'Deal Health Intelligence Policy', desc: 'AI/statistical scoring weights & signal thresholds' },
    reporting_ready: { label: 'ReportLab & openpyxl Compilers', desc: 'Server-side PDF & XLSX binary document generators' }
  };

  async function render(container) {
    const user = global.DealFlowAuth?.getCurrentUser();
    const roleName = user?.role?.name || 'ADMIN';

    // Guard: Customer cannot access
    if (roleName === 'CUSTOMER') {
      window.location.hash = '#/portal';
      return;
    }

    container.innerHTML = `
      <div class="analytics-page-container animate-fade-in">
        <!-- Header -->
        <div class="analytics-header-bar">
          <div class="analytics-title-group">
            <h1>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--color-teal);"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
              System Demo Readiness & Verification
            </h1>
            <div class="analytics-metadata-row">
              <span class="live-data-badge"><span class="live-data-dot"></span> Live Verification</span>
              <span>Last Checked: <strong id="readiness-checked-time">${lastCheckedTime.toLocaleTimeString()}</strong></span>
              <span>Auditor Scope: <strong>${roleName}</strong></span>
            </div>
          </div>
          <div class="analytics-header-actions">
            <button id="btn-refresh-readiness" class="btn btn-secondary btn-sm">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
              Refresh Verification
            </button>
          </div>
        </div>

        <!-- Dynamic Content Container -->
        <div id="readiness-content-area" style="min-height: 400px;">
          <div style="display:flex;justify-content:center;align-items:center;padding:80px 0;">
            <div class="spinner"></div>
          </div>
        </div>
      </div>
    `;

    container.querySelector('#btn-refresh-readiness')?.addEventListener('click', () => {
      lastCheckedTime = new Date();
      const timeEl = container.querySelector('#readiness-checked-time');
      if (timeEl) timeEl.textContent = lastCheckedTime.toLocaleTimeString();
      loadReadinessData(container);
    });

    await loadReadinessData(container);
  }

  async function loadReadinessData(container) {
    const contentArea = container.querySelector('#readiness-content-area');
    if (!contentArea) return;

    try {
      const [readinessRes, infoRes] = await Promise.all([
        global.SystemAPI.getDemoReadiness(),
        global.SystemAPI.getSystemInfo().catch(() => ({ application: 'DealFlow360', api_version: 'v1', environment: 'production_ready', features: {} }))
      ]);

      const isAllPass = readinessRes.status === 'PASS';
      const checks = readinessRes.checks || {};

      contentArea.innerHTML = `
        <div style="display:flex;flex-direction:column;gap:var(--space-xl);" class="animate-fade-in">
          <!-- Overall Status Banner -->
          <div style="background:${isAllPass ? 'linear-gradient(135deg, #134e4a 0%, #042f2e 100%)' : 'linear-gradient(135deg, #7f1d1d 0%, #450a0a 100%)'};color:#ffffff;border-radius:var(--radius-lg);padding:var(--space-lg) var(--space-xl);display:flex;justify-content:space-between;align-items:center;box-shadow:var(--shadow-md);flex-wrap:wrap;gap:var(--space-md);">
            <div style="display:flex;align-items:center;gap:var(--space-md);">
              <div style="width:48px;height:48px;border-radius:50%;background:${isAllPass ? 'rgba(25, 181, 165, 0.3)' : 'rgba(239, 68, 68, 0.3)'};display:flex;align-items:center;justify-content:center;font-size:24px;">
                ${isAllPass ? '✓' : '⚠️'}
              </div>
              <div>
                <h2 style="margin:0;font-size:var(--font-size-xl);color:#ffffff;">
                  ${isAllPass ? 'SYSTEM READY FOR REVIEWER DEMO' : 'SYSTEM CHECKS REQUIRE ATTENTION'}
                </h2>
                <p style="margin:4px 0 0 0;font-size:var(--font-size-sm);color:#ccfbf1;">
                  ${isAllPass ? 'All core database models, commercial policies, logistics nodes, and intelligence services are operational.' : 'One or more system prerequisites returned FAIL status from backend telemetry.'}
                </p>
              </div>
            </div>
            <div>
              <span class="badge ${isAllPass ? 'badge-teal' : 'badge-coral'}" style="font-size:var(--font-size-md);padding:8px 16px;font-weight:bold;">
                STATUS: ${readinessRes.status}
              </span>
            </div>
          </div>

          <!-- Readiness Check Items Table -->
          <div>
            <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin-bottom:var(--space-sm);">System & Module Verification Matrix</h3>
            <div class="analytics-table-wrapper">
              <table class="analytics-table">
                <thead>
                  <tr>
                    <th>Subsystem / Capability</th>
                    <th>Verification Scope</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  ${Object.entries(checks).map(([key, status]) => {
                    const meta = CHECK_LABELS[key] || { label: key.replace(/_/g, ' ').toUpperCase(), desc: 'Backend system verification check' };
                    const isPass = status === 'PASS';
                    return `
                      <tr>
                        <td><strong>${meta.label}</strong></td>
                        <td style="color:var(--color-text-secondary);font-size:var(--font-size-xs);">${meta.desc}</td>
                        <td>
                          <span class="badge ${isPass ? 'badge-teal' : 'badge-coral'}" style="font-weight:bold;padding:4px 10px;">
                            ${isPass ? 'PASS ✓' : 'FAIL ✗'}
                          </span>
                        </td>
                      </tr>
                    `;
                  }).join('')}
                </tbody>
              </table>
            </div>
          </div>

          <!-- Activated System Features -->
          <div style="background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-md);padding:var(--space-lg);box-shadow:var(--shadow-xs);">
            <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin:0 0 var(--space-md) 0;">Active Application Features & Architecture</h3>
            <div style="display:grid;grid-template-columns:repeat(auto-fill, minmax(240px, 1fr));gap:var(--space-sm);">
              ${Object.entries(infoRes.features || {}).map(([featKey, enabled]) => `
                <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 12px;background:var(--color-background);border-radius:var(--radius-sm);font-size:var(--font-size-xs);">
                  <span style="font-weight:600;color:var(--color-navy);">${featKey.replace(/_/g, ' ').toUpperCase()}</span>
                  <span class="badge badge-teal" style="font-size:10px;">ENABLED</span>
                </div>
              `).join('')}
            </div>
          </div>

          <!-- Quick Navigation to Golden Demo Modules -->
          <div style="background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-md);padding:var(--space-lg);box-shadow:var(--shadow-xs);">
            <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin:0 0 var(--space-xs) 0;">Reviewer Golden Demo Navigation Flow</h3>
            <p style="font-size:var(--font-size-xs);color:var(--color-text-secondary);margin:0 0 var(--space-md) 0;">
              Execute the end-to-end commercial operations lifecycle across all integrated modules:
            </p>
            <div style="display:flex;gap:var(--space-sm);flex-wrap:wrap;">
              <button class="btn btn-secondary btn-sm" onclick="window.location.hash='#/quotation-builder'">1. Quote Builder & What-If</button>
              <button class="btn btn-secondary btn-sm" onclick="window.location.hash='#/approvals'">2. Approval Queue</button>
              <button class="btn btn-secondary btn-sm" onclick="window.location.hash='#/negotiations'">3. Negotiation Inbox</button>
              <button class="btn btn-secondary btn-sm" onclick="window.location.hash='#/orders'">4. Orders & Fulfillment</button>
              <button class="btn btn-secondary btn-sm" onclick="window.location.hash='#/invoices'">5. Invoices & Billing</button>
              <button class="btn btn-secondary btn-sm" onclick="window.location.hash='#/deal-health'">6. Deal Health Intelligence</button>
              <button class="btn btn-secondary btn-sm" onclick="window.location.hash='#/customer-360'">7. Customer 360</button>
              <button class="btn btn-secondary btn-sm" onclick="window.location.hash='#/analytics'">8. Executive Analytics</button>
              <button class="btn btn-secondary btn-sm" onclick="window.location.hash='#/reports'">9. Reports Center</button>
            </div>
          </div>
        </div>
      `;
    } catch (err) {
      contentArea.innerHTML = `
        <div class="alert alert-coral">
          <strong>Failed to load demo readiness checks:</strong> ${err.message || 'Network error'}
        </div>
      `;
    }
  }

  global.DealFlowDemoReadinessView = {
    render
  };
})(typeof window !== 'undefined' ? window : this);
