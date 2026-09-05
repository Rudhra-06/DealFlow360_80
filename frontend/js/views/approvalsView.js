/**
 * DealFlow360 — Phase 3 Approval Queue & Commercial Governance View
 * Allows Sales Managers and Finance Operations to review pending quotations,
 * inspect explainable policy trigger causes, and execute Approve / Reject / Return decisions.
 */
(function (global) {
  'use strict';

  let currentPendingQuotes = [];
  let userRole = 'ADMIN';

  async function render(container) {
    const user = global.DealFlowAuth?.getCurrentUser();
    userRole = user?.role?.name || 'ADMIN';

    container.innerHTML = `
      <div class="animate-fade-in">
        <div class="approval-queue-header">
          <div>
            <h1 style="font-size: var(--font-size-2xl); color: var(--color-navy); margin-bottom: 4px;">Approval Queue</h1>
            <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary);">
              Review pending commercial deals, evaluate policy triggers, and authorize approval routing.
            </p>
          </div>

          <div style="display: flex; gap: var(--space-sm);">
            <button id="btn-refresh-approvals" class="btn btn-secondary btn-sm">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
              <span>Refresh Queue</span>
            </button>
          </div>
        </div>

        <!-- Role Context Banner -->
        <div class="card" style="padding: var(--space-md); margin-bottom: var(--space-lg); background: var(--color-background); display: flex; justify-content: space-between; align-items: center;">
          <div style="font-size: var(--font-size-xs); color: var(--color-text-secondary);">
            Logged in as: <strong style="color: var(--color-navy);">${global.DealFlowNav?.formatRole(userRole)}</strong> | Authority: 
            <span class="badge badge-navy" style="font-size: 0.6875rem;">
              ${userRole === 'SALES_MANAGER' ? 'Manager Approval' : (userRole === 'FINANCE_OPERATIONS' ? 'Finance Approval' : 'Full Governance')}
            </span>
          </div>

          <div style="display: flex; align-items: center; gap: var(--space-xs);">
            <label style="font-size: var(--font-size-xs); color: var(--color-text-secondary);">Filter Queue:</label>
            <select id="approval-status-filter" class="form-input" style="font-size: var(--font-size-xs); padding: 4px 8px; width: 220px;">
              <option value="">All Pending Approvals</option>
              <option value="PENDING_MANAGER_APPROVAL" ${userRole === 'SALES_MANAGER' ? 'selected' : ''}>Pending Manager Approval</option>
              <option value="PENDING_FINANCE_APPROVAL" ${userRole === 'FINANCE_OPERATIONS' ? 'selected' : ''}>Pending Finance Approval</option>
              <option value="APPROVED">Recently Approved</option>
              <option value="RETURNED_FOR_REVISION">Returned for Revision</option>
              <option value="REJECTED">Rejected</option>
            </select>
          </div>
        </div>

        <!-- Approvals List Container -->
        <div id="approvals-queue-container">
          <div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Loading approval queue...</div>
        </div>
      </div>
    `;

    setupEvents(container);
    await loadApprovalQueue();
  }

  function setupEvents(container) {
    container.querySelector('#btn-refresh-approvals')?.addEventListener('click', loadApprovalQueue);
    container.querySelector('#approval-status-filter')?.addEventListener('change', loadApprovalQueue);
  }

  async function loadApprovalQueue() {
    const container = document.getElementById('approvals-queue-container');
    if (!container) return;

    container.innerHTML = `<div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Querying pending quotations...</div>`;

    const filterStatus = document.getElementById('approval-status-filter')?.value || '';

    try {
      let statusParam = filterStatus || undefined;
      const res = await global.QuotationsAPI.list({
        status: statusParam,
        limit: 100
      });

      if (!res.ok) {
        container.innerHTML = `
          <div class="alert alert-coral">
            <span>Failed to load approval queue: ${res.data?.detail || res.error || 'Server error'}</span>
          </div>
        `;
        return;
      }

      let quotes = res.data || [];
      if (!filterStatus) {
        // Default to pending approvals first
        quotes = quotes.filter(q => q.status === 'PENDING_MANAGER_APPROVAL' || q.status === 'PENDING_FINANCE_APPROVAL');
      }

      currentPendingQuotes = quotes;
      renderQueueList(container);
    } catch (e) {
      container.innerHTML = `<div class="alert alert-coral">Error connecting to Approval service.</div>`;
    }
  }

  function renderQueueList(container) {
    if (currentPendingQuotes.length === 0) {
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 60px 20px;">
          <div style="width: 48px; height: 48px; border-radius: var(--radius-full); background: var(--color-teal-light); color: var(--color-teal-hover); display: flex; align-items: center; justify-content: center; margin: 0 auto var(--space-md);">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
          </div>
          <h3 style="font-size: var(--font-size-md); color: var(--color-navy); margin-bottom: 4px;">No quotations waiting for approval</h3>
          <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary);">All submitted deals are currently reviewed or within standard policy thresholds.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: var(--space-md);">
        ${currentPendingQuotes.map(q => {
          const custName = q.customer ? q.customer.name : `Customer #${q.customer_id}`;
          const repName = q.sales_rep ? q.sales_rep.full_name : `User #${q.sales_rep_id}`;
          const marginVal = Number(q.margin_pct || 0);
          const marginColor = marginVal >= 15 ? 'var(--color-teal)' : (marginVal >= 0 ? '#B45309' : 'var(--color-coral)');

          return `
            <div class="approval-card-wrapper">
              <div class="approval-card-top">
                <div style="display: flex; align-items: center; gap: var(--space-md);">
                  <span style="font-family: monospace; font-size: var(--font-size-md); font-weight: 700; color: var(--color-navy);">${q.quote_number}</span>
                  ${formatStatusBadge(q.status)}
                  <span class="badge ${q.risk_level === 'GREEN' ? 'badge-teal' : 'badge-coral'}">Risk: ${q.risk_level} (${Number(q.blended_risk_score).toFixed(1)})</span>
                </div>

                <div>
                  <button class="btn btn-primary btn-sm btn-review-quote" data-quote-id="${q.id}">
                    <span>Review & Decide</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"></polyline></svg>
                  </button>
                </div>
              </div>

              <div class="approval-card-body">
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--space-md);">
                  <div>
                    <div style="font-size: var(--font-size-xs); color: var(--color-text-secondary);">Customer</div>
                    <div style="font-weight: 600; color: var(--color-navy);">${custName}</div>
                  </div>
                  <div>
                    <div style="font-size: var(--font-size-xs); color: var(--color-text-secondary);">Sales Rep</div>
                    <div style="font-weight: 600; color: var(--color-text);">${repName}</div>
                  </div>
                  <div>
                    <div style="font-size: var(--font-size-xs); color: var(--color-text-secondary);">Net Total</div>
                    <div style="font-weight: 700; font-size: var(--font-size-md); color: var(--color-navy);">${q.currency} ${Number(q.net_total).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                  </div>
                  <div>
                    <div style="font-size: var(--font-size-xs); color: var(--color-text-secondary);">Margin %</div>
                    <div style="font-weight: 700; font-size: var(--font-size-md); color: ${marginColor};">${marginVal.toFixed(1)}%</div>
                  </div>
                </div>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;

    container.querySelectorAll('.btn-review-quote').forEach(btn => {
      btn.addEventListener('click', () => {
        const qId = parseInt(btn.dataset.quoteId, 10);
        openApprovalDetailModal(qId);
      });
    });
  }

  async function openApprovalDetailModal(quotationId) {
    const modal = document.getElementById('dealflow-modal-overlay');
    if (!modal) return;

    modal.innerHTML = `
      <div class="modal-dialog animate-fade-in" style="max-width: 850px;">
        <div class="modal-header">
          <h3 class="modal-title">Quotation Review & Decision</h3>
          <button class="modal-close" onclick="window.DealFlowUI.closeModal();">&times;</button>
        </div>
        <div class="modal-body" id="approval-modal-body">
          <div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Loading quotation details & approval triggers...</div>
        </div>
      </div>
    `;

    global.DealFlowUI.openModal();

    try {
      const [quoteRes, stepsRes] = await Promise.all([
        global.QuotationsAPI.get(quotationId),
        global.QuotationsAPI.getApprovals(quotationId)
      ]);

      const bodyEl = document.getElementById('approval-modal-body');
      if (!bodyEl) return;

      if (!quoteRes.ok) {
        bodyEl.innerHTML = `<div class="alert alert-coral">Failed to load quotation details.</div>`;
        return;
      }

      const q = quoteRes.data;
      const steps = stepsRes.ok ? (stepsRes.data || []) : [];

      // Find pending step for the active round
      const pendingStep = steps.find(s => s.status === 'PENDING');
      const canDecide = pendingStep && (userRole === 'ADMIN' || userRole === pendingStep.approval_role);

      // Collect all triggers across active pending steps
      const activeTriggers = pendingStep ? (pendingStep.triggers || []) : [];

      bodyEl.innerHTML = `
        <!-- Header summary -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-md); padding-bottom: var(--space-sm); border-bottom: 1px solid var(--color-border);">
          <div>
            <div style="font-size: var(--font-size-lg); font-weight: 700; color: var(--color-navy);">${q.quote_number}</div>
            <div style="font-size: var(--font-size-xs); color: var(--color-text-secondary);">${q.customer?.name || 'Customer'} | ${q.sales_rep?.full_name || 'Sales Rep'}</div>
          </div>
          <div style="text-align: right;">
            <div style="font-size: var(--font-size-lg); font-weight: 700; color: var(--color-navy);">${q.currency} ${Number(q.net_total).toFixed(2)}</div>
            <div style="font-size: var(--font-size-xs); font-weight: 600; color: ${Number(q.margin_pct) >= 15 ? 'var(--color-teal)' : 'var(--color-coral)'};">Margin: ${Number(q.margin_pct).toFixed(1)}%</div>
          </div>
        </div>

        <!-- Explainable Approval Triggers Banner -->
        ${activeTriggers.length > 0 ? `
          <div class="approval-triggers-banner">
            <div class="triggers-banner-title">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
              <span>Why Approval Was Triggered (${pendingStep.approval_role}):</span>
            </div>
            <div class="triggers-list">
              ${activeTriggers.map(t => `
                <div class="trigger-item">
                  <strong>${t.trigger_code}:</strong> ${t.message}
                  ${(t.actual_value !== null && t.threshold_value !== null) ? `(Actual: ${Number(t.actual_value)} vs Threshold: ${Number(t.threshold_value)})` : ''}
                </div>
              `).join('')}
            </div>
          </div>
        ` : ''}

        <!-- Line Items Table -->
        <div style="margin-bottom: var(--space-md);">
          <div style="font-size: var(--font-size-xs); font-weight: 700; color: var(--color-navy); margin-bottom: var(--space-xs); text-transform: uppercase;">Quotation Line Items</div>
          <table class="lines-table" style="font-size: 0.75rem;">
            <thead>
              <tr>
                <th>Product</th>
                <th>Qty</th>
                <th>List Price</th>
                <th>Discount</th>
                <th>Allowed Max</th>
                <th>Net Total</th>
                <th>Margin</th>
                <th>Risk</th>
              </tr>
            </thead>
            <tbody>
              ${(q.lines || []).map(l => `
                <tr>
                  <td>
                    <div style="font-weight: 600;">${l.product ? l.product.name : 'Line #' + l.id}</div>
                    <div style="color: var(--color-text-muted); font-size: 0.6875rem;">${l.product ? l.product.sku : ''}</div>
                  </td>
                  <td>${Number(l.quantity)}</td>
                  <td>$${Number(l.unit_list_price).toFixed(2)}</td>
                  <td style="font-weight: 700; color: ${Number(l.discount_overage_pct) > 0 ? 'var(--color-coral)' : 'inherit'};">
                    ${Number(l.line_discount_pct).toFixed(1)}%
                  </td>
                  <td>${l.max_discount_pct_snapshot ? Number(l.max_discount_pct_snapshot).toFixed(0) + '%' : '—'}</td>
                  <td>$${Number(l.net_line_total).toFixed(2)}</td>
                  <td style="font-weight: 600; color: ${Number(l.margin_pct) >= 15 ? 'var(--color-teal)' : 'var(--color-coral)'};">${Number(l.margin_pct).toFixed(1)}%</td>
                  <td><span class="badge ${l.risk_level === 'GREEN' ? 'badge-teal' : 'badge-coral'}" style="font-size: 0.65rem;">${l.risk_level}</span></td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>

        <!-- Multi-Round Approval History Timeline -->
        <div class="approval-rounds-timeline">
          <div style="font-size: var(--font-size-xs); font-weight: 700; color: var(--color-navy); text-transform: uppercase;">
            Approval Rounds & History (${steps.length} Steps)
          </div>
          ${steps.length === 0 ? `
            <div style="font-size: var(--font-size-xs); color: var(--color-text-muted);">No approval steps generated yet.</div>
          ` : `
            <div style="display: flex; flex-direction: column; gap: var(--space-xs);">
              ${steps.map(s => {
                const decider = s.decided_by_user ? s.decided_by_user.full_name : (s.decided_by_user_id ? 'User #' + s.decided_by_user_id : 'Pending');
                return `
                  <div class="approval-round-card">
                    <div class="round-header">
                      <span class="round-title">Round ${s.approval_round} — ${global.DealFlowNav?.formatRole(s.approval_role)}</span>
                      <span class="badge ${s.status === 'APPROVED' ? 'badge-teal' : (s.status === 'PENDING' ? 'badge-coral' : 'badge-navy')}" style="font-size: 0.65rem;">
                        ${s.status}
                      </span>
                    </div>
                    <div style="font-size: var(--font-size-xs); color: var(--color-text-secondary); display: flex; justify-content: space-between;">
                      <span>Reviewer: <strong>${decider}</strong></span>
                      <span>Requested: ${new Date(s.requested_at).toLocaleDateString()}</span>
                    </div>
                    ${s.decision_reason ? `
                      <div class="decision-reason-box">Reason: ${s.decision_reason}</div>
                    ` : ''}
                  </div>
                `;
              }).join('')}
            </div>
          `}
        </div>

        <!-- Action Decision Box -->
        ${canDecide ? `
          <div class="card" style="margin-top: var(--space-lg); padding: var(--space-md); background: var(--color-background); border: 1px solid var(--color-border);">
            <div style="font-size: var(--font-size-xs); font-weight: 700; color: var(--color-navy); margin-bottom: var(--space-xs);">
              Execute Governance Decision
            </div>

            <div class="form-group" style="margin-bottom: var(--space-md);">
              <label class="form-label" for="decision-reason-input">Decision Comment / Revision Reason</label>
              <textarea id="decision-reason-input" class="form-input" rows="2" placeholder="Required when returning for revision or rejecting..."></textarea>
            </div>

            <div style="display: flex; justify-content: flex-end; gap: var(--space-sm);">
              <button id="btn-decision-return" class="btn btn-secondary btn-sm" style="color: #B45309;">
                <span>Return for Revision</span>
              </button>
              <button id="btn-decision-reject" class="btn btn-secondary btn-sm" style="color: var(--color-coral);">
                <span>Reject</span>
              </button>
              <button id="btn-decision-approve" class="btn btn-primary btn-sm">
                <span>Approve Quotation</span>
              </button>
            </div>
          </div>
        ` : `
          <div style="text-align: right; margin-top: var(--space-lg);">
            <button class="btn btn-secondary" onclick="window.DealFlowUI.closeModal();">Close</button>
          </div>
        `}
      `;

      if (canDecide) {
        setupDecisionActions(quotationId, pendingStep.id);
      }
    } catch (err) {
      console.error('Error rendering approval modal:', err);
    }
  }

  function setupDecisionActions(quotationId, stepId) {
    const reasonInput = document.getElementById('decision-reason-input');

    document.getElementById('btn-decision-approve')?.addEventListener('click', async () => {
      if (!confirm('Approve this commercial quotation step?')) return;
      const reason = reasonInput?.value.trim() || null;
      try {
        const res = await global.QuotationsAPI.approveStep(quotationId, stepId, reason);
        if (res.ok) {
          global.DealFlowUI.closeModal();
          global.DealFlowUI.toast('Quotation step approved successfully!', 'teal');
          await loadApprovalQueue();
        } else {
          global.DealFlowUI.toast(res.data?.detail || 'Approval failed.', 'coral');
        }
      } catch (e) {
        global.DealFlowUI.toast('Network error executing approval.', 'coral');
      }
    });

    document.getElementById('btn-decision-return')?.addEventListener('click', async () => {
      const reason = reasonInput?.value.trim();
      if (!reason) {
        alert('Please enter a reason explaining what revision is required.');
        reasonInput?.focus();
        return;
      }
      if (!confirm('Return quotation to sales rep for revision?')) return;

      try {
        const res = await global.QuotationsAPI.returnStep(quotationId, stepId, reason);
        if (res.ok) {
          global.DealFlowUI.closeModal();
          global.DealFlowUI.toast('Quotation returned for revision.', 'coral');
          await loadApprovalQueue();
        } else {
          global.DealFlowUI.toast(res.data?.detail || 'Return action failed.', 'coral');
        }
      } catch (e) {
        global.DealFlowUI.toast('Network error returning quotation.', 'coral');
      }
    });

    document.getElementById('btn-decision-reject')?.addEventListener('click', async () => {
      const reason = reasonInput?.value.trim();
      if (!reason) {
        alert('Please enter a rejection reason.');
        reasonInput?.focus();
        return;
      }
      if (!confirm('Reject this quotation permanently?')) return;

      try {
        const res = await global.QuotationsAPI.rejectStep(quotationId, stepId, reason);
        if (res.ok) {
          global.DealFlowUI.closeModal();
          global.DealFlowUI.toast('Quotation rejected.', 'coral');
          await loadApprovalQueue();
        } else {
          global.DealFlowUI.toast(res.data?.detail || 'Rejection failed.', 'coral');
        }
      } catch (e) {
        global.DealFlowUI.toast('Network error rejecting quotation.', 'coral');
      }
    });
  }

  function formatStatusBadge(status) {
    const map = {
      'DRAFT': { label: 'Draft', cls: 'badge-navy' },
      'PENDING_MANAGER_APPROVAL': { label: 'Pending Manager Approval', cls: 'badge-coral' },
      'PENDING_FINANCE_APPROVAL': { label: 'Pending Finance Approval', cls: 'badge-coral' },
      'APPROVED': { label: 'Approved', cls: 'badge-teal' },
      'RETURNED_FOR_REVISION': { label: 'Returned for Revision', cls: 'badge-coral' },
      'REJECTED': { label: 'Rejected', cls: 'badge-coral' },
      'CANCELLED': { label: 'Cancelled', cls: 'badge-navy' }
    };
    const s = map[status] || { label: status, cls: 'badge-navy' };
    return `<span class="badge ${s.cls}">${s.label}</span>`;
  }

  global.ApprovalsView = {
    render: render
  };
})(typeof window !== 'undefined' ? window : this);
