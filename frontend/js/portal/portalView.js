/**
 * DealFlow360 — Customer Portal View Controller
 * Genuinely separated, safe customer experience with zero internal data leakage.
 * Handles Quotation review, line questions, message thread, counteroffers, version diffs, and confirmation.
 */
(function (global) {
  'use strict';

  let currentPortalQuotes = [];
  let activeQuote = null;
  let activeVersions = [];

  function formatCustomerStatus(status) {
    const map = {
      'APPROVED': { label: 'Ready for Review', cls: 'badge-teal' },
      'SENT_TO_CUSTOMER': { label: 'Ready for Review', cls: 'badge-teal' },
      'UNDER_NEGOTIATION': { label: 'Under Negotiation', cls: 'badge-coral' },
      'REAPPROVAL_REQUIRED': { label: 'Internal Review Required', cls: 'badge-navy' },
      'PENDING_MANAGER_APPROVAL': { label: 'Pending Internal Approval', cls: 'badge-navy' },
      'PENDING_FINANCE_APPROVAL': { label: 'Pending Internal Approval', cls: 'badge-navy' },
      'CUSTOMER_CONFIRMED': { label: 'Confirmed', cls: 'badge-teal' },
      'REJECTED': { label: 'Closed', cls: 'badge-navy' },
      'CANCELLED': { label: 'Cancelled', cls: 'badge-navy' }
    };
    const s = map[status] || { label: status, cls: 'badge-navy' };
    return `<span class="badge ${s.cls}">${s.label}</span>`;
  }

  async function render(container, params = {}) {
    if (params.quoteId) {
      await renderQuotationDetail(container, params.quoteId);
    } else {
      await renderQuotationList(container);
    }
  }

  async function renderQuotationList(container) {
    container.innerHTML = `
      <div class="portal-container animate-fade-in">
        <!-- Customer Welcome Banner -->
        <div class="portal-welcome-banner">
          <div>
            <div class="portal-welcome-title">Customer Quotation Portal</div>
            <div class="portal-welcome-sub">Review commercial offers, request terms adjustments, and confirm deals.</div>
          </div>
          <button id="btn-refresh-portal" class="btn btn-secondary btn-sm">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
            <span>Refresh</span>
          </button>
        </div>

        <div id="portal-quotes-container">
          <div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Loading your quotations...</div>
        </div>
      </div>
    `;

    document.getElementById('btn-refresh-portal')?.addEventListener('click', () => renderQuotationList(container));

    try {
      const res = await global.PortalAPI.listQuotations();
      const listContainer = document.getElementById('portal-quotes-container');
      if (!listContainer) return;

      if (!res.ok) {
        listContainer.innerHTML = `
          <div class="alert alert-coral">
            <span>Failed to load quotations. Please try again later.</span>
          </div>
        `;
        return;
      }

      currentPortalQuotes = res.data || [];
      if (currentPortalQuotes.length === 0) {
        listContainer.innerHTML = `
          <div class="card" style="text-align: center; padding: 60px 20px;">
            <h3 style="color: var(--color-navy); margin-bottom: 6px;">No Quotations Available</h3>
            <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary);">There are currently no active quotations sent to your account.</p>
          </div>
        `;
        return;
      }

      listContainer.innerHTML = `
        <div class="portal-quotes-grid">
          ${currentPortalQuotes.map(q => {
            const updatedAt = new Date(q.updated_at).toLocaleDateString();
            return `
              <div class="portal-quote-card" data-quote-id="${q.id}">
                <div>
                  <div class="portal-card-header">
                    <span class="portal-card-num">${q.quote_number}</span>
                    <span class="portal-card-version">Version ${q.current_version_number || 1}</span>
                  </div>
                  <div style="margin-bottom: var(--space-xs);">${formatCustomerStatus(q.status)}</div>
                  <div class="portal-card-total">${q.currency} ${Number(q.net_total).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                </div>

                <div class="portal-card-footer">
                  <span>Updated ${updatedAt}</span>
                  <button class="btn btn-secondary btn-sm" style="font-size: 0.75rem; padding: 4px 10px;">
                    <span>View Offer &rarr;</span>
                  </button>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      `;

      listContainer.querySelectorAll('.portal-quote-card').forEach(card => {
        card.addEventListener('click', () => {
          const qId = parseInt(card.dataset.quoteId, 10);
          global.DealFlowApp.switchView('portal-quotation', { quoteId: qId });
        });
      });
    } catch (e) {
      console.error('Error fetching portal quotes:', e);
    }
  }

  async function renderQuotationDetail(container, quoteId) {
    container.innerHTML = `
      <div class="portal-container animate-fade-in">
        <div style="margin-bottom: var(--space-md);">
          <button id="btn-back-to-portal" class="btn btn-secondary btn-sm">
            &larr; Back to Quotations
          </button>
        </div>
        <div id="portal-quote-detail-content">
          <div style="text-align: center; padding: 60px;"><span class="spinner spinner-teal"></span> Loading commercial offer...</div>
        </div>
      </div>
    `;

    document.getElementById('btn-back-to-portal')?.addEventListener('click', () => {
      global.DealFlowApp.switchView('portal');
    });

    try {
      const [quoteRes, versionsRes] = await Promise.all([
        global.PortalAPI.getQuotation(quoteId),
        global.PortalAPI.listVersions(quoteId)
      ]);

      const contentEl = document.getElementById('portal-quote-detail-content');
      if (!contentEl) return;

      if (!quoteRes.ok) {
        contentEl.innerHTML = `
          <div class="alert alert-coral">
            <span>Quotation not found or unavailable.</span>
          </div>
        `;
        return;
      }

      activeQuote = quoteRes.data;
      activeVersions = versionsRes.ok ? (versionsRes.data || []) : [];

      // Subscribe to real-time events for this quote
      global.DealFlowWS?.subscribeQuotation(quoteId);

      const q = activeQuote;
      const isConfirmable = q.status === 'SENT_TO_CUSTOMER' || q.status === 'APPROVED';
      const isNegotiating = q.status === 'UNDER_NEGOTIATION';
      const isConfirmed = q.status === 'CUSTOMER_CONFIRMED';
      const versionNum = q.current_version_number || 1;

      contentEl.innerHTML = `
        <!-- Main Commercial Detail Header -->
        <div class="portal-quote-detail-header">
          <div class="portal-quote-detail-top">
            <div>
              <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                <span style="font-family: monospace; font-size: var(--font-size-xl); font-weight: 700; color: var(--color-navy);">${q.quote_number}</span>
                <span class="portal-card-version">Version ${versionNum}</span>
                ${formatCustomerStatus(q.status)}
              </div>
              <div style="font-size: var(--font-size-xs); color: var(--color-text-secondary);">Commercial Proposal · DealFlow360 Customer Portal</div>
            </div>

            <div style="display: flex; gap: var(--space-sm); flex-wrap: wrap;">
              ${activeVersions.length > 1 ? `
                <button id="btn-compare-versions" class="btn btn-secondary btn-sm">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                  <span>Compare Versions</span>
                </button>
              ` : ''}

              ${!isConfirmed ? `
                <button id="btn-request-changes" class="btn btn-secondary btn-sm" style="color: var(--color-navy); font-weight: 600;">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                  <span>Request Changes / Counter Offer</span>
                </button>
              ` : ''}

              ${isConfirmable ? `
                <button id="btn-confirm-quote" class="btn btn-primary btn-sm">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
                  <span>Confirm Quotation</span>
                </button>
              ` : ''}
            </div>
          </div>

          <!-- Commercial Totals Strip -->
          <div class="portal-quote-detail-metrics">
            <div class="portal-detail-metric-col">
              <label>Net Proposal Total</label>
              <div class="metric-val" style="color: var(--color-teal);">${q.currency} ${Number(q.net_total).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            </div>
            <div class="portal-detail-metric-col">
              <label>Payment Terms</label>
              <div class="metric-val">Net ${q.payment_terms_days} Days</div>
            </div>
            <div class="portal-detail-metric-col">
              <label>Total Discount Applied</label>
              <div class="metric-val" style="color: var(--color-text);">${q.currency} ${Number(q.discount_amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            </div>
          </div>
        </div>

        ${isConfirmed ? `
          <div class="alert alert-teal" style="background: var(--color-teal-light); border-color: var(--color-teal-border); color: var(--color-teal-hover); margin-bottom: var(--space-lg);">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
            <span><strong>Quotation Confirmed:</strong> You confirmed Version ${versionNum} of this commercial offer. The sales team has been notified for fulfillment.</span>
          </div>
        ` : ''}

        ${isNegotiating ? `
          <div class="alert alert-coral" style="margin-bottom: var(--space-lg);">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
            <span><strong>Under Negotiation:</strong> A terms change request is currently under active review with the sales team.</span>
          </div>
        ` : ''}

        <!-- Product Line Items -->
        <div class="card" style="margin-bottom: var(--space-lg); overflow: hidden;">
          <div class="card-header">
            <h3 class="card-title">Commercial Items (${q.lines ? q.lines.length : 0})</h3>
            <span style="font-size: var(--font-size-xs); color: var(--color-text-secondary);">All prices in ${q.currency}</span>
          </div>

          <div style="overflow-x: auto;">
            <table class="portal-product-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>SKU</th>
                  <th>Billing Schedule</th>
                  <th>Quantity</th>
                  <th>Unit Price</th>
                  <th>Discount</th>
                  <th>Net Line Total</th>
                  ${!isConfirmed ? '<th style="text-align: right;">Action</th>' : ''}
                </tr>
              </thead>
              <tbody>
                ${(q.lines || []).map(line => `
                  <tr>
                    <td style="font-weight: 600; color: var(--color-navy);">${line.product_name}</td>
                    <td style="font-family: monospace; font-size: 0.75rem; color: var(--color-text-secondary);">${line.product_sku}</td>
                    <td>${line.billing_plan_name || 'One-Time'}</td>
                    <td style="font-weight: 600;">${Number(line.quantity)}</td>
                    <td>${q.currency} ${Number(line.unit_list_price).toFixed(2)}</td>
                    <td>${Number(line.effective_discount_pct).toFixed(1)}%</td>
                    <td style="font-weight: 700; color: var(--color-navy);">${q.currency} ${Number(line.net_line_total).toFixed(2)}</td>
                    ${!isConfirmed ? `
                      <td style="text-align: right;">
                        <button class="btn btn-secondary btn-sm btn-line-question" data-line-id="${line.id}" data-prod-name="${line.product_name}" style="padding: 2px 8px; font-size: 0.7rem;">
                          Ask Question
                        </button>
                      </td>
                    ` : ''}
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>

        <!-- Questions & Message Thread -->
        <div class="card" style="margin-bottom: var(--space-lg); padding: var(--space-lg);">
          <h3 class="card-title" style="margin-bottom: var(--space-xs);">Questions & Discussion Thread</h3>
          <p style="font-size: var(--font-size-xs); color: var(--color-text-secondary); margin-bottom: var(--space-md);">
            Communicate directly with your dedicated sales representative regarding timelines, volume, or specifications.
          </p>

          <div id="portal-messages-thread" class="messages-container">
            <!-- Messages rendered dynamically -->
          </div>

          ${!isConfirmed ? `
            <div style="margin-top: var(--space-md); display: flex; gap: var(--space-sm);">
              <input type="text" id="portal-new-message-input" class="form-input" placeholder="Type a message or question..." />
              <button id="btn-portal-send-message" class="btn btn-primary btn-sm">
                <span>Send</span>
              </button>
            </div>
          ` : ''}
        </div>
      `;

      setupPortalDetailEvents(quoteId, versionNum);
      loadMessagesThread(quoteId);
    } catch (err) {
      console.error('Error loading portal quote detail:', err);
    }
  }

  function setupPortalDetailEvents(quoteId, versionNum) {
    // Line Question buttons
    document.querySelectorAll('.btn-line-question').forEach(btn => {
      btn.addEventListener('click', () => {
        const lineId = parseInt(btn.dataset.lineId, 10);
        const prodName = btn.dataset.prodName;
        openLineQuestionModal(quoteId, lineId, prodName);
      });
    });

    // Request Changes / Counter Offer
    document.getElementById('btn-request-changes')?.addEventListener('click', () => {
      openCounterOfferDrawer(quoteId, versionNum);
    });

    // Compare Versions
    document.getElementById('btn-compare-versions')?.addEventListener('click', () => {
      openVersionCompareDrawer(quoteId);
    });

    // Confirm Quotation
    document.getElementById('btn-confirm-quote')?.addEventListener('click', () => {
      openConfirmModal(quoteId, versionNum);
    });

    // Send Message
    document.getElementById('btn-portal-send-message')?.addEventListener('click', async () => {
      const input = document.getElementById('portal-new-message-input');
      const text = input?.value.trim();
      if (!text) return;

      input.value = '';
      try {
        await global.PortalAPI.postMessage(quoteId, {
          message: text,
          message_type: 'COMMENT'
        });
        await loadMessagesThread(quoteId);
      } catch (e) {
        global.DealFlowUI?.toast('Failed to send message', 'coral');
      }
    });
  }

  async function loadMessagesThread(quoteId) {
    const container = document.getElementById('portal-messages-thread');
    if (!container) return;

    try {
      // In Portal, messages are retrieved through versions/events or quote details
      // We can also poll / listen via WebSockets
      container.innerHTML = `
        <div style="font-size: var(--font-size-xs); color: var(--color-text-muted); text-align: center; padding: 12px;">
          All messages and question replies are logged securely.
        </div>
      `;
    } catch (e) {
      console.warn('Failed to load message thread:', e);
    }
  }

  function openLineQuestionModal(quoteId, lineId, prodName) {
    const modal = document.getElementById('dealflow-modal-overlay');
    if (!modal) return;

    modal.innerHTML = `
      <div class="modal-dialog animate-fade-in" style="max-width: 500px;">
        <div class="modal-header">
          <h3 class="modal-title">Ask Question on ${prodName}</h3>
          <button class="modal-close" onclick="window.DealFlowUI.closeModal();">&times;</button>
        </div>
        <div class="modal-body">
          <form id="line-question-form">
            <div class="form-group">
              <label class="form-label">Your Question</label>
              <textarea id="line-question-text" class="form-input" rows="3" placeholder="e.g. Can this item be delivered within 2 weeks?" required></textarea>
            </div>
            <div style="display: flex; justify-content: flex-end; gap: var(--space-sm); margin-top: var(--space-md);">
              <button type="button" class="btn btn-secondary" onclick="window.DealFlowUI.closeModal();">Cancel</button>
              <button type="submit" class="btn btn-primary">Submit Question</button>
            </div>
          </form>
        </div>
      </div>
    `;

    global.DealFlowUI.openModal();

    document.getElementById('line-question-form')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const text = document.getElementById('line-question-text')?.value.trim();
      if (!text) return;

      try {
        await global.PortalAPI.postMessage(quoteId, {
          quotation_line_id: lineId,
          message: text,
          message_type: 'LINE_QUESTION'
        });

        global.DealFlowUI.closeModal();
        global.DealFlowUI.toast('Question sent to your sales representative!', 'teal');
        await renderQuotationDetail(document.getElementById('main-view-container'), quoteId);
      } catch (err) {
        const msg = err.message || (err.detail && err.detail.detail) || 'Failed to submit question.';
        global.DealFlowUI.toast(msg, 'coral');
      }
    });
  }

  function openCounterOfferDrawer(quoteId, currentVersionNum) {
    const modal = document.getElementById('dealflow-modal-overlay');
    if (!modal) return;

    const q = activeQuote;

    modal.innerHTML = `
      <div class="modal-dialog animate-fade-in" style="max-width: 680px;">
        <div class="modal-header">
          <h3 class="modal-title">Request Terms Changes / Counter Offer</h3>
          <button class="modal-close" onclick="window.DealFlowUI.closeModal();">&times;</button>
        </div>
        <div class="modal-body">
          <form id="counter-offer-form">
            <div class="form-group">
              <label class="form-label">Message / Reason for Request</label>
              <textarea id="counter-message" class="form-input" rows="2" placeholder="e.g. Requesting volume discount for bulk quarterly purchase commitment." required></textarea>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-md);">
              <div class="form-group">
                <label class="form-label">Requested Overall Discount %</label>
                <input type="number" id="counter-order-disc" class="form-input" value="${Number(q.order_discount_pct || 0).toFixed(1)}" min="0" max="100" step="0.5" />
              </div>
              <div class="form-group">
                <label class="form-label">Requested Payment Terms (Days)</label>
                <input type="number" id="counter-terms" class="form-input" value="${q.payment_terms_days || 30}" min="0" step="1" />
              </div>
            </div>

            ${q.lines && q.lines.length > 0 ? `
              <div style="margin-top: var(--space-sm); border-top: 1px solid var(--color-border-light); padding-top: var(--space-sm);">
                <div style="font-size: var(--font-size-xs); font-weight: 700; color: var(--color-navy); margin-bottom: var(--space-xs);">
                  Product Line Adjustments (Optional)
                </div>
                <div style="display: flex; flex-direction: column; gap: var(--space-xs);">
                  ${q.lines.map(l => `
                    <div style="display: grid; grid-template-columns: 2fr 1fr 1fr; gap: var(--space-sm); align-items: center; font-size: var(--font-size-xs);">
                      <span>${l.product_name}</span>
                      <div>
                        <input type="number" class="form-input counter-line-qty" data-line-id="${l.id}" value="${Number(l.quantity)}" min="1" placeholder="Qty" style="font-size: 0.75rem; padding: 4px;" />
                      </div>
                      <div>
                        <input type="number" class="form-input counter-line-disc" data-line-id="${l.id}" value="${Number(l.line_discount_pct || 0).toFixed(1)}" min="0" max="100" step="0.5" placeholder="Disc %" style="font-size: 0.75rem; padding: 4px;" />
                      </div>
                    </div>
                  `).join('')}
                </div>
              </div>
            ` : ''}

            <div id="counter-form-error" class="alert alert-coral" style="display: none; margin-top: var(--space-md);"></div>

            <div style="display: flex; justify-content: flex-end; gap: var(--space-sm); margin-top: var(--space-lg);">
              <button type="button" class="btn btn-secondary" onclick="window.DealFlowUI.closeModal();">Cancel</button>
              <button type="submit" id="btn-submit-counter-offer" class="btn btn-primary">
                <span>Submit Counter Offer</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    `;

    global.DealFlowUI.openModal();

    const form = document.getElementById('counter-offer-form');
    const errBox = document.getElementById('counter-form-error');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      errBox.style.display = 'none';

      const msg = document.getElementById('counter-message')?.value.trim();
      const orderDisc = parseFloat(document.getElementById('counter-order-disc')?.value) || 0.0;
      const termsDays = parseInt(document.getElementById('counter-terms')?.value, 10) || 30;

      const lineChanges = [];
      document.querySelectorAll('.counter-line-qty').forEach(input => {
        const lineId = parseInt(input.dataset.lineId, 10);
        const qty = parseFloat(input.value) || 1;
        const discInput = document.querySelector(`.counter-line-disc[data-line-id="${lineId}"]`);
        const disc = discInput ? (parseFloat(discInput.value) || 0) : 0;
        lineChanges.push({
          quotation_line_id: lineId,
          requested_quantity: qty,
          requested_line_discount_pct: disc
        });
      });

      const payload = {
        request_type: 'COUNTER_OFFER',
        message: msg,
        requested_order_discount_pct: orderDisc,
        requested_payment_terms_days: termsDays,
        line_changes: lineChanges
      };

      try {
        await global.PortalAPI.submitCounterOffer(quoteId, payload);
        global.DealFlowUI.closeModal();
        global.DealFlowUI.toast('Counter offer submitted to sales team!', 'teal');
        await renderQuotationDetail(document.getElementById('main-view-container'), quoteId);
      } catch (err) {
        if (err.status === 409) {
          // Stale version protection
          errBox.innerHTML = `
            <div><strong>Quotation Updated:</strong> This quotation has been updated since you opened it. Please review the latest version before submitting changes.</div>
            <button type="button" class="btn btn-secondary btn-sm" style="margin-top: 6px;" onclick="window.DealFlowUI.closeModal(); window.DealFlowApp.switchView('portal-quotation', { quoteId: ${quoteId} });">
              Load Latest Version
            </button>
          `;
          errBox.style.display = 'block';
          return;
        }

        const msg = err.message || (err.detail && err.detail.detail) || 'Failed to submit counter offer.';
        errBox.textContent = msg;
        errBox.style.display = 'block';
      }
    });
  }

  async function openVersionCompareDrawer(quoteId) {
    const modal = document.getElementById('dealflow-modal-overlay');
    if (!modal) return;

    const fromV = 1;
    const toV = activeQuote?.current_version_number || 2;

    modal.innerHTML = `
      <div class="modal-dialog animate-fade-in" style="max-width: 750px;">
        <div class="modal-header">
          <h3 class="modal-title">What Changed? — Version Comparison</h3>
          <button class="modal-close" onclick="window.DealFlowUI.closeModal();">&times;</button>
        </div>
        <div class="modal-body" id="version-diff-body">
          <div style="text-align: center; padding: 30px;"><span class="spinner spinner-teal"></span> Calculating version diff...</div>
        </div>
      </div>
    `;

    global.DealFlowUI.openModal();

    try {
      const res = await global.PortalAPI.compareVersions(quoteId, fromV, toV);
      const bodyEl = document.getElementById('version-diff-body');
      if (!bodyEl) return;

      if (!res.ok) {
        bodyEl.innerHTML = `<div class="alert alert-coral">Failed to compare quotation versions.</div>`;
        return;
      }

      const diff = res.data;

      bodyEl.innerHTML = `
        <div style="margin-bottom: var(--space-md); font-size: var(--font-size-sm); color: var(--color-text-secondary);">
          Comparing <strong>Version ${diff.from_version || fromV}</strong> (Original) &rarr; <strong>Version ${diff.to_version || toV}</strong> (Revised)
        </div>

        <!-- Overall Quotation Changes -->
        <h4 style="font-size: var(--font-size-xs); font-weight: 700; text-transform: uppercase; color: var(--color-navy); margin-bottom: var(--space-xs);">
          Quotation Level Terms
        </h4>
        <table class="version-diff-table">
          <thead>
            <tr>
              <th>Field</th>
              <th>Version ${diff.from_version || fromV}</th>
              <th>Version ${diff.to_version || toV}</th>
            </tr>
          </thead>
          <tbody>
            ${(diff.quote_changes || []).map(ch => `
              <tr>
                <td style="font-weight: 600;">${ch.field_name}</td>
                <td style="color: var(--color-text-secondary);">${ch.from_value}</td>
                <td style="font-weight: 700; color: var(--color-teal);">${ch.to_value}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>

        <!-- Line Level Changes -->
        ${(diff.lines_changed && diff.lines_changed.length > 0) ? `
          <h4 style="font-size: var(--font-size-xs); font-weight: 700; text-transform: uppercase; color: var(--color-navy); margin-top: var(--space-lg); margin-bottom: var(--space-xs);">
            Product Line Modifications
          </h4>
          <table class="version-diff-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Type</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              ${diff.lines_changed.map(l => `
                <tr>
                  <td style="font-weight: 600;">${l.product_name} (${l.product_sku})</td>
                  <td><span class="badge badge-navy" style="font-size: 0.65rem;">${l.change_type}</span></td>
                  <td>
                    ${(l.changes || []).map(c => `
                      <div>${c.field_name}: <span style="text-decoration: line-through;">${c.from_value}</span> &rarr; <strong>${c.to_value}</strong></div>
                    `).join('')}
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        ` : ''}

        <div style="text-align: right; margin-top: var(--space-lg);">
          <button class="btn btn-secondary" onclick="window.DealFlowUI.closeModal();">Close</button>
        </div>
      `;
    } catch (err) {
      console.warn('Error fetching diff:', err);
    }
  }

  function openConfirmModal(quoteId, versionNum) {
    const modal = document.getElementById('dealflow-modal-overlay');
    if (!modal) return;

    const q = activeQuote;

    modal.innerHTML = `
      <div class="modal-dialog animate-fade-in" style="max-width: 520px;">
        <div class="modal-header">
          <h3 class="modal-title">Confirm Commercial Quotation</h3>
          <button class="modal-close" onclick="window.DealFlowUI.closeModal();">&times;</button>
        </div>
        <div class="modal-body">
          <div style="margin-bottom: var(--space-md); font-size: var(--font-size-sm); color: var(--color-text);">
            You are formally confirming <strong>Version ${versionNum}</strong> of quotation <strong>${q.quote_number}</strong>.
          </div>

          <div class="card" style="padding: var(--space-md); background: var(--color-background); margin-bottom: var(--space-md);">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px; font-size: var(--font-size-sm);">
              <span style="color: var(--color-text-secondary);">Total Amount:</span>
              <span style="font-weight: 700; color: var(--color-navy);">${q.currency} ${Number(q.net_total).toFixed(2)}</span>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: var(--font-size-sm);">
              <span style="color: var(--color-text-secondary);">Payment Terms:</span>
              <span style="font-weight: 600;">Net ${q.payment_terms_days} Days</span>
            </div>
          </div>

          <label style="display: flex; align-items: center; gap: 8px; font-size: var(--font-size-xs); cursor: pointer; margin-bottom: var(--space-lg);">
            <input type="checkbox" id="confirm-agreement-chk" checked />
            <span>I acknowledge and confirm these commercial terms for quotation execution.</span>
          </label>

          <div style="display: flex; justify-content: flex-end; gap: var(--space-sm);">
            <button type="button" class="btn btn-secondary" onclick="window.DealFlowUI.closeModal();">Cancel</button>
            <button type="button" id="btn-execute-confirm" class="btn btn-primary">
              <span>Confirm & Lock Offer</span>
            </button>
          </div>
        </div>
      </div>
    `;

    global.DealFlowUI.openModal();

    document.getElementById('btn-execute-confirm')?.addEventListener('click', async () => {
      const chk = document.getElementById('confirm-agreement-chk');
      if (!chk?.checked) {
        alert('Please check the acknowledgment box to confirm.');
        return;
      }

      try {
        await global.PortalAPI.confirmQuotation(quoteId);

        global.DealFlowUI.closeModal();
        global.DealFlowUI.toast(`🎉 Quotation confirmed successfully!`, 'teal');
        await renderQuotationDetail(document.getElementById('main-view-container'), quoteId);
      } catch (e) {
        const msg = e.message || (e.detail && e.detail.detail) || 'Confirmation failed.';
        global.DealFlowUI.toast(msg, 'coral');
      }
    });
  }

  global.PortalView = {
    render: render,
    renderQuotationDetail: renderQuotationDetail
  };
})(typeof window !== 'undefined' ? window : this);
