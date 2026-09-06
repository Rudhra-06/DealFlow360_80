/**
 * DealFlow360 — Invoices View Controller
 * Manages customer invoice listings, receipt details, payment tracking, and PDF exports.
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
            <button id="btn-export-billing-pdf" class="btn btn-secondary btn-sm">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              <span>Export Billing PDF</span>
            </button>
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
    const exportPdfBtn = container.querySelector('#btn-export-billing-pdf');

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

    exportPdfBtn?.addEventListener('click', async () => {
      try {
        global.DealFlowUI.toast('Generating Billing Summary PDF...', 'teal');
        await global.ReportsAPI.exportReport({
          report_type: 'BILLING',
          format: 'PDF'
        });
        global.DealFlowUI.toast('Billing Summary PDF downloaded successfully!', 'teal');
      } catch (err) {
        global.DealFlowUI.toast(err.message || 'Failed to download report', 'coral');
      }
    });
  }

  async function loadInvoices() {
    try {
      const res = await global.InvoicesAPI.list({
        status: currentFilters.status || undefined,
        invoice_type: currentFilters.invoice_type || undefined,
        limit: 100
      });

      invoices = res || [];
      renderTable();
    } catch (err) {
      console.error('Error loading invoices:', err);
      document.getElementById('invoices-table-container').innerHTML = `
        <div class="alert alert-coral" style="margin: 20px;">
          <span>Failed to load invoices: ${err.message || 'Server error'}</span>
        </div>
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
              <td style="text-align: right; display: flex; justify-content: flex-end; gap: 6px;">
                <button class="btn btn-secondary btn-sm btn-view-invoice" data-invoice-id="${inv.id}" style="padding: 4px 10px; font-size: 0.75rem;">
                  <span>View Details</span>
                </button>
                <button class="btn btn-secondary btn-sm btn-download-invoice" data-invoice-id="${inv.id}" data-invoice-num="${inv.invoice_number}" style="padding: 4px 8px; font-size: 0.75rem;" title="Download PDF Invoice">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
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

    container.querySelectorAll('.btn-download-invoice').forEach(btn => {
      btn.addEventListener('click', async () => {
        const invId = parseInt(btn.dataset.invoiceId, 10);
        const invNum = btn.dataset.invoiceNum;
        await downloadSingleInvoicePDF(invId, invNum);
      });
    });
  }

  async function downloadSingleInvoicePDF(invoiceId, invoiceNumber) {
    try {
      global.DealFlowUI.toast(`Downloading PDF for Invoice ${invoiceNumber}...`, 'teal');
      await global.ReportsAPI.exportReport({
        report_type: 'INVOICE',
        format: 'PDF',
        invoice_id: invoiceId
      });
      global.DealFlowUI.toast(`Invoice ${invoiceNumber} PDF downloaded successfully!`, 'teal');
    } catch (err) {
      global.DealFlowUI.toast('Error exporting invoice PDF: ' + err.message, 'coral');
    }
  }

  async function openInvoiceDetailDrawer(invoiceId) {
    const backdrop = document.getElementById('dealflow-drawer-backdrop');
    const panel = document.getElementById('dealflow-drawer-panel');
    if (!panel || !backdrop) return;

    panel.innerHTML = `<div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Loading invoice details...</div>`;
    backdrop.classList.add('show');
    backdrop.classList.add('active');
    panel.classList.add('open');
    panel.classList.add('active');

    const closeDrawer = () => {
      backdrop.classList.remove('show');
      backdrop.classList.remove('active');
      panel.classList.remove('open');
      panel.classList.remove('active');
    };
    backdrop.onclick = closeDrawer;

    try {
      const res = await global.InvoicesAPI.get(invoiceId);
      const inv = (res && res.data) ? res.data : res;
      if (!inv || !inv.invoice_number) {
        panel.innerHTML = `<div class="alert alert-coral" style="margin: 20px;">Failed to load invoice details.</div>`;
        return;
      }

      panel.innerHTML = `
        <div class="drawer-header" style="display: flex; justify-content: space-between; align-items: center; padding: var(--space-md) var(--space-lg); border-bottom: 1px solid var(--color-border);">
          <div>
            <h3 style="margin: 0; color: var(--color-navy); font-size: var(--font-size-md);">Invoice ${inv.invoice_number}</h3>
            <div style="font-size: 0.75rem; color: var(--color-text-secondary); margin-top: 2px;">${inv.invoice_type} &bull; Issued ${new Date(inv.issue_date).toLocaleDateString()}</div>
          </div>
          <div style="display: flex; gap: 8px; align-items: center;">
            <button id="btn-drawer-download-pdf" class="btn btn-secondary btn-sm" style="font-size: 0.75rem;">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              <span>PDF</span>
            </button>
            <button class="drawer-close-btn" id="btn-close-inv-drawer" style="font-size: 1.5rem; background: none; border: none; cursor: pointer;">&times;</button>
          </div>
        </div>

        <div class="drawer-body" style="padding: 20px; overflow-y: auto;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            ${formatInvoiceStatusBadge(inv.status)}
            <span style="font-size: 0.8rem; color: var(--color-text-secondary);">Due Date: <strong>${new Date(inv.due_date).toLocaleDateString()}</strong></span>
          </div>

          <div class="card" style="padding: var(--space-md); background: var(--color-background); margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: var(--font-size-sm);">
              <span style="color: var(--color-text-secondary);">Subtotal:</span>
              <strong>${inv.currency} ${Number(inv.subtotal).toFixed(2)}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: var(--font-size-sm);">
              <span style="color: var(--color-text-secondary);">Tax Amount:</span>
              <span>${inv.currency} ${Number(inv.tax_amount).toFixed(2)}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: var(--font-size-md); font-weight: 700; color: var(--color-navy); border-top: 1px solid var(--color-border); padding-top: 6px;">
              <span>Total Amount:</span>
              <span>${inv.currency} ${Number(inv.total_amount).toFixed(2)}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: var(--font-size-sm);">
              <span style="color: var(--color-text-secondary);">Paid to Date:</span>
              <span style="color: var(--color-teal); font-weight: 600;">${inv.currency} ${Number(inv.paid_amount).toFixed(2)}</span>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: var(--font-size-sm); font-weight: 700; color: ${Number(inv.balance_due) > 0 ? 'var(--color-coral)' : 'var(--color-teal)'};">
              <span>Balance Due:</span>
              <span>${inv.currency} ${Number(inv.balance_due).toFixed(2)}</span>
            </div>
          </div>

          <h4 style="font-size: 0.85rem; color: var(--color-navy); margin: 20px 0 8px;">Invoice Line Items</h4>
          <table class="data-table" style="font-size: 0.75rem; width: 100%;">
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
                <tr><td colspan="4" style="text-align: center; color: var(--color-text-muted);">No item lines recorded.</td></tr>
              `}
            </tbody>
          </table>

          ${Number(inv.balance_due) > 0 ? `
            <div style="margin-top: 24px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
              <button id="btn-razorpay-this-invoice" class="btn btn-primary" style="background: #0284C7; border-color: #0284C7;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
                <span>Pay with Razorpay</span>
              </button>
              <button id="btn-pay-this-invoice" class="btn btn-secondary">
                <span>Record Manual Payment</span>
              </button>
            </div>
          ` : ''}
        </div>
      `;

      document.getElementById('btn-close-inv-drawer').onclick = closeDrawer;
      document.getElementById('btn-drawer-download-pdf')?.addEventListener('click', async () => {
        await downloadSingleInvoicePDF(inv.id, inv.invoice_number);
      });
      document.getElementById('btn-razorpay-this-invoice')?.addEventListener('click', () => {
        triggerRazorpayPayment(inv);
      });
      document.getElementById('btn-pay-this-invoice')?.addEventListener('click', () => {
        closeDrawer();
        window.DealFlowApp.switchView('payments');
      });
    } catch (e) {
      console.error('Error in invoice detail drawer:', e);
      panel.innerHTML = `<div class="alert alert-coral" style="margin: 20px;">Error loading invoice detail: ${e.message || e}</div>`;
    }
  }

  async function triggerRazorpayPayment(invoice) {
    try {
      global.DealFlowUI.toast('Initializing Razorpay Payment Gateway...', 'teal');
      const orderRes = await global.PaymentsAPI.createRazorpayOrder({
        amount: Number(invoice.balance_due),
        currency: invoice.currency || 'USD',
        invoice_id: invoice.id,
        customer_id: invoice.customer_id
      });

      const orderId = (orderRes && orderRes.order_id) || `order_${Date.now()}`;

      if (global.RazorpayGatewayModal) {
        global.RazorpayGatewayModal.open({
          order_id: orderId,
          amount: Number(invoice.balance_due),
          currency: invoice.currency || 'USD',
          invoice_number: invoice.invoice_number,
          invoice_id: invoice.id,
          customer_id: invoice.customer_id,
          onSuccess: async (res) => {
            if (window.DealFlowFirebase) {
              window.DealFlowFirebase.logAnalyticsEvent('invoice_payment_completed', {
                invoice_id: invoice.id,
                payment_method: 'RAZORPAY',
                amount: Number(invoice.balance_due)
              });
            }
            global.DealFlowUI.toast(`Razorpay Payment Successful! Ref: ${res.razorpay_payment_id}`, 'teal');
            const backdrop = document.getElementById('dealflow-drawer-backdrop');
            const panel = document.getElementById('dealflow-drawer-panel');
            if (backdrop) {
              backdrop.classList.remove('show');
              backdrop.classList.remove('active');
            }
            if (panel) {
              panel.classList.remove('open');
              panel.classList.remove('active');
            }
            await loadInvoices();
          },
          onError: (err) => {
            global.DealFlowUI.toast(err || 'Razorpay payment cancelled.', 'coral');
          }
        });
      } else if (window.Razorpay) {
        const options = {
          key: global.DealFlowConfig.RAZORPAY_KEY_ID,
          amount: orderRes.amount,
          currency: 'INR',
          name: 'DealFlow360',
          description: `Payment for Invoice ${invoice.invoice_number}`,
          order_id: orderId,
          handler: async function (response) {
            await global.PaymentsAPI.verifyRazorpayPayment({
              razorpay_order_id: response.razorpay_order_id || orderId,
              razorpay_payment_id: response.razorpay_payment_id || `pay_${Date.now()}`,
              razorpay_signature: response.razorpay_signature || `mock_sig_${Date.now()}`,
              customer_id: invoice.customer_id,
              invoice_id: invoice.id,
              amount: Number(invoice.balance_due),
              currency: invoice.currency || 'USD'
            });
            global.DealFlowUI.toast('Razorpay Payment Settled.', 'teal');
            await loadInvoices();
          }
        };
        new window.Razorpay(options).open();
      }
    } catch (err) {
      global.DealFlowUI.toast('Razorpay Error: ' + (err.message || err), 'coral');
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
    render: render,
    openInvoiceDetailDrawer: openInvoiceDetailDrawer
  };
})(typeof window !== 'undefined' ? window : this);
