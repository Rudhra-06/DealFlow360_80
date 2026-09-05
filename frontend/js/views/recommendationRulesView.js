/**
 * DealFlow360 — Recommendation Rules Settings View
 * Configuration interface for product affinity, cross-sell pairings, promotions, and margin safeguards.
 */
(function (global) {
  'use strict';

  let currentRules = [];
  let cachedProducts = [];

  async function render(container) {
    container.innerHTML = `
      <div class="animate-fade-in">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-lg);">
          <div>
            <h2 style="font-size: var(--font-size-xl); color: var(--color-navy); margin-bottom: 2px;">Recommendation & Upsell Rules</h2>
            <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary);">Configure automated cross-sell pairings, affinity rankings, and promotional suggestions.</p>
          </div>
          <button id="btn-add-rec-rule" class="btn btn-primary">
            <span>+ Add Recommendation Rule</span>
          </button>
        </div>

        <div id="rec-rules-table-container">
          <div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Loading recommendation rules...</div>
        </div>
      </div>
    `;

    setupEvents(container);
    await loadInitialData();
  }

  function setupEvents(container) {
    container.querySelector('#btn-add-rec-rule')?.addEventListener('click', () => {
      openRuleModal(null);
    });
  }

  async function loadInitialData() {
    try {
      const [rulesRes, prodRes] = await Promise.all([
        global.RecommendationRulesAPI.list({ limit: 100 }),
        global.ProductsAPI.list({ limit: 100 })
      ]);

      cachedProducts = prodRes.ok ? (prodRes.data || []) : [];
      currentRules = rulesRes.ok ? (rulesRes.data || []) : [];
      renderTable();
    } catch (e) {
      console.error('Failed to load recommendation rules:', e);
    }
  }

  function renderTable() {
    const container = document.getElementById('rec-rules-table-container');
    if (!container) return;

    if (currentRules.length === 0) {
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 40px;">
          <h4 style="color: var(--color-navy); margin-bottom: 4px;">No Recommendation Rules Configured</h4>
          <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: 16px;">Set up automated product affinity pairings to drive upsell revenue in the quotation builder.</p>
          <button class="btn btn-primary" onclick="document.getElementById('btn-add-rec-rule')?.click();">+ Add Rule</button>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="table-card">
        <table class="data-table">
          <thead>
            <tr>
              <th>Anchor / Source Product</th>
              <th>Suggested Product</th>
              <th>Affinity Score</th>
              <th>Rec. Qty</th>
              <th>Promotion</th>
              <th>Min Margin %</th>
              <th>Priority</th>
              <th>Status</th>
              <th style="text-align: right;">Action</th>
            </tr>
          </thead>
          <tbody>
            ${currentRules.map(r => {
              const srcName = r.source_product ? r.source_product.name : `Product #${r.source_product_id}`;
              const sugName = r.suggested_product ? r.suggested_product.name : `Product #${r.suggested_product_id}`;

              return `
                <tr>
                  <td style="font-weight: 600; color: var(--color-navy);">${srcName}</td>
                  <td style="font-weight: 600; color: var(--color-teal);">${sugName}</td>
                  <td>${Number(r.affinity_score).toFixed(2)}</td>
                  <td>${Number(r.recommended_qty)}</td>
                  <td>
                    ${r.is_promoted ? `<span class="badge badge-teal" style="font-size: 0.65rem;">${r.promotion_label || 'Promoted'}</span>` : '<span style="color: var(--color-text-muted);">—</span>'}
                  </td>
                  <td>${r.min_margin_pct !== null ? `${Number(r.min_margin_pct)}%` : '—'}</td>
                  <td>${r.priority}</td>
                  <td>
                    <span class="badge ${r.is_active ? 'badge-teal' : 'badge-navy'}">
                      ${r.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td style="text-align: right;">
                    <button class="btn btn-secondary btn-sm btn-edit-rule" data-rule-id="${r.id}">Edit</button>
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    `;

    container.querySelectorAll('.btn-edit-rule').forEach(btn => {
      btn.addEventListener('click', () => {
        const rId = parseInt(btn.dataset.ruleId, 10);
        const rule = currentRules.find(r => r.id === rId);
        if (rule) openRuleModal(rule);
      });
    });
  }

  function openRuleModal(rule) {
    const modal = document.getElementById('dealflow-modal-overlay');
    if (!modal) return;

    const isEdit = !!rule;

    modal.innerHTML = `
      <div class="modal-dialog animate-fade-in" style="max-width: 600px;">
        <div class="modal-header">
          <h3 class="modal-title">${isEdit ? 'Edit Recommendation Rule' : 'Create Recommendation Rule'}</h3>
          <button class="modal-close" onclick="window.DealFlowUI.closeModal();">&times;</button>
        </div>
        <div class="modal-body">
          <form id="rec-rule-form">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-md);">
              <div class="form-group">
                <label class="form-label" for="rule-source-prod">Anchor / Source Product *</label>
                <select id="rule-source-prod" class="form-input" required>
                  <option value="">-- Select Source Product --</option>
                  ${cachedProducts.map(p => `
                    <option value="${p.id}" ${rule?.source_product_id === p.id ? 'selected' : ''}>${p.name} (${p.sku})</option>
                  `).join('')}
                </select>
              </div>

              <div class="form-group">
                <label class="form-label" for="rule-sug-prod">Suggested / Upsell Product *</label>
                <select id="rule-sug-prod" class="form-input" required>
                  <option value="">-- Select Suggested Product --</option>
                  ${cachedProducts.map(p => `
                    <option value="${p.id}" ${rule?.suggested_product_id === p.id ? 'selected' : ''}>${p.name} (${p.sku})</option>
                  `).join('')}
                </select>
              </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: var(--space-md);">
              <div class="form-group">
                <label class="form-label" for="rule-affinity">Affinity Score</label>
                <input type="number" id="rule-affinity" class="form-input" value="${rule?.affinity_score || '1.00'}" step="0.1" min="0" required />
              </div>
              <div class="form-group">
                <label class="form-label" for="rule-qty">Rec. Qty</label>
                <input type="number" id="rule-qty" class="form-input" value="${rule?.recommended_qty || '1'}" step="1" min="1" required />
              </div>
              <div class="form-group">
                <label class="form-label" for="rule-priority">Priority (lower=first)</label>
                <input type="number" id="rule-priority" class="form-input" value="${rule?.priority || '100'}" step="1" required />
              </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-md);">
              <div class="form-group">
                <label class="form-label" for="rule-min-margin">Min Acceptable Margin %</label>
                <input type="number" id="rule-min-margin" class="form-input" value="${rule?.min_margin_pct !== null && rule?.min_margin_pct !== undefined ? rule.min_margin_pct : ''}" placeholder="e.g. 15" step="0.5" />
              </div>
              <div class="form-group">
                <label class="form-label" for="rule-promo-label">Promotion Label</label>
                <input type="text" id="rule-promo-label" class="form-input" value="${rule?.promotion_label || ''}" placeholder="e.g. 'Featured Upgrade'" />
              </div>
            </div>

            <div style="display: flex; gap: var(--space-xl); margin-top: var(--space-sm);">
              <label style="display: flex; align-items: center; gap: 6px; font-size: var(--font-size-sm); cursor: pointer;">
                <input type="checkbox" id="rule-is-promoted" ${rule?.is_promoted ? 'checked' : ''} />
                <span>Promote to Top Rank</span>
              </label>

              <label style="display: flex; align-items: center; gap: 6px; font-size: var(--font-size-sm); cursor: pointer;">
                <input type="checkbox" id="rule-is-active" ${rule ? (rule.is_active ? 'checked' : '') : 'checked'} />
                <span>Active</span>
              </label>
            </div>

            <div id="rule-form-error" class="alert alert-coral" style="display: none; margin-top: var(--space-md);"></div>

            <div style="display: flex; justify-content: flex-end; gap: var(--space-sm); margin-top: var(--space-lg);">
              <button type="button" class="btn btn-secondary" onclick="window.DealFlowUI.closeModal();">Cancel</button>
              <button type="submit" id="btn-save-rule" class="btn btn-primary">
                <span>Save Rule</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    `;

    global.DealFlowUI.openModal();

    const form = document.getElementById('rec-rule-form');
    const errBox = document.getElementById('rule-form-error');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      errBox.style.display = 'none';

      const srcProd = parseInt(document.getElementById('rule-source-prod').value, 10);
      const sugProd = parseInt(document.getElementById('rule-sug-prod').value, 10);
      const affinity = parseFloat(document.getElementById('rule-affinity').value) || 1.0;
      const qty = parseFloat(document.getElementById('rule-qty').value) || 1.0;
      const priority = parseInt(document.getElementById('rule-priority').value, 10) || 100;
      const minMarginVal = document.getElementById('rule-min-margin').value.trim();
      const minMargin = minMarginVal ? parseFloat(minMarginVal) : null;
      const promoLabel = document.getElementById('rule-promo-label').value.trim() || null;
      const isPromoted = document.getElementById('rule-is-promoted').checked;
      const isActive = document.getElementById('rule-is-active').checked;

      if (!srcProd || !sugProd) {
        errBox.textContent = 'Please select both source and suggested products.';
        errBox.style.display = 'block';
        return;
      }

      if (srcProd === sugProd) {
        errBox.textContent = 'Source product and suggested product cannot be the same.';
        errBox.style.display = 'block';
        return;
      }

      const payload = {
        source_product_id: srcProd,
        suggested_product_id: sugProd,
        affinity_score: affinity,
        recommended_qty: qty,
        priority: priority,
        min_margin_pct: minMargin,
        promotion_label: promoLabel,
        is_promoted: isPromoted,
        is_active: isActive
      };

      try {
        let res;
        if (isEdit) {
          res = await global.RecommendationRulesAPI.update(rule.id, payload);
        } else {
          res = await global.RecommendationRulesAPI.create(payload);
        }

        if (!res.ok) {
          errBox.textContent = res.data?.detail || res.error || 'Failed to save recommendation rule.';
          errBox.style.display = 'block';
          return;
        }

        global.DealFlowUI.closeModal();
        global.DealFlowUI.toast(`Recommendation rule ${isEdit ? 'updated' : 'created'} successfully!`, 'teal');
        await loadInitialData();
      } catch (err) {
        errBox.textContent = 'Network error saving rule.';
        errBox.style.display = 'block';
      }
    });
  }

  global.RecommendationRulesView = {
    render: render
  };
})(typeof window !== 'undefined' ? window : this);
