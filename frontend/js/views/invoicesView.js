/**
 * DealFlow360 — Invoices View Controller
 * Manages customer invoice listings and receipt details.
 */
(function (global) {
  'use strict';

  let invoices = [];
  let currentFilters = {
    status: '',
    invoice_type: ''
  };

  async function render(container) {
    container.innerHTML = `
      <div class="invoices-page-wrapper animate-fade-in">
        <div class="page-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-md); flex-wrap: wrap; gap: var(--space-md);">
          <div>
            <h1 class="page-title" style="margin: 0;">Invoices</h1>
            <p class="page-subtitle" style="margin-top: 4px; color: var(--color-text-secondary); font-size: var(--font-size-sm);">
              Customer billing invoices, one-time charges, and payment balances.
            </p>
          </div>
          <div style="display: flex; gap: var(--space-sm);">
            <button id="btn-refresh-invoices" class="btn btn-secondary btn-sm">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
              <span>Refresh</span>
            </button>
          </div>
        </div>

        <!-- Filter Strip -->
        <div class="card" style="padding: var(--space-md); margin-bottom: var(--space-md); display: flex; gap: var(--space-md); flex-wrap: wrap; align-items: center;">
          <select id="invoice-status-filter" class="form-input" style="width: 180px;">
            <option value="">All Statuses</option>
            <option value="DRAFT" ${currentFilters.status === 'DRAFT' ? 'selected' : ''}>Draft</option>
            <option value="ISSUED" ${currentFilters.status === 'ISSUED' ? 'selected' : ''}>Issued</option>
            <option value="PARTIALLY_PAID" ${currentFilters.status === 'PARTIALLY_PAID' ? 'selected' : ''}>Partially Paid</option>
            <option value="PAID" ${currentFilters.status === 'PAID' ? 'selected' : ''}>Paid</option>
            <option value="CREDITED" ${currentFilters.status === 'CREDITED' ? 'selected' : ''}>Credited</option>
            <option value="CANCELLED" ${currentFilters.status === 'CANCELLED' ? 'selected' : ''}>Cancelled</option>
          </select>

          <select id="invoice-type-filter" class="form-input" style="width: 180px;">
            <option value="">All Types</option>
            <option value="ONE_TIME" ${currentFilters.invoice_type === 'ONE_TIME' ? 'selected' : ''}>One-Time</option>
            <option value="RECURRING" ${currentFilters.invoice_type === 'RECURRING' ? 'selected' : ''}>Recurring</option>
          </select>

          <div id="invoice-count-badge" style="margin-left: auto; font-size: var(--font-size-xs); color: var(--color-text-secondary); font-weight: 600;">
            Loading invoices...
          </div>
        </div>

        <!-- Invoices Table -->
        <div class="card" style="padding: 0; overflow: hidden;">
          <div id="invoices-table-container" style="overflow-x: auto;">
            <div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Loading invoices...</div>
          </div>
        </div>
      </div>
    `;

    setupEvents(container);
    await loadInvoices();
  }

  function setupEvents(container) {
    const statusFilter = container.querySelector('#invoice-status-filter');
    const typeFilter = container.querySelector('#invoice-type-filter');
    const refreshBtn = container.querySelector('#btn-refresh-invoices');

    statusFilter?.addEventListener('change', async () => {
      currentFilters.status = statusFilter.value;
      await loadInvoices();
    });

    typeFilter?.addEventListener('change', async () => {
      currentFilters.invoice_type = typeFilter.value;
      await loadInvoices();
    });

    refreshBtn?.addEventListener('click', async () => {
      await loadInvoices();
      global.DealFlowUI.toast('Invoices refreshed.', 'teal');
    });
  }

  async function loadInvoices() {
    try {
      const res = await global.InvoicesAPI.list({
        status: currentFilters.status || undefined,
        invoice_type: currentFilters.invoice_type || undefined,
        limit: 100
      });

      if (!res.ok) {
        document.getElementById('invoices-table-container').innerHTML = `
          <div class="alert alert-coral" style="margin: 20px;">
            <span>Failed to load invoices: ${res.data?.detail || res.error || 'Server error'}</span>
          </div>
        `;
        return;
      }

      invoices = res.data || [];
      renderTable();
    } catch (err) {
      console.error(err);
      document.getElementById('invoices-table-container').innerHTML = `
        <div class="alert alert-coral" style="margin: 20px;">Error connecting to Invoices API.</div>
      `;
    }
  }

  function renderTable() {
    const container = document.getElementById('invoices-table-container');
    const badge = document.getElementById('invoice-count-badge');
    if (!container) return;

    if (badge) badge.textContent = `Showing ${invoices.length} invoices`;

    if (invoices.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 48px; color: var(--color-text-muted);">
          <div style="font-weight: 600; margin-bottom: 4px;">No Invoices Found</div>
          <p style="font-size: var(--font-size-xs);">Invoices are generated upon order fulfillment or recurring billing cycles.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <table class="data-table">
        <thead>
          <tr>
            <th>Invoice Number</th>
            <th>Type</th>
            <th>Issue Date</th>
            <th>Due Date</th>
            <th>Total Amount</th>
            <th>Paid</th>
            <th>Balance Due</th>
            <th>Status</th>
            <th style="text-align: right;">Action</th>
          </tr>
        </thead>
        <tbody>
          ${invoices.map(inv => `
            <tr>
              <td>
                <span style="font-family: monospace; font-weight: 700; color: var(--color-navy);">${inv.invoice_number}</span>
              </td>
              <td>
                <span class="badge ${inv.invoice_type === 'RECURRING' ? 'badge-teal' : 'badge-navy'}" style="font-size: 0.7rem;">
                  ${inv.invoice_type === 'RECURRING' ? 'Recurring' : 'One-Time'}
                </span>
              </td>
              <td style="font-size: var(--font-size-xs);">${new Date(inv.issue_date).toLocaleDateString()}</td>
              <td style="font-size: var(--font-size-xs);">${new Date(inv.due_date).toLocaleDateString()}</td>
              <td style="font-family: monospace; font-weight: 700;">${inv.currency} ${Number(inv.total_amount).toFixed(2)}</td>
              <td style="font-family: monospace; color: var(--color-teal);">${inv.currency} ${Number(inv.paid_amount).toFixed(2)}</td>
              <td style="font-family: monospace; font-weight: 700; color: ${Number(inv.balance_due) > 0 ? 'var(--color-coral)' : 'var(--color-teal)'};">
                ${inv.currency} ${Number(inv.balance_due).toFixed(2)}
              </td>
              <td>${formatInvoiceStatusBadge(inv.status)}</td>
              <td style="text-align: right;">
                <button class="btn btn-secondary btn-sm btn-view-invoice" data-invoice-id="${inv.id}" style="padding: 4px 10px; font-size: 0.75rem;">
                  <span>View Details</span>
                </button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;

    container.querySelectorAll('.btn-view-invoice').forEach(btn => {
      btn.addEventListener('click', () => {
        const invId = parseInt(btn.dataset.invoiceId, 10);
        openInvoiceDetailDrawer(invId);
      });
    });
  }

  async function openInvoiceDetailDrawer(invoiceId) {
    const backdrop = document.getElementById('dealflow-drawer-backdrop');
    const panel = document.getElementById('dealflow-drawer-panel');
    if (!panel || !backdrop) return;

    panel.innerHTML = `<div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Loading invoice details...</div>`;
    backdrop.classList.add('active');
    panel.classList.add('active');

    const closeDrawer = () => {
      backdrop.classList.remove('active');
      panel.classList.remove('active');
    };
    backdrop.onclick = closeDrawer;

    try {
      const res = await global.InvoicesAPI.get(invoiceId);
      if (!res.ok) {
        panel.innerHTML = `<div class="alert alert-coral" style="margin: 20px;">Failed to load invoice.</div>`;
        return;
      }

      const inv = res.data;
      panel.innerHTML = `
        <div class="drawer-header">
          <div>
            <h3>Invoice ${inv.invoice_number}</h3>
            <div style="font-size: 0.75rem; color: var(--color-text-secondary);">${inv.invoice_type} &bull; Issued ${new Date(inv.issue_date).toLocaleDateString()}</div>
          </div>
          <button class="drawer-close-btn" id="btn-close-inv-drawer">&times;</button>
        </div>

        <div class="drawer-body" style="padding: 20px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            ${formatInvoiceStatusBadge(inv.status)}
            <span style="font-size: 0.8rem; color: var(--color-text-secondary);">Due: <strong>${new Date(inv.due_date).toLocaleDateString()}</strong></span>
          </div>

          <div class="invoice-summary-box">
            <div class="invoice-summary-row">
              <span>Subtotal:</span>
              <strong>${inv.currency} ${Number(inv.subtotal).toFixed(2)}</strong>
            </div>
            <div class="invoice-summary-row">
              <span>Tax:</span>
              <span>${inv.currency} ${Number(inv.tax_amount).toFixed(2)}</span>
            </div>
            <div class="invoice-summary-row total-row">
              <span>Total Amount:</span>
              <span>${inv.currency} ${Number(inv.total_amount).toFixed(2)}</span>
            </div>
            <div class="invoice-summary-row">
              <span>Paid to Date:</span>
              <span style="color: var(--color-teal);">${inv.currency} ${Number(inv.paid_amount).toFixed(2)}</span>
            </div>
            <div class="invoice-summary-row">
              <span>Credited Amount:</span>
              <span>${inv.currency} ${Number(inv.credited_amount).toFixed(2)}</span>
            </div>
            <div class="invoice-summary-row balance-row">
              <span>Balance Due:</span>
              <span>${inv.currency} ${Number(inv.balance_due).toFixed(2)}</span>
            </div>
          </div>

          <h4 style="font-size: 0.85rem; color: var(--color-navy); margin: 20px 0 8px;">Invoice Line Items</h4>
          <table class="data-table" style="font-size: 0.75rem;">
            <thead>
              <tr>
                <th>Description</th>
                <th>Qty</th>
                <th>Price</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              ${inv.lines && inv.lines.length > 0 ? inv.lines.map(l => `
                <tr>
                  <td>${l.description}</td>
                  <td>${Number(l.quantity)}</td>
                  <td>${inv.currency} ${Number(l.unit_price).toFixed(2)}</td>
                  <td style="font-weight: 700;">${inv.currency} ${Number(l.amount).toFixed(2)}</td>
                </tr>
              `).join('') : `
                <tr><td colspan="4" style="text-align: center;">No item lines.</td></tr>
              `}
            </tbody>
          </table>

          ${Number(inv.balance_due) > 0 ? `
            <div style="margin-top: 24px;">
              <button id="btn-pay-this-invoice" class="btn btn-primary btn-block">
                <span>Record Payment for this Invoice</span>
              </button>
            </div>
          ` : ''}
        </div>
      `;

      document.getElementById('btn-close-inv-drawer').onclick = closeDrawer;
      document.getElementById('btn-pay-this-invoice')?.addEventListener('click', () => {
        closeDrawer();
        window.DealFlowApp.switchView('payments');
      });
    } catch (e) {
      console.error(e);
    }
  }

  function formatInvoiceStatusBadge(status) {
    const map = {
      'DRAFT': { label: 'Draft', cls: 'badge-navy' },
      'ISSUED': { label: 'Issued', cls: 'badge-navy' },
      'PARTIALLY_PAID': { label: 'Partially Paid', cls: 'badge-coral' },
      'PAID': { label: 'Paid', cls: 'badge-teal' },
      'CREDITED': { label: 'Credited', cls: 'badge-teal' },
      'CANCELLED': { label: 'Cancelled', cls: 'badge-navy' }
    };
    const s = map[status] || { label: status, cls: 'badge-navy' };
    return `<span class="badge ${s.cls}">${s.label}</span>`;
  }

  global.InvoicesView = {
    render: render
  };
})(typeof window !== 'undefined' ? window : this);
