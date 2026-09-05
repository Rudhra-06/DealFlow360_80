/**
 * DealFlow360 — Deal Health Policy Configuration View Controller
 * Internal Management UI for score thresholds, signal weights, and anomaly criteria.
 */
(function (global) {
  'use strict';

  let currentConfig = null;

  async function render(container) {
    container.innerHTML = `
      <div id="health-config-wrapper" class="animate-fade-in">
        <div style="text-align: center; padding: 60px;"><span class="spinner spinner-teal"></span> Loading deal health configuration...</div>
      </div>
    `;

    await loadConfig(container);
  }

  async function loadConfig(container) {
    try {
      const res = await global.DealHealthAPI.getConfig();
      if (!res.ok) {
        container.innerHTML = `
          <div class="alert alert-coral" style="margin: 20px;">
            <span>Failed to load configuration: ${res.data?.detail || res.error || 'Access denied or server error'}</span>
          </div>
        `;
        return;
      }

      currentConfig = res.data;
      renderConfigForm(container);
    } catch (err) {
      container.innerHTML = `
        <div class="alert alert-coral" style="margin: 20px;">
          <span>Error connecting to Deal Health Configuration service.</span>
        </div>
      `;
    }
  }

  function renderConfigForm(container) {
    const c = currentConfig || {};
    const updatedStr = c.updated_at ? new Date(c.updated_at).toLocaleString() : 'Default';

    container.innerHTML = `
      <div class="animate-fade-in" style="max-width: 900px; margin: 0 auto;">
        <!-- Header -->
        <div class="view-header" style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--space-lg);">
          <div>
            <div style="display: flex; align-items: center; gap: var(--space-sm); margin-bottom: 4px;">
              <h1 style="font-size: var(--font-size-2xl); color: var(--color-navy); margin: 0;">Deal Health Configuration</h1>
              <span class="badge badge-teal" style="font-weight: 700;">ACTIVE POLICY</span>
            </div>
            <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary);">
              Define health score bands, velocity delay thresholds, discount anomaly tolerances, and signal score penalties.
            </p>
          </div>
          <div style="font-size: var(--font-size-xs); color: var(--color-text-muted); text-align: right;">
            Last Updated: <strong>${updatedStr}</strong>
          </div>
        </div>

        <form id="deal-health-config-form">
          <!-- Section 1: Health Score Thresholds -->
          <div class="config-section-card">
            <div class="config-section-title">Health Score Bands (0–100)</div>
            <div class="config-section-desc">Minimum score thresholds required to classify deal health into respective operational tiers.</div>

            <div class="config-field-grid">
              <div class="form-group">
                <label class="form-label" for="cfg-healthy-min">Healthy Minimum Score (Teal)</label>
                <input type="number" id="cfg-healthy-min" class="form-input" min="0" max="100" step="1" value="${c.healthy_min_score || 80}" required />
                <div class="config-help-text">Scores at or above this value are marked as HEALTHY.</div>
              </div>

              <div class="form-group">
                <label class="form-label" for="cfg-watch-min">Watch Minimum Score (Amber)</label>
                <input type="number" id="cfg-watch-min" class="form-input" min="0" max="100" step="1" value="${c.watch_min_score || 60}" required />
                <div class="config-help-text">Scores at or above this value (below Healthy) are marked as WATCH.</div>
              </div>

              <div class="form-group">
                <label class="form-label" for="cfg-at-risk-min">At-Risk Minimum Score (Coral)</label>
                <input type="number" id="cfg-at-risk-min" class="form-input" min="0" max="100" step="1" value="${c.at_risk_min_score || 30}" required />
                <div class="config-help-text">Scores at or above this value are AT_RISK; below this are CRITICAL.</div>
              </div>
            </div>
          </div>

          <!-- Section 2: Time & Velocity Delay Thresholds -->
          <div class="config-section-card">
            <div class="config-section-title">Velocity & Time Thresholds</div>
            <div class="config-section-desc">Duration tolerances before risk signals and alerts are raised across the deal lifecycle.</div>

            <div class="config-field-grid">
              <div class="form-group">
                <label class="form-label" for="cfg-stalled-days">Stalled Quote Days</label>
                <input type="number" id="cfg-stalled-days" class="form-input" min="0" step="1" value="${c.stalled_quote_days || 5}" required />
                <div class="config-help-text">Days without activity in draft/revision status.</div>
              </div>

              <div class="form-group">
                <label class="form-label" for="cfg-approval-hours">Approval Delay Hours</label>
                <input type="number" id="cfg-approval-hours" class="form-input" min="0" step="1" value="${c.approval_delay_hours || 24}" required />
                <div class="config-help-text">Hours pending manager or finance approval.</div>
              </div>

              <div class="form-group">
                <label class="form-label" for="cfg-negotiation-days">Negotiation Stall Days</label>
                <input type="number" id="cfg-negotiation-days" class="form-input" min="0" step="1" value="${c.negotiation_stall_days || 3}" required />
                <div class="config-help-text">Days inactive during customer portal negotiation.</div>
              </div>

              <div class="form-group">
                <label class="form-label" for="cfg-delivery-days">Delivery Slippage Days</label>
                <input type="number" id="cfg-delivery-days" class="form-input" min="0" step="1" value="${c.delivery_slippage_days || 2}" required />
                <div class="config-help-text">Days past estimated shipment completion.</div>
              </div>

              <div class="form-group">
                <label class="form-label" for="cfg-backorder-days">Backorder Age Days</label>
                <input type="number" id="cfg-backorder-days" class="form-input" min="0" step="1" value="${c.backorder_age_days || 3}" required />
                <div class="config-help-text">Days unfulfilled stock remains in backorder status.</div>
              </div>

              <div class="form-group">
                <label class="form-label" for="cfg-invoice-days">Invoice Overdue Days</label>
                <input type="number" id="cfg-invoice-days" class="form-input" min="0" step="1" value="${c.invoice_overdue_days || 1}" required />
                <div class="config-help-text">Days past payment due date before alert.</div>
              </div>
            </div>
          </div>

          <!-- Section 3: Commercial Anomaly Criteria -->
          <div class="config-section-card">
            <div class="config-section-title">Commercial Anomaly Criteria</div>
            <div class="config-section-desc">Statistical deviation criteria for identifying irregular discount patterns.</div>

            <div class="config-field-grid">
              <div class="form-group">
                <label class="form-label" for="cfg-discount-anomaly">Discount Anomaly Threshold (Percentage Points)</label>
                <input type="number" id="cfg-discount-anomaly" class="form-input" min="0" max="100" step="0.5" value="${c.discount_anomaly_threshold_pct || 10}" required />
                <div class="config-help-text">Minimum percentage-point difference between quotation discount and sales rep's historical average.</div>
              </div>
            </div>
          </div>

          <!-- Section 4: Signal Score Penalty Weights -->
          <div class="config-section-card">
            <div class="config-section-title">Signal Score Penalty Weights</div>
            <div class="config-section-desc">Score deduction points deducted from base score (100) when a specific risk signal triggers.</div>

            <div class="config-field-grid">
              <div class="form-group">
                <label class="form-label" for="cfg-w-stalled">Weight: Stalled Quote (pts)</label>
                <input type="number" id="cfg-w-stalled" class="form-input" min="0" max="50" step="1" value="${c.weight_stalled_quote || 20}" required />
              </div>

              <div class="form-group">
                <label class="form-label" for="cfg-w-discount">Weight: Discount Anomaly (pts)</label>
                <input type="number" id="cfg-w-discount" class="form-input" min="0" max="50" step="1" value="${c.weight_discount_anomaly || 15}" required />
              </div>

              <div class="form-group">
                <label class="form-label" for="cfg-w-approval">Weight: Approval Delay (pts)</label>
                <input type="number" id="cfg-w-approval" class="form-input" min="0" max="50" step="1" value="${c.weight_approval_delay || 10}" required />
              </div>

              <div class="form-group">
                <label class="form-label" for="cfg-w-negotiation">Weight: Negotiation Stall (pts)</label>
                <input type="number" id="cfg-w-negotiation" class="form-input" min="0" max="50" step="1" value="${c.weight_negotiation_stall || 15}" required />
              </div>

              <div class="form-group">
                <label class="form-label" for="cfg-w-delivery">Weight: Delivery Slippage (pts)</label>
                <input type="number" id="cfg-w-delivery" class="form-input" min="0" max="50" step="1" value="${c.weight_delivery_slippage || 20}" required />
              </div>

              <div class="form-group">
                <label class="form-label" for="cfg-w-backorder">Weight: Backorder (pts)</label>
                <input type="number" id="cfg-w-backorder" class="form-input" min="0" max="50" step="1" value="${c.weight_backorder || 10}" required />
              </div>

              <div class="form-group">
                <label class="form-label" for="cfg-w-invoice">Weight: Invoice Overdue (pts)</label>
                <input type="number" id="cfg-w-invoice" class="form-input" min="0" max="50" step="1" value="${c.weight_invoice_overdue || 10}" required />
              </div>
            </div>
          </div>

          <div style="display: flex; justify-content: flex-end; gap: var(--space-md); margin-bottom: var(--space-2xl);">
            <button type="button" class="btn btn-secondary" onclick="window.DealFlowApp.switchView('deal-health');">Cancel</button>
            <button type="submit" id="btn-save-health-config" class="btn btn-primary">
              <span>Save Policy Configuration</span>
            </button>
          </div>
        </form>
      </div>
    `;

    document.getElementById('deal-health-config-form')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = document.getElementById('btn-save-health-config');
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner spinner-white"></span> Saving...`;

      const payload = {
        name: c.name || "Default Health Policy",
        is_active: true,
        healthy_min_score: parseFloat(document.getElementById('cfg-healthy-min').value),
        watch_min_score: parseFloat(document.getElementById('cfg-watch-min').value),
        at_risk_min_score: parseFloat(document.getElementById('cfg-at-risk-min').value),
        stalled_quote_days: parseInt(document.getElementById('cfg-stalled-days').value, 10),
        approval_delay_hours: parseInt(document.getElementById('cfg-approval-hours').value, 10),
        negotiation_stall_days: parseInt(document.getElementById('cfg-negotiation-days').value, 10),
        delivery_slippage_days: parseInt(document.getElementById('cfg-delivery-days').value, 10),
        backorder_age_days: parseInt(document.getElementById('cfg-backorder-days').value, 10),
        invoice_overdue_days: parseInt(document.getElementById('cfg-invoice-days').value, 10),
        discount_anomaly_threshold_pct: parseFloat(document.getElementById('cfg-discount-anomaly').value),
        weight_stalled_quote: parseFloat(document.getElementById('cfg-w-stalled').value),
        weight_discount_anomaly: parseFloat(document.getElementById('cfg-w-discount').value),
        weight_approval_delay: parseFloat(document.getElementById('cfg-w-approval').value),
        weight_negotiation_stall: parseFloat(document.getElementById('cfg-w-negotiation').value),
        weight_delivery_slippage: parseFloat(document.getElementById('cfg-w-delivery').value),
        weight_backorder: parseFloat(document.getElementById('cfg-w-backorder').value),
        weight_invoice_overdue: parseFloat(document.getElementById('cfg-w-invoice').value)
      };

      try {
        let res;
        if (c.id) {
          res = await global.DealHealthAPI.updateConfig(c.id, payload);
        } else {
          res = await global.DealHealthAPI.createConfig(payload);
        }

        if (res.ok) {
          global.DealFlowUI.toast('Deal Health configuration updated successfully.', 'teal');
          await loadConfig(container);
        } else {
          global.DealFlowUI.toast(res.data?.detail || 'Failed to update configuration.', 'coral');
          btn.disabled = false;
          btn.innerHTML = `<span>Save Policy Configuration</span>`;
        }
      } catch (err) {
        global.DealFlowUI.toast('Network error updating configuration.', 'coral');
        btn.disabled = false;
        btn.innerHTML = `<span>Save Policy Configuration</span>`;
      }
    });
  }

  global.DealHealthConfigView = {
    render: render
  };
})(typeof window !== 'undefined' ? window : this);
