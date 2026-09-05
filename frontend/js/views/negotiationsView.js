/**
 * DealFlow360 — Internal Negotiation Inbox View Controller
 * Allows Sales Reps and Managers to inspect customer counter-offers,
 * view side-by-side proposed terms deltas, accept and trigger recalculation/reapproval, or reject with reason.
 */
(function (global) {
  'use strict';

  let currentNegotiationQuotes = [];

  async function render(container) {
    container.innerHTML = `
      <div class="animate-fade-in">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-lg);">
          <div>
            <h1 style="font-size: var(--font-size-2xl); color: var(--color-navy); margin-bottom: 4px;">Negotiation Inbox</h1>
            <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary);">
              Review customer terms revision requests, counter-offers, and line-level adjustments.
            </p>
          </div>

          <button id="btn-refresh-inbox" class="btn btn-secondary btn-sm">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
            <span>Refresh Inbox</span>
          </button>
        </div>

        <div id="negotiation-inbox-container">
          <div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Loading negotiation requests...</div>
        </div>
      </div>
    `;

    document.getElementById('btn-refresh-inbox')?.addEventListener('click', () => loadNegotiations(container));
    await loadNegotiations(container);
  }

  async function loadNegotiations(container) {
    const inboxList = document.getElementById('negotiation-inbox-container');
    if (!inboxList) return;

    try {
      // Find quotations with status UNDER_NEGOTIATION or list all quotations with pending negotiation inbox items
      const res = await global.QuotationsAPI.list({
        status: 'UNDER_NEGOTIATION',
        limit: 50
      });

      if (!res.ok) {
        inboxList.innerHTML = `<div class="alert alert-coral">Failed to load negotiation inbox.</div>`;
        return;
      }

      currentNegotiationQuotes = res.data || [];

      if (currentNegotiationQuotes.length === 0) {
        inboxList.innerHTML = `
          <div class="card" style="text-align: center; padding: 60px 20px;">
            <div style="width: 48px; height: 48px; border-radius: 50%; background: var(--color-teal-light); color: var(--color-teal-hover); display: flex; align-items: center; justify-content: center; margin: 0 auto var(--space-md);">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
            </div>
            <h3 style="color: var(--color-navy); margin-bottom: 4px;">No Pending Negotiations</h3>
            <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary);">All customer proposals are currently reviewed or awaiting customer response.</p>
          </div>
        `;
        return;
      }

      inboxList.innerHTML = `
        <div class="negotiation-inbox-grid">
          ${currentNegotiationQuotes.map(q => {
            const custName = q.customer ? q.customer.name : `Customer #${q.customer_id}`;
            const repName = q.sales_rep ? q.sales_rep.full_name : `Sales Rep #${q.sales_rep_id}`;

            return `
              <div class="negotiation-card" data-quote-id="${q.id}">
                <div class="negotiation-card-left">
                  <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 2px;">
                    <span class="negotiation-card-num">${q.quote_number}</span>
                    <span class="badge badge-coral">Under Negotiation</span>
                  </div>
                  <div class="negotiation-card-cust">${custName} (Sales Rep: ${repName})</div>

                  <div class="negotiation-deltas-box">
                    <div class="delta-item">
                      <label>Current Net Total</label>
                      <div class="val">${q.currency} ${Number(q.net_total).toFixed(2)}</div>
                    </div>
                    <div class="delta-item">
                      <label>Payment Terms</label>
                      <div class="val">Net ${q.payment_terms_days} Days</div>
                    </div>
                    <div class="delta-item">
                      <label>Current Margin</label>
                      <div class="val" style="color: ${Number(q.margin_pct) >= 15 ? 'var(--color-teal)' : 'var(--color-coral)'};">${Number(q.margin_pct).toFixed(1)}%</div>
                    </div>
                  </div>
                </div>

                <div class="negotiation-actions-panel">
                  <button class="btn btn-primary btn-sm btn-review-negotiation" data-quote-id="${q.id}">
                    <span>Review Terms</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"></polyline></svg>
                  </button>
                  <button class="btn btn-secondary btn-sm" onclick="window.DealFlowApp.switchView('quotation-builder', { quoteId: ${q.id} });">
                    <span>Open Quote</span>
                  </button>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      `;

      inboxList.querySelectorAll('.btn-review-negotiation').forEach(btn => {
        btn.addEventListener('click', () => {
          const qId = parseInt(btn.dataset.quoteId, 10);
          openNegotiationReviewModal(qId);
        });
      });
    } catch (e) {
      console.warn('Error loading negotiations:', e);
    }
  }

  async function openNegotiationReviewModal(quotationId) {
    const modal = document.getElementById('dealflow-modal-overlay');
    if (!modal) return;

    modal.innerHTML = `
      <div class="modal-dialog animate-fade-in" style="max-width: 750px;">
        <div class="modal-header">
          <h3 class="modal-title">Review Customer Counter-Offer</h3>
          <button class="modal-close" onclick="window.DealFlowUI.closeModal();">&times;</button>
        </div>
        <div class="modal-body" id="negotiation-review-body">
          <div style="text-align: center; padding: 30px;"><span class="spinner spinner-teal"></span> Loading counter-offer details...</div>
        </div>
      </div>
    `;

    global.DealFlowUI.openModal();

    try {
      const [quoteRes, inboxRes] = await Promise.all([
        global.QuotationsAPI.get(quotationId),
        global.NegotiationAPI.getNegotiationInbox(quotationId)
      ]);

      const bodyEl = document.getElementById('negotiation-review-body');
      if (!bodyEl) return;

      if (!quoteRes.ok) {
        bodyEl.innerHTML = `<div class="alert alert-coral">Failed to load quotation.</div>`;
        return;
      }

      const q = quoteRes.data;
      const reqs = inboxRes.ok ? (inboxRes.data || []) : [];
      const pendingReq = reqs.find(r => r.status === 'PENDING') || reqs[0];

      if (!pendingReq) {
        bodyEl.innerHTML = `
          <div style="text-align: center; padding: 20px;">
            <p>No active pending negotiation requests on this quotation.</p>
            <button class="btn btn-secondary" onclick="window.DealFlowUI.closeModal();">Close</button>
          </div>
        `;
        return;
      }

      bodyEl.innerHTML = `
        <div style="margin-bottom: var(--space-md);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-family: monospace; font-size: var(--font-size-md); font-weight: 700; color: var(--color-navy);">${q.quote_number}</span>
            <span class="badge badge-coral">Counter-Offer Received</span>
          </div>
          <div style="font-size: var(--font-size-xs); color: var(--color-text-secondary);">${q.customer?.name || 'Customer'} · Requested on ${new Date(pendingReq.created_at).toLocaleString()}</div>
        </div>

        <!-- Customer Message -->
        <div class="card" style="padding: var(--space-md); background: var(--color-background); margin-bottom: var(--space-md);">
          <div style="font-size: var(--font-size-xs); font-weight: 700; color: var(--color-navy); margin-bottom: 2px;">Customer Request Note:</div>
          <div style="font-size: var(--font-size-sm); color: var(--color-text);">${pendingReq.message || 'No written comment provided.'}</div>
        </div>

        <!-- Terms Comparison Table -->
        <h4 style="font-size: var(--font-size-xs); font-weight: 700; text-transform: uppercase; color: var(--color-navy); margin-bottom: var(--space-xs);">
          Proposed Terms Changes
        </h4>
        <table class="version-diff-table" style="margin-bottom: var(--space-md);">
          <thead>
            <tr>
              <th>Metric</th>
              <th>Current Approved</th>
              <th>Customer Requested</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style="font-weight: 600;">Overall Order Discount %</td>
              <td>${Number(q.order_discount_pct || 0).toFixed(1)}%</td>
              <td style="font-weight: 700; color: var(--color-coral);">${Number(pendingReq.requested_order_discount_pct !== null ? pendingReq.requested_order_discount_pct : q.order_discount_pct || 0).toFixed(1)}%</td>
            </tr>
            <tr>
              <td style="font-weight: 600;">Payment Terms</td>
              <td>Net ${q.payment_terms_days} Days</td>
              <td style="font-weight: 700; color: var(--color-coral);">Net ${pendingReq.requested_payment_terms_days !== null ? pendingReq.requested_payment_terms_days : q.payment_terms_days} Days</td>
            </tr>
          </tbody>
        </table>

        <!-- Actions Panel -->
        <div class="card" style="padding: var(--space-md); border: 1px solid var(--color-border); background: var(--color-surface); margin-top: var(--space-lg);">
          <div style="margin-bottom: var(--space-sm);">
            <label class="form-label" for="rejection-reason-text">Resolution / Rejection Reason (If rejecting)</label>
            <input type="text" id="rejection-reason-text" class="form-input" placeholder="e.g. Requested discount exceeds maximum policy boundary." />
          </div>

          <div style="display: flex; justify-content: flex-end; gap: var(--space-sm);">
            <button id="btn-reject-negotiation" class="btn btn-secondary btn-sm" style="color: var(--color-coral);">
              <span>Reject Request</span>
            </button>
            <button id="btn-accept-negotiation" class="btn btn-primary btn-sm">
              <span>Accept & Recalculate Quote</span>
            </button>
          </div>
        </div>
      `;

      // Accept Handler
      document.getElementById('btn-accept-negotiation')?.addEventListener('click', async () => {
        if (!confirm('Accept these customer counter-offer terms? A revised quotation version will be generated.')) {
          return;
        }

        try {
          const res = await global.NegotiationAPI.acceptCounterOffer(quotationId, pendingReq.id);
          global.DealFlowUI.closeModal();

          if (res.ok) {
            const revisedQuote = res.data;
            if (revisedQuote.status === 'REAPPROVAL_REQUIRED' || revisedQuote.status === 'PENDING_MANAGER_APPROVAL') {
              alert('Counter-offer accepted!\n\nNotice: The revised commercial terms exceed standard policy thresholds and have been routed for internal approval.');
            } else {
              global.DealFlowUI.toast('Counter-offer accepted! Revised quotation generated.', 'teal');
            }
            global.DealFlowApp.switchView('quotation-builder', { quoteId: quotationId });
          } else {
            global.DealFlowUI.toast(res.data?.detail || 'Failed to accept counter-offer.', 'coral');
          }
        } catch (err) {
          global.DealFlowUI.toast('Network error accepting counter-offer.', 'coral');
        }
      });

      // Reject Handler
      document.getElementById('btn-reject-negotiation')?.addEventListener('click', async () => {
        const reason = document.getElementById('rejection-reason-text')?.value.trim();
        if (!reason) {
          alert('Please enter a reason explaining why the request is rejected.');
          document.getElementById('rejection-reason-text')?.focus();
          return;
        }

        if (!confirm('Reject this customer counter-offer?')) return;

        try {
          const res = await global.NegotiationAPI.rejectCounterOffer(quotationId, pendingReq.id, reason);
          global.DealFlowUI.closeModal();

          if (res.ok) {
            global.DealFlowUI.toast('Customer counter-offer rejected.', 'coral');
            await loadNegotiations(document.getElementById('main-view-container'));
          } else {
            global.DealFlowUI.toast(res.data?.detail || 'Failed to reject counter-offer.', 'coral');
          }
        } catch (err) {
          global.DealFlowUI.toast('Network error rejecting counter-offer.', 'coral');
        }
      });
    } catch (err) {
      console.warn('Error loading negotiation review modal:', err);
    }
  }

  global.NegotiationsView = {
    render: render
  };
})(typeof window !== 'undefined' ? window : this);
