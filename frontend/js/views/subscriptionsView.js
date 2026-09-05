/**
 * DealFlow360 — Subscriptions View Controller
 * Manages recurring SaaS subscriptions, proration, billing schedules, and cancellations.
 */
(function (global) {
  'use strict';

  let subscriptions = [];
  let currentFilters = {
    status: ''
  };

  async function render(container) {
    container.innerHTML = `
      <div class="subscriptions-page-wrapper animate-fade-in">
        <div class="page-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-md); flex-wrap: wrap; gap: var(--space-md);">
          <div>
            <h1 class="page-title" style="margin: 0;">Subscriptions</h1>
            <p class="page-subtitle" style="margin-top: 4px; color: var(--color-text-secondary); font-size: var(--font-size-sm);">
              Recurring revenue, subscription lifecycle, mid-cycle proration, and billing schedules.
            </p>
          </div>
          <div style="display: flex; gap: var(--space-sm);">
            <button id="btn-generate-due-billing" class="btn btn-primary btn-sm">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
              <span>Generate Due Invoices</span>
            </button>
            <button id="btn-refresh-subscriptions" class="btn btn-secondary btn-sm">
              <span>Refresh</span>
            </button>
          </div>
        </div>

        <!-- Filter Strip -->
        <div class="card" style="padding: var(--space-md); margin-bottom: var(--space-md); display: flex; gap: var(--space-md); align-items: center;">
          <select id="sub-status-filter" class="form-input" style="width: 200px;">
            <option value="">All Statuses</option>
            <option value="ACTIVE" ${currentFilters.status === 'ACTIVE' ? 'selected' : ''}>Active</option>
            <option value="PENDING_CANCELLATION" ${currentFilters.status === 'PENDING_CANCELLATION' ? 'selected' : ''}>Pending Cancellation</option>
            <option value="CANCELLED" ${currentFilters.status === 'CANCELLED' ? 'selected' : ''}>Cancelled</option>
            <option value="ENDED" ${currentFilters.status === 'ENDED' ? 'selected' : ''}>Ended</option>
          </select>
          <div id="sub-count-badge" style="margin-left: auto; font-size: var(--font-size-xs); color: var(--color-text-secondary); font-weight: 600;">
            Loading subscriptions...
          </div>
        </div>

        <!-- Subscriptions Table -->
        <div class="card" style="padding: 0; overflow: hidden;">
          <div id="subscriptions-table-container" style="overflow-x: auto;">
            <div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Loading subscriptions...</div>
          </div>
        </div>
      </div>
    `;

    setupEvents(container);
    await loadSubscriptions();
  }

  function setupEvents(container) {
    const statusFilter = container.querySelector('#sub-status-filter');
    const refreshBtn = container.querySelector('#btn-refresh-subscriptions');
    const generateBtn = container.querySelector('#btn-generate-due-billing');

    statusFilter?.addEventListener('change', async () => {
      currentFilters.status = statusFilter.value;
      await loadSubscriptions();
    });

    refreshBtn?.addEventListener('click', async () => {
      await loadSubscriptions();
      global.DealFlowUI.toast('Subscriptions refreshed.', 'teal');
    });

    generateBtn?.addEventListener('click', async () => {
      try {
        const res = await global.BillingAPI.generateDueInvoices();
        if (res.ok) {
          const count = res.data ? res.data.length : 0;
          global.DealFlowUI.toast(`Generated ${count} due recurring invoices.`, 'teal');
          await loadSubscriptions();
        } else {
          global.DealFlowUI.toast(res.data?.detail || 'Failed to generate recurring billing.', 'coral');
        }
      } catch (e) {
        global.DealFlowUI.toast('Network error executing due billing.', 'coral');
      }
    });
  }

  async function loadSubscriptions() {
    try {
      const res = await global.SubscriptionsAPI.list({
        status: currentFilters.status || undefined,
        limit: 100
      });

      if (!res.ok) {
        document.getElementById('subscriptions-table-container').innerHTML = `
          <div class="alert alert-coral" style="margin: 20px;">Failed to load subscriptions.</div>
        `;
        return;
      }

      subscriptions = res.data || [];
      renderTable();
    } catch (err) {
      console.error(err);
      document.getElementById('subscriptions-table-container').innerHTML = `
        <div class="alert alert-coral" style="margin: 20px;">Error connecting to Subscriptions service.</div>
      `;
    }
  }

  function renderTable() {
    const container = document.getElementById('subscriptions-table-container');
    const badge = document.getElementById('sub-count-badge');
    if (!container) return;

    if (badge) badge.textContent = `Showing ${subscriptions.length} subscriptions`;

    if (subscriptions.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 48px; color: var(--color-text-muted);">
          <div style="font-weight: 600; margin-bottom: 4px;">No Recurring Subscriptions Found</div>
          <p style="font-size: var(--font-size-xs);">Subscriptions are automatically provisioned from recurring order lines.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <table class="data-table">
        <thead>
          <tr>
            <th>Subscription #</th>
            <th>Quantity</th>
            <th>Monthly Recurring Revenue</th>
            <th>Interval</th>
            <th>Current Period</th>
            <th>Next Billing Date</th>
            <th>Status</th>
            <th style="text-align: right;">Action</th>
          </tr>
        </thead>
        <tbody>
          ${subscriptions.map(sub => `
            <tr>
              <td>
                <span style="font-family: monospace; font-weight: 700; color: var(--color-navy);">${sub.subscription_number}</span>
              </td>
              <td style="font-weight: 600;">${Number(sub.quantity)}</td>
              <td style="font-family: monospace; font-weight: 700; color: var(--color-teal);">
                ${sub.currency} ${Number(sub.monthly_recurring_revenue || sub.unit_price).toFixed(2)}
              </td>
              <td>${sub.interval_months === 1 ? 'Monthly' : (sub.interval_months === 12 ? 'Annual' : `${sub.interval_months} Mos`)}</td>
              <td style="font-size: var(--font-size-xs); color: var(--color-text-secondary);">
                ${new Date(sub.current_period_start).toLocaleDateString()} &ndash; ${new Date(sub.current_period_end).toLocaleDateString()}
              </td>
              <td style="font-size: var(--font-size-xs); font-weight: 600;">
                ${new Date(sub.next_billing_date).toLocaleDateString()}
              </td>
              <td>
                <span class="badge ${sub.status === 'ACTIVE' ? 'badge-teal' : (sub.status === 'PENDING_CANCELLATION' ? 'badge-coral' : 'badge-navy')}">
                  ${sub.status}
                </span>
              </td>
              <td style="text-align: right;">
                <button class="btn btn-secondary btn-sm btn-manage-sub" data-sub-id="${sub.id}" style="padding: 4px 10px; font-size: 0.75rem;">
                  <span>Manage</span>
                </button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;

    container.querySelectorAll('.btn-manage-sub').forEach(btn => {
      btn.addEventListener('click', () => {
        const subId = parseInt(btn.dataset.subId, 10);
        openSubscriptionDetailModal(subId);
      });
    });
  }

  async function openSubscriptionDetailModal(subscriptionId) {
    const overlay = document.getElementById('dealflow-modal-overlay');
    if (!overlay) return;

    overlay.innerHTML = `
      <div class="modal-card" style="max-width: 800px; width: 90%;">
        <div class="modal-header">
          <h3>Subscription Management</h3>
          <button class="modal-close-btn" id="btn-close-sub-modal">&times;</button>
        </div>
        <div class="modal-body" id="sub-modal-body">
          <div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Loading subscription schedule...</div>
        </div>
      </div>
    `;

    overlay.classList.add('active');
    const closeModal = () => overlay.classList.remove('active');
    document.getElementById('btn-close-sub-modal').onclick = closeModal;

    try {
      const res = await global.SubscriptionsAPI.get(subscriptionId);
      if (!res.ok) {
        document.getElementById('sub-modal-body').innerHTML = `<div class="alert alert-coral">Failed to load subscription.</div>`;
        return;
      }

      const sub = res.data;
      document.getElementById('sub-modal-body').innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; background: #F8FAFC; padding: 12px 16px; border-radius: var(--radius-md);">
          <div>
            <div style="font-family: monospace; font-weight: 700; font-size: 1.1rem; color: var(--color-navy);">${sub.subscription_number}</div>
            <div style="font-size: 0.75rem; color: var(--color-text-secondary);">
              Proration Method: <strong>${sub.proration_method || 'EXACT_DAY'}</strong> &bull; Cancellation: <strong>${sub.cancellation_method || 'END_OF_PERIOD'}</strong>
            </div>
          </div>
          <div style="display: flex; gap: 8px;">
            ${sub.status === 'ACTIVE' ? `
              <button class="btn btn-secondary btn-sm" id="btn-trigger-change-qty">Change Quantity</button>
              <button class="btn btn-secondary btn-sm" id="btn-trigger-cancel-sub" style="color: var(--color-coral);">Cancel Subscription</button>
            ` : ''}
          </div>
        </div>

        <h4 style="font-size: 0.85rem; color: var(--color-navy); margin-bottom: 8px;">Scheduled Billing Pipeline</h4>
        <div style="max-height: 250px; overflow-y: auto; border: 1px solid var(--color-border); border-radius: var(--radius-sm);">
          <table class="subscription-schedule-table">
            <thead>
              <tr>
                <th>Seq</th>
                <th>Billing Date</th>
                <th>Period</th>
                <th>Amount</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${sub.schedules && sub.schedules.length > 0 ? sub.schedules.map(sch => `
                <tr>
                  <td>#${sch.sequence}</td>
                  <td>${new Date(sch.billing_date).toLocaleDateString()}</td>
                  <td>${new Date(sch.period_start).toLocaleDateString()} &ndash; ${new Date(sch.period_end).toLocaleDateString()}</td>
                  <td style="font-family: monospace; font-weight: 700;">${sub.currency} ${Number(sch.scheduled_amount).toFixed(2)}</td>
                  <td>
                    <span class="badge ${sch.status === 'INVOICED' ? 'badge-teal' : 'badge-navy'}">${sch.status}</span>
                  </td>
                </tr>
              `).join('') : `
                <tr><td colspan="5" style="text-align: center; padding: 16px;">No schedules generated yet.</td></tr>
              `}
            </tbody>
          </table>
        </div>

        <div id="sub-action-container" style="margin-top: 16px;"></div>
      `;

      // Change Quantity Trigger
      document.getElementById('btn-trigger-change-qty')?.addEventListener('click', () => {
        const actionCont = document.getElementById('sub-action-container');
        actionCont.innerHTML = `
          <div class="card" style="background: #F8FAFC; padding: 16px; border: 1px solid var(--color-border);">
            <h4 style="margin: 0 0 8px; font-size: 0.85rem; color: var(--color-navy);">Modify Subscription Quantity (Mid-Cycle Proration)</h4>
            <div style="display: flex; gap: 12px; align-items: flex-end;">
              <div>
                <label style="font-size: 0.75rem; font-weight: 600;">New Quantity</label>
                <input type="number" id="new-sub-qty-input" class="form-input" value="${Number(sub.quantity) + 1}" min="1" step="1" style="width: 100px;" />
              </div>
              <div style="flex: 1;">
                <label style="font-size: 0.75rem; font-weight: 600;">Change Reason</label>
                <input type="text" id="sub-change-reason" class="form-input" placeholder="e.g. Added 5 team seats..." />
              </div>
              <button id="btn-submit-change-qty" class="btn btn-primary btn-sm">Apply Prorated Change</button>
            </div>
          </div>
        `;

        document.getElementById('btn-submit-change-qty').onclick = async () => {
          const newQty = parseFloat(document.getElementById('new-sub-qty-input').value);
          const reason = document.getElementById('sub-change-reason').value;

          try {
            const changeRes = await global.SubscriptionsAPI.changeQuantity(subscriptionId, {
              new_quantity: newQty,
              reason: reason
            });

            if (changeRes.ok) {
              global.DealFlowUI.toast('Subscription quantity updated with backend proration.', 'teal');
              closeModal();
              await loadSubscriptions();
            } else {
              global.DealFlowUI.toast(changeRes.data?.detail || 'Failed to update quantity.', 'coral');
            }
          } catch (e) {
            global.DealFlowUI.toast('Network error updating subscription.', 'coral');
          }
        };
      });

      // Cancel Subscription Trigger
      document.getElementById('btn-trigger-cancel-sub')?.addEventListener('click', () => {
        const actionCont = document.getElementById('sub-action-container');
        actionCont.innerHTML = `
          <div class="card" style="background: #FFF5F2; padding: 16px; border: 1px solid #FECDD3;">
            <h4 style="margin: 0 0 8px; font-size: 0.85rem; color: var(--color-coral);">Cancel Subscription</h4>
            <p style="font-size: 0.75rem; color: #9F1239; margin-bottom: 8px;">
              Cancellation policy: <strong>${sub.cancellation_method}</strong>. (Access remains active until period end or immediately according to plan settings).
            </p>
            <div style="display: flex; gap: 12px; align-items: flex-end;">
              <div style="flex: 1;">
                <label style="font-size: 0.75rem; font-weight: 600;">Cancellation Reason</label>
                <input type="text" id="sub-cancel-reason" class="form-input" placeholder="e.g. Customer requested downgrade..." />
              </div>
              <button id="btn-confirm-cancel-sub" class="btn btn-primary btn-sm" style="background: var(--color-coral); border-color: var(--color-coral);">Confirm Cancellation</button>
            </div>
          </div>
        `;

        document.getElementById('btn-confirm-cancel-sub').onclick = async () => {
          const reason = document.getElementById('sub-cancel-reason').value;
          try {
            const cancelRes = await global.SubscriptionsAPI.cancel(subscriptionId, { reason });
            if (cancelRes.ok) {
              global.DealFlowUI.toast('Subscription cancellation processed.', 'navy');
              closeModal();
              await loadSubscriptions();
            } else {
              global.DealFlowUI.toast(cancelRes.data?.detail || 'Failed to cancel subscription.', 'coral');
            }
          } catch (e) {
            global.DealFlowUI.toast('Network error cancelling subscription.', 'coral');
          }
        };
      });

    } catch (e) {
      console.error(e);
    }
  }

  global.SubscriptionsView = {
    render: render
  };
})(typeof window !== 'undefined' ? window : this);
