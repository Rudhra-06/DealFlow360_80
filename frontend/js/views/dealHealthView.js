/**
 * DealFlow360 — Deal Health Workspace View Controller
 * Implements Deal Health intelligence board, health score badges,
 * explainable risk signals, health history, recalculate, and bulk scan.
 */
(function (global) {
  'use strict';

  let currentDeals = [];
  let currentFilters = {
    health_level: '',
    search: '',
    quotation_status: '',
    limit: 100,
    offset: 0
  };

  function formatHealthLevelBadge(level, score) {
    const map = {
      'HEALTHY': { label: 'Healthy', cls: 'badge-health-healthy' },
      'WATCH': { label: 'Watch', cls: 'badge-health-watch' },
      'AT_RISK': { label: 'At Risk', cls: 'badge-health-at-risk' },
      'CRITICAL': { label: 'Critical', cls: 'badge-health-critical' }
    };
    const item = map[level] || { label: level || 'Unknown', cls: 'badge-navy' };
    const scoreText = (score !== undefined && score !== null) ? ` (${Number(score).toFixed(0)})` : '';
    return `<span class="badge ${item.cls}">${item.label}${scoreText}</span>`;
  }

  function formatSeverityBadge(sev) {
    const map = {
      'INFO': { label: 'Info', cls: 'badge-severity-info' },
      'WARNING': { label: 'Warning', cls: 'badge-severity-warning' },
      'HIGH': { label: 'High', cls: 'badge-severity-high' },
      'CRITICAL': { label: 'Critical', cls: 'badge-severity-critical' }
    };
    const item = map[sev] || { label: sev || 'Info', cls: 'badge-navy' };
    return `<span class="badge ${item.cls}">${item.label}</span>`;
  }

  function humanizeSignalType(sigType) {
    if (!sigType) return 'Risk Signal';
    return sigType
      .replace(/_/g, ' ')
      .toLowerCase()
      .replace(/\b\w/g, l => l.toUpperCase());
  }

  async function render(container, params = {}) {
    if (params.quoteId || params.quotation_id) {
      await renderDetailView(container, params.quoteId || params.quotation_id);
      return;
    }

    const user = global.DealFlowAuth?.getCurrentUser();
    const canScan = user && (user.role?.name === 'ADMIN' || user.role?.name === 'SALES_MANAGER');

    container.innerHTML = `
      <div class="animate-fade-in">
        <!-- Header -->
        <div class="view-header" style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--space-lg);">
          <div>
            <h1 style="font-size: var(--font-size-2xl); color: var(--color-navy); margin-bottom: 4px;">Deal Health Intelligence</h1>
            <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary);">
              AI & rule-based commercial risk scoring, anomaly detection, velocity tracking, and proactive deal intervention.
            </p>
          </div>
          <div style="display: flex; gap: var(--space-sm);">
            ${canScan ? `
              <button id="btn-run-health-scan" class="btn btn-secondary">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                <span>Run Health Scan</span>
              </button>
            ` : ''}
            <button id="btn-refresh-health" class="btn btn-secondary" title="Refresh list">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
              <span>Refresh</span>
            </button>
          </div>
        </div>

        <!-- Filter Bar -->
        <div class="card" style="padding: var(--space-md); margin-bottom: var(--space-lg);">
          <div style="display: grid; grid-template-columns: 2fr 1.5fr 1.5fr auto; gap: var(--space-md); align-items: center;">
            <div class="input-wrapper">
              <input type="text" id="health-search-input" class="form-input" placeholder="Search quote # or customer name..." value="${currentFilters.search}" />
            </div>
            <div>
              <select id="health-level-filter" class="form-input">
                <option value="">All Health Levels</option>
                <option value="CRITICAL" ${currentFilters.health_level === 'CRITICAL' ? 'selected' : ''}>Critical</option>
                <option value="AT_RISK" ${currentFilters.health_level === 'AT_RISK' ? 'selected' : ''}>At Risk</option>
                <option value="WATCH" ${currentFilters.health_level === 'WATCH' ? 'selected' : ''}>Watch</option>
                <option value="HEALTHY" ${currentFilters.health_level === 'HEALTHY' ? 'selected' : ''}>Healthy</option>
              </select>
            </div>
            <div>
              <select id="health-status-filter" class="form-input">
                <option value="">All Quotation Statuses</option>
                <option value="DRAFT">Draft</option>
                <option value="PENDING_MANAGER_APPROVAL">Pending Manager Approval</option>
                <option value="PENDING_FINANCE_APPROVAL">Pending Finance Approval</option>
                <option value="APPROVED">Approved</option>
                <option value="SENT_TO_CUSTOMER">Sent to Customer</option>
                <option value="CUSTOMER_CONFIRMED">Customer Confirmed</option>
              </select>
            </div>
            <div>
              <button id="btn-reset-filters" class="btn btn-secondary">Reset</button>
            </div>
          </div>
        </div>

        <!-- Deal Health Summaries List -->
        <div id="health-list-container">
          <div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Loading deal health intelligence...</div>
        </div>
      </div>
    `;

    setupListEvents(container);
    await loadDealHealthList();
  }

  function setupListEvents(container) {
    const searchInput = container.querySelector('#health-search-input');
    const levelFilter = container.querySelector('#health-level-filter');
    const statusFilter = container.querySelector('#health-status-filter');
    const resetBtn = container.querySelector('#btn-reset-filters');
    const refreshBtn = container.querySelector('#btn-refresh-health');
    const scanBtn = container.querySelector('#btn-run-health-scan');

    let searchTimer = null;
    searchInput?.addEventListener('input', () => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => {
        currentFilters.search = searchInput.value.trim();
        loadDealHealthList();
      }, 300);
    });

    levelFilter?.addEventListener('change', () => {
      currentFilters.health_level = levelFilter.value;
      loadDealHealthList();
    });

    statusFilter?.addEventListener('change', () => {
      currentFilters.quotation_status = statusFilter.value;
      loadDealHealthList();
    });

    resetBtn?.addEventListener('click', () => {
      currentFilters = { health_level: '', search: '', quotation_status: '', limit: 100, offset: 0 };
      if (searchInput) searchInput.value = '';
      if (levelFilter) levelFilter.value = '';
      if (statusFilter) statusFilter.value = '';
      loadDealHealthList();
    });

    refreshBtn?.addEventListener('click', loadDealHealthList);

    scanBtn?.addEventListener('click', openBulkScanModal);
  }

  async function loadDealHealthList() {
    const container = document.getElementById('health-list-container');
    if (!container) return;

    container.innerHTML = `<div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Loading health records...</div>`;

    try {
      const res = await global.DealHealthAPI.list(currentFilters);
      if (!res.ok) {
        container.innerHTML = `
          <div class="alert alert-coral" style="margin: 20px 0;">
            <span>Failed to load deal health: ${res.data?.detail || res.error || 'Server error'}</span>
          </div>
        `;
        return;
      }

      currentDeals = res.data || [];
      renderDealsTable(container);
    } catch (err) {
      container.innerHTML = `
        <div class="alert alert-coral" style="margin: 20px 0;">
          <span>Error connecting to Deal Health API.</span>
        </div>
      `;
    }
  }

  function renderDealsTable(container) {
    if (currentDeals.length === 0) {
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 60px 20px;">
          <div style="width: 48px; height: 48px; border-radius: var(--radius-full); background: rgba(25, 181, 165, 0.1); color: var(--color-teal); display: flex; align-items: center; justify-content: center; margin: 0 auto var(--space-md);">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
          </div>
          <h3 style="font-size: var(--font-size-md); color: var(--color-navy); margin-bottom: 4px;">No deals match the selected filters</h3>
          <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary);">All evaluated deals are currently healthy or no records match your filter criteria.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="table-card">
        <table class="data-table">
          <thead>
            <tr>
              <th style="width: 140px;">Health</th>
              <th>Quotation #</th>
              <th>Customer</th>
              <th>Sales Rep</th>
              <th>Workflow Status</th>
              <th>Top Risk Signal</th>
              <th>Alerts</th>
              <th>Calculated</th>
              <th style="text-align: right;">Action</th>
            </tr>
          </thead>
          <tbody>
            ${currentDeals.map(d => {
              const lastCalc = d.calculated_at ? new Date(d.calculated_at).toLocaleDateString() : '—';
              const openAlerts = d.open_alert_count || 0;
              const topSig = d.top_signal_title || 'None';

              return `
                <tr style="cursor: pointer;" onclick="window.DealFlowApp.switchView('deal-health', { quoteId: ${d.quotation_id} });">
                  <td>${formatHealthLevelBadge(d.health_level, d.health_score)}</td>
                  <td>
                    <span style="font-family: monospace; font-weight: 700; color: var(--color-navy);">${d.quote_number}</span>
                  </td>
                  <td><div style="font-weight: 600; color: var(--color-text);">${d.customer_name || 'Customer #' + d.customer_id}</div></td>
                  <td style="font-size: var(--font-size-xs); color: var(--color-text-secondary);">${d.sales_rep_name || 'Rep #' + d.sales_rep_id}</td>
                  <td><span class="badge badge-navy" style="font-size: 0.7rem;">${d.quotation_status}</span></td>
                  <td>
                    <span style="font-size: var(--font-size-xs); font-weight: 600; color: ${topSig !== 'None' ? 'var(--color-coral)' : 'var(--color-teal)'};">
                      ${topSig}
                    </span>
                  </td>
                  <td>
                    ${openAlerts > 0 ? `
                      <span class="badge badge-coral" style="font-weight: 700;">${openAlerts} Open</span>
                    ` : `<span style="font-size: var(--font-size-xs); color: var(--color-text-muted);">0</span>`}
                  </td>
                  <td style="font-size: var(--font-size-xs); color: var(--color-text-muted);">${lastCalc}</td>
                  <td style="text-align: right;">
                    <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); window.DealFlowApp.switchView('deal-health', { quoteId: ${d.quotation_id} });">
                      <span>View Health</span>
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"></polyline></svg>
                    </button>
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  // --- DETAIL VIEW ---
  async function renderDetailView(container, quotationId) {
    container.innerHTML = `
      <div id="health-detail-container" class="animate-fade-in">
        <div style="text-align: center; padding: 60px;"><span class="spinner spinner-teal"></span> Loading deal health details...</div>
      </div>
    `;

    try {
      const [healthRes, historyRes, alertsRes] = await Promise.all([
        global.DealHealthAPI.getQuotationHealth(quotationId),
        global.DealHealthAPI.getHistory(quotationId, 10),
        global.DealAlertsAPI.list({ quotation_id: quotationId, limit: 10 })
      ]);

      if (!healthRes.ok) {
        container.innerHTML = `
          <div class="alert alert-coral" style="margin: 20px;">
            <span>Failed to load health snapshot: ${healthRes.data?.detail || healthRes.error || 'Record not found'}</span>
          </div>
          <button class="btn btn-secondary" onclick="window.DealFlowApp.switchView('deal-health');">Back to Deal Health</button>
        `;
        return;
      }

      const h = healthRes.data;
      const history = historyRes.ok ? historyRes.data : [];
      const alerts = alertsRes.ok ? alertsRes.data : [];

      const calcDate = h.calculated_at ? new Date(h.calculated_at).toLocaleString() : '—';
      const signals = h.signals || [];

      container.innerHTML = `
        <div class="animate-fade-in">
          <!-- Topbar -->
          <div class="view-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-lg);">
            <div style="display: flex; align-items: center; gap: var(--space-md);">
              <button class="btn btn-secondary btn-sm" onclick="window.DealFlowApp.switchView('deal-health');">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
                <span>Back to Health List</span>
              </button>
              <div>
                <h1 style="font-size: var(--font-size-xl); color: var(--color-navy); margin: 0;">Deal Health Intelligence</h1>
                <span style="font-size: var(--font-size-xs); color: var(--color-text-secondary);">Quotation #${quotationId} · Calculated ${calcDate}</span>
              </div>
            </div>

            <div style="display: flex; gap: var(--space-sm);">
              <button id="btn-open-quote" class="btn btn-secondary btn-sm">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                <span>Open Quotation</span>
              </button>
              <button id="btn-recalculate-health" class="btn btn-primary btn-sm">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                <span>Recalculate Health</span>
              </button>
            </div>
          </div>

          <!-- Main 2-Column Grid -->
          <div class="deal-health-grid">
            <!-- Left Column: Health Score & Explainable Signals -->
            <div>
              <!-- Health Score Overview Card -->
              <div class="card" style="padding: var(--space-lg); margin-bottom: var(--space-lg); display: flex; align-items: center; gap: var(--space-lg);">
                <div class="health-score-card">
                  <div class="health-score-value health-level-${(h.health_level || '').toLowerCase().replace('_', '-')}">${Number(h.health_score).toFixed(0)}</div>
                  <div class="health-score-label health-level-${(h.health_level || '').toLowerCase().replace('_', '-')}">${h.health_level}</div>
                </div>
                <div style="flex: 1;">
                  <h3 style="font-size: var(--font-size-md); color: var(--color-navy); margin-bottom: 6px;">Commercial Health Summary</h3>
                  <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary); line-height: 1.45; margin-bottom: var(--space-xs);">
                    ${h.summary || 'No detailed evaluation narrative available.'}
                  </p>
                  <div style="font-size: var(--font-size-xs); color: var(--color-text-muted);">
                    Active Risk Signals: <strong>${h.signal_count || signals.length}</strong>
                  </div>
                </div>
              </div>

              <!-- Explainable Signals Section -->
              <div class="card" style="padding: var(--space-lg); margin-bottom: var(--space-lg);">
                <h3 style="font-size: var(--font-size-md); color: var(--color-navy); margin-bottom: var(--space-md); display: flex; justify-content: space-between; align-items: center;">
                  <span>Why This Deal Is At Risk</span>
                  <span class="badge badge-navy" style="font-size: 0.7rem;">${signals.length} Signals</span>
                </h3>

                ${signals.length === 0 ? `
                  <div style="text-align: center; padding: 30px; color: var(--color-teal); font-size: var(--font-size-sm); background: rgba(25,181,165,0.05); border-radius: var(--radius-sm); border: 1px dashed rgba(25,181,165,0.3);">
                    No risk signals detected. Deal commercial velocity and pricing are healthy.
                  </div>
                ` : signals.map(sig => `
                  <div class="signal-card severity-${sig.severity}">
                    <div class="signal-header">
                      <div class="signal-title">${humanizeSignalType(sig.signal_type)}: ${sig.title}</div>
                      <div style="display: flex; gap: var(--space-xs); align-items: center;">
                        ${formatSeverityBadge(sig.severity)}
                        <span class="badge badge-coral" style="font-weight: 800;">-${Number(sig.score_penalty).toFixed(0)} pts</span>
                      </div>
                    </div>

                    <p class="signal-explanation">${sig.explanation}</p>

                    ${(sig.metric_value !== null || sig.threshold_value !== null) ? `
                      <table class="signal-metrics-table">
                        <tbody>
                          ${sig.metric_value !== null ? `
                            <tr>
                              <td class="metric-label">Current Metric Value:</td>
                              <td class="metric-value">${Number(sig.metric_value).toFixed(1)}</td>
                            </tr>
                          ` : ''}
                          ${sig.threshold_value !== null ? `
                            <tr>
                              <td class="metric-label">Configured Policy Threshold:</td>
                              <td class="metric-value">${Number(sig.threshold_value).toFixed(1)}</td>
                            </tr>
                          ` : ''}
                        </tbody>
                      </table>
                    ` : ''}
                  </div>
                `).join('')}
              </div>
            </div>

            <!-- Right Column: Active Alerts & Health Snapshot History -->
            <div>
              <!-- Active Alerts Box -->
              <div class="card" style="padding: var(--space-lg); margin-bottom: var(--space-lg);">
                <h3 style="font-size: var(--font-size-md); color: var(--color-navy); margin-bottom: var(--space-md); display: flex; justify-content: space-between; align-items: center;">
                  <span>Deal Alerts</span>
                  <button class="btn btn-secondary btn-sm" onclick="window.DealFlowApp.switchView('deal-alerts', { quotation_id: ${quotationId} });">View In Alerts Inbox</button>
                </h3>

                ${alerts.length === 0 ? `
                  <div style="text-align: center; padding: 24px; color: var(--color-text-muted); font-size: var(--font-size-xs); border: 1px dashed var(--color-border); border-radius: var(--radius-sm);">
                    No open alerts for this quotation.
                  </div>
                ` : alerts.map(a => `
                  <div class="alert-item-card status-${a.status}">
                    <div class="alert-item-header">
                      <div class="alert-item-title">${a.title}</div>
                      ${formatSeverityBadge(a.severity)}
                    </div>
                    <div class="alert-item-message">${a.message}</div>
                    <div class="alert-item-meta">
                      <span>Status: <strong>${a.status}</strong></span>
                      <span>Triggered: <strong>${a.occurrence_count || 1}x</strong></span>
                    </div>
                    <div class="alert-actions-bar">
                      ${a.status === 'OPEN' ? `
                        <button class="btn btn-secondary btn-sm btn-ack-alert" data-alert-id="${a.id}">Acknowledge</button>
                      ` : `<span style="font-size: 0.75rem; color: var(--color-teal); font-weight: 700;">✓ Acknowledged</span>`}
                      <button class="btn btn-secondary btn-sm btn-nudge-alert" data-alert-id="${a.id}">Nudge Rep</button>
                    </div>
                  </div>
                `).join('')}
              </div>

              <!-- Snapshot History Timeline -->
              <div class="card" style="padding: var(--space-lg);">
                <h3 style="font-size: var(--font-size-md); color: var(--color-navy); margin-bottom: var(--space-md);">
                  Health Evaluation History
                </h3>

                ${history.length === 0 ? `
                  <div style="text-align: center; padding: 20px; color: var(--color-text-muted); font-size: var(--font-size-xs);">
                    No previous evaluations recorded.
                  </div>
                ` : `
                  <div class="health-history-timeline">
                    ${history.map(item => `
                      <div class="history-timeline-item">
                        <div>
                          <div style="font-weight: 700; color: var(--color-navy);">${new Date(item.calculated_at).toLocaleDateString()} ${new Date(item.calculated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                          <div style="color: var(--color-text-secondary); font-size: 0.7rem;">${item.summary || 'Periodic evaluation'}</div>
                        </div>
                        <div style="text-align: right;">
                          ${formatHealthLevelBadge(item.health_level, item.health_score)}
                          <div style="font-size: 0.65rem; color: var(--color-text-muted); margin-top: 2px;">${item.signal_count || 0} signals</div>
                        </div>
                      </div>
                    `).join('')}
                  </div>
                `}
              </div>
            </div>
          </div>
        </div>
      `;

      // Setup Detail Events
      document.getElementById('btn-open-quote')?.addEventListener('click', () => {
        global.DealFlowApp.switchView('quotation-builder', { quoteId: quotationId });
      });

      document.getElementById('btn-recalculate-health')?.addEventListener('click', async () => {
        const btn = document.getElementById('btn-recalculate-health');
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner spinner-white"></span> Recalculating...`;

        try {
          const evalRes = await global.DealHealthAPI.evaluateQuotationHealth(quotationId);
          if (evalRes.ok) {
            global.DealFlowUI.toast('Deal Health recalculated successfully.', 'teal');
            renderDetailView(container, quotationId);
          } else {
            global.DealFlowUI.toast(evalRes.data?.detail || 'Failed to recalculate health.', 'coral');
            btn.disabled = false;
            btn.innerHTML = `<span>Recalculate Health</span>`;
          }
        } catch (e) {
          global.DealFlowUI.toast('Error communicating with Deal Health engine.', 'coral');
          btn.disabled = false;
          btn.innerHTML = `<span>Recalculate Health</span>`;
        }
      });

      // Wire alert buttons inside detail
      container.querySelectorAll('.btn-ack-alert').forEach(btn => {
        btn.addEventListener('click', async () => {
          const aid = btn.dataset.alertId;
          btn.disabled = true;
          try {
            const ares = await global.DealAlertsAPI.acknowledge(aid);
            if (ares.ok) {
              global.DealFlowUI.toast('Alert acknowledged.', 'teal');
              renderDetailView(container, quotationId);
            }
          } catch (e) {
            btn.disabled = false;
          }
        });
      });

      container.querySelectorAll('.btn-nudge-alert').forEach(btn => {
        btn.addEventListener('click', () => {
          openNudgeModal(btn.dataset.alertId, () => renderDetailView(container, quotationId));
        });
      });

    } catch (err) {
      console.error('Error rendering deal health detail:', err);
    }
  }

  // --- BULK SCAN MODAL ---
  function openBulkScanModal() {
    const modal = document.getElementById('dealflow-modal-overlay');
    if (!modal) return;

    modal.innerHTML = `
      <div class="modal-dialog animate-fade-in" style="max-width: 520px;">
        <div class="modal-header">
          <h3 class="modal-title">Run Bulk Deal Health Scan</h3>
          <button class="modal-close" onclick="window.DealFlowUI.closeModal();">&times;</button>
        </div>
        <div class="modal-body">
          <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: var(--space-md); line-height: 1.5;">
            Evaluate all open and eligible quotations against the active Deal Health policy thresholds. This will refresh health scores, identify risk anomalies, and trigger operational alerts.
          </p>

          <div id="scan-results-box" style="display: none; background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: var(--space-md); margin-bottom: var(--space-md);">
            <!-- Populated after scan -->
          </div>

          <div style="display: flex; justify-content: flex-end; gap: var(--space-sm);">
            <button type="button" class="btn btn-secondary" onclick="window.DealFlowUI.closeModal();">Cancel</button>
            <button type="button" id="btn-confirm-scan" class="btn btn-primary">
              <span>Execute Bulk Scan</span>
            </button>
          </div>
        </div>
      </div>
    `;

    global.DealFlowUI.openModal();

    document.getElementById('btn-confirm-scan').addEventListener('click', async () => {
      const btn = document.getElementById('btn-confirm-scan');
      const box = document.getElementById('scan-results-box');
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner spinner-white"></span> Evaluating Deals...`;

      try {
        const res = await global.DealHealthAPI.runScan();
        if (res.ok && res.data) {
          const d = res.data;
          box.style.display = 'block';
          box.innerHTML = `
            <div style="font-weight: 700; color: var(--color-navy); margin-bottom: 8px;">Scan Completed Successfully</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: var(--font-size-xs);">
              <div>Evaluated Deals: <strong>${d.evaluated_count}</strong></div>
              <div>Alerts Created: <strong style="color: var(--color-coral);">${d.alerts_created}</strong></div>
              <div>Healthy Deals: <strong style="color: var(--color-teal);">${d.healthy_count}</strong></div>
              <div>Watch Deals: <strong style="color: #D97706;">${d.watch_count}</strong></div>
              <div>At-Risk Deals: <strong style="color: var(--color-coral);">${d.at_risk_count}</strong></div>
              <div>Critical Deals: <strong style="color: #DC2626;">${d.critical_count}</strong></div>
            </div>
          `;

          btn.innerHTML = `<span>Done</span>`;
          btn.disabled = false;
          btn.onclick = () => {
            global.DealFlowUI.closeModal();
            loadDealHealthList();
          };
          global.DealFlowUI.toast(`Scan complete: ${d.evaluated_count} deals evaluated.`, 'teal');
        } else {
          global.DealFlowUI.toast(res.data?.detail || 'Scan failed.', 'coral');
          btn.disabled = false;
          btn.innerHTML = `<span>Execute Bulk Scan</span>`;
        }
      } catch (e) {
        global.DealFlowUI.toast('Network error during scan.', 'coral');
        btn.disabled = false;
        btn.innerHTML = `<span>Execute Bulk Scan</span>`;
      }
    });
  }

  // --- NUDGE MODAL HELPER ---
  function openNudgeModal(alertId, onComplete) {
    const modal = document.getElementById('dealflow-modal-overlay');
    if (!modal) return;

    modal.innerHTML = `
      <div class="modal-dialog animate-fade-in" style="max-width: 480px;">
        <div class="modal-header">
          <h3 class="modal-title">Nudge Sales Rep</h3>
          <button class="modal-close" onclick="window.DealFlowUI.closeModal();">&times;</button>
        </div>
        <div class="modal-body">
          <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: var(--space-md);">
            Dispatch an actionable nudge notification regarding this deal alert to the assigned deal owner.
          </p>
          <div class="form-group">
            <label class="form-label" for="nudge-msg-input">Nudge Message (Optional)</label>
            <textarea id="nudge-msg-input" class="form-input" rows="3" placeholder="e.g. Please follow up on this commercial discount anomaly with the customer today."></textarea>
          </div>
          <div style="display: flex; justify-content: flex-end; gap: var(--space-sm); margin-top: var(--space-lg);">
            <button type="button" class="btn btn-secondary" onclick="window.DealFlowUI.closeModal();">Cancel</button>
            <button type="button" id="btn-submit-nudge" class="btn btn-teal">
              <span>Send Nudge</span>
            </button>
          </div>
        </div>
      </div>
    `;

    global.DealFlowUI.openModal();

    document.getElementById('btn-submit-nudge').addEventListener('click', async () => {
      const msg = document.getElementById('nudge-msg-input').value.trim();
      const btn = document.getElementById('btn-submit-nudge');
      btn.disabled = true;

      try {
        const res = await global.DealAlertsAPI.nudge(alertId, {
          action_type: 'NUDGE_SALES_REP',
          message: msg || undefined
        });

        if (res.ok) {
          global.DealFlowUI.closeModal();
          global.DealFlowUI.toast('Nudge sent to Sales Rep.', 'teal');
          if (onComplete) onComplete();
        } else {
          global.DealFlowUI.toast(res.data?.detail || 'Failed to send nudge.', 'coral');
          btn.disabled = false;
        }
      } catch (e) {
        global.DealFlowUI.toast('Error sending nudge.', 'coral');
        btn.disabled = false;
      }
    });
  }

  global.DealHealthView = {
    render: render
  };
})(typeof window !== 'undefined' ? window : this);
