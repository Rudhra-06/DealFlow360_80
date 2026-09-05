/**
 * DealFlow360 — Customer 360 Full Dossier View Controller
 * Implements unified customer intelligence, commercial summary, deal health,
 * operations, billing/MRR, activity timeline stream, and direct PDF/XLSX export.
 */
(function (global) {
  'use strict';

  let currentCustomerId = null;
  let currentTab = 'overview';
  let customerList = [];

  function formatCurrency(amount, currency = 'USD') {
    if (amount === null || amount === undefined) return '—';
    try {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency || 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(Number(amount));
    } catch (_) {
      return `${currency} ${Number(amount).toFixed(2)}`;
    }
  }

  function formatPercent(value) {
    if (value === null || value === undefined) return '—';
    return `${Number(value).toFixed(1)}%`;
  }

  function formatCount(value) {
    if (value === null || value === undefined) return '0';
    return new Intl.NumberFormat('en-US').format(Number(value));
  }

  function formatHealthLevelBadge(level) {
    const map = {
      'HEALTHY': { label: 'Healthy', cls: 'badge-health-healthy', bg: '#10b981' },
      'WATCH': { label: 'Watch', cls: 'badge-health-watch', bg: '#f59e0b' },
      'AT_RISK': { label: 'At Risk', cls: 'badge-health-at-risk', bg: '#f28c6b' },
      'CRITICAL': { label: 'Critical', cls: 'badge-health-critical', bg: '#ef4444' }
    };
    return map[level] || { label: level || 'Unknown', cls: 'badge-navy', bg: '#172a46' };
  }

  function getActivityIcon(eventType) {
    if (!eventType) return '📌';
    const type = eventType.toUpperCase();
    if (type.includes('QUOTE')) return '📄';
    if (type.includes('ORDER')) return '📦';
    if (type.includes('SHIPMENT')) return '🚚';
    if (type.includes('INVOICE')) return '💳';
    if (type.includes('PAYMENT')) return '💰';
    if (type.includes('SUBSCRIPTION')) return '🔄';
    if (type.includes('ALERT') || type.includes('HEALTH')) return '⚠️';
    return '📌';
  }

  /**
   * Main Render Function
   */
  async function render(container, params = {}) {
    const user = global.DealFlowAuth?.getCurrentUser();
    const roleName = user?.role?.name || 'ADMIN';

    // Route guard for customer role
    if (roleName === 'CUSTOMER') {
      window.location.hash = '#/portal';
      return;
    }

    if (params.customerId || params.id) {
      currentCustomerId = parseInt(params.customerId || params.id, 10);
    }

    container.innerHTML = `
      <div class="customer-360-container animate-fade-in">
        <!-- Top Action Bar -->
        <div class="analytics-header-bar">
          <div class="analytics-title-group">
            <h1>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--color-teal);"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
              Customer 360 Unified Intelligence
            </h1>
            <div class="analytics-metadata-row">
              <span>Comprehensive 360-degree commercial, operational, and financial dossier</span>
            </div>
          </div>
          <div class="analytics-header-actions">
            <!-- Customer Selector -->
            <div style="display:flex;align-items:center;gap:8px;">
              <label for="c360-customer-select" style="font-size:var(--font-size-xs);font-weight:600;color:var(--color-text-secondary);text-transform:uppercase;">Select Account:</label>
              <select id="c360-customer-select" style="padding:7px 12px;border:1px solid var(--color-border);border-radius:var(--radius-sm);font-size:var(--font-size-sm);min-width:240px;background:#ffffff;">
                <option value="">Loading accounts...</option>
              </select>
            </div>
            <button id="btn-c360-export-pdf" class="btn btn-secondary btn-sm" title="Export Customer 360 Dossier as PDF">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              Export PDF
            </button>
            <button id="btn-c360-export-xlsx" class="btn btn-secondary btn-sm" title="Export Customer 360 Dossier as XLSX">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              Export XLSX
            </button>
          </div>
        </div>

        <!-- Customer 360 Dynamic Content -->
        <div id="c360-content-area" style="min-height:400px;">
          <div style="display:flex;justify-content:center;align-items:center;padding:80px 0;">
            <div class="spinner"></div>
          </div>
        </div>
      </div>
    `;

    await initializeCustomerSelector(container);
  }

  async function initializeCustomerSelector(container) {
    const selectEl = container.querySelector('#c360-customer-select');
    try {
      // Fetch customers list authorized for user
      const res = await global.DealFlowAPI.get('/api/v1/customers');
      customerList = Array.isArray(res) ? res : (res.items || res.customers || []);

      if (customerList.length === 0) {
        selectEl.innerHTML = `<option value="">No authorized customers found</option>`;
        showEmptyState(container, 'No accessible customers found for your account scope.');
        return;
      }

      selectEl.innerHTML = customerList.map(c => `
        <option value="${c.id}" ${currentCustomerId === c.id ? 'selected' : ''}>
          ${c.name} (${c.customer_code || `CUST-${c.id}`})
        </option>
      `).join('');

      if (!currentCustomerId || !customerList.some(c => c.id === currentCustomerId)) {
        currentCustomerId = customerList[0].id;
      }
      selectEl.value = currentCustomerId;

      // Bind selection change
      selectEl.addEventListener('change', (e) => {
        currentCustomerId = parseInt(e.target.value, 10);
        loadCustomerDossier(container);
      });

      // Bind Exports
      container.querySelector('#btn-c360-export-pdf')?.addEventListener('click', () => triggerExport('PDF'));
      container.querySelector('#btn-c360-export-xlsx')?.addEventListener('click', () => triggerExport('XLSX'));

      await loadCustomerDossier(container);
    } catch (err) {
      selectEl.innerHTML = `<option value="">Error loading accounts</option>`;
      showErrorState(container, err.message);
    }
  }

  async function triggerExport(format) {
    if (!currentCustomerId) {
      global.UI?.showToast('Please select a customer first.', 'coral');
      return;
    }

    try {
      global.UI?.showToast(`Generating Customer 360 ${format} report...`, 'teal');
      await global.ReportsAPI.exportReport({
        report_type: 'CUSTOMER_360',
        format: format,
        customer_id: currentCustomerId
      });
      global.UI?.showToast(`Customer 360 ${format} report downloaded successfully.`, 'teal');
    } catch (err) {
      global.UI?.showToast(`Export failed: ${err.message}`, 'coral');
    }
  }

  async function loadCustomerDossier(container) {
    const contentArea = container.querySelector('#c360-content-area');
    if (!contentArea || !currentCustomerId) return;

    contentArea.innerHTML = `
      <div style="display:flex;justify-content:center;align-items:center;padding:80px 0;">
        <div style="display:flex;flex-direction:column;align-items:center;gap:12px;">
          <div class="spinner"></div>
          <span style="font-size:var(--font-size-sm);color:var(--color-text-secondary);">Loading Customer 360 Dossier...</span>
        </div>
      </div>
    `;

    try {
      const data = await global.AnalyticsAPI.getCustomer360(currentCustomerId);
      renderDossier(contentArea, data);
    } catch (err) {
      showErrorState(container, err.message);
    }
  }

  function renderDossier(container, data) {
    const cust = data.customer || {};
    const comm = data.commercial || {};
    const health = data.deal_health || {};
    const orders = data.orders || {};
    const billing = data.billing || {};
    const subs = data.subscriptions || {};
    const activity = data.recent_activity || [];

    const healthInfo = formatHealthLevelBadge(health.health_level);

    container.innerHTML = `
      <div style="display:flex;flex-direction:column;gap:var(--space-xl);" class="animate-fade-in">
        <!-- 1. Customer Hero Header -->
        <div class="customer-360-hero">
          <div class="c360-hero-info">
            <div class="c360-company-title">
              <span>${cust.name || 'Account'}</span>
              <span class="c360-tier-badge">${cust.customer_tier || 'Standard Tier'}</span>
            </div>
            <div class="c360-meta-pills">
              <span>Code: <strong>${cust.customer_code || `CUST-${cust.customer_id}`}</strong></span>
              <span>Owner: <strong>${cust.assigned_sales_rep || 'Unassigned'}</strong></span>
              <span>Status: <strong style="color:#5eead4;">${cust.is_active ? 'Active Customer' : 'Inactive'}</strong></span>
              <span>Since: <strong>${cust.created_at ? new Date(cust.created_at).toLocaleDateString() : 'N/A'}</strong></span>
            </div>
          </div>

          <!-- Deal Health Ribbon -->
          <div class="c360-hero-health">
            <div class="c360-health-score-circle" style="background:${healthInfo.bg};">
              ${health.health_score !== null && health.health_score !== undefined ? Number(health.health_score).toFixed(0) : '—'}
            </div>
            <div style="display:flex;flex-direction:column;">
              <span style="font-size:11px;text-transform:uppercase;color:#cbd5e1;letter-spacing:0.5px;">Deal Health Status</span>
              <span style="font-size:var(--font-size-md);font-weight:var(--font-weight-bold);color:#ffffff;">
                ${healthInfo.label}
              </span>
              <span style="font-size:11px;color:#94a3b8;">${health.open_alert_count || 0} active alerts</span>
            </div>
          </div>
        </div>

        <!-- 2. Sub-Tabs Bar -->
        <div class="analytics-tab-bar" style="margin-top:-8px;">
          <button class="analytics-tab-btn ${currentTab === 'overview' ? 'active' : ''}" data-tab="overview">Overview Dossier</button>
          <button class="analytics-tab-btn ${currentTab === 'commercial' ? 'active' : ''}" data-tab="commercial">Commercial & Quotes</button>
          <button class="analytics-tab-btn ${currentTab === 'health' ? 'active' : ''}" data-tab="health">Deal Health & Signals</button>
          <button class="analytics-tab-btn ${currentTab === 'orders' ? 'active' : ''}" data-tab="orders">Orders & Fulfillment</button>
          <button class="analytics-tab-btn ${currentTab === 'billing' ? 'active' : ''}" data-tab="billing">Financial & Receivables</button>
          <button class="analytics-tab-btn ${currentTab === 'subscriptions' ? 'active' : ''}" data-tab="subscriptions">Subscriptions & MRR</button>
          <button class="analytics-tab-btn ${currentTab === 'activity' ? 'active' : ''}" data-tab="activity">Unified Activity Stream (${activity.length})</button>
        </div>

        <!-- 3. Dynamic Sub-tab Panel Content -->
        <div id="c360-tab-panel">
          ${renderTabContent(currentTab, { cust, comm, health, orders, billing, subs, activity })}
        </div>
      </div>
    `;

    // Bind sub-tabs
    container.querySelectorAll('.analytics-tab-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        container.querySelectorAll('.analytics-tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentTab = btn.dataset.tab;
        const panel = container.querySelector('#c360-tab-panel');
        if (panel) {
          panel.innerHTML = renderTabContent(currentTab, { cust, comm, health, orders, billing, subs, activity });
        }
      });
    });
  }

  function renderTabContent(tab, d) {
    if (tab === 'overview') {
      return renderOverviewDossier(d);
    } else if (tab === 'commercial') {
      return renderCommercialDossier(d);
    } else if (tab === 'health') {
      return renderHealthDossier(d);
    } else if (tab === 'orders') {
      return renderOrdersDossier(d);
    } else if (tab === 'billing') {
      return renderBillingDossier(d);
    } else if (tab === 'subscriptions') {
      return renderSubscriptionsDossier(d);
    } else if (tab === 'activity') {
      return renderActivityDossier(d);
    }
    return '';
  }

  function renderOverviewDossier({ comm, orders, billing, subs, health }) {
    return `
      <div style="display:flex;flex-direction:column;gap:var(--space-xl);">
        <!-- Summary Matrix -->
        <div>
          <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin-bottom:var(--space-sm);">Customer Portfolio Highlights</h3>
          <div class="kpi-metric-grid">
            <div class="kpi-card">
              <span class="kpi-card-label">Total Quotes</span>
              <span class="kpi-card-value">${formatCount(comm.total_quotations)}</span>
              <span class="kpi-card-subtext">${comm.open_quotations || 0} open in-flight</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Confirmed Quotes</span>
              <span class="kpi-card-value" style="color:var(--color-teal);">${formatCount(comm.confirmed_quotations)}</span>
              <span class="kpi-card-subtext">Win rate: ${formatPercent(comm.confirmation_rate)}</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Open Orders</span>
              <span class="kpi-card-value">${formatCount(orders.open_orders)}</span>
              <span class="kpi-card-subtext">${orders.in_fulfillment_orders || 0} in fulfillment</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Backorders</span>
              <span class="kpi-card-value" style="color:${Number(orders.backordered_orders || 0) > 0 ? 'var(--color-coral)' : 'var(--color-navy)'};">
                ${formatCount(orders.backordered_orders)}
              </span>
              <span class="kpi-card-subtext">Fulfillment bottlenecks</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Active Subscriptions</span>
              <span class="kpi-card-value" style="color:var(--color-navy);">${formatCount(subs.active_subscriptions)}</span>
              <span class="kpi-card-subtext">Recurring accounts</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Open Alerts</span>
              <span class="kpi-card-value" style="color:${Number(health.open_alert_count || 0) > 0 ? 'var(--color-coral)' : 'var(--color-teal)'};">
                ${formatCount(health.open_alert_count)}
              </span>
              <span class="kpi-card-subtext">Risk telemetry</span>
            </div>
          </div>
        </div>

        <!-- Financial Summary by Currency -->
        <div>
          <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin-bottom:4px;">Financial Breakdown by Currency</h3>
          <p style="font-size:var(--font-size-xs);color:var(--color-text-secondary);margin-bottom:var(--space-md);">
            ISO transacted currencies are segregated without client-side cross-currency summation.
          </p>
          <div style="display:flex;flex-direction:column;gap:var(--space-md);">
            ${Object.keys(billing.invoiced_value_by_currency || {}).length === 0 ? `
              <div style="padding:20px;background:var(--color-background);border-radius:var(--radius-sm);color:var(--color-text-muted);font-size:var(--font-size-sm);">
                No financial transactions recorded for this account.
              </div>
            ` : Object.keys(billing.invoiced_value_by_currency || {}).map(curr => `
              <div class="currency-section-card">
                <div class="currency-section-header">
                  <span class="currency-badge-tag">${curr}</span>
                  <span style="font-size:var(--font-size-xs);color:var(--color-text-secondary);">Currency: ${curr}</span>
                </div>
                <div class="currency-values-grid">
                  <div class="currency-stat-item">
                    <span class="currency-stat-label">Confirmed Value</span>
                    <span class="currency-stat-val positive">${formatCurrency(comm.confirmed_value_by_currency?.[curr], curr)}</span>
                  </div>
                  <div class="currency-stat-item">
                    <span class="currency-stat-label">Invoiced</span>
                    <span class="currency-stat-val">${formatCurrency(billing.invoiced_value_by_currency?.[curr], curr)}</span>
                  </div>
                  <div class="currency-stat-item">
                    <span class="currency-stat-label">Paid</span>
                    <span class="currency-stat-val positive">${formatCurrency(billing.payments_received_by_currency?.[curr], curr)}</span>
                  </div>
                  <div class="currency-stat-item">
                    <span class="currency-stat-label">Outstanding Balance</span>
                    <span class="currency-stat-val ${Number(billing.outstanding_balance_by_currency?.[curr] || 0) > 0 ? 'warning' : ''}">
                      ${formatCurrency(billing.outstanding_balance_by_currency?.[curr], curr)}
                    </span>
                  </div>
                  ${subs.monthly_recurring_revenue?.[curr] !== undefined ? `
                    <div class="currency-stat-item">
                      <span class="currency-stat-label">Active MRR</span>
                      <span class="currency-stat-val" style="color:var(--color-navy);">${formatCurrency(subs.monthly_recurring_revenue?.[curr], curr)}</span>
                    </div>
                  ` : ''}
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  }

  function renderCommercialDossier({ comm }) {
    return `
      <div style="display:flex;flex-direction:column;gap:var(--space-lg);">
        <div class="kpi-metric-grid">
          <div class="kpi-card">
            <span class="kpi-card-label">Total Quotations</span>
            <span class="kpi-card-value">${formatCount(comm.total_quotations)}</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-card-label">Confirmed Quotations</span>
            <span class="kpi-card-value" style="color:var(--color-teal);">${formatCount(comm.confirmed_quotations)}</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-card-label">Confirmation Rate</span>
            <span class="kpi-card-value">${formatPercent(comm.confirmation_rate)}</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-card-label">Avg Discount</span>
            <span class="kpi-card-value">${formatPercent(comm.average_discount_pct)}</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-card-label">Avg Margin</span>
            <span class="kpi-card-value" style="color:var(--color-teal);">${formatPercent(comm.average_margin_pct)}</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-card-label">Latest Quote</span>
            <span class="kpi-card-value" style="font-size:var(--font-size-lg);">${comm.latest_quote_number || '—'}</span>
          </div>
        </div>
      </div>
    `;
  }

  function renderHealthDossier({ health }) {
    const info = formatHealthLevelBadge(health.health_level);
    return `
      <div style="display:flex;flex-direction:column;gap:var(--space-lg);">
        <div style="background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-md);padding:var(--space-lg);box-shadow:var(--shadow-xs);">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-md);">
            <div style="display:flex;align-items:center;gap:var(--space-md);">
              <div class="c360-health-score-circle" style="background:${info.bg};width:56px;height:56px;font-size:22px;">
                ${health.health_score !== null && health.health_score !== undefined ? Number(health.health_score).toFixed(0) : '—'}
              </div>
              <div>
                <h4 style="margin:0;color:var(--color-navy);font-size:var(--font-size-lg);">Health Assessment: ${info.label}</h4>
                <span style="font-size:var(--font-size-xs);color:var(--color-text-secondary);">
                  Last evaluated: ${health.last_activity_at ? new Date(health.last_activity_at).toLocaleString() : 'Recent'}
                </span>
              </div>
            </div>
            <button class="btn btn-secondary btn-sm" onclick="window.location.hash='#/deal-health'">Open Deal Health Workspace &rarr;</button>
          </div>

          <h5 style="margin:var(--space-md) 0 var(--space-xs) 0;color:var(--color-navy);font-size:var(--font-size-sm);">Active Risk Signals</h5>
          ${(health.top_signals && health.top_signals.length > 0) ? `
            <div style="display:flex;flex-direction:column;gap:6px;">
              ${health.top_signals.map(s => `
                <div style="display:flex;align-items:center;gap:8px;padding:8px 12px;background:var(--color-background);border-radius:var(--radius-sm);font-size:var(--font-size-sm);">
                  <span style="color:var(--color-coral);font-weight:bold;">⚠️</span>
                  <span>${s}</span>
                </div>
              `).join('')}
            </div>
          ` : `
            <p style="font-size:var(--font-size-sm);color:var(--color-teal);font-weight:500;">✓ No active adverse risk signals detected.</p>
          `}
        </div>
      </div>
    `;
  }

  function renderOrdersDossier({ orders }) {
    return `
      <div style="display:flex;flex-direction:column;gap:var(--space-lg);">
        <div class="kpi-metric-grid">
          <div class="kpi-card">
            <span class="kpi-card-label">Total Orders</span>
            <span class="kpi-card-value">${formatCount(orders.total_orders)}</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-card-label">Open Orders</span>
            <span class="kpi-card-value">${formatCount(orders.open_orders)}</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-card-label">In Fulfillment</span>
            <span class="kpi-card-value">${formatCount(orders.in_fulfillment_orders)}</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-card-label">Backordered</span>
            <span class="kpi-card-value" style="color:var(--color-coral);">${formatCount(orders.backordered_orders)}</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-card-label">Recent Shipments</span>
            <span class="kpi-card-value">${formatCount(orders.recent_shipment_count)}</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-card-label">Latest Order #</span>
            <span class="kpi-card-value" style="font-size:var(--font-size-lg);">${orders.latest_order_number || '—'}</span>
          </div>
        </div>
      </div>
    `;
  }

  function renderBillingDossier({ billing }) {
    return `
      <div style="display:flex;flex-direction:column;gap:var(--space-lg);">
        <div class="kpi-metric-grid">
          <div class="kpi-card">
            <span class="kpi-card-label">Total Invoices</span>
            <span class="kpi-card-value">${formatCount(billing.invoice_count)}</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-card-label">Outstanding Invoices</span>
            <span class="kpi-card-value">${formatCount(billing.outstanding_invoices)}</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-card-label">Overdue Invoices</span>
            <span class="kpi-card-value" style="color:${Number(billing.overdue_invoices || 0) > 0 ? 'var(--color-coral)' : 'var(--color-navy)'};">
              ${formatCount(billing.overdue_invoices)}
            </span>
          </div>
          <div class="kpi-card">
            <span class="kpi-card-label">Credit Notes</span>
            <span class="kpi-card-value">${formatCount(billing.credit_note_count)}</span>
          </div>
        </div>
      </div>
    `;
  }

  function renderSubscriptionsDossier({ subs }) {
    return `
      <div style="display:flex;flex-direction:column;gap:var(--space-lg);">
        <div class="kpi-metric-grid">
          <div class="kpi-card">
            <span class="kpi-card-label">Active Subscriptions</span>
            <span class="kpi-card-value" style="color:var(--color-teal);">${formatCount(subs.active_subscriptions)}</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-card-label">Next Billing Date</span>
            <span class="kpi-card-value" style="font-size:var(--font-size-lg);">
              ${subs.next_billing_date ? new Date(subs.next_billing_date).toLocaleDateString() : '—'}
            </span>
          </div>
        </div>

        <div style="background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-md);padding:var(--space-lg);box-shadow:var(--shadow-xs);">
          <h4 style="margin:0 0 var(--space-md) 0;color:var(--color-navy);font-size:var(--font-size-md);">Monthly Recurring Revenue (MRR)</h4>
          ${Object.keys(subs.monthly_recurring_revenue || {}).length === 0 ? `
            <p style="font-size:var(--font-size-sm);color:var(--color-text-muted);">No active recurring billing contracts.</p>
          ` : `
            <div style="display:flex;gap:var(--space-lg);flex-wrap:wrap;">
              ${Object.entries(subs.monthly_recurring_revenue).map(([curr, mrr]) => `
                <div style="background:var(--color-background);padding:12px 18px;border-radius:var(--radius-sm);border-left:3px solid var(--color-teal);">
                  <div style="font-size:var(--font-size-xs);color:var(--color-text-secondary);">${curr} MRR</div>
                  <div style="font-size:var(--font-size-xl);font-weight:bold;color:var(--color-navy);">${formatCurrency(mrr, curr)}</div>
                </div>
              `).join('')}
            </div>
          `}
        </div>
      </div>
    `;
  }

  function renderActivityDossier({ activity }) {
    if (!activity || activity.length === 0) {
      return `
        <div style="padding:40px;text-align:center;background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-md);color:var(--color-text-muted);font-size:var(--font-size-sm);">
          No chronological activity recorded for this customer yet.
        </div>
      `;
    }

    return `
      <div class="timeline-stream">
        ${activity.map(item => `
          <div class="timeline-event-card">
            <div class="timeline-event-icon-dot">${getActivityIcon(item.event_type)}</div>
            <div class="timeline-event-header">
              <span class="timeline-event-title">${item.title || item.event_type}</span>
              <span class="timeline-event-time">${item.timestamp ? new Date(item.timestamp).toLocaleString() : ''}</span>
            </div>
            ${item.description ? `<p class="timeline-event-desc" style="margin:4px 0 0 0;">${item.description}</p>` : ''}
            ${item.reference_id ? `
              <div style="margin-top:6px;">
                <span class="badge badge-navy" style="font-size:11px;">Ref: ${item.reference_id}</span>
              </div>
            ` : ''}
          </div>
        `).join('')}
      </div>
    `;
  }

  function showEmptyState(container, msg) {
    const content = container.querySelector('#c360-content-area');
    if (content) {
      content.innerHTML = `
        <div style="padding:60px 20px;text-align:center;background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-md);">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="color:var(--color-text-muted);margin-bottom:12px;"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          <h3 style="color:var(--color-navy);margin-bottom:6px;">No Customer Selected</h3>
          <p style="color:var(--color-text-secondary);font-size:var(--font-size-sm);">${msg}</p>
        </div>
      `;
    }
  }

  function showErrorState(container, errorMsg) {
    const content = container.querySelector('#c360-content-area');
    if (content) {
      content.innerHTML = `
        <div class="alert alert-coral" style="margin-top:20px;">
          <strong>Error loading Customer 360 dossier:</strong> ${errorMsg}
        </div>
      `;
    }
  }

  global.DealFlowCustomer360View = {
    render
  };
})(typeof window !== 'undefined' ? window : this);
