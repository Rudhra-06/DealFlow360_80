/**
 * DealFlow360 — Commercial Approval Policies View Controller
 */
(function (global) {
  'use strict';

  let approvalFilter = { customer_tier_id: '', approval_role: '', is_active: '', effective_only: false, limit: 50, offset: 0 };
  let tiersCache = [];

  const ApprovalPoliciesView = {
    async render(container) {
      const currentUser = global.DealFlowAuth.getCurrentUser();
      const roleName = currentUser?.role?.name || 'ADMIN';
      const canWrite = ['ADMIN', 'SALES_MANAGER', 'FINANCE_OPERATIONS'].includes(roleName.toUpperCase());

      try {
        tiersCache = await global.CustomerTiersAPI.list({ limit: 100 });
      } catch (e) {
        tiersCache = [];
      }

      container.innerHTML = `
        <div class="view-header animate-fade-in">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-md);flex-wrap:wrap;gap:var(--space-md);">
            <div>
              <h2>Approval Policies</h2>
              <p>Configure commercial thresholds that will drive commercial approval routing.</p>
            </div>
            <div>
              ${canWrite ? `
                <button class="btn btn-primary btn-sm" id="btn-add-approval-policy">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                  <span>Add Approval Policy</span>
                </button>
              ` : ''}
            </div>
          </div>

          <!-- Informational Banner -->
          <div class="alert alert-navy" style="margin-bottom:var(--space-md);">
            <svg class="alert-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            <span>This workspace manages commercial threshold rules. Quote approval queues and multi-tier decision workflows will be activated in Phase 3.</span>
          </div>

          <!-- Filter Toolbar -->
          <div class="filter-toolbar">
            <div class="filter-group-left">
              <select id="appr-tier-filter" class="filter-select">
                <option value="">All Customer Tiers</option>
                ${tiersCache.map(t => `<option value="${t.id}" ${approvalFilter.customer_tier_id == t.id ? 'selected' : ''}>${t.name}</option>`).join('')}
              </select>

              <select id="appr-role-filter" class="filter-select">
                <option value="">All Approver Roles</option>
                <option value="SALES_MANAGER" ${approvalFilter.approval_role === 'SALES_MANAGER' ? 'selected' : ''}>Sales Manager</option>
                <option value="FINANCE_OPERATIONS" ${approvalFilter.approval_role === 'FINANCE_OPERATIONS' ? 'selected' : ''}>Finance / Operations</option>
              </select>

              <select id="appr-status-filter" class="filter-select">
                <option value="">All Statuses</option>
                <option value="true" ${approvalFilter.is_active === 'true' ? 'selected' : ''}>Active</option>
                <option value="false" ${approvalFilter.is_active === 'false' ? 'selected' : ''}>Inactive</option>
              </select>
            </div>
          </div>

          <!-- Table Card -->
          <div class="table-card">
            <div class="table-responsive">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Policy Name</th>
                    <th>Customer Tier</th>
                    <th>Approval Triggers</th>
                    <th>Required Approver</th>
                    <th>Priority</th>
                    <th>Effective Period</th>
                    <th>Status</th>
                    <th style="text-align:right;">Actions</th>
                  </tr>
                </thead>
                <tbody id="approval-table-body">
                  <tr><td colspan="8" style="text-align:center; padding: 2rem;"><span class="spinner spinner-teal"></span> Loading approval policies...</td></tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      `;

      document.getElementById('appr-tier-filter').addEventListener('change', (e) => {
        approvalFilter.customer_tier_id = e.target.value;
        this.loadApprovalData(canWrite);
      });

      document.getElementById('appr-role-filter').addEventListener('change', (e) => {
        approvalFilter.approval_role = e.target.value;
        this.loadApprovalData(canWrite);
      });

      document.getElementById('appr-status-filter').addEventListener('change', (e) => {
        approvalFilter.is_active = e.target.value;
        this.loadApprovalData(canWrite);
      });

      if (canWrite) {
        document.getElementById('btn-add-approval-policy').addEventListener('click', () => {
          this.openApprovalPolicyFormModal(null, canWrite);
        });
      }

      await this.loadApprovalData(canWrite);
    },

    async loadApprovalData(canWrite) {
      const tbody = document.getElementById('approval-table-body');
      try {
        const list = await global.ApprovalPoliciesAPI.list(approvalFilter);

        if (!list || list.length === 0) {
          tbody.innerHTML = `
            <tr>
              <td colspan="8">
                <div class="table-empty-state">
                  <h4 style="color:var(--color-navy);">No Approval Policies Configured</h4>
                  <p style="font-size:var(--font-size-xs);">Define discount exceptions, margin floors, and payment term escalation rules.</p>
                </div>
              </td>
            </tr>
          `;
          return;
        }

        let html = '';
        list.forEach(p => {
          const tierName = p.customer_tier ? p.customer_tier.name : '<span class="text-muted">Global</span>';
          const approverRoleName = global.DealFlowNav.formatRole(p.approval_role);

          // Build Trigger Chips
          let triggerChips = [];
          if (p.discount_above_pct !== null && p.discount_above_pct !== undefined) {
            triggerChips.push(`<span class="trigger-chip">Discount &gt; ${p.discount_above_pct}%</span>`);
          }
          if (p.margin_below_pct !== null && p.margin_below_pct !== undefined) {
            triggerChips.push(`<span class="trigger-chip" style="background:#fff3f0;color:#9c3617;border-color:rgba(242,140,107,0.3);">Margin &lt; ${p.margin_below_pct}%</span>`);
          }
          if (p.payment_terms_above_days !== null && p.payment_terms_above_days !== undefined) {
            triggerChips.push(`<span class="trigger-chip">Terms &gt; ${p.payment_terms_above_days}d</span>`);
          }

          const triggersDisplay = triggerChips.length > 0 ? triggerChips.join('') : '<span class="text-muted">None</span>';

          const effectivePeriod = (p.effective_from || p.effective_to)
            ? `${p.effective_from ? new Date(p.effective_from).toLocaleDateString() : '—'} to ${p.effective_to ? new Date(p.effective_to).toLocaleDateString() : 'Ongoing'}`
            : 'Always Effective';

          const statusBadge = p.is_active
            ? `<span class="badge badge-teal"><span class="status-dot status-dot-teal"></span>Active</span>`
            : `<span class="badge badge-gray">Inactive</span>`;

          html += `
            <tr>
              <td><span class="table-primary-text">${p.name}</span></td>
              <td><span class="badge badge-navy">${tierName}</span></td>
              <td>${triggersDisplay}</td>
              <td><span class="badge badge-teal">${approverRoleName}</span></td>
              <td><span class="badge badge-gray">${p.priority}</span></td>
              <td><span class="table-secondary-text">${effectivePeriod}</span></td>
              <td>${statusBadge}</td>
              <td style="text-align:right;">
                ${canWrite ? `<button class="btn btn-secondary btn-sm edit-approval-btn" data-id="${p.id}">Edit</button>` : '—'}
              </td>
            </tr>
          `;
        });

        tbody.innerHTML = html;

        tbody.querySelectorAll('.edit-approval-btn').forEach(btn => {
          btn.addEventListener('click', () => {
            const id = btn.getAttribute('data-id');
            const policy = list.find(x => x.id == id);
            if (policy) this.openApprovalPolicyFormModal(policy, canWrite);
          });
        });
      } catch (err) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding: 2rem; color: var(--color-coral);">${err.message || 'Failed to load approval policies.'}</td></tr>`;
      }
    },

    openApprovalPolicyFormModal(existingPolicy, canWrite) {
      const isEdit = Boolean(existingPolicy);
      const title = isEdit ? `Edit Approval Policy: ${existingPolicy.name}` : 'Add Approval Policy';

      const fromVal = existingPolicy?.effective_from ? existingPolicy.effective_from.slice(0, 16) : '';
      const toVal = existingPolicy?.effective_to ? existingPolicy.effective_to.slice(0, 16) : '';

      const formHtml = `
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label" for="appr-form-name">Policy Name *</label>
            <input type="text" id="appr-form-name" class="form-input" required placeholder="e.g. High Discount Manager Review" value="${existingPolicy?.name || ''}" />
          </div>
          <div class="form-group">
            <label class="form-label" for="appr-form-tier">Customer Tier Scope</label>
            <select id="appr-form-tier" class="form-input">
              <option value="">Global (All Tiers)</option>
              ${tiersCache.map(t => `<option value="${t.id}" ${existingPolicy?.customer_tier_id == t.id ? 'selected' : ''}>${t.name}</option>`).join('')}
            </select>
          </div>
        </div>

        <div class="drawer-section-title" style="margin-top:10px;">Approval Trigger Conditions (At least one required)</div>

        <div class="form-grid-3">
          <div class="form-group">
            <label class="form-label" for="appr-form-discount">Discount Above %</label>
            <input type="number" step="0.01" min="0" max="100" id="appr-form-discount" class="form-input" placeholder="e.g. 15.00" value="${existingPolicy?.discount_above_pct ?? ''}" />
          </div>
          <div class="form-group">
            <label class="form-label" for="appr-form-margin">Margin Below %</label>
            <input type="number" step="0.01" min="-100" max="100" id="appr-form-margin" class="form-input" placeholder="e.g. 10.00" value="${existingPolicy?.margin_below_pct ?? ''}" />
          </div>
          <div class="form-group">
            <label class="form-label" for="appr-form-terms">Terms Above (Days)</label>
            <input type="number" min="0" id="appr-form-terms" class="form-input" placeholder="e.g. 60" value="${existingPolicy?.payment_terms_above_days ?? ''}" />
          </div>
        </div>

        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label" for="appr-form-role">Required Operational Approver *</label>
            <select id="appr-form-role" class="form-input" required>
              <option value="SALES_MANAGER" ${existingPolicy?.approval_role === 'SALES_MANAGER' ? 'selected' : ''}>Sales Manager</option>
              <option value="FINANCE_OPERATIONS" ${existingPolicy?.approval_role === 'FINANCE_OPERATIONS' ? 'selected' : ''}>Finance / Operations</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label" for="appr-form-priority">Priority Ranking *</label>
            <input type="number" min="1" id="appr-form-priority" class="form-input" required value="${existingPolicy?.priority ?? 100}" />
            <div class="form-helper-text">Lower integer = higher priority.</div>
          </div>
        </div>

        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label" for="appr-form-from">Effective From</label>
            <input type="datetime-local" id="appr-form-from" class="form-input" value="${fromVal}" />
          </div>
          <div class="form-group">
            <label class="form-label" for="appr-form-to">Effective To</label>
            <input type="datetime-local" id="appr-form-to" class="form-input" value="${toVal}" />
          </div>
        </div>

        <div class="form-group">
          <label class="form-toggle-wrap">
            <input type="checkbox" id="appr-form-active" ${existingPolicy ? (existingPolicy.is_active ? 'checked' : '') : 'checked'} />
            <span style="font-size:var(--font-size-sm);font-weight:500;">Active Policy</span>
          </label>
        </div>
      `;

      global.DealFlowUI.showFormModal({
        title,
        size: 'lg',
        formHtml,
        submitLabel: isEdit ? 'Update Policy' : 'Create Policy',
        onSubmit: async (form, setErrorMessage) => {
          const name = document.getElementById('appr-form-name').value.trim();
          const tierVal = document.getElementById('appr-form-tier').value;
          const tier_id = tierVal ? parseInt(tierVal, 10) : null;
          const discVal = document.getElementById('appr-form-discount').value.trim();
          const marginVal = document.getElementById('appr-form-margin').value.trim();
          const termsVal = document.getElementById('appr-form-terms').value.trim();
          const approval_role = document.getElementById('appr-form-role').value;
          const priority = parseInt(document.getElementById('appr-form-priority').value, 10);
          const fromInput = document.getElementById('appr-form-from').value;
          const toInput = document.getElementById('appr-form-to').value;
          const is_active = document.getElementById('appr-form-active').checked;

          const discount_above_pct = discVal !== '' ? discVal : null;
          const margin_below_pct = marginVal !== '' ? marginVal : null;
          const payment_terms_above_days = termsVal !== '' ? parseInt(termsVal, 10) : null;

          if (!name || isNaN(priority)) {
            setErrorMessage('Policy name and priority are required.');
            throw new Error('Validation failed');
          }

          if (discount_above_pct === null && margin_below_pct === null && payment_terms_above_days === null) {
            setErrorMessage('At least one trigger condition (Discount %, Margin %, or Payment Terms) must be specified.');
            throw new Error('Trigger validation failed');
          }

          const payload = {
            name,
            customer_tier_id: tier_id,
            discount_above_pct,
            margin_below_pct,
            payment_terms_above_days,
            approval_role,
            priority,
            effective_from: fromInput ? new Date(fromInput).toISOString() : null,
            effective_to: toInput ? new Date(toInput).toISOString() : null,
            is_active
          };

          try {
            if (isEdit) {
              await global.ApprovalPoliciesAPI.update(existingPolicy.id, payload);
              global.DealFlowUI.showToast(`Approval policy ${name} updated.`, 'teal');
            } else {
              await global.ApprovalPoliciesAPI.create(payload);
              global.DealFlowUI.showToast(`Approval policy ${name} created.`, 'teal');
            }
            this.loadApprovalData(canWrite);
          } catch (err) {
            setErrorMessage(err.message || 'Operation failed.');
            throw err;
          }
        }
      });
    }
  };

  global.ApprovalPoliciesView = ApprovalPoliciesView;
})(typeof window !== 'undefined' ? window : this);
