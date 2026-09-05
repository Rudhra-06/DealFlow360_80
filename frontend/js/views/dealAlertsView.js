/**
 * DealFlow360 — Deal Alerts Inbox View Controller
 * Phase 6 Part 1 Triage Workspace: Acknowledge, Resolve, Nudge, Escalate, and Dismiss.
 */
(function (global) {
  'use strict';

  let currentAlerts = [];
  let alertFilters = {
    status: '',
    severity: '',
    quotation_id: '',
    limit: 100,
    offset: 0
  };

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

  function formatStatusBadge(status) {
    const map = {
      'OPEN': { label: 'Open', cls: 'badge-coral' },
      'ACKNOWLEDGED': { label: 'Acknowledged', cls: 'badge-navy' },
      'RESOLVED': { label: 'Resolved', cls: 'badge-teal' },
      'DISMISSED': { label: 'Dismissed', cls: 'badge-navy' }
    };
    const item = map[status] || { label: status, cls: 'badge-navy' };
    return `<span class="badge ${item.cls}">${item.label}</span>`;
  }

  async function render(container, params = {}) {
    if (params.quotation_id || params.quoteId) {
      alertFilters.quotation_id = params.quotation_id || params.quoteId;
    }

    container.innerHTML = `
      <div class="animate-fade-in">
        <!-- Header -->
        <div class="view-header" style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--space-lg);">
          <div>
            <h1 style="font-size: var(--font-size-2xl); color: var(--color-navy); margin-bottom: 4px;">Deal Alerts & Actions</h1>
            <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary);">
              Operational and commercial risk notifications requiring review, acknowledgement, sales rep nudges, or management escalation.
            </p>
          </div>
          <div>
            <button id="btn-refresh-alerts" class="btn btn-secondary">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
              <span>Refresh</span>
            </button>
          </div>
        </div>

        <!-- Filter Bar -->
        <div class="card" style="padding: var(--space-md); margin-bottom: var(--space-lg);">
          <div style="display: grid; grid-template-columns: 1.5fr 1.5fr 1fr auto; gap: var(--space-md); align-items: center;">
            <div>
              <select id="alerts-status-filter" class="form-input">
                <option value="">All Statuses</option>
                <option value="OPEN" ${alertFilters.status === 'OPEN' ? 'selected' : ''}>Open</option>
                <option value="ACKNOWLEDGED" ${alertFilters.status === 'ACKNOWLEDGED' ? 'selected' : ''}>Acknowledged</option>
                <option value="RESOLVED" ${alertFilters.status === 'RESOLVED' ? 'selected' : ''}>Resolved</option>
                <option value="DISMISSED" ${alertFilters.status === 'DISMISSED' ? 'selected' : ''}>Dismissed</option>
              </select>
            </div>
            <div>
              <select id="alerts-severity-filter" class="form-input">
                <option value="">All Severities</option>
                <option value="CRITICAL" ${alertFilters.severity === 'CRITICAL' ? 'selected' : ''}>Critical</option>
                <option value="HIGH" ${alertFilters.severity === 'HIGH' ? 'selected' : ''}>High</option>
                <option value="WARNING" ${alertFilters.severity === 'WARNING' ? 'selected' : ''}>Warning</option>
                <option value="INFO" ${alertFilters.severity === 'INFO' ? 'selected' : ''}>Info</option>
              </select>
            </div>
            <div>
              <input type="number" id="alerts-quote-filter" class="form-input" placeholder="Quote ID..." value="${alertFilters.quotation_id || ''}" />
            </div>
            <div>
              <button id="btn-reset-alert-filters" class="btn btn-secondary">Reset</button>
            </div>
          </div>
        </div>

        <!-- Alerts Stream -->
        <div id="alerts-feed-container">
          <div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Loading deal alerts...</div>
        </div>
      </div>
    `;

    setupEvents(container);
    await loadAlerts();
  }

  function setupEvents(container) {
    const statusSelect = container.querySelector('#alerts-status-filter');
    const sevSelect = container.querySelector('#alerts-severity-filter');
    const quoteInput = container.querySelector('#alerts-quote-filter');
    const resetBtn = container.querySelector('#btn-reset-alert-filters');
    const refreshBtn = container.querySelector('#btn-refresh-alerts');

    statusSelect?.addEventListener('change', () => {
      alertFilters.status = statusSelect.value;
      loadAlerts();
    });

    sevSelect?.addEventListener('change', () => {
      alertFilters.severity = sevSelect.value;
      loadAlerts();
    });

    quoteInput?.addEventListener('change', () => {
      alertFilters.quotation_id = quoteInput.value.trim() ? parseInt(quoteInput.value.trim(), 10) : '';
      loadAlerts();
    });

    resetBtn?.addEventListener('click', () => {
      alertFilters = { status: '', severity: '', quotation_id: '', limit: 100, offset: 0 };
      if (statusSelect) statusSelect.value = '';
      if (sevSelect) sevSelect.value = '';
      if (quoteInput) quoteInput.value = '';
      loadAlerts();
    });

    refreshBtn?.addEventListener('click', loadAlerts);
  }

  async function loadAlerts() {
    const container = document.getElementById('alerts-feed-container');
    if (!container) return;

    container.innerHTML = `<div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Loading alerts...</div>`;

    try {
      const res = await global.DealAlertsAPI.list(alertFilters);
      if (!res.ok) {
        container.innerHTML = `
          <div class="alert alert-coral" style="margin: 20px 0;">
            <span>Failed to load alerts: ${res.data?.detail || res.error || 'Server error'}</span>
          </div>
        `;
        return;
      }

      currentAlerts = res.data || [];
      renderAlertsList(container);
    } catch (err) {
      container.innerHTML = `
        <div class="alert alert-coral" style="margin: 20px 0;">
          <span>Error connecting to Deal Alerts API.</span>
        </div>
      `;
    }
  }

  function renderAlertsList(container) {
    if (currentAlerts.length === 0) {
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 60px 20px;">
          <div style="width: 48px; height: 48px; border-radius: var(--radius-full); background: rgba(25, 181, 165, 0.1); color: var(--color-teal); display: flex; align-items: center; justify-content: center; margin: 0 auto var(--space-md);">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
          </div>
          <h3 style="font-size: var(--font-size-md); color: var(--color-navy); margin-bottom: 4px;">No active alerts</h3>
          <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary);">There are no unresolved alerts matching the selected filters.</p>
        </div>
      `;
      return;
    }

    const user = global.DealFlowAuth?.getCurrentUser();
    const canEscalate = user && (user.role?.name === 'ADMIN' || user.role?.name === 'SALES_MANAGER' || user.role?.name === 'FINANCE_OPERATIONS');

    container.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: var(--space-md);">
        ${currentAlerts.map(a => {
          const createdStr = a.created_at ? new Date(a.created_at).toLocaleString() : '—';
          const isResolved = a.status === 'RESOLVED' || a.status === 'DISMISSED';

          return `
            <div class="alert-item-card status-${a.status}">
              <div class="alert-item-header">
                <div style="display: flex; align-items: center; gap: var(--space-sm);">
                  ${formatSeverityBadge(a.severity)}
                  <span class="alert-item-title">${a.title}</span>
                </div>
                <div>
                  ${formatStatusBadge(a.status)}
                </div>
              </div>

              <div class="alert-item-meta">
                <span>Quotation: <strong style="color: var(--color-navy); font-family: monospace;">${a.quote_number || '#' + a.quotation_id}</strong></span>
                <span>Customer: <strong>${a.customer_name || 'Customer'}</strong></span>
                <span>Sales Rep: <strong>${a.sales_rep_name || 'Assigned Rep'}</strong></span>
                <span>Triggered: <strong>${a.occurrence_count || 1} times</strong></span>
                <span>Created: <strong>${createdStr}</strong></span>
              </div>

              <div class="alert-item-message">${a.message}</div>

              <div class="alert-actions-bar">
                <div style="display: flex; gap: var(--space-xs);">
                  <button class="btn btn-secondary btn-sm btn-open-deal-health" data-quote-id="${a.quotation_id}">
                    <span>View Deal Health</span>
                  </button>
                  <button class="btn btn-secondary btn-sm btn-open-quote" data-quote-id="${a.quotation_id}">
                    <span>Open Quote</span>
                  </button>
                </div>

                <div style="display: flex; gap: var(--space-xs);">
                  ${!isResolved ? `
                    ${a.status === 'OPEN' ? `
                      <button class="btn btn-secondary btn-sm btn-ack-alert" data-alert-id="${a.id}">
                        <span>Acknowledge</span>
                      </button>
                    ` : ''}

                    <button class="btn btn-secondary btn-sm btn-nudge-alert" data-alert-id="${a.id}">
                      <span>Nudge Rep</span>
                    </button>

                    ${canEscalate ? `
                      <button class="btn btn-secondary btn-sm btn-escalate-alert" data-alert-id="${a.id}" style="color: var(--color-coral);">
                        <span>Escalate</span>
                      </button>
                    ` : ''}

                    <button class="btn btn-primary btn-sm btn-resolve-alert" data-alert-id="${a.id}">
                      <span>Resolve Alert</span>
                    </button>

                    <button class="btn btn-secondary btn-sm btn-dismiss-alert" data-alert-id="${a.id}" title="Dismiss alert with reason">
                      <span>Dismiss</span>
                    </button>
                  ` : `
                    <span style="font-size: 0.75rem; color: var(--color-teal); font-weight: 700; align-self: center;">
                      ✓ ${a.status}
                    </span>
                  `}
                </div>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;

    // Wire action buttons
    container.querySelectorAll('.btn-open-deal-health').forEach(btn => {
      btn.addEventListener('click', () => {
        global.DealFlowApp.switchView('deal-health', { quoteId: btn.dataset.quoteId });
      });
    });

    container.querySelectorAll('.btn-open-quote').forEach(btn => {
      btn.addEventListener('click', () => {
        global.DealFlowApp.switchView('quotation-builder', { quoteId: btn.dataset.quoteId });
      });
    });

    container.querySelectorAll('.btn-ack-alert').forEach(btn => {
      btn.addEventListener('click', async () => {
        const aid = btn.dataset.alertId;
        btn.disabled = true;
        btn.textContent = 'Acknowledging...';
        try {
          const res = await global.DealAlertsAPI.acknowledge(aid);
          if (res.ok) {
            global.DealFlowUI.toast('Alert acknowledged.', 'teal');
            loadAlerts();
          } else {
            global.DealFlowUI.toast(res.data?.detail || 'Failed to acknowledge alert.', 'coral');
            btn.disabled = false;
            btn.textContent = 'Acknowledge';
          }
        } catch (e) {
          btn.disabled = false;
          btn.textContent = 'Acknowledge';
        }
      });
    });

    container.querySelectorAll('.btn-resolve-alert').forEach(btn => {
      btn.addEventListener('click', () => {
        openResolveModal(btn.dataset.alertId);
      });
    });

    container.querySelectorAll('.btn-dismiss-alert').forEach(btn => {
      btn.addEventListener('click', () => {
        openDismissModal(btn.dataset.alertId);
      });
    });

    container.querySelectorAll('.btn-nudge-alert').forEach(btn => {
      btn.addEventListener('click', () => {
        openNudgeModal(btn.dataset.alertId);
      });
    });

    container.querySelectorAll('.btn-escalate-alert').forEach(btn => {
      btn.addEventListener('click', () => {
        openEscalateModal(btn.dataset.alertId);
      });
    });
  }

  // --- RESOLVE MODAL ---
  function openResolveModal(alertId) {
    const modal = document.getElementById('dealflow-modal-overlay');
    if (!modal) return;

    modal.innerHTML = `
      <div class="modal-dialog animate-fade-in" style="max-width: 480px;">
        <div class="modal-header">
          <h3 class="modal-title">Resolve Deal Alert</h3>
          <button class="modal-close" onclick="window.DealFlowUI.closeModal();">&times;</button>
        </div>
        <div class="modal-body">
          <form id="resolve-alert-form">
            <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: var(--space-md);">
              Provide a resolution note detailing the action taken to address this risk alert.
            </p>
            <div class="form-group">
              <label class="form-label" for="resolve-note-input">Resolution Note *</label>
              <textarea id="resolve-note-input" class="form-input" rows="3" required placeholder="e.g. Customer approved revised margin terms; quote resubmitted."></textarea>
            </div>
            <div style="display: flex; justify-content: flex-end; gap: var(--space-sm); margin-top: var(--space-lg);">
              <button type="button" class="btn btn-secondary" onclick="window.DealFlowUI.closeModal();">Cancel</button>
              <button type="submit" id="btn-submit-resolve" class="btn btn-primary">
                <span>Resolve Alert</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    `;

    global.DealFlowUI.openModal();

    document.getElementById('resolve-alert-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const note = document.getElementById('resolve-note-input').value.trim();
      const btn = document.getElementById('btn-submit-resolve');
      btn.disabled = true;

      try {
        const res = await global.DealAlertsAPI.resolve(alertId, note);
        if (res.ok) {
          global.DealFlowUI.closeModal();
          global.DealFlowUI.toast('Alert resolved successfully.', 'teal');
          loadAlerts();
        } else {
          global.DealFlowUI.toast(res.data?.detail || 'Failed to resolve alert.', 'coral');
          btn.disabled = false;
        }
      } catch (err) {
        global.DealFlowUI.toast('Network error resolving alert.', 'coral');
        btn.disabled = false;
      }
    });
  }

  // --- DISMISS MODAL ---
  function openDismissModal(alertId) {
    const modal = document.getElementById('dealflow-modal-overlay');
    if (!modal) return;

    modal.innerHTML = `
      <div class="modal-dialog animate-fade-in" style="max-width: 480px;">
        <div class="modal-header">
          <h3 class="modal-title">Dismiss Deal Alert</h3>
          <button class="modal-close" onclick="window.DealFlowUI.closeModal();">&times;</button>
        </div>
        <div class="modal-body">
          <form id="dismiss-alert-form">
            <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: var(--space-md);">
              Dismiss this alert from active queue if no action is warranted.
            </p>
            <div class="form-group">
              <label class="form-label" for="dismiss-reason-input">Dismissal Reason (Optional)</label>
              <textarea id="dismiss-reason-input" class="form-input" rows="2" placeholder="e.g. Expected commercial exception agreed with management."></textarea>
            </div>
            <div style="display: flex; justify-content: flex-end; gap: var(--space-sm); margin-top: var(--space-lg);">
              <button type="button" class="btn btn-secondary" onclick="window.DealFlowUI.closeModal();">Cancel</button>
              <button type="submit" id="btn-submit-dismiss" class="btn btn-secondary" style="color: var(--color-coral);">
                <span>Dismiss Alert</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    `;

    global.DealFlowUI.openModal();

    document.getElementById('dismiss-alert-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const reason = document.getElementById('dismiss-reason-input').value.trim();
      const btn = document.getElementById('btn-submit-dismiss');
      btn.disabled = true;

      try {
        const res = await global.DealAlertsAPI.dismiss(alertId, reason || null);
        if (res.ok) {
          global.DealFlowUI.closeModal();
          global.DealFlowUI.toast('Alert dismissed.', 'navy');
          loadAlerts();
        } else {
          global.DealFlowUI.toast(res.data?.detail || 'Failed to dismiss alert.', 'coral');
          btn.disabled = false;
        }
      } catch (err) {
        global.DealFlowUI.toast('Network error dismissing alert.', 'coral');
        btn.disabled = false;
      }
    });
  }

  // --- NUDGE MODAL ---
  function openNudgeModal(alertId) {
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
          loadAlerts();
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

  // --- ESCALATE MODAL ---
  function openEscalateModal(alertId) {
    const modal = document.getElementById('dealflow-modal-overlay');
    if (!modal) return;

    modal.innerHTML = `
      <div class="modal-dialog animate-fade-in" style="max-width: 480px;">
        <div class="modal-header">
          <h3 class="modal-title">Escalate Deal Alert</h3>
          <button class="modal-close" onclick="window.DealFlowUI.closeModal();">&times;</button>
        </div>
        <div class="modal-body">
          <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: var(--space-md);">
            Escalate this critical risk alert to senior commercial leadership and sales management.
          </p>
          <div class="form-group">
            <label class="form-label" for="escalate-msg-input">Escalation Note (Optional)</label>
            <textarea id="escalate-msg-input" class="form-input" rows="3" placeholder="e.g. Critical margin deviation requires VP of Sales review."></textarea>
          </div>
          <div style="display: flex; justify-content: flex-end; gap: var(--space-sm); margin-top: var(--space-lg);">
            <button type="button" class="btn btn-secondary" onclick="window.DealFlowUI.closeModal();">Cancel</button>
            <button type="button" id="btn-submit-escalate" class="btn btn-coral">
              <span>Escalate Alert</span>
            </button>
          </div>
        </div>
      </div>
    `;

    global.DealFlowUI.openModal();

    document.getElementById('btn-submit-escalate').addEventListener('click', async () => {
      const msg = document.getElementById('escalate-msg-input').value.trim();
      const btn = document.getElementById('btn-submit-escalate');
      btn.disabled = true;

      try {
        const res = await global.DealAlertsAPI.escalate(alertId, {
          message: msg || undefined
        });

        if (res.ok) {
          global.DealFlowUI.closeModal();
          global.DealFlowUI.toast('Alert escalated to Management.', 'coral');
          loadAlerts();
        } else {
          global.DealFlowUI.toast(res.data?.detail || 'Failed to escalate alert.', 'coral');
          btn.disabled = false;
        }
      } catch (e) {
        global.DealFlowUI.toast('Error escalating alert.', 'coral');
        btn.disabled = false;
      }
    });
  }

  global.DealAlertsView = {
    render: render
  };
})(typeof window !== 'undefined' ? window : this);
