/**
 * DealFlow360 — Reports Center View Controller
 * Implements professional report generation, PDF & XLSX binary downloads,
 * contextual report filters, and recent export audit logging.
 */
(function (global) {
  'use strict';

  let selectedReportType = 'EXECUTIVE_SUMMARY';
  let selectedFormat = 'PDF';
  let customerList = [];
  let isGenerating = false;

  async function render(container, params = {}) {
    const user = global.DealFlowAuth?.getCurrentUser();
    const roleName = user?.role?.name || 'ADMIN';

    // Route guard for customer role
    if (roleName === 'CUSTOMER') {
      window.location.hash = '#/portal';
      return;
    }

    if (params.type && global.ReportsAPI.REPORT_TYPES[params.type]) {
      selectedReportType = params.type;
    }

    container.innerHTML = `
      <div class="reports-page-container animate-fade-in">
        <!-- Header -->
        <div class="analytics-header-bar">
          <div class="analytics-title-group">
            <h1>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--color-teal);"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
              Report Generation & Export Center
            </h1>
            <div class="analytics-metadata-row">
              <span>Authoritative server-side ReportLab (PDF) and openpyxl (XLSX) document compiler</span>
            </div>
          </div>
          <div class="analytics-header-actions">
            <button id="btn-refresh-history" class="btn btn-secondary btn-sm">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
              Refresh History
            </button>
          </div>
        </div>

        <!-- Report Generation Builder Card -->
        <div class="report-export-builder-card">
          <div>
            <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin:0 0 4px 0;">1. Select Report Type</h3>
            <p style="font-size:var(--font-size-xs);color:var(--color-text-secondary);margin:0 0 var(--space-md) 0;">
              Choose the enterprise intelligence report to compile.
            </p>
            <div class="report-type-selector-grid">
              ${Object.entries(global.ReportsAPI.REPORT_LABELS).map(([key, label]) => `
                <div class="report-type-card-option ${selectedReportType === key ? 'selected' : ''}" data-type="${key}">
                  <div style="width:16px;height:16px;border-radius:50%;border:2px solid ${selectedReportType === key ? 'var(--color-teal)' : 'var(--color-border)'};display:flex;align-items:center;justify-content:center;margin-top:2px;flex-shrink:0;">
                    ${selectedReportType === key ? '<div style="width:8px;height:8px;border-radius:50%;background:var(--color-teal);"></div>' : ''}
                  </div>
                  <div>
                    <strong style="font-size:var(--font-size-sm);color:var(--color-navy);display:block;">${label}</strong>
                    <span style="font-size:11px;color:var(--color-text-secondary);">${key}</span>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>

          <!-- Format Selection -->
          <div>
            <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin:0 0 4px 0;">2. Output Document Format</h3>
            <div class="format-toggle-group" style="margin-top:var(--space-xs);">
              <div class="format-toggle-option ${selectedFormat === 'PDF' ? 'active' : ''}" data-format="PDF">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                PDF Document (.pdf)
              </div>
              <div class="format-toggle-option ${selectedFormat === 'XLSX' ? 'active' : ''}" data-format="XLSX">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/></svg>
                Excel Spreadsheet (.xlsx)
              </div>
            </div>
          </div>

          <!-- Dynamic Filters -->
          <div id="dynamic-report-filters-section">
            <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin:0 0 4px 0;">3. Report Scope & Parameters</h3>
            <div class="analytics-filter-card" style="margin-top:var(--space-xs);">
              <div class="filter-control-group" id="group-filter-customer" style="display:${selectedReportType === 'CUSTOMER_360' ? 'flex' : 'none'};">
                <label>Customer Account *</label>
                <select id="report-param-customer">
                  <option value="">Select account...</option>
                </select>
              </div>
              <div class="filter-control-group" id="group-filter-start">
                <label>Start Date</label>
                <input type="date" id="report-param-start">
              </div>
              <div class="filter-control-group" id="group-filter-end">
                <label>End Date</label>
                <input type="date" id="report-param-end">
              </div>
              <div class="filter-control-group" id="group-filter-currency" style="flex:0 0 130px;">
                <label>Currency Scope</label>
                <select id="report-param-currency">
                  <option value="">All Currencies</option>
                  <option value="USD">USD ($)</option>
                  <option value="EUR">EUR (€)</option>
                  <option value="GBP">GBP (£)</option>
                  <option value="INR">INR (₹)</option>
                </select>
              </div>
            </div>
          </div>

          <!-- Generate Action -->
          <div style="display:flex;justify-content:flex-end;gap:var(--space-md);align-items:center;padding-top:var(--space-md);border-top:1px solid var(--color-border-light);">
            <span id="report-generation-status" style="font-size:var(--font-size-sm);color:var(--color-text-secondary);"></span>
            <button id="btn-generate-report" class="btn btn-primary" style="padding:10px 24px;">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              Generate & Download Report
            </button>
          </div>
        </div>

        <!-- Recent Exports Audit History -->
        <div>
          <h3 style="font-size:var(--font-size-md);color:var(--color-navy);margin-bottom:var(--space-sm);">Recent Export Audit Log</h3>
          <div id="export-history-table-container">
            <div style="display:flex;justify-content:center;padding:40px;"><div class="spinner"></div></div>
          </div>
        </div>
      </div>
    `;

    bindEvents(container);
    await loadCustomerOptions(container);
    await loadExportHistory(container);
  }

  function bindEvents(container) {
    // Report type card selection
    container.querySelectorAll('.report-type-card-option').forEach(card => {
      card.addEventListener('click', () => {
        container.querySelectorAll('.report-type-card-option').forEach(c => {
          c.classList.remove('selected');
          const indicator = c.querySelector('div');
          if (indicator) indicator.style.borderColor = 'var(--color-border)';
          const dot = indicator?.querySelector('div');
          if (dot) dot.remove();
        });

        card.classList.add('selected');
        const ind = card.querySelector('div');
        if (ind) {
          ind.style.borderColor = 'var(--color-teal)';
          ind.innerHTML = '<div style="width:8px;height:8px;border-radius:50%;background:var(--color-teal);"></div>';
        }

        selectedReportType = card.dataset.type;
        updateDynamicFilterVisibility(container);
      });
    });

    // Format toggle
    container.querySelectorAll('.format-toggle-option').forEach(btn => {
      btn.addEventListener('click', () => {
        container.querySelectorAll('.format-toggle-option').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        selectedFormat = btn.dataset.format;
      });
    });

    // Refresh History
    container.querySelector('#btn-refresh-history')?.addEventListener('click', () => {
      loadExportHistory(container);
    });

    // Generate Button
    container.querySelector('#btn-generate-report')?.addEventListener('click', async () => {
      if (isGenerating) return;

      const customerSelect = container.querySelector('#report-param-customer');
      const startDateInput = container.querySelector('#report-param-start');
      const endDateInput = container.querySelector('#report-param-end');
      const currencySelect = container.querySelector('#report-param-currency');
      const genBtn = container.querySelector('#btn-generate-report');
      const statusEl = container.querySelector('#report-generation-status');

      if (selectedReportType === 'CUSTOMER_360' && !customerSelect.value) {
        global.UI?.showToast('Please select a customer for Customer 360 report.', 'coral');
        customerSelect.focus();
        return;
      }

      isGenerating = true;
      genBtn.disabled = true;
      genBtn.innerHTML = `<span class="spinner" style="width:14px;height:14px;border-width:2px;"></span> Compiling ${selectedFormat}...`;
      if (statusEl) statusEl.textContent = `Compiling ${global.ReportsAPI.REPORT_LABELS[selectedReportType]} (${selectedFormat})...`;

      const payload = {
        report_type: selectedReportType,
        format: selectedFormat
      };

      if (startDateInput.value) payload.start_date = new Date(startDateInput.value).toISOString();
      if (endDateInput.value) payload.end_date = new Date(endDateInput.value + 'T23:59:59').toISOString();
      if (customerSelect.value) payload.customer_id = parseInt(customerSelect.value, 10);
      if (currencySelect.value) payload.currency = currencySelect.value;

      try {
        const res = await global.ReportsAPI.exportReport(payload);
        global.UI?.showToast(`Report downloaded: ${res.filename}`, 'teal');
        if (statusEl) statusEl.textContent = `Downloaded: ${res.filename}`;
        await loadExportHistory(container);
      } catch (err) {
        global.UI?.showToast(`Export failed: ${err.message}`, 'coral');
        if (statusEl) statusEl.textContent = `Error: ${err.message}`;
      } finally {
        isGenerating = false;
        genBtn.disabled = false;
        genBtn.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Generate & Download Report
        `;
      }
    });
  }

  function updateDynamicFilterVisibility(container) {
    const custGroup = container.querySelector('#group-filter-customer');
    if (custGroup) {
      custGroup.style.display = selectedReportType === 'CUSTOMER_360' ? 'flex' : 'none';
    }
  }

  async function loadCustomerOptions(container) {
    const select = container.querySelector('#report-param-customer');
    if (!select) return;
    try {
      const res = await global.DealFlowAPI.get('/api/v1/customers');
      customerList = Array.isArray(res) ? res : (res.items || res.customers || []);
      select.innerHTML = `
        <option value="">Select customer account...</option>
        ${customerList.map(c => `<option value="${c.id}">${c.name} (${c.customer_code || `CUST-${c.id}`})</option>`).join('')}
      `;
    } catch (_) {
      select.innerHTML = `<option value="">Failed to load customer list</option>`;
    }
  }

  async function loadExportHistory(container) {
    const historyContainer = container.querySelector('#export-history-table-container');
    if (!historyContainer) return;

    try {
      const items = await global.ReportsAPI.getExportHistory({ limit: 50 });
      if (!Array.isArray(items) || items.length === 0) {
        historyContainer.innerHTML = `
          <div style="padding:40px;text-align:center;background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-md);color:var(--color-text-muted);font-size:var(--font-size-sm);">
            No report exports have been generated in this session yet.
          </div>
        `;
        return;
      }

      historyContainer.innerHTML = `
        <div class="analytics-table-wrapper">
          <table class="analytics-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Report Type</th>
                <th>Format</th>
                <th>Filename</th>
                <th>Generated At</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${items.map(item => `
                <tr>
                  <td>#${item.id}</td>
                  <td><strong>${global.ReportsAPI.REPORT_LABELS[item.report_type] || item.report_type}</strong></td>
                  <td><span class="badge ${item.format === 'PDF' ? 'badge-coral' : 'badge-teal'}">${item.format}</span></td>
                  <td><code style="font-size:12px;color:var(--color-navy);">${item.filename}</code></td>
                  <td>${item.generated_at ? new Date(item.generated_at).toLocaleString() : '—'}</td>
                  <td>
                    <span class="badge ${item.status === 'SUCCESS' ? 'badge-teal' : 'badge-coral'}">
                      ${item.status}
                    </span>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    } catch (err) {
      historyContainer.innerHTML = `
        <div class="alert alert-coral">Failed to load export history: ${err.message}</div>
      `;
    }
  }

  global.DealFlowReportsView = {
    render
  };
})(typeof window !== 'undefined' ? window : this);
