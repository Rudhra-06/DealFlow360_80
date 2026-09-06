/**
 * DealFlow360 — Quotations List & Pipeline Kanban View
 * Handles Quotation browsing, status filters, search, pipeline grouping, and + New Quotation creation.
 */
(function (global) {
  'use strict';

  let currentQuotations = [];
  let currentViewMode = 'list'; // 'list' or 'pipeline'
  let cachedCustomers = [];

  function formatStatusBadge(status) {
    const map = {
      'DRAFT': { label: 'Draft', cls: 'badge-navy' },
      'PENDING_MANAGER_APPROVAL': { label: 'Pending Manager Approval', cls: 'badge-coral' },
      'PENDING_FINANCE_APPROVAL': { label: 'Pending Finance Approval', cls: 'badge-coral' },
      'APPROVED': { label: 'Approved', cls: 'badge-teal' },
      'SENT_TO_CUSTOMER': { label: 'Sent to Customer', cls: 'badge-teal' },
      'CUSTOMER_CONFIRMED': { label: 'Customer Confirmed', cls: 'badge-teal' },
      'RETURNED_FOR_REVISION': { label: 'Returned for Revision', cls: 'badge-coral' },
      'REJECTED': { label: 'Rejected', cls: 'badge-coral' },
      'CANCELLED': { label: 'Cancelled', cls: 'badge-navy' }
    };
    const s = map[status] || { label: status, cls: 'badge-navy' };
    return `<span class="badge ${s.cls}">${s.label}</span>`;
  }

  function formatRiskBadge(level, score) {
    let cls = 'badge-navy';
    if (level === 'GREEN') cls = 'badge-teal';
    else if (level === 'YELLOW') cls = 'badge-coral';
    else if (level === 'CORAL_RED') cls = 'badge-coral';
    return `<span class="badge ${cls}" style="font-weight: 600;">${level} (${Number(score).toFixed(1)})</span>`;
  }

  async function render(container, initialMode = 'list') {
    currentViewMode = initialMode;
    container.innerHTML = `
      <div class="animate-fade-in">
        <div class="quote-view-header">
          <div>
            <h1 style="font-size: var(--font-size-2xl); color: var(--color-navy); margin-bottom: 4px;">Sales Quotations</h1>
            <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary);">Manage B2B deals, commercial pricing, approval status, and deal velocity.</p>
          </div>

          <div style="display: flex; align-items: center; gap: var(--space-md);">
            <!-- View Mode Switcher -->
            <div class="view-toggle-group">
              <button id="view-mode-list-btn" class="view-toggle-btn ${currentViewMode === 'list' ? 'active' : ''}">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
                <span>List View</span>
              </button>
              <button id="view-mode-pipeline-btn" class="view-toggle-btn ${currentViewMode === 'pipeline' ? 'active' : ''}">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
                <span>Pipeline Board</span>
              </button>
            </div>

            <!-- New Quotation Action -->
            <button id="btn-new-quotation" class="btn btn-primary">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
              <span>+ New Quotation</span>
            </button>
          </div>
        </div>

        <!-- Filter Bar -->
        <div class="card" style="padding: var(--space-md); margin-bottom: var(--space-lg);">
          <div style="display: grid; grid-template-columns: 2fr 1.5fr 1.5fr auto; gap: var(--space-md); align-items: center;">
            <div class="input-wrapper">
              <input type="text" id="quote-search-input" class="form-input" placeholder="Search quote # or customer name..." />
            </div>

            <div>
              <select id="quote-status-filter" class="form-input">
                <option value="">All Statuses</option>
                <option value="DRAFT">Draft</option>
                <option value="PENDING_MANAGER_APPROVAL">Pending Manager Approval</option>
                <option value="PENDING_FINANCE_APPROVAL">Pending Finance Approval</option>
                <option value="APPROVED">Approved</option>
                <option value="SENT_TO_CUSTOMER">Sent to Customer</option>
                <option value="CUSTOMER_CONFIRMED">Customer Confirmed (Order Active)</option>
                <option value="RETURNED_FOR_REVISION">Returned for Revision</option>
                <option value="REJECTED">Rejected</option>
                <option value="CANCELLED">Cancelled</option>
              </select>
            </div>

            <div>
              <select id="quote-customer-filter" class="form-input">
                <option value="">All Customers</option>
              </select>
            </div>

            <div>
              <button id="btn-refresh-quotes" class="btn btn-secondary">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
                <span>Refresh</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Main Display Container -->
        <div id="quotes-display-container">
          <div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Loading quotations...</div>
        </div>
      </div>
    `;

    setupEvents(container);
    await loadFilterOptions();
    await loadQuotations();
  }

  function setupEvents(container) {
    container.querySelector('#view-mode-list-btn').addEventListener('click', () => {
      currentViewMode = 'list';
      container.querySelector('#view-mode-list-btn').classList.add('active');
      container.querySelector('#view-mode-pipeline-btn').classList.remove('active');
      renderQuotesDisplay();
    });

    container.querySelector('#view-mode-pipeline-btn').addEventListener('click', () => {
      currentViewMode = 'pipeline';
      container.querySelector('#view-mode-pipeline-btn').classList.add('active');
      container.querySelector('#view-mode-list-btn').classList.remove('active');
      renderQuotesDisplay();
    });

    container.querySelector('#btn-new-quotation').addEventListener('click', () => {
      openNewQuotationModal();
    });

    container.querySelector('#btn-refresh-quotes').addEventListener('click', () => {
      loadQuotations();
    });

    let searchTimeout = null;
    container.querySelector('#quote-search-input').addEventListener('input', () => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(loadQuotations, 300);
    });

    container.querySelector('#quote-status-filter').addEventListener('change', loadQuotations);
    container.querySelector('#quote-customer-filter').addEventListener('change', loadQuotations);
  }

  async function loadFilterOptions() {
    try {
      const custRes = await global.CustomersAPI.list({ limit: 100 });
      if (custRes.ok && custRes.data) {
        cachedCustomers = custRes.data;
        const custSelect = document.getElementById('quote-customer-filter');
        if (custSelect) {
          custSelect.innerHTML = '<option value="">All Customers</option>' +
            cachedCustomers.map(c => `<option value="${c.id}">${c.name} (${c.customer_code})</option>`).join('');
        }
      }
    } catch (e) {
      console.warn('Failed to populate customer filter options:', e);
    }
  }

  async function loadQuotations() {
    const display = document.getElementById('quotes-display-container');
    if (!display) return;

    display.innerHTML = `<div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Loading quotations from backend...</div>`;

    const statusVal = document.getElementById('quote-status-filter')?.value || '';
    const custVal = document.getElementById('quote-customer-filter')?.value || '';
    const searchVal = document.getElementById('quote-search-input')?.value.trim() || '';

    try {
      const res = await global.QuotationsAPI.list({
        status: statusVal || undefined,
        customer_id: custVal || undefined,
        search: searchVal || undefined,
        limit: 100
      });

      if (!res.ok) {
        display.innerHTML = `
          <div class="alert alert-coral" style="margin: 20px 0;">
            <span>Failed to load quotations: ${res.data?.detail || res.error || 'Server error'}</span>
          </div>
        `;
        return;
      }

      currentQuotations = res.data || [];
      renderQuotesDisplay();
    } catch (err) {
      display.innerHTML = `
        <div class="alert alert-coral" style="margin: 20px 0;">
          <span>Error connecting to Quotations API.</span>
        </div>
      `;
    }
  }

  function renderQuotesDisplay() {
    const display = document.getElementById('quotes-display-container');
    if (!display) return;

    if (currentQuotations.length === 0) {
      display.innerHTML = `
        <div class="card" style="text-align: center; padding: 60px 20px;">
          <div style="width: 48px; height: 48px; border-radius: var(--radius-full); background: var(--color-navy-muted); color: var(--color-navy); display: flex; align-items: center; justify-content: center; margin: 0 auto var(--space-md);">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          </div>
          <h3 style="font-size: var(--font-size-md); color: var(--color-navy); margin-bottom: 4px;">No quotations found</h3>
          <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: var(--space-lg);">No quotation records match the current filters or no quotes have been created yet.</p>
          <button class="btn btn-primary" onclick="document.getElementById('btn-new-quotation')?.click();">
            <span>+ Create First Quotation</span>
          </button>
        </div>
      `;
      return;
    }

    if (currentViewMode === 'list') {
      renderTableView(display);
    } else {
      renderPipelineView(display);
    }
  }

  function renderTableView(container) {
    container.innerHTML = `
      <div class="table-card">
        <table class="data-table">
          <thead>
            <tr>
              <th>Quote #</th>
              <th>Customer</th>
              <th>Sales Rep</th>
              <th>Status</th>
              <th>Net Total</th>
              <th>Margin %</th>
              <th>Risk</th>
              <th>Updated</th>
              <th style="text-align: right;">Action</th>
            </tr>
          </thead>
          <tbody>
            ${currentQuotations.map(q => {
              const custName = q.customer ? `${q.customer.name}` : `Cust #${q.customer_id}`;
              const repName = q.sales_rep ? `${q.sales_rep.full_name}` : `Rep #${q.sales_rep_id}`;
              const marginVal = Number(q.margin_pct || 0);
              const marginColor = marginVal >= 15 ? 'var(--color-teal)' : (marginVal >= 0 ? '#B45309' : 'var(--color-coral)');
              const updatedAt = q.updated_at ? new Date(q.updated_at).toLocaleDateString() : '—';

              return `
                <tr style="cursor: pointer;" onclick="window.DealFlowApp.switchView('quotation-builder', { quoteId: ${q.id} });">
                  <td>
                    <span style="font-family: monospace; font-weight: 700; color: var(--color-navy);">${q.quote_number}</span>
                  </td>
                  <td>
                    <div style="font-weight: 600; color: var(--color-text);">${custName}</div>
                    ${q.customer?.tier ? `<span style="font-size: 0.7rem; color: var(--color-text-secondary);">${q.customer.tier.name}</span>` : ''}
                  </td>
                  <td style="font-size: var(--font-size-xs); color: var(--color-text-secondary);">${repName}</td>
                  <td>${formatStatusBadge(q.status)}</td>
                  <td style="font-weight: 700; color: var(--color-navy);">${q.currency} ${Number(q.net_total).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                  <td style="font-weight: 600; color: ${marginColor};">${marginVal.toFixed(1)}%</td>
                  <td>${formatRiskBadge(q.risk_level, q.blended_risk_score)}</td>
                  <td style="font-size: var(--font-size-xs); color: var(--color-text-muted);">${updatedAt}</td>
                  <td style="text-align: right;">
                    <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); window.QuotationsView.exportQuotePdf(${q.id}, '${q.quote_number}');" title="Export Quotation PDF" style="margin-right: 4px; padding: 2px 8px; font-size: 0.75rem;">
                      <span>PDF</span>
                    </button>
                    <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); window.DealFlowApp.switchView('quotation-builder', { quoteId: ${q.id} });">
                      <span>Open</span>
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

  function renderPipelineView(container) {
    const columns = [
      { key: 'DRAFT', title: 'Draft' },
      { key: 'PENDING_MANAGER_APPROVAL', title: 'Pending Manager' },
      { key: 'PENDING_FINANCE_APPROVAL', title: 'Pending Finance' },
      { key: 'APPROVED', title: 'Approved' },
      { key: 'SENT_TO_CUSTOMER', title: 'Sent to Customer' },
      { key: 'CUSTOMER_CONFIRMED', title: 'Confirmed (Order Active)' },
      { key: 'RETURNED_FOR_REVISION', title: 'Returned for Revision' },
      { key: 'REJECTED_CANCELLED', title: 'Rejected / Cancelled', statuses: ['REJECTED', 'CANCELLED'] }
    ];

    container.innerHTML = `
      <div class="kanban-board">
        ${columns.map(col => {
          const quotes = currentQuotations.filter(q => {
            if (col.statuses) return col.statuses.includes(q.status);
            return q.status === col.key;
          });
          const totalVal = quotes.reduce((acc, q) => acc + Number(q.net_total || 0), 0);

          return `
            <div class="kanban-column">
              <div class="kanban-col-header">
                <span class="kanban-col-title">${col.title}</span>
                <span class="kanban-col-count">${quotes.length}</span>
              </div>
              <div style="font-size: 0.75rem; font-weight: 700; color: var(--color-text-secondary); margin-bottom: var(--space-sm);">
                Total: $${totalVal.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </div>

              <div class="kanban-cards-container">
                ${quotes.length === 0 ? `
                  <div style="text-align: center; padding: 24px 8px; color: var(--color-text-muted); font-size: var(--font-size-xs); border: 1px dashed var(--color-border); border-radius: var(--radius-sm);">
                    No quotes
                  </div>
                ` : quotes.map(q => {
                  const custName = q.customer ? q.customer.name : `Cust #${q.customer_id}`;
                  const marginVal = Number(q.margin_pct || 0);
                  const marginColor = marginVal >= 15 ? 'var(--color-teal)' : (marginVal >= 0 ? '#B45309' : 'var(--color-coral)');

                  return `
                    <div class="kanban-card" onclick="window.DealFlowApp.switchView('quotation-builder', { quoteId: ${q.id} });">
                      <div class="kanban-card-top">
                        <span class="kanban-card-num">${q.quote_number}</span>
                        ${formatRiskBadge(q.risk_level, q.blended_risk_score)}
                      </div>
                      <div class="kanban-card-customer" title="${custName}">${custName}</div>
                      <div class="kanban-card-metrics">
                        <div>
                          <div style="font-size: 0.6875rem; color: var(--color-text-muted);">Net Total</div>
                          <div class="kanban-metric-total">${q.currency} ${Number(q.net_total).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                        </div>
                        <div style="text-align: right;">
                          <div style="font-size: 0.6875rem; color: var(--color-text-muted);">Margin</div>
                          <div class="kanban-metric-margin" style="color: ${marginColor};">${marginVal.toFixed(1)}%</div>
                        </div>
                      </div>
                    </div>
                  `;
                }).join('')}
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  }

  function showModalOverlay() {
    let modalOverlay = document.getElementById('dealflow-modal-overlay');
    if (!modalOverlay) {
      modalOverlay = document.createElement('div');
      modalOverlay.id = 'dealflow-modal-overlay';
      modalOverlay.className = 'modal-overlay';
      document.body.appendChild(modalOverlay);
    }
    modalOverlay.classList.add('show');
  }

  function hideModalOverlay() {
    const modalOverlay = document.getElementById('dealflow-modal-overlay');
    if (modalOverlay) {
      modalOverlay.classList.remove('show');
    }
  }

  async function openNewQuotationModal() {
    showModalOverlay();
    const modal = document.getElementById('dealflow-modal-overlay');
    if (!modal) return;

    if (cachedCustomers.length === 0) {
      try {
        const custRes = await global.CustomersAPI.list({ limit: 100 });
        if (custRes.ok && custRes.data) {
          cachedCustomers = custRes.data;
        }
      } catch (e) {
        console.warn('Failed to load customers for modal:', e);
      }
    }

    modal.innerHTML = `
      <div class="modal-dialog animate-fade-in" style="max-width: 520px;">
        <div class="modal-header">
          <h3 class="modal-title">Create New Quotation</h3>
          <button class="modal-close" id="btn-close-quote-modal-top">&times;</button>
        </div>
        <div class="modal-body">
          <form id="new-quote-form">
            <div class="form-group">
              <label class="form-label" for="quote-cust-select">Select Customer *</label>
              <select id="quote-cust-select" class="form-input" required>
                <option value="">${cachedCustomers.length > 0 ? '-- Select an active customer --' : '-- No customers found --'}</option>
                ${cachedCustomers.map(c => `
                  <option value="${c.id}" data-terms="${c.payment_terms_days || 30}" data-tier="${c.tier?.name || 'Standard'}" data-currency="${c.currency || 'USD'}">
                    ${c.name} (${c.customer_code}) — ${c.tier?.name || 'Standard Tier'}
                  </option>
                `).join('')}
              </select>
            </div>

            <div id="cust-preview-box" class="card" style="display: none; padding: var(--space-sm); background: var(--color-background); margin-bottom: var(--space-md); font-size: var(--font-size-xs);">
              <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                <span style="color: var(--color-text-secondary);">Customer Tier:</span>
                <span id="prev-tier" style="font-weight: 700; color: var(--color-navy);">—</span>
              </div>
              <div style="display: flex; justify-content: space-between;">
                <span style="color: var(--color-text-secondary);">Currency:</span>
                <span id="prev-currency" style="font-weight: 700; color: var(--color-navy);">USD</span>
              </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-md);">
              <div class="form-group">
                <label class="form-label" for="quote-terms-input">Payment Terms (Days)</label>
                <input type="number" id="quote-terms-input" class="form-input" value="30" min="0" step="1" required />
              </div>

              <div class="form-group">
                <label class="form-label" for="quote-order-disc-input">Order Discount %</label>
                <input type="number" id="quote-order-disc-input" class="form-input" value="0.00" min="0" max="100" step="0.01" />
              </div>
            </div>

            <div id="quote-form-error" class="alert alert-coral" style="display: none; margin-top: var(--space-sm);"></div>

            <div style="display: flex; justify-content: flex-end; gap: var(--space-sm); margin-top: var(--space-lg);">
              <button type="button" class="btn btn-secondary" id="btn-cancel-quote-modal">Cancel</button>
              <button type="submit" id="btn-submit-create-quote" class="btn btn-primary">
                <span class="spinner" style="display: none;"></span>
                <span>Create & Open Builder</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    `;

    document.getElementById('btn-close-quote-modal-top')?.addEventListener('click', hideModalOverlay);
    document.getElementById('btn-cancel-quote-modal')?.addEventListener('click', hideModalOverlay);

    const form = document.getElementById('new-quote-form');
    const custSelect = document.getElementById('quote-cust-select');
    const termsInput = document.getElementById('quote-terms-input');
    const prevBox = document.getElementById('cust-preview-box');
    const prevTier = document.getElementById('prev-tier');
    const prevCurrency = document.getElementById('prev-currency');
    const errBox = document.getElementById('quote-form-error');
    const submitBtn = document.getElementById('btn-submit-create-quote');

    custSelect.addEventListener('change', () => {
      const sel = custSelect.selectedOptions[0];
      if (sel && sel.value) {
        termsInput.value = sel.dataset.terms || '30';
        prevTier.textContent = sel.dataset.tier || 'Standard';
        prevCurrency.textContent = sel.dataset.currency || 'USD';
        prevBox.style.display = 'block';
      } else {
        prevBox.style.display = 'none';
      }
    });

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      errBox.style.display = 'none';
      errBox.textContent = '';

      const customerId = parseInt(custSelect.value, 10);
      const termsDays = parseInt(termsInput.value, 10) || 30;
      const orderDisc = parseFloat(document.getElementById('quote-order-disc-input').value) || 0.0;

      if (!customerId) {
        errBox.textContent = 'Please select a customer.';
        errBox.style.display = 'block';
        return;
      }

      submitBtn.disabled = true;
      if (submitBtn.querySelector('.spinner')) submitBtn.querySelector('.spinner').style.display = 'inline-block';

      try {
        const payload = {
          customer_id: customerId,
          payment_terms_days: termsDays,
          order_discount_pct: orderDisc
        };

        const res = await global.QuotationsAPI.create(payload);
        if (!res.ok) {
          submitBtn.disabled = false;
          if (submitBtn.querySelector('.spinner')) submitBtn.querySelector('.spinner').style.display = 'none';
          errBox.textContent = res.data?.detail || res.error || 'Failed to create quotation.';
          errBox.style.display = 'block';
          return;
        }

        hideModalOverlay();
        if (global.DealFlowUI && typeof global.DealFlowUI.toast === 'function') {
          global.DealFlowUI.toast('Quotation created successfully!', 'teal');
        }
        window.location.hash = `#/quotation-builder?id=${res.data.id}`;
        global.DealFlowApp.switchView('quotation-builder', { quoteId: res.data.id });
      } catch (err) {
        submitBtn.disabled = false;
        if (submitBtn.querySelector('.spinner')) submitBtn.querySelector('.spinner').style.display = 'none';
        errBox.textContent = 'An error occurred while creating quotation.';
        errBox.style.display = 'block';
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          const spinner = submitBtn.querySelector('.spinner');
          if (spinner) spinner.style.display = 'none';
        }
      }
    });
  }

  async function exportQuotePdf(quoteId, quoteNumber) {
    try {
      if (global.DealFlowUI) global.DealFlowUI.toast(`Generating PDF for quotation ${quoteNumber || quoteId}...`, 'info');
      await global.ReportsAPI.exportReport({
        report_type: 'QUOTATION',
        quotation_id: quoteId,
        format: 'PDF'
      });
      if (global.DealFlowUI) global.DealFlowUI.toast(`Quotation ${quoteNumber || quoteId} PDF exported successfully!`, 'teal');
    } catch (err) {
      if (global.DealFlowUI) global.DealFlowUI.toast('Failed to export quotation PDF: ' + err.message, 'coral');
    }
  }

  global.QuotationsView = {
    render: render,
    openNewQuotationModal: openNewQuotationModal,
    exportQuotePdf: exportQuotePdf
  };
})(typeof window !== 'undefined' ? window : this);


