/**
 * DealFlow360 — Billing Plans View Controller
 */
(function (global) {
  'use strict';

  let billingFilter = { billing_type: '', is_active: '', limit: 50, offset: 0 };

  const BillingPlansView = {
    async render(container) {
      const currentUser = global.DealFlowAuth.getCurrentUser();
      const roleName = currentUser?.role?.name || 'ADMIN';
      const canWrite = ['ADMIN', 'FINANCE_OPERATIONS'].includes(roleName.toUpperCase());

      container.innerHTML = `
        <div class="view-header animate-fade-in">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-md);flex-wrap:wrap;gap:var(--space-md);">
            <div>
              <h2>Billing Plans</h2>
              <p>Configure commercial billing frequencies, payment milestones, and terms.</p>
            </div>
            <div>
              ${canWrite ? `
                <button class="btn btn-primary btn-sm" id="btn-add-billing-plan">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                  <span>Add Billing Plan</span>
                </button>
              ` : ''}
            </div>
          </div>

          <!-- Informational Banner -->
          <div class="alert alert-navy" style="margin-bottom:var(--space-md);">
            <svg class="alert-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            <span>Billing Plans establish terms for commercial contracts. Invoice generation and payment collection will be implemented in subsequent phases.</span>
          </div>

          <!-- Filter Toolbar -->
          <div class="filter-toolbar">
            <div class="filter-group-left">
              <select id="bill-type-filter" class="filter-select">
                <option value="">All Billing Types</option>
                <option value="ONE_TIME" ${billingFilter.billing_type === 'ONE_TIME' ? 'selected' : ''}>One-Time Payment</option>
                <option value="RECURRING" ${billingFilter.billing_type === 'RECURRING' ? 'selected' : ''}>Recurring Schedule</option>
              </select>

              <select id="bill-status-filter" class="filter-select">
                <option value="">All Statuses</option>
                <option value="true" ${billingFilter.is_active === 'true' ? 'selected' : ''}>Active</option>
                <option value="false" ${billingFilter.is_active === 'false' ? 'selected' : ''}>Inactive</option>
              </select>
            </div>
          </div>

          <!-- Table Card -->
          <div class="table-card">
            <div class="table-responsive">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Plan Code</th>
                    <th>Plan Name</th>
                    <th>Billing Type</th>
                    <th>Frequency Interval</th>
                    <th>Payment Due Days</th>
                    <th>Status</th>
                    <th style="text-align:right;">Actions</th>
                  </tr>
                </thead>
                <tbody id="billing-table-body">
                  <tr><td colspan="7" style="text-align:center; padding: 2rem;"><span class="spinner spinner-teal"></span> Loading billing plans...</td></tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      `;

      document.getElementById('bill-type-filter').addEventListener('change', (e) => {
        billingFilter.billing_type = e.target.value;
        this.loadBillingData(canWrite);
      });

      document.getElementById('bill-status-filter').addEventListener('change', (e) => {
        billingFilter.is_active = e.target.value;
        this.loadBillingData(canWrite);
      });

      if (canWrite) {
        document.getElementById('btn-add-billing-plan').addEventListener('click', () => {
          this.openBillingPlanFormModal(null, canWrite);
        });
      }

      await this.loadBillingData(canWrite);
    },

    async loadBillingData(canWrite) {
      const tbody = document.getElementById('billing-table-body');
      try {
        const list = await global.BillingPlansAPI.list(billingFilter);

        if (!list || list.length === 0) {
          tbody.innerHTML = `
            <tr>
              <td colspan="7">
                <div class="table-empty-state">
                  <h4 style="color:var(--color-navy);">No Billing Plans Configured</h4>
                  <p style="font-size:var(--font-size-xs);">Create standard commercial terms (e.g. Monthly, Net-30, Annual Prepaid).</p>
                </div>
              </td>
            </tr>
          `;
          return;
        }

        let html = '';
        list.forEach(p => {
          const typeBadge = p.billing_type === 'RECURRING'
            ? `<span class="badge badge-navy">Recurring</span>`
            : `<span class="badge badge-gray">One-Time</span>`;

          const intervalDisplay = p.billing_type === 'RECURRING'
            ? (p.billing_interval_months === 1 ? 'Every Month' : (p.billing_interval_months === 12 ? 'Annual (12 Months)' : `Every ${p.billing_interval_months} Months`))
            : '<span class="text-muted">—</span>';

          const statusBadge = p.is_active
            ? `<span class="badge badge-teal"><span class="status-dot status-dot-teal"></span>Active</span>`
            : `<span class="badge badge-gray">Inactive</span>`;

          html += `
            <tr>
              <td><span class="table-code">${p.code}</span></td>
              <td><span class="table-primary-text">${p.name}</span></td>
              <td>${typeBadge}</td>
              <td>${intervalDisplay}</td>
              <td><strong>Net ${p.payment_due_days}</strong> days</td>
              <td>${statusBadge}</td>
              <td style="text-align:right;">
                ${canWrite ? `<button class="btn btn-secondary btn-sm edit-billing-btn" data-id="${p.id}">Edit</button>` : '—'}
              </td>
            </tr>
          `;
        });

        tbody.innerHTML = html;

        tbody.querySelectorAll('.edit-billing-btn').forEach(btn => {
          btn.addEventListener('click', () => {
            const id = btn.getAttribute('data-id');
            const plan = list.find(x => x.id == id);
            if (plan) this.openBillingPlanFormModal(plan, canWrite);
          });
        });
      } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 2rem; color: var(--color-coral);">${err.message || 'Failed to load billing plans.'}</td></tr>`;
      }
    },

    openBillingPlanFormModal(existingPlan, canWrite) {
      const isEdit = Boolean(existingPlan);
      const title = isEdit ? `Edit Billing Plan: ${existingPlan.code}` : 'Add New Billing Plan';

      const initialType = existingPlan?.billing_type || 'ONE_TIME';

      const formHtml = `
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label" for="bill-form-code">Plan Code *</label>
            <input type="text" id="bill-form-code" class="form-input" required placeholder="e.g. NET30_MONTHLY" value="${existingPlan?.code || ''}" />
          </div>
          <div class="form-group">
            <label class="form-label" for="bill-form-name">Plan Name *</label>
            <input type="text" id="bill-form-name" class="form-input" required placeholder="e.g. Monthly Standard Net-30" value="${existingPlan?.name || ''}" />
          </div>
        </div>

        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label" for="bill-form-type">Billing Type *</label>
            <select id="bill-form-type" class="form-input" required>
              <option value="ONE_TIME" ${initialType === 'ONE_TIME' ? 'selected' : ''}>One-Time Payment</option>
              <option value="RECURRING" ${initialType === 'RECURRING' ? 'selected' : ''}>Recurring Schedule</option>
            </select>
          </div>
          <div class="form-group" id="bill-interval-group" style="${initialType === 'RECURRING' ? '' : 'display:none;'}">
            <label class="form-label" for="bill-form-interval">Billing Interval (Months) *</label>
            <input type="number" min="1" id="bill-form-interval" class="form-input" placeholder="1 = Monthly, 3 = Quarterly, 12 = Annual" value="${existingPlan?.billing_interval_months || '1'}" />
            <div class="form-helper-text">1 = Monthly, 3 = Quarterly, 12 = Annual</div>
          </div>
        </div>

        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label" for="bill-form-due">Payment Due Days *</label>
            <input type="number" min="0" id="bill-form-due" class="form-input" required placeholder="30" value="${existingPlan?.payment_due_days ?? 30}" />
          </div>
          <div class="form-group" style="justify-content:center;">
            <label class="form-toggle-wrap">
              <input type="checkbox" id="bill-form-active" ${existingPlan ? (existingPlan.is_active ? 'checked' : '') : 'checked'} />
              <span style="font-size:var(--font-size-sm);font-weight:500;">Active Plan</span>
            </label>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="bill-form-desc">Description</label>
          <textarea id="bill-form-desc" class="form-input" style="height:60px;" placeholder="Commercial billing details and contract terms">${existingPlan?.description || ''}</textarea>
        </div>
      `;

      global.DealFlowUI.showFormModal({
        title,
        size: 'md',
        formHtml,
        submitLabel: isEdit ? 'Update Plan' : 'Create Plan',
        onSubmit: async (form, setErrorMessage) => {
          const code = document.getElementById('bill-form-code').value.trim().toUpperCase();
          const name = document.getElementById('bill-form-name').value.trim();
          const billing_type = document.getElementById('bill-form-type').value;
          const dueDays = parseInt(document.getElementById('bill-form-due').value, 10);
          const desc = document.getElementById('bill-form-desc').value.trim() || null;
          const is_active = document.getElementById('bill-form-active').checked;

          let billing_interval_months = null;
          if (billing_type === 'RECURRING') {
            const intervalVal = document.getElementById('bill-form-interval').value.trim();
            billing_interval_months = parseInt(intervalVal, 10);
            if (isNaN(billing_interval_months) || billing_interval_months < 1) {
              setErrorMessage('Billing interval must be an integer >= 1 for recurring plans.');
              throw new Error('Validation error');
            }
          }

          if (!code || !name || isNaN(dueDays)) {
            setErrorMessage('Code, Name, and Payment Due Days are required.');
            throw new Error('Validation error');
          }

          const payload = {
            code,
            name,
            billing_type,
            billing_interval_months,
            payment_due_days: dueDays,
            description: desc,
            is_active
          };

          try {
            if (isEdit) {
              await global.BillingPlansAPI.update(existingPlan.id, payload);
              global.DealFlowUI.showToast(`Billing plan ${code} updated.`, 'teal');
            } else {
              await global.BillingPlansAPI.create(payload);
              global.DealFlowUI.showToast(`Billing plan ${code} created.`, 'teal');
            }
            this.loadBillingData(canWrite);
          } catch (err) {
            setErrorMessage(err.message || 'Operation failed.');
            throw err;
          }
        }
      });

      // Toggle interval visibility dynamically
      document.getElementById('bill-form-type')?.addEventListener('change', (e) => {
        const group = document.getElementById('bill-interval-group');
        const intervalInput = document.getElementById('bill-form-interval');
        if (e.target.value === 'RECURRING') {
          group.style.display = 'block';
          if (!intervalInput.value) intervalInput.value = '1';
        } else {
          group.style.display = 'none';
          intervalInput.value = '';
        }
      });
    }
  };

  global.BillingPlansView = BillingPlansView;
})(typeof window !== 'undefined' ? window : this);
