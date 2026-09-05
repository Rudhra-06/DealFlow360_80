/**
 * DealFlow360 — Comprehensive Analytics View Controller
 * Implements Executive Overview, Trends, Quotation Funnel, Sales Performance,
 * Commercial (Discounts/Margins), Approvals/Negotiations, Deal Health Analytics,
 * Operations (Fulfillment/Warehouses/Backorders/Shipments), Billing/Receivables/MRR,
 * and Product Analytics.
 */
(function (global) {
  'use strict';

  let currentTab = 'overview';
  let activeFilters = {
    granularity: 'DAY',
    start_date: '',
    end_date: '',
    currency: '',
    sales_rep_id: '',
    customer_id: '',
    warehouse_id: '',
    product_category_id: ''
  };
  let lastRefreshedTime = new Date();
  let currentRequestId = 0;

  // Format Helpers
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

  function formatDuration(hours) {
    if (hours === null || hours === undefined) return '—';
    return `${Number(hours).toFixed(1)}h`;
  }

  function setDatePreset(preset) {
    const now = new Date();
    let start = new Date();
    let end = new Date();

    if (preset === 'today') {
      start.setHours(0, 0, 0, 0);
      end.setHours(23, 59, 59, 999);
    } else if (preset === 'last7') {
      start.setDate(now.getDate() - 7);
    } else if (preset === 'last30') {
      start.setDate(now.getDate() - 30);
    } else if (preset === 'this_month') {
      start = new Date(now.getFullYear(), now.getMonth(), 1);
    } else if (preset === 'last90') {
      start.setDate(now.getDate() - 90);
    }

    if (preset !== 'all') {
      activeFilters.start_date = start.toISOString().split('T')[0];
      activeFilters.end_date = end.toISOString().split('T')[0];
    } else {
      activeFilters.start_date = '';
      activeFilters.end_date = '';
    }
  }

  // Set default to last 30 days
  setDatePreset('last30');

  /**
   * Main Render Entry Point
   */
  async function render(container, params = {}) {
    if (params.tab) {
      currentTab = params.tab;
    }

    const user = global.DealFlowAuth?.getCurrentUser();
    const roleName = user?.role?.name || 'ADMIN';

    // Customer route guard
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
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--color-teal);"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
              Executive & Operations Analytics
            </h1>
            <div class="analytics-metadata-row">
              <span class="live-data-badge"><span class="live-data-dot"></span> Live Data</span>
              <span>Refreshed: <strong id="analytics-refreshed-time">${lastRefreshedTime.toLocaleTimeString()}</strong></span>
              <span id="analytics-period-label">Period: Last 30 Days</span>
            </div>
          </div>
          <div class="analytics-header-actions">
            <button id="btn-refresh-analytics" class="btn btn-secondary btn-sm" title="Refresh live telemetry">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
              Refresh
            </button>
            <button id="btn-export-current-analytics" class="btn btn-primary btn-sm" title="Export this report">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              Export Report
            </button>
          </div>
        </div>

        <!-- Tab Navigation -->
        <div class="analytics-tab-bar" role="tablist">
          <button class="analytics-tab-btn ${currentTab === 'overview' ? 'active' : ''}" data-tab="overview">Executive Overview</button>
          <button class="analytics-tab-btn ${currentTab === 'commercial' ? 'active' : ''}" data-tab="commercial">Commercial & Sales</button>
          <button class="analytics-tab-btn ${currentTab === 'approvals' ? 'active' : ''}" data-tab="approvals">Approvals & Negotiation</button>
          <button class="analytics-tab-btn ${currentTab === 'deal_health' ? 'active' : ''}" data-tab="deal_health">Deal Health Analytics</button>
          <button class="analytics-tab-btn ${currentTab === 'operations' ? 'active' : ''}" data-tab="operations">Operations & Fulfillment</button>
          <button class="analytics-tab-btn ${currentTab === 'billing' ? 'active' : ''}" data-tab="billing">Billing, Receivables & MRR</button>
          <button class="analytics-tab-btn ${currentTab === 'products' ? 'active' : ''}" data-tab="products">Products & Categories</button>
        </div>

        <!-- Global Filter Bar -->
        <div class="analytics-filter-card">
          <div class="filter-control-group" style="flex: 0 0 160px;">
            <label>Date Preset</label>
            <select id="analytics-filter-preset">
              <option value="last30" selected>Last 30 Days</option>
              <option value="today">Today</option>
              <option value="last7">Last 7 Days</option>
              <option value="this_month">This Month</option>
              <option value="last90">Last 90 Days</option>
              <option value="all">All Time</option>
              <option value="custom">Custom Range</option>
            </select>
          </div>
          <div class="filter-control-group">
            <label>Start Date</label>
            <input type="date" id="analytics-filter-start" value="${activeFilters.start_date || ''}">
          </div>
          <div class="filter-control-group">
            <label>End Date</label>
            <input type="date" id="analytics-filter-end" value="${activeFilters.end_date || ''}">
          </div>
          <div class="filter-control-group" style="flex: 0 0 130px;">
            <label>Granularity</label>
            <select id="analytics-filter-granularity">
              <option value="DAY" ${activeFilters.granularity === 'DAY' ? 'selected' : ''}>Daily</option>
              <option value="WEEK" ${activeFilters.granularity === 'WEEK' ? 'selected' : ''}>Weekly</option>
              <option value="MONTH" ${activeFilters.granularity === 'MONTH' ? 'selected' : ''}>Monthly</option>
            </select>
          </div>
          <div class="filter-actions">
            <button id="btn-apply-filters" class="btn btn-primary btn-sm">Apply Filters</button>
            <button id="btn-reset-filters" class="btn btn-ghost btn-sm">Reset</button>
          </div>
        </div>

        <!-- Dynamic Tab Content View Container -->
        <div id="analytics-tab-content" style="min-height: 400px;">
          <div style="display:flex;justify-content:center;align-items:center;padding:60px 0;">
            <div class="spinner"></div>
          </div>
        </div>
      </div>
    `;

    bindHeaderEvents(container);
    await loadActiveTabContent();
  }

  function bindHeaderEvents(container) {
    // Tab switching
    container.querySelectorAll('.analytics-tab-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        container.querySelectorAll('.analytics-tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentTab = btn.dataset.tab;
        loadActiveTabContent();
      });
    });

    // Refresh
    container.querySelector('#btn-refresh-analytics')?.addEventListener('click', () => {
      lastRefreshedTime = new Date();
      const refTimeEl = container.querySelector('#analytics-refreshed-time');
      if (refTimeEl) refTimeEl.textContent = lastRefreshedTime.toLocaleTimeString();
      loadActiveTabContent();
    });

    // Export button -> routes to reports view pre-configured
    container.querySelector('#btn-export-current-analytics')?.addEventListener('click', () => {
      let reportType = 'EXECUTIVE_SUMMARY';
      if (currentTab === 'commercial') reportType = 'SALES_PERFORMANCE';
      if (currentTab === 'approvals') reportType = 'APPROVAL_ANALYTICS';
      if (currentTab === 'deal_health') reportType = 'DEAL_HEALTH';
      if (currentTab === 'operations') reportType = 'FULFILLMENT';
      if (currentTab === 'billing') reportType = 'BILLING';
      if (currentTab === 'products') reportType = 'PRODUCT_PERFORMANCE';

      window.location.hash = `#/reports?type=${reportType}&start_date=${activeFilters.start_date}&end_date=${activeFilters.end_date}`;
    });

    // Preset selector
    container.querySelector('#analytics-filter-preset')?.addEventListener('change', (e) => {
      if (e.target.value !== 'custom') {
        setDatePreset(e.target.value);
        container.querySelector('#analytics-filter-start').value = activeFilters.start_date;
        container.querySelector('#analytics-filter-end').value = activeFilters.end_date;
        loadActiveTabContent();
      }
    });

    // Apply filters
    container.querySelector('#btn-apply-filters')?.addEventListener('click', () => {
      activeFilters.start_date = container.querySelector('#analytics-filter-start').value;
      activeFilters.end_date = container.querySelector('#analytics-filter-end').value;
      activeFilters.granularity = container.querySelector('#analytics-filter-granularity').value;
      loadActiveTabContent();
    });

    // Reset filters
    container.querySelector('#btn-reset-filters')?.addEventListener('click', () => {
      setDatePreset('last30');
      container.querySelector('#analytics-filter-preset').value = 'last30';
      container.querySelector('#analytics-filter-start').value = activeFilters.start_date;
      container.querySelector('#analytics-filter-end').value = activeFilters.end_date;
      container.querySelector('#analytics-filter-granularity').value = 'DAY';
      activeFilters.granularity = 'DAY';
      loadActiveTabContent();
    });
  }

  async function loadActiveTabContent() {
    const contentEl = document.getElementById('analytics-tab-content');
    if (!contentEl) return;

    contentEl.innerHTML = `
      <div style="display:flex;justify-content:center;align-items:center;padding:80px 0;">
        <div style="display:flex;flex-direction:column;align-items:center;gap:12px;">
          <div class="spinner"></div>
          <span style="font-size:var(--font-size-sm);color:var(--color-text-secondary);">Loading analytics telemetry...</span>
        </div>
      </div>
    `;

    const reqId = ++currentRequestId;

    try {
      if (currentTab === 'overview') {
        await renderOverviewTab(contentEl, reqId);
      } else if (currentTab === 'commercial') {
        await renderCommercialTab(contentEl, reqId);
      } else if (currentTab === 'approvals') {
        await renderApprovalsTab(contentEl, reqId);
      } else if (currentTab === 'deal_health') {
        await renderDealHealthTab(contentEl, reqId);
      } else if (currentTab === 'operations') {
        await renderOperationsTab(contentEl, reqId);
      } else if (currentTab === 'billing') {
        await renderBillingTab(contentEl, reqId);
      } else if (currentTab === 'products') {
        await renderProductsTab(contentEl, reqId);
      }
    } catch (err) {
      if (reqId !== currentRequestId) return;
      contentEl.innerHTML = `
        <div class="alert alert-coral" style="margin-top:20px;">
          <strong>Failed to load analytics:</strong> ${err.message || 'An unexpected error occurred.'}
        </div>
      `;
    }
  }

  /**
   * 1. EXECUTIVE OVERVIEW TAB
   */
  async function renderOverviewTab(container, reqId) {
    const [overviewData, trendData, summaryText] = await Promise.all([
      global.AnalyticsAPI.getOverview(activeFilters),
      global.AnalyticsAPI.getOverviewTrend(activeFilters),
      global.AnalyticsAPI.getExecutiveSummaryText(activeFilters).catch(() => ({ summary: '' }))
    ]);

    if (reqId !== currentRequestId) return;

    // Render Currency Groups
    let currencyHtml = '';
    const allCurrencies = new Set([
      ...Object.keys(overviewData.confirmed_order_value || {}),
      ...Object.keys(overviewData.invoiced_value || {}),
      ...Object.keys(overviewData.payments_received || {}),
      ...Object.keys(overviewData.outstanding_receivables || {}),
      ...Object.keys(overviewData.monthly_recurring_revenue || {}),
      ...Object.keys(overviewData.financial_by_currency || {}),
      ...Object.keys(overviewData.currencies || {})
    ]);

    const currencyBreakdown = {};
    for (const c of allCurrencies) {
      currencyBreakdown[c] = {
        confirmed_value: overviewData.confirmed_order_value?.[c] ?? overviewData.financial_by_currency?.[c]?.confirmed_value ?? overviewData.financial_by_currency?.[c]?.confirmed,
        invoiced_value: overviewData.invoiced_value?.[c] ?? overviewData.financial_by_currency?.[c]?.invoiced_value ?? overviewData.financial_by_currency?.[c]?.invoiced,
        paid_value: overviewData.payments_received?.[c] ?? overviewData.financial_by_currency?.[c]?.paid_value ?? overviewData.financial_by_currency?.[c]?.paid,
        outstanding_value: overviewData.outstanding_receivables?.[c] ?? overviewData.financial_by_currency?.[c]?.outstanding_value ?? overviewData.financial_by_currency?.[c]?.outstanding,
        mrr: overviewData.monthly_recurring_revenue?.[c] ?? overviewData.financial_by_currency?.[c]?.mrr
      };
    }

    if (Object.keys(currencyBreakdown).length === 0) {
      currencyHtml = `<p style="font-size:var(--font-size-sm);color:var(--color-text-muted);">No financial transaction activity recorded in this period.</p>`;
    } else {
      currencyHtml = `
        <div class="currency-metrics-container">
          <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin-bottom:4px;">Commercial & Financial Breakdown by Currency</h3>
          <p style="font-size:var(--font-size-xs);color:var(--color-text-secondary);margin-bottom:var(--space-md);">
            Strict multi-currency isolation. Financial figures are presented in their native transacted currencies.
          </p>
          <div style="display:flex;flex-direction:column;gap:var(--space-md);">
            ${Object.entries(currencyBreakdown).map(([curr, stats]) => `
              <div class="currency-section-card">
                <div class="currency-section-header">
                  <span class="currency-badge-tag">${curr}</span>
                  <span style="font-size:var(--font-size-xs);color:var(--color-text-secondary);">ISO Currency Scope: ${curr}</span>
                </div>
                <div class="currency-values-grid">
                  <div class="currency-stat-item">
                    <span class="currency-stat-label">Confirmed Value</span>
                    <span class="currency-stat-val positive">${formatCurrency(stats.confirmed_value ?? stats.confirmed, curr)}</span>
                  </div>
                  <div class="currency-stat-item">
                    <span class="currency-stat-label">Invoiced Value</span>
                    <span class="currency-stat-val">${formatCurrency(stats.invoiced_value ?? stats.invoiced, curr)}</span>
                  </div>
                  <div class="currency-stat-item">
                    <span class="currency-stat-label">Paid Value</span>
                    <span class="currency-stat-val positive">${formatCurrency(stats.paid_value ?? stats.paid, curr)}</span>
                  </div>
                  <div class="currency-stat-item">
                    <span class="currency-stat-label">Outstanding Balance</span>
                    <span class="currency-stat-val ${Number(stats.outstanding_value ?? stats.outstanding) > 0 ? 'warning' : ''}">
                      ${formatCurrency(stats.outstanding_value ?? stats.outstanding, curr)}
                    </span>
                  </div>
                  ${stats.mrr !== undefined ? `
                    <div class="currency-stat-item">
                      <span class="currency-stat-label">Monthly Recurring (MRR)</span>
                      <span class="currency-stat-val" style="color:var(--color-navy);">${formatCurrency(stats.mrr, curr)}</span>
                    </div>
                  ` : ''}
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    container.innerHTML = `
      <div style="display:flex;flex-direction:column;gap:var(--space-xl);">
        <!-- Executive Narrative Summary if returned -->
        ${summaryText?.summary ? `
          <div style="background:var(--color-surface);border:1px solid var(--color-border);border-left:4px solid var(--color-teal);border-radius:var(--radius-md);padding:var(--space-md) var(--space-lg);box-shadow:var(--shadow-xs);">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
              <span class="badge badge-teal" style="font-size:11px;">Executive Telemetry Intelligence</span>
              <strong style="color:var(--color-navy);font-size:var(--font-size-sm);">Management Summary</strong>
            </div>
            <p style="font-size:var(--font-size-sm);color:var(--color-text);margin:0;line-height:1.5;">${summaryText.summary}</p>
          </div>
        ` : ''}

        <!-- Top Headline KPIs -->
        <div>
          <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin-bottom:var(--space-sm);">Key Pipeline & Operational Metrics</h3>
          <div class="kpi-metric-grid">
            <div class="kpi-card">
              <span class="kpi-card-label">Quotes Created</span>
              <span class="kpi-card-value">${formatCount(overviewData.quotation_count ?? overviewData.quotes_created ?? overviewData.total_quotes)}</span>
              <span class="kpi-card-subtext">Total active quotations</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Customer Confirmed</span>
              <span class="kpi-card-value" style="color:var(--color-teal);">${formatCount(overviewData.confirmed_quote_count ?? overviewData.confirmed_quotes ?? overviewData.quotes_confirmed)}</span>
              <span class="kpi-card-subtext">Win count</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Confirmation Rate</span>
              <span class="kpi-card-value">${formatPercent(overviewData.confirmation_rate)}</span>
              <span class="kpi-card-subtext">Win conversion ratio</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Open Quotes</span>
              <span class="kpi-card-value">${formatCount(overviewData.open_quote_count ?? overviewData.open_quotes)}</span>
              <span class="kpi-card-subtext">In-flight deal flow</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">At-Risk Deals</span>
              <span class="kpi-card-value" style="color:var(--color-coral);">${formatCount(overviewData.at_risk_deal_count ?? overviewData.at_risk_deals ?? overviewData.at_risk_count)}</span>
              <span class="kpi-card-badge kpi-badge-coral">Action Needed</span>
              <span class="kpi-card-subtext">Health score &lt; 60</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Critical Deals</span>
              <span class="kpi-card-value" style="color:#b91c1c;">${formatCount(overviewData.critical_deal_count ?? overviewData.critical_deals ?? overviewData.critical_count)}</span>
              <span class="kpi-card-badge kpi-badge-coral">Urgent</span>
              <span class="kpi-card-subtext">Health score &lt; 40</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Orders in Fulfillment</span>
              <span class="kpi-card-value">${formatCount(overviewData.orders_in_fulfillment ?? overviewData.fulfillment_orders)}</span>
              <span class="kpi-card-subtext">Active warehouse queue</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Backordered Orders</span>
              <span class="kpi-card-value" style="color:${Number(overviewData.backordered_order_count ?? overviewData.backordered_orders ?? 0) > 0 ? 'var(--color-coral)' : 'var(--color-navy)'};">
                ${formatCount(overviewData.backordered_order_count ?? overviewData.backordered_orders)}
              </span>
              <span class="kpi-card-subtext">Stock deficit bottlenecks</span>
            </div>
          </div>
        </div>

        <!-- Trend Chart Section -->
        <div class="trend-chart-card">
          <div class="trend-chart-header">
            <div>
              <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin:0;">Overview Trend Timeline</h3>
              <p style="font-size:var(--font-size-xs);color:var(--color-text-secondary);margin:4px 0 0 0;">
                Activity volume across quotes, orders, invoices and payments.
              </p>
            </div>
            <span class="badge badge-navy">${activeFilters.granularity} Cadence</span>
          </div>

          <!-- Trend Chart Visualizer -->
          <div id="overview-trend-container" style="padding:10px 0;">
            ${renderSimpleTrendChart(trendData?.points || trendData || [])}
          </div>

          <div class="trend-legend-row">
            <div class="trend-legend-item"><span class="legend-dot" style="background:var(--color-navy);"></span> Quotes Created</div>
            <div class="trend-legend-item"><span class="legend-dot" style="background:var(--color-teal);"></span> Quotes Confirmed</div>
            <div class="trend-legend-item"><span class="legend-dot" style="background:#6366f1;"></span> Orders Created</div>
            <div class="trend-legend-item"><span class="legend-dot" style="background:#f59e0b;"></span> Invoices Issued</div>
            <div class="trend-legend-item"><span class="legend-dot" style="background:var(--color-coral);"></span> At-Risk Deals</div>
          </div>
        </div>

        <!-- Currency Group Breakdown -->
        ${currencyHtml}
      </div>
    `;
  }

  /**
   * Lightweight SVG Trend Chart Generator
   */
  function renderSimpleTrendChart(points) {
    if (!Array.isArray(points) || points.length === 0) {
      return `
        <div style="height:160px;display:flex;align-items:center;justify-content:center;background:var(--color-background);border-radius:var(--radius-sm);color:var(--color-text-muted);font-size:var(--font-size-sm);">
          No trend timeline points recorded for the selected date range.
        </div>
      `;
    }

    const width = 1000;
    const height = 200;
    const padding = 30;

    // Extract maximum value for scale
    const maxVal = Math.max(...points.map(p => Math.max(
      p.quotes_created || 0,
      p.quotes_confirmed || 0,
      p.orders_created || 0,
      p.invoices_issued || 0,
      p.at_risk_deals || 0,
      5
    )));

    const getX = (i) => padding + (i / Math.max(1, points.length - 1)) * (width - padding * 2);
    const getY = (val) => height - padding - (val / maxVal) * (height - padding * 2);

    const buildPath = (key) => {
      return points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(p[key] || 0)}`).join(' ');
    };

    return `
      <div class="trend-chart-svg-container">
        <svg class="trend-chart-svg" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
          <!-- Grid Lines -->
          <line x1="${padding}" y1="${getY(0)}" x2="${width - padding}" y2="${getY(0)}" stroke="#e2e8f0" stroke-width="1" />
          <line x1="${padding}" y1="${getY(maxVal / 2)}" x2="${width - padding}" y2="${getY(maxVal / 2)}" stroke="#e2e8f0" stroke-dasharray="4" stroke-width="1" />
          <line x1="${padding}" y1="${getY(maxVal)}" x2="${width - padding}" y2="${getY(maxVal)}" stroke="#e2e8f0" stroke-dasharray="4" stroke-width="1" />

          <!-- Value Axis Labels -->
          <text x="${padding - 5}" y="${getY(0)}" fill="#94a3b8" font-size="10" text-anchor="end">0</text>
          <text x="${padding - 5}" y="${getY(maxVal / 2)}" fill="#94a3b8" font-size="10" text-anchor="end">${Math.round(maxVal / 2)}</text>
          <text x="${padding - 5}" y="${getY(maxVal)}" fill="#94a3b8" font-size="10" text-anchor="end">${maxVal}</text>

          <!-- Series Paths -->
          <path d="${buildPath('quotes_created')}" fill="none" stroke="var(--color-navy)" stroke-width="2.5" />
          <path d="${buildPath('quotes_confirmed')}" fill="none" stroke="var(--color-teal)" stroke-width="2.5" />
          <path d="${buildPath('orders_created')}" fill="none" stroke="#6366f1" stroke-width="2" />
          <path d="${buildPath('invoices_issued')}" fill="none" stroke="#f59e0b" stroke-width="2" />
          <path d="${buildPath('at_risk_deals')}" fill="none" stroke="var(--color-coral)" stroke-width="2" stroke-dasharray="3 3" />

          <!-- Data Points & Period Labels -->
          ${points.map((p, i) => `
            <circle cx="${getX(i)}" cy="${getY(p.quotes_created || 0)}" r="3" fill="var(--color-navy)" />
            <circle cx="${getX(i)}" cy="${getY(p.quotes_confirmed || 0)}" r="3" fill="var(--color-teal)" />
            <text x="${getX(i)}" y="${height - 8}" fill="#64748b" font-size="9" text-anchor="middle">
              ${(p.period || p.date || '').substring(5, 10)}
            </text>
          `).join('')}
        </svg>
      </div>
    `;
  }

  /**
   * 2. COMMERCIAL & SALES TAB (Funnel, Rep Performance, Discounts, Margins)
   */
  async function renderCommercialTab(container, reqId) {
    const [funnelData, salesPerfData, discountsData, marginsData] = await Promise.all([
      global.AnalyticsAPI.getQuotationFunnel(activeFilters),
      global.AnalyticsAPI.getSalesPerformance(activeFilters),
      global.AnalyticsAPI.getDiscounts(activeFilters),
      global.AnalyticsAPI.getMargins(activeFilters)
    ]);

    if (reqId !== currentRequestId) return;

    // Build Funnel Stages
    const stages = funnelData?.stages || [
      { name: 'Created', count: funnelData?.created ?? 0 },
      { name: 'Submitted', count: funnelData?.submitted ?? 0 },
      { name: 'Approved', count: funnelData?.approved ?? 0 },
      { name: 'Sent to Customer', count: funnelData?.sent ?? 0 },
      { name: 'Under Negotiation', count: funnelData?.under_negotiation ?? 0 },
      { name: 'Customer Confirmed', count: funnelData?.confirmed ?? 0 }
    ];

    const maxStage = Math.max(...stages.map(s => s.count || 0), 1);

    container.innerHTML = `
      <div style="display:flex;flex-direction:column;gap:var(--space-xl);">
        <!-- Quotation Funnel -->
        <div class="funnel-container">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
              <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin:0;">Quotation Conversion Funnel</h3>
              <p style="font-size:var(--font-size-xs);color:var(--color-text-secondary);margin:4px 0 0 0;">
                Workflow lifecycle progression from creation to customer confirmation.
              </p>
            </div>
            <div style="text-align:right;">
              <span style="font-size:var(--font-size-xs);color:var(--color-text-secondary);">Confirmation Rate</span>
              <div style="font-size:var(--font-size-xl);font-weight:var(--font-weight-bold);color:var(--color-teal);">
                ${formatPercent(funnelData.confirmation_rate)}
              </div>
            </div>
          </div>

          <div style="display:flex;flex-direction:column;gap:10px;margin-top:var(--space-sm);">
            ${stages.map(stg => {
              const pct = ((stg.count || 0) / maxStage) * 100;
              return `
                <div class="funnel-stage-row">
                  <div class="funnel-stage-name">${stg.name}</div>
                  <div class="funnel-bar-track">
                    <div class="funnel-bar-fill" style="width: ${Math.max(6, pct)}%;">
                      ${stg.count > 0 ? stg.count : ''}
                    </div>
                  </div>
                  <div class="funnel-stage-count">${formatCount(stg.count)}</div>
                </div>
              `;
            }).join('')}
          </div>

          ${(funnelData.rejected !== undefined || funnelData.cancelled !== undefined) ? `
            <div style="display:flex;gap:var(--space-lg);padding-top:var(--space-sm);border-top:1px solid var(--color-border-light);font-size:var(--font-size-xs);color:var(--color-text-secondary);">
              <span>Terminated / Rejected: <strong style="color:var(--color-coral);">${formatCount(funnelData.rejected)}</strong></span>
              <span>Cancelled: <strong>${formatCount(funnelData.cancelled)}</strong></span>
            </div>
          ` : ''}
        </div>

        <!-- Sales Performance Table -->
        <div>
          <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin-bottom:var(--space-sm);">Sales Representative Performance</h3>
          <div class="analytics-table-wrapper">
            <table class="analytics-table">
              <thead>
                <tr>
                  <th>Sales Rep</th>
                  <th>Quotes</th>
                  <th>Sent</th>
                  <th>Confirmed</th>
                  <th>Win Rate</th>
                  <th>Avg Discount</th>
                  <th>Avg Margin</th>
                  <th>At-Risk</th>
                  <th>Critical</th>
                  <th>Avg Turnaround</th>
                  <th>Confirmed Value</th>
                </tr>
              </thead>
              <tbody>
                ${(salesPerfData?.reps || salesPerfData || []).map(r => `
                  <tr>
                    <td><strong>${r.sales_rep_name || r.name || `Rep #${r.sales_rep_id || r.id}`}</strong></td>
                    <td>${formatCount(r.quotes_created ?? r.quotes)}</td>
                    <td>${formatCount(r.quotes_sent ?? r.sent)}</td>
                    <td><strong style="color:var(--color-teal);">${formatCount(r.confirmed_quotes ?? r.confirmed)}</strong></td>
                    <td>${formatPercent(r.confirmation_rate)}</td>
                    <td>${formatPercent(r.avg_discount)}</td>
                    <td>${formatPercent(r.avg_margin)}</td>
                    <td><span class="badge badge-coral">${formatCount(r.at_risk_deals ?? r.at_risk)}</span></td>
                    <td><span class="badge badge-coral" style="background:#fee2e2;color:#991b1b;">${formatCount(r.critical_deals ?? r.critical)}</span></td>
                    <td>${formatDuration(r.avg_turnaround_hours ?? r.avg_approval_time)}</td>
                    <td>
                      ${r.confirmed_values ? Object.entries(r.confirmed_values).map(([c, val]) => `
                        <div><strong style="color:var(--color-navy);">${formatCurrency(val, c)}</strong></div>
                      `).join('') : formatCurrency(r.confirmed_value, r.currency || 'USD')}
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>

        <!-- Commercial Governance: Discounts & Margins Summary -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(320px, 1fr));gap:var(--space-lg);">
          <!-- Discount Governance -->
          <div style="background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-md);padding:var(--space-lg);box-shadow:var(--shadow-xs);">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:var(--space-md);">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--color-coral);"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="M9 9h.01"/><path d="M15 15h.01"/></svg>
              <h4 style="margin:0;color:var(--color-navy);font-size:var(--font-size-md);">Discount Analytics & Anomalies</h4>
            </div>
            <div class="kpi-metric-grid" style="grid-template-columns:repeat(2, 1fr);margin-bottom:var(--space-md);">
              <div class="kpi-card">
                <span class="kpi-card-label">Weighted Avg</span>
                <span class="kpi-card-value">${formatPercent(discountsData.weighted_avg_discount ?? discountsData.avg_discount)}</span>
              </div>
              <div class="kpi-card">
                <span class="kpi-card-label">Max Discount</span>
                <span class="kpi-card-value" style="color:var(--color-coral);">${formatPercent(discountsData.max_discount)}</span>
              </div>
            </div>
            <div style="display:flex;flex-direction:column;gap:8px;font-size:var(--font-size-sm);">
              <div style="display:flex;justify-content:space-between;border-bottom:1px solid var(--color-border-light);padding-bottom:4px;">
                <span>High-Discount Quotes (&gt;Policy Threshold):</span>
                <strong style="color:var(--color-coral);">${formatCount(discountsData.high_discount_count)}</strong>
              </div>
              <div style="display:flex;justify-content:space-between;">
                <span>Discount Anomalies (Statistical):</span>
                <strong>${formatCount(discountsData.anomaly_count)}</strong>
              </div>
            </div>
          </div>

          <!-- Margin Governance -->
          <div style="background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-md);padding:var(--space-lg);box-shadow:var(--shadow-xs);">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:var(--space-md);">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--color-teal);"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
              <h4 style="margin:0;color:var(--color-navy);font-size:var(--font-size-md);">Margin Analytics & Profitability</h4>
            </div>
            <div class="kpi-metric-grid" style="grid-template-columns:repeat(2, 1fr);margin-bottom:var(--space-md);">
              <div class="kpi-card">
                <span class="kpi-card-label">Weighted Margin</span>
                <span class="kpi-card-value" style="color:var(--color-teal);">${formatPercent(marginsData.weighted_margin ?? marginsData.avg_margin)}</span>
              </div>
              <div class="kpi-card">
                <span class="kpi-card-label">Negative Deals</span>
                <span class="kpi-card-value" style="color:${Number(marginsData.negative_margin_count || 0) > 0 ? '#b91c1c' : 'var(--color-navy)'};">
                  ${formatCount(marginsData.negative_margin_count)}
                </span>
              </div>
            </div>
            <div style="font-size:var(--font-size-xs);color:var(--color-text-secondary);line-height:1.4;">
              * Weighted margin reflects total gross profit relative to total net order value as computed authoritatively by the backend valuation engine.
            </div>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * 3. APPROVALS & NEGOTIATION TAB
   */
  async function renderApprovalsTab(container, reqId) {
    const [approvalsData, negotiationsData] = await Promise.all([
      global.AnalyticsAPI.getApprovals(activeFilters),
      global.AnalyticsAPI.getNegotiations(activeFilters)
    ]);

    if (reqId !== currentRequestId) return;

    container.innerHTML = `
      <div style="display:flex;flex-direction:column;gap:var(--space-xl);">
        <!-- Approval Turnaround & Velocity -->
        <div>
          <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin-bottom:var(--space-sm);">Approval Workflow & Velocity</h3>
          <div class="kpi-metric-grid">
            <div class="kpi-card">
              <span class="kpi-card-label">Approval Rounds</span>
              <span class="kpi-card-value">${formatCount(approvalsData.total_rounds ?? approvalsData.total_requests)}</span>
              <span class="kpi-card-subtext">Total governance requests</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Manager Avg Time</span>
              <span class="kpi-card-value">${formatDuration(approvalsData.avg_manager_turnaround_hours)}</span>
              <span class="kpi-card-subtext">Sales leadership SLA</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Finance Avg Time</span>
              <span class="kpi-card-value">${formatDuration(approvalsData.avg_finance_turnaround_hours)}</span>
              <span class="kpi-card-subtext">Commercial finance review</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Total Cycle Time</span>
              <span class="kpi-card-value" style="color:var(--color-navy);">${formatDuration(approvalsData.avg_total_cycle_hours)}</span>
              <span class="kpi-card-subtext">End-to-end turnaround</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Approved</span>
              <span class="kpi-card-value" style="color:var(--color-teal);">${formatCount(approvalsData.approved_count)}</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Rejected / Returned</span>
              <span class="kpi-card-value" style="color:var(--color-coral);">${formatCount(approvalsData.rejected_count ?? approvalsData.returned_count)}</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Reapproval Count</span>
              <span class="kpi-card-value">${formatCount(approvalsData.reapproval_count)}</span>
              <span class="kpi-card-subtext">Triggered by counteroffers</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Delay Alerts</span>
              <span class="kpi-card-value" style="color:var(--color-coral);">${formatCount(approvalsData.delay_alerts_count)}</span>
              <span class="kpi-card-subtext">SLA breaches</span>
            </div>
          </div>
        </div>

        <!-- Negotiation Dynamics -->
        <div>
          <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin-bottom:var(--space-sm);">Customer Negotiation Dynamics</h3>
          <div class="kpi-metric-grid">
            <div class="kpi-card">
              <span class="kpi-card-label">Entered Negotiation</span>
              <span class="kpi-card-value">${formatCount(negotiationsData.quotes_in_negotiation ?? negotiationsData.negotiation_count)}</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Counteroffers Received</span>
              <span class="kpi-card-value">${formatCount(negotiationsData.counteroffers_received)}</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Acceptance Rate</span>
              <span class="kpi-card-value" style="color:var(--color-teal);">${formatPercent(negotiationsData.acceptance_rate)}</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Avg Duration</span>
              <span class="kpi-card-value">${formatDuration(negotiationsData.avg_negotiation_hours)}</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Avg Discount Shift</span>
              <span class="kpi-card-value">${formatPercent(negotiationsData.avg_discount_change)}</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Reapproval Trigger %</span>
              <span class="kpi-card-value">${formatPercent(negotiationsData.reapproval_trigger_rate)}</span>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * 4. DEAL HEALTH ANALYTICS TAB (Part 1 Visual integration + Click-throughs)
   */
  async function renderDealHealthTab(container, reqId) {
    const [healthData, healthTrendData] = await Promise.all([
      global.AnalyticsAPI.getDealHealth(activeFilters),
      global.AnalyticsAPI.getDealHealthTrend(activeFilters)
    ]);

    if (reqId !== currentRequestId) return;

    container.innerHTML = `
      <div style="display:flex;flex-direction:column;gap:var(--space-xl);">
        <!-- Health Distribution Cards with Click-through to Part 1 -->
        <div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-sm);">
            <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin:0;">Portfolio Deal Health Breakdown</h3>
            <span style="font-size:var(--font-size-xs);color:var(--color-text-secondary);">Click any metric card to inspect in Deal Health Workspace</span>
          </div>
          <div class="kpi-metric-grid">
            <div class="kpi-card" style="cursor:pointer;" onclick="window.location.hash='#/deal-health?health_level=HEALTHY'">
              <span class="kpi-card-label">Healthy Deals</span>
              <span class="kpi-card-value" style="color:var(--color-teal);">${formatCount(healthData.healthy_count ?? healthData.HEALTHY)}</span>
              <span class="kpi-card-badge kpi-badge-teal">Score 80–100</span>
              <span class="kpi-card-subtext">Click to filter list &rarr;</span>
            </div>
            <div class="kpi-card" style="cursor:pointer;" onclick="window.location.hash='#/deal-health?health_level=WATCH'">
              <span class="kpi-card-label">Watch Deals</span>
              <span class="kpi-card-value" style="color:#f59e0b;">${formatCount(healthData.watch_count ?? healthData.WATCH)}</span>
              <span class="kpi-card-badge kpi-badge-amber">Score 60–79</span>
              <span class="kpi-card-subtext">Click to filter list &rarr;</span>
            </div>
            <div class="kpi-card" style="cursor:pointer;" onclick="window.location.hash='#/deal-health?health_level=AT_RISK'">
              <span class="kpi-card-label">At-Risk Deals</span>
              <span class="kpi-card-value" style="color:var(--color-coral);">${formatCount(healthData.at_risk_count ?? healthData.AT_RISK)}</span>
              <span class="kpi-card-badge kpi-badge-coral">Score 40–59</span>
              <span class="kpi-card-subtext">Click to filter list &rarr;</span>
            </div>
            <div class="kpi-card" style="cursor:pointer;" onclick="window.location.hash='#/deal-health?health_level=CRITICAL'">
              <span class="kpi-card-label">Critical Deals</span>
              <span class="kpi-card-value" style="color:#b91c1c;">${formatCount(healthData.critical_count ?? healthData.CRITICAL)}</span>
              <span class="kpi-card-badge kpi-badge-coral" style="background:#fee2e2;color:#991b1b;">Score &lt; 40</span>
              <span class="kpi-card-subtext">Click to filter list &rarr;</span>
            </div>
          </div>
        </div>

        <!-- Average Score & Alert Breakdown -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(300px, 1fr));gap:var(--space-lg);">
          <div style="background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-md);padding:var(--space-lg);box-shadow:var(--shadow-xs);">
            <h4 style="margin:0 0 var(--space-md) 0;color:var(--color-navy);font-size:var(--font-size-md);">Average Portfolio Health Score</h4>
            <div style="display:flex;align-items:center;gap:var(--space-lg);">
              <div style="width:72px;height:72px;border-radius:50%;background:var(--color-navy);color:#ffffff;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:bold;">
                ${healthData.avg_health_score ? Number(healthData.avg_health_score).toFixed(0) : '—'}
              </div>
              <div style="font-size:var(--font-size-sm);color:var(--color-text-secondary);">
                Blended health score across all open pipeline deals evaluated by telemetry engine.
              </div>
            </div>
          </div>

          <div style="background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-md);padding:var(--space-lg);box-shadow:var(--shadow-xs);">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-sm);">
              <h4 style="margin:0;color:var(--color-navy);font-size:var(--font-size-md);">Active Alerts by Severity</h4>
              <button class="btn btn-ghost btn-xs" onclick="window.location.hash='#/deal-alerts'">View Inbox &rarr;</button>
            </div>
            <div style="display:flex;gap:var(--space-sm);flex-wrap:wrap;">
              <span class="badge badge-coral" style="padding:6px 12px;font-size:12px;">CRITICAL: ${formatCount(healthData.critical_alerts_count ?? healthData.alerts_by_severity?.CRITICAL)}</span>
              <span class="badge badge-coral" style="padding:6px 12px;font-size:12px;">HIGH: ${formatCount(healthData.high_alerts_count ?? healthData.alerts_by_severity?.HIGH)}</span>
              <span class="badge badge-navy" style="padding:6px 12px;font-size:12px;">WARNING: ${formatCount(healthData.warning_alerts_count ?? healthData.alerts_by_severity?.WARNING)}</span>
            </div>
          </div>
        </div>

        <!-- Top Signals Triggered -->
        ${healthData.top_signals && healthData.top_signals.length > 0 ? `
          <div style="background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-md);padding:var(--space-lg);box-shadow:var(--shadow-xs);">
            <h4 style="margin:0 0 var(--space-md) 0;color:var(--color-navy);font-size:var(--font-size-md);">Most Frequent Risk Signals</h4>
            <div style="display:flex;flex-direction:column;gap:8px;">
              ${healthData.top_signals.map(s => `
                <div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid var(--color-border-light);font-size:var(--font-size-sm);">
                  <span><strong>${s.signal_type || s.name}</strong></span>
                  <span class="badge badge-navy">${formatCount(s.count)} occurrences</span>
                </div>
              `).join('')}
            </div>
          </div>
        ` : ''}
      </div>
    `;
  }

  /**
   * 5. OPERATIONS & FULFILLMENT TAB
   */
  async function renderOperationsTab(container, reqId) {
    const [fulfillmentData, warehousesData, backordersData, shipmentsData] = await Promise.all([
      global.AnalyticsAPI.getFulfillment(activeFilters),
      global.AnalyticsAPI.getWarehouses(activeFilters),
      global.AnalyticsAPI.getBackorders(activeFilters),
      global.AnalyticsAPI.getShipments(activeFilters)
    ]);

    if (reqId !== currentRequestId) return;

    container.innerHTML = `
      <div style="display:flex;flex-direction:column;gap:var(--space-xl);">
        <!-- Fulfillment Engine Adoption & KPIs -->
        <div>
          <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin-bottom:var(--space-sm);">Operations & Multi-Warehouse Fulfillment</h3>
          <div class="kpi-metric-grid">
            <div class="kpi-card">
              <span class="kpi-card-label">Total Orders</span>
              <span class="kpi-card-value">${formatCount(fulfillmentData.total_orders)}</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Single Warehouse</span>
              <span class="kpi-card-value" style="color:var(--color-teal);">${formatPercent(fulfillmentData.single_warehouse_rate)}</span>
              <span class="kpi-card-subtext">Direct single-node ship</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Multi-Warehouse Split</span>
              <span class="kpi-card-value" style="color:var(--color-navy);">${formatPercent(fulfillmentData.multi_warehouse_split_rate)}</span>
              <span class="kpi-card-subtext">Smart line splitting</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Backorder Rate</span>
              <span class="kpi-card-value" style="color:${Number(fulfillmentData.backorder_rate || 0) > 0 ? 'var(--color-coral)' : 'var(--color-navy)'};">
                ${formatPercent(fulfillmentData.backorder_rate)}
              </span>
              <span class="kpi-card-subtext">Stockout deficit</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Manual Overrides</span>
              <span class="kpi-card-value">${formatCount(fulfillmentData.manual_override_count)}</span>
              <span class="kpi-card-subtext">Dispatcher adjustments</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Avg Warehouses / Order</span>
              <span class="kpi-card-value">${Number(fulfillmentData.avg_warehouses_per_order || 1).toFixed(1)}</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Avg Shipments / Order</span>
              <span class="kpi-card-value">${Number(fulfillmentData.avg_shipments_per_order || 1).toFixed(1)}</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Open Backorder Qty</span>
              <span class="kpi-card-value" style="color:var(--color-coral);">${formatCount(fulfillmentData.open_backorder_qty)}</span>
            </div>
          </div>
        </div>

        <!-- Warehouse Breakdown Table -->
        <div>
          <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin-bottom:var(--space-sm);">Warehouse Node Performance</h3>
          <div class="analytics-table-wrapper">
            <table class="analytics-table">
              <thead>
                <tr>
                  <th>Warehouse</th>
                  <th>Code</th>
                  <th>Orders Allocated</th>
                  <th>Lines Allocated</th>
                  <th>Reserved Qty</th>
                  <th>Fulfilled Qty</th>
                  <th>Shipment Count</th>
                  <th>Estimated Shipping Cost</th>
                </tr>
              </thead>
              <tbody>
                ${(warehousesData?.warehouses || warehousesData || []).map(w => `
                  <tr>
                    <td><strong>${w.name || `Warehouse #${w.warehouse_id || w.id}`}</strong></td>
                    <td><span class="badge badge-navy">${w.code || '—'}</span></td>
                    <td>${formatCount(w.orders_allocated)}</td>
                    <td>${formatCount(w.lines_allocated)}</td>
                    <td>${formatCount(w.reserved_qty)}</td>
                    <td><strong style="color:var(--color-teal);">${formatCount(w.fulfilled_qty)}</strong></td>
                    <td>${formatCount(w.shipment_count)}</td>
                    <td>${w.estimated_shipping_cost !== undefined ? formatCurrency(w.estimated_shipping_cost, w.currency || 'USD') : '—'}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>

        <!-- Oldest Open Backorders Table -->
        <div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-sm);">
            <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin:0;">Oldest Open Backorders</h3>
            <button class="btn btn-ghost btn-xs" onclick="window.location.hash='#/backorders'">View All Backorders &rarr;</button>
          </div>
          <div class="analytics-table-wrapper">
            <table class="analytics-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Customer</th>
                  <th>Backorder Qty</th>
                  <th>Created</th>
                  <th>Age</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                ${(backordersData?.oldest_backorders || backordersData?.items || []).map(b => `
                  <tr>
                    <td><strong>${b.product_name || `Product #${b.product_id}`}</strong></td>
                    <td>${b.customer_name || `Customer #${b.customer_id}`}</td>
                    <td><strong style="color:var(--color-coral);">${formatCount(b.backorder_qty ?? b.quantity)}</strong></td>
                    <td>${b.created_at ? new Date(b.created_at).toLocaleDateString() : '—'}</td>
                    <td><span class="badge badge-coral">${b.age_days ? `${b.age_days} days` : 'Open'}</span></td>
                    <td><span class="badge badge-navy">${b.status || 'OPEN'}</span></td>
                    <td>
                      ${b.order_id ? `
                        <button class="btn btn-ghost btn-xs" onclick="window.location.hash='#/orders?orderId=${b.order_id}'">Open Order</button>
                      ` : '—'}
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * 6. BILLING, RECEIVABLES & MRR TAB (Multi-Currency Safe)
   */
  async function renderBillingTab(container, reqId) {
    const [billingData, receivablesData, paymentsData, subscriptionsData] = await Promise.all([
      global.AnalyticsAPI.getBilling(activeFilters),
      global.AnalyticsAPI.getReceivables(activeFilters),
      global.AnalyticsAPI.getPayments(activeFilters),
      global.AnalyticsAPI.getSubscriptions(activeFilters)
    ]);

    if (reqId !== currentRequestId) return;

    // Currency safe receivables aging render
    const agingByCurrency = receivablesData.aging_by_currency || receivablesData.currencies || {};

    container.innerHTML = `
      <div style="display:flex;flex-direction:column;gap:var(--space-xl);">
        <!-- Billing KPIs -->
        <div>
          <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin-bottom:var(--space-sm);">Invoicing & Billing Execution</h3>
          <div class="kpi-metric-grid">
            <div class="kpi-card">
              <span class="kpi-card-label">Invoice Count</span>
              <span class="kpi-card-value">${formatCount(billingData.total_invoices ?? billingData.invoice_count)}</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Paid Invoices</span>
              <span class="kpi-card-value" style="color:var(--color-teal);">${formatCount(billingData.paid_invoices_count)}</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Overdue Invoices</span>
              <span class="kpi-card-value" style="color:${Number(billingData.overdue_invoices_count || 0) > 0 ? 'var(--color-coral)' : 'var(--color-navy)'};">
                ${formatCount(billingData.overdue_invoices_count)}
              </span>
            </div>
            <div class="kpi-card">
              <span class="kpi-card-label">Active Subscriptions</span>
              <span class="kpi-card-value" style="color:var(--color-navy);">${formatCount(subscriptionsData.active_subscriptions ?? subscriptionsData.active_count)}</span>
            </div>
          </div>
        </div>

        <!-- Receivables Aging by Currency -->
        <div>
          <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin-bottom:4px;">Receivables Aging Breakdown</h3>
          <p style="font-size:var(--font-size-xs);color:var(--color-text-secondary);margin-bottom:var(--space-sm);">
            Multi-currency aged accounts receivable categorized into standard 30-day buckets.
          </p>
          <div style="display:flex;flex-direction:column;gap:var(--space-md);">
            ${Object.entries(agingByCurrency).map(([curr, buckets]) => `
              <div class="currency-section-card">
                <div class="currency-section-header">
                  <span class="currency-badge-tag">${curr} Receivables</span>
                  <span style="font-size:var(--font-size-xs);color:var(--color-text-secondary);">
                    Total Outstanding: <strong>${formatCurrency(buckets.total_outstanding ?? buckets.total, curr)}</strong>
                  </span>
                </div>
                <div class="aging-bucket-grid">
                  <div class="aging-bucket-card current">
                    <span class="aging-bucket-title">Current (Not Due)</span>
                    <span class="aging-bucket-val">${formatCurrency(buckets.current, curr)}</span>
                  </div>
                  <div class="aging-bucket-card">
                    <span class="aging-bucket-title">1–30 Days</span>
                    <span class="aging-bucket-val">${formatCurrency(buckets.days_1_30 ?? buckets['1-30'], curr)}</span>
                  </div>
                  <div class="aging-bucket-card">
                    <span class="aging-bucket-title">31–60 Days</span>
                    <span class="aging-bucket-val">${formatCurrency(buckets.days_31_60 ?? buckets['31-60'], curr)}</span>
                  </div>
                  <div class="aging-bucket-card overdue">
                    <span class="aging-bucket-title">61–90 Days</span>
                    <span class="aging-bucket-val">${formatCurrency(buckets.days_61_90 ?? buckets['61-90'], curr)}</span>
                  </div>
                  <div class="aging-bucket-card overdue">
                    <span class="aging-bucket-title">90+ Days</span>
                    <span class="aging-bucket-val" style="color:#b91c1c;">${formatCurrency(buckets.days_90_plus ?? buckets['90+'], curr)}</span>
                  </div>
                </div>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Subscription MRR / ARR Telemetry -->
        <div>
          <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin-bottom:var(--space-sm);">Recurring Revenue (MRR / ARR)</h3>
          <div class="kpi-metric-grid">
            ${subscriptionsData.mrr_by_currency ? Object.entries(subscriptionsData.mrr_by_currency).map(([c, mrrVal]) => `
              <div class="kpi-card">
                <span class="kpi-card-label">${c} MRR</span>
                <span class="kpi-card-value" style="color:var(--color-teal);">${formatCurrency(mrrVal, c)}</span>
                <span class="kpi-card-subtext">Normalized Monthly Recurring</span>
              </div>
            `).join('') : `
              <div class="kpi-card">
                <span class="kpi-card-label">Normalized MRR</span>
                <span class="kpi-card-value" style="color:var(--color-teal);">${formatCurrency(subscriptionsData.mrr, subscriptionsData.currency || 'USD')}</span>
              </div>
            `}
          </div>
        </div>
      </div>
    `;
  }

  /**
   * 7. PRODUCTS & CATEGORIES TAB
   */
  async function renderProductsTab(container, reqId) {
    const [productsData, categoriesData] = await Promise.all([
      global.AnalyticsAPI.getProducts(activeFilters),
      global.AnalyticsAPI.getProductCategories(activeFilters)
    ]);

    if (reqId !== currentRequestId) return;

    container.innerHTML = `
      <div style="display:flex;flex-direction:column;gap:var(--space-xl);">
        <!-- Products Table -->
        <div>
          <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin-bottom:var(--space-sm);">Product Performance & Velocity</h3>
          <div class="analytics-table-wrapper">
            <table class="analytics-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>SKU</th>
                  <th>Category</th>
                  <th>Quoted Qty</th>
                  <th>Confirmed Qty</th>
                  <th>Order Qty</th>
                  <th>Avg Discount</th>
                  <th>Avg Margin</th>
                  <th>Confirmed Value</th>
                </tr>
              </thead>
              <tbody>
                ${(productsData?.products || productsData || []).map(p => `
                  <tr>
                    <td><strong>${p.name || `Product #${p.product_id || p.id}`}</strong></td>
                    <td><span class="badge badge-navy">${p.sku || '—'}</span></td>
                    <td>${p.category_name || p.category || '—'}</td>
                    <td>${formatCount(p.quoted_qty)}</td>
                    <td><strong style="color:var(--color-teal);">${formatCount(p.confirmed_qty)}</strong></td>
                    <td>${formatCount(p.order_qty)}</td>
                    <td>${formatPercent(p.avg_discount)}</td>
                    <td>${formatPercent(p.avg_margin)}</td>
                    <td>
                      ${p.confirmed_values ? Object.entries(p.confirmed_values).map(([c, val]) => `
                        <div>${formatCurrency(val, c)}</div>
                      `).join('') : formatCurrency(p.confirmed_value, p.currency || 'USD')}
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>

        <!-- Product Categories Table -->
        <div>
          <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin-bottom:var(--space-sm);">Product Category Aggregates</h3>
          <div class="analytics-table-wrapper">
            <table class="analytics-table">
              <thead>
                <tr>
                  <th>Category</th>
                  <th>Quotes</th>
                  <th>Confirmed Quotes</th>
                  <th>Confirmed Qty</th>
                  <th>Avg Discount</th>
                  <th>Avg Margin</th>
                </tr>
              </thead>
              <tbody>
                ${(categoriesData?.categories || categoriesData || []).map(c => `
                  <tr>
                    <td><strong>${c.name || `Category #${c.category_id || c.id}`}</strong></td>
                    <td>${formatCount(c.quote_count ?? c.quotes)}</td>
                    <td><strong style="color:var(--color-teal);">${formatCount(c.confirmed_count ?? c.confirmed)}</strong></td>
                    <td>${formatCount(c.confirmed_qty)}</td>
                    <td>${formatPercent(c.avg_discount)}</td>
                    <td>${formatPercent(c.avg_margin)}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `;
  }

  global.DealFlowAnalyticsView = {
    render
  };
})(typeof window !== 'undefined' ? window : this);
