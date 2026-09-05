/**
 * DealFlow360 — Payments View Controller
 * Manages customer payment records and multi-invoice allocations.
 */
(function (global) {
  'use strict';

  let payments = [];
  let customers = [];
  let currentFilters = {
    customer_id: '',
    status: ''
  };

  async function render(container) {
    container.innerHTML = `
      <div class="payments-page-wrapper animate-fade-in">
        <div class="page-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-md); flex-wrap: wrap; gap: var(--space-md);">
          <div>
            <h1 class="page-title" style="margin: 0;">Payments</h1>
            <p class="page-subtitle" style="margin-top: 4px; color: var(--color-text-secondary); font-size: var(--font-size-sm);">
              Customer payment ledger, multi-invoice allocations, and settlement tracking.
            </p>
          </div>
          <div style="display: flex; gap: var(--space-sm);">
            <button id="btn-open-record-payment" class="btn btn-primary btn-sm">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
              <span>Record Payment</span>
            </button>
            <button id="btn-refresh-payments" class="btn btn-secondary btn-sm">
              <span>Refresh</span>
            </button>
          </div>
        </div>

        <!-- Filter Strip -->
        <div class="card" style="padding: var(--space-md); margin-bottom: var(--space-md); display: flex; gap: var(--space-md); align-items: center;">
          <select id="payment-customer-filter" class="form-input" style="width: 220px;">
            <option value="">All Customers</option>
          </select>
          <div id="payment-count-badge" style="margin-left: auto; font-size: var(--font-size-xs); color: var(--color-text-secondary); font-weight: 600;">
            Loading payments...
          </div>
        </div>

        <!-- Payments Table -->
        <div class="card" style="padding: 0; overflow: hidden;">
          <div id="payments-table-container" style="overflow-x: auto;">
            <div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Loading payments...</div>
          </div>
        </div>
      </div>
    `;

    setupEvents(container);
    await loadInitialData();
  }

  function setupEvents(container) {
    const custFilter = container.querySelector('#payment-customer-filter');
    const refreshBtn = container.querySelector('#btn-refresh-payments');
    const recordBtn = container.querySelector('#btn-open-record-payment');

    custFilter?.addEventListener('change', async () => {
      currentFilters.customer_id = custFilter.value;
      await loadPayments();
    });

    refreshBtn?.addEventListener('click', async () => {
      await loadPayments();
      global.DealFlowUI.toast('Payments refreshed.', 'teal');
    });

    recordBtn?.addEventListener('click', () => {
      openRecordPaymentModal();
    });
  }

  async function loadInitialData() {
    try {
      const custRes = await global.CustomersAPI.list({ limit: 100 });
      customers = custRes.ok ? custRes.data : [];

      const select = document.getElementById('payment-customer-filter');
      if (select) {
        select.innerHTML = '<option value="">All Customers</option>' +
          customers.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
      }

      await loadPayments();
    } catch (e) {
      console.error(e);
    }
  }

  async function loadPayments() {
    try {
      const res = await global.PaymentsAPI.list({
        customer_id: currentFilters.customer_id || undefined,
        limit: 100
      });

      if (!res.ok) {
        document.getElementById('payments-table-container').innerHTML = `
          <div class="alert alert-coral" style="margin: 20px;">Failed to load payments.</div>
        `;
        return;
      }

      payments = res.data || [];
      renderTable();
    } catch (err) {
      console.error(err);
      document.getElementById('payments-table-container').innerHTML = `
        <div class="alert alert-coral" style="margin: 20px;">Error connecting to Payments service.</div>
      `;
    }
  }

  function renderTable() {
    const container = document.getElementById('payments-table-container');
    const badge = document.getElementById('payment-count-badge');
    if (!container) return;

    if (badge) badge.textContent = `Showing ${payments.length} payment records`;

    if (payments.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 48px; color: var(--color-text-muted);">
          <div style="font-weight: 600; margin-bottom: 4px;">No Payments Recorded</div>
          <p style="font-size: var(--font-size-xs);">Click 'Record Payment' to post cash settlements against outstanding invoices.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <table class="data-table">
        <thead>
          <tr>
            <th>Payment #</th>
            <th>Customer</th>
            <th>Amount</th>
            <th>Method</th>
            <th>Reference</th>
            <th>Received Date</th>
            <th>Allocations</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          ${payments.map(p => {
            const cust = customers.find(c => c.id === p.customer_id);
            const custName = cust ? cust.name : `Customer #${p.customer_id}`;
            const allocCount = p.allocations ? p.allocations.length : 0;

            return `
              <tr>
                <td>
                  <span style="font-family: monospace; font-weight: 700; color: var(--color-navy);">${p.payment_number}</span>
                </td>
                <td style="font-weight: 600;">${custName}</td>
                <td style="font-family: monospace; font-weight: 700; color: var(--color-teal);">
                  ${p.currency} ${Number(p.amount).toFixed(2)}
                </td>
                <td>
                  <span class="badge badge-navy" style="font-size: 0.7rem;">${p.payment_method}</span>
                </td>
                <td style="font-family: monospace; font-size: 0.75rem; color: var(--color-text-secondary);">${p.reference || '—'}</td>
                <td style="font-size: var(--font-size-xs);">${new Date(p.received_at).toLocaleDateString()}</td>
                <td>
                  <span class="badge badge-teal" style="font-size: 0.65rem;">${allocCount} Invoice${allocCount === 1 ? '' : 's'}</span>
                </td>
                <td>
                  <span class="badge badge-teal">${p.status}</span>
                </td>
              </tr>
            `;
          }).join('')}
        </tbody>
      </table>
    `;
  }

  async function openRecordPaymentModal() {
    const overlay = document.getElementById('dealflow-modal-overlay');
    if (!overlay) return;

    overlay.innerHTML = `
      <div class="modal-card" style="max-width: 750px; width: 90%;">
        <div class="modal-header">
          <h3>Record Customer Payment</h3>
          <button class="modal-close-btn" id="btn-close-pay-modal">&times;</button>
        </div>
        <div class="modal-body">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px;">
            <div>
              <label style="font-size: 0.75rem; font-weight: 600;">Customer</label>
              <select id="pay-customer-select" class="form-input">
                <option value="">Select Customer...</option>
                ${customers.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}
              </select>
            </div>
            <div>
              <label style="font-size: 0.75rem; font-weight: 600;">Payment Amount ($)</label>
              <input type="number" id="pay-amount-input" class="form-input" min="0.01" step="0.01" placeholder="0.00" style="font-weight: 700;" />
            </div>
            <div>
              <label style="font-size: 0.75rem; font-weight: 600;">Payment Method</label>
              <select id="pay-method-select" class="form-input">
                <option value="BANK_TRANSFER">Bank Wire Transfer</option>
                <option value="CREDIT_CARD">Credit Card</option>
                <option value="ACH">ACH Direct Debit</option>
                <option value="CHECK">Corporate Check</option>
              </select>
            </div>
            <div>
              <label style="font-size: 0.75rem; font-weight: 600;">Reference / Check #</label>
              <input type="text" id="pay-ref-input" class="form-input" placeholder="e.g. WIRE-89410" />
            </div>
          </div>

          <h4 style="font-size: 0.85rem; color: var(--color-navy); margin: 16px 0 8px;">Allocate Against Outstanding Invoices</h4>
          <div id="pay-invoices-allocation-container" style="max-height: 220px; overflow-y: auto; border: 1px solid var(--color-border); border-radius: var(--radius-sm); margin-bottom: 12px;">
            <div style="text-align: center; padding: 24px; color: var(--color-text-muted); font-size: 0.75rem;">
              Select a customer above to view open invoices.
            </div>
          </div>

          <div class="allocation-totals-banner">
            <div>Total Payment: <strong id="banner-pay-total">$0.00</strong></div>
            <div>Allocated: <strong id="banner-allocated-total" style="color: var(--color-teal);">$0.00</strong></div>
            <div>Remaining Unallocated: <strong id="banner-unallocated-total" style="color: var(--color-navy);">$0.00</strong></div>
          </div>

          <div style="display: flex; justify-content: flex-end; gap: 8px; margin-top: 20px;">
            <button class="btn btn-secondary btn-sm" id="btn-cancel-pay">Cancel</button>
            <button class="btn btn-primary btn-sm" id="btn-submit-payment">Post & Settle Payment</button>
          </div>
        </div>
      </div>
    `;

    overlay.classList.add('active');
    const closeModal = () => overlay.classList.remove('active');
    document.getElementById('btn-close-pay-modal').onclick = closeModal;
    document.getElementById('btn-cancel-pay').onclick = closeModal;

    const custSelect = document.getElementById('pay-customer-select');
    const amountInput = document.getElementById('pay-amount-input');

    const updateTotals = () => {
      const payAmount = parseFloat(amountInput.value) || 0;
      let allocated = 0;
      document.querySelectorAll('.invoice-alloc-input').forEach(inp => {
        allocated += parseFloat(inp.value) || 0;
      });

      const remaining = payAmount - allocated;
      document.getElementById('banner-pay-total').textContent = `$${payAmount.toFixed(2)}`;
      document.getElementById('banner-allocated-total').textContent = `$${allocated.toFixed(2)}`;
      document.getElementById('banner-unallocated-total').textContent = `$${remaining.toFixed(2)}`;
      document.getElementById('banner-unallocated-total').style.color = remaining < 0 ? 'var(--color-coral)' : 'var(--color-navy)';
    };

    amountInput.addEventListener('input', updateTotals);

    custSelect.addEventListener('change', async () => {
      const custId = parseInt(custSelect.value, 10);
      const container = document.getElementById('pay-invoices-allocation-container');
      if (!custId) {
        container.innerHTML = `<div style="text-align: center; padding: 24px; color: var(--color-text-muted); font-size: 0.75rem;">Select a customer above to view open invoices.</div>`;
        return;
      }

      container.innerHTML = `<div style="text-align: center; padding: 20px;"><span class="spinner spinner-teal"></span> Loading open invoices...</div>`;

      try {
        const res = await global.InvoicesAPI.list({ customer_id: custId, limit: 50 });
        const invList = (res.ok ? res.data : []).filter(i => Number(i.balance_due) > 0);

        if (invList.length === 0) {
          container.innerHTML = `<div style="text-align: center; padding: 20px; color: var(--color-text-muted); font-size: 0.75rem;">No unpaid invoices found for this customer.</div>`;
          return;
        }

        container.innerHTML = `
          <table class="payment-allocation-table">
            <thead>
              <tr>
                <th>Invoice #</th>
                <th>Due Date</th>
                <th>Total</th>
                <th>Balance Due</th>
                <th>Allocate ($)</th>
              </tr>
            </thead>
            <tbody>
              ${invList.map(i => `
                <tr data-invoice-id="${i.id}">
                  <td style="font-family: monospace; font-weight: 700;">${i.invoice_number}</td>
                  <td>${new Date(i.due_date).toLocaleDateString()}</td>
                  <td>${i.currency} ${Number(i.total_amount).toFixed(2)}</td>
                  <td style="font-weight: 700; color: var(--color-coral);">${i.currency} ${Number(i.balance_due).toFixed(2)}</td>
                  <td>
                    <input type="number" class="form-input invoice-alloc-input" data-invoice-id="${i.id}" data-max="${i.balance_due}" value="0.00" min="0" max="${i.balance_due}" step="0.01" />
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        `;

        container.querySelectorAll('.invoice-alloc-input').forEach(inp => {
          inp.addEventListener('input', updateTotals);
        });
      } catch (e) {
        container.innerHTML = `<div class="alert alert-coral">Error loading invoices.</div>`;
      }
    });

    document.getElementById('btn-submit-payment').onclick = async () => {
      const custId = parseInt(custSelect.value, 10);
      const amount = parseFloat(amountInput.value) || 0;
      const method = document.getElementById('pay-method-select').value;
      const ref = document.getElementById('pay-ref-input').value;

      if (!custId || amount <= 0) {
        global.DealFlowUI.toast('Please select a customer and enter a valid payment amount.', 'coral');
        return;
      }

      const allocations = [];
      document.querySelectorAll('.invoice-alloc-input').forEach(inp => {
        const val = parseFloat(inp.value) || 0;
        if (val > 0) {
          allocations.push({
            invoice_id: parseInt(inp.dataset.invoiceId, 10),
            amount: val
          });
        }
      });

      if (allocations.length === 0) {
        global.DealFlowUI.toast('Please allocate payment against at least one invoice.', 'coral');
        return;
      }

      try {
        const res = await global.PaymentsAPI.record({
          customer_id: custId,
          amount: amount,
          currency: 'USD',
          payment_method: method,
          reference: ref,
          allocations: allocations
        });

        if (res.ok) {
          global.DealFlowUI.toast('Payment recorded and allocated successfully.', 'teal');
          closeModal();
          await loadPayments();
        } else {
          global.DealFlowUI.toast(res.data?.detail || 'Failed to record payment.', 'coral');
        }
      } catch (e) {
        global.DealFlowUI.toast('Network error recording payment.', 'coral');
      }
    };
  }

  global.PaymentsView = {
    render: render
  };
})(typeof window !== 'undefined' ? window : this);
