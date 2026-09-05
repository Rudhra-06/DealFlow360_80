/**
 * DealFlow360 — Discount Policies & Policy Resolver View Controller
 */
(function (global) {
  'use strict';

  let discountFilter = { customer_tier_id: '', product_category_id: '', product_id: '', is_active: '', effective_only: false, limit: 50, offset: 0 };
  let tiersCache = [];
  let categoriesCache = [];
  let productsCache = [];

  const DiscountPoliciesView = {
    async render(container) {
      const currentUser = global.DealFlowAuth.getCurrentUser();
      const roleName = currentUser?.role?.name || 'ADMIN';
      const canWrite = ['ADMIN', 'SALES_MANAGER'].includes(roleName.toUpperCase());

      // Load reference data
      try {
        [tiersCache, categoriesCache, productsCache] = await Promise.all([
          global.CustomerTiersAPI.list({ limit: 100 }),
          global.ProductCategoriesAPI.list({ limit: 100 }),
          global.ProductsAPI.list({ limit: 100 })
        ]);
      } catch (e) {
        tiersCache = [];
        categoriesCache = [];
        productsCache = [];
      }

      container.innerHTML = `
        <div class="view-header animate-fade-in">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-md);flex-wrap:wrap;gap:var(--space-md);">
            <div>
              <h2>Discount Policies</h2>
              <p>Configure commercial discount boundaries by customer and product scope.</p>
            </div>
            <div>
              ${canWrite ? `
                <button class="btn btn-primary btn-sm" id="btn-add-discount-policy">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                  <span>Add Discount Policy</span>
                </button>
              ` : ''}
            </div>
          </div>

          <!-- Policy Precedence Explanation Info Box -->
          <div class="precedence-info-box">
            <div style="display:flex;align-items:center;gap:6px;font-weight:600;color:var(--color-navy);margin-bottom:4px;">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
              <span>Commercial Specificity Precedence Order (Authoritative Backend Resolution)</span>
            </div>
            <p style="margin-bottom:8px;">When evaluating deals, the backend evaluates the highest-specificity applicable rule first. Lower priority integers resolve ties.</p>
            <div class="precedence-list">
              <div class="precedence-step"><span class="precedence-num">1</span> Tier + Product</div>
              <div class="precedence-step"><span class="precedence-num">2</span> Product</div>
              <div class="precedence-step"><span class="precedence-num">3</span> Tier + Category</div>
              <div class="precedence-step"><span class="precedence-num">4</span> Category</div>
              <div class="precedence-step"><span class="precedence-num">5</span> Tier</div>
              <div class="precedence-step"><span class="precedence-num">6</span> Global Default</div>
            </div>
          </div>

          <!-- Policy Resolver Tool Panel -->
          <div class="card" style="margin-bottom:var(--space-lg);">
            <div class="card-header">
              <div>
                <h3 class="card-title" style="font-size:var(--font-size-sm);">Test Policy Resolution</h3>
                <div class="card-subtitle">Verify which discount policy the backend selects for a customer tier and product combination.</div>
              </div>
              <span class="badge badge-teal">Live Resolver</span>
            </div>
            <div class="card-body">
              <div class="form-grid-3" style="align-items:flex-end;">
                <div class="form-group" style="margin-bottom:0;">
                  <label class="form-label" for="resolver-tier">Customer Tier</label>
                  <select id="resolver-tier" class="form-input">
                    <option value="">Global / No Tier</option>
                    ${tiersCache.map(t => `<option value="${t.id}">${t.name}</option>`).join('')}
                  </select>
                </div>
                <div class="form-group" style="margin-bottom:0;">
                  <label class="form-label" for="resolver-prod">Product</label>
                  <select id="resolver-prod" class="form-input">
                    <option value="">Any / No Product</option>
                    ${productsCache.map(p => `<option value="${p.id}">${p.name} (${p.sku})</option>`).join('')}
                  </select>
                </div>
                <div>
                  <button class="btn btn-secondary btn-block" id="btn-run-resolver" style="height:42px;">
                    <span id="resolver-spinner" class="spinner spinner-teal" style="display:none;"></span>
                    <span id="resolver-btn-label">Resolve Policy</span>
                  </button>
                </div>
              </div>

              <!-- Resolver Output Box -->
              <div id="resolver-result-box" style="margin-top:16px;display:none;"></div>
            </div>
          </div>

          <!-- Filter Toolbar -->
          <div class="filter-toolbar">
            <div class="filter-group-left">
              <select id="discount-tier-filter" class="filter-select">
                <option value="">All Tiers</option>
                ${tiersCache.map(t => `<option value="${t.id}" ${discountFilter.customer_tier_id == t.id ? 'selected' : ''}>${t.name}</option>`).join('')}
              </select>

              <select id="discount-category-filter" class="filter-select">
                <option value="">All Categories</option>
                ${categoriesCache.map(c => `<option value="${c.id}" ${discountFilter.product_category_id == c.id ? 'selected' : ''}>${c.name}</option>`).join('')}
              </select>

              <select id="discount-status-filter" class="filter-select">
                <option value="">All Statuses</option>
                <option value="true" ${discountFilter.is_active === 'true' ? 'selected' : ''}>Active</option>
                <option value="false" ${discountFilter.is_active === 'false' ? 'selected' : ''}>Inactive</option>
              </select>
            </div>
          </div>

          <!-- Policies Table -->
          <div class="table-card">
            <div class="table-responsive">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Policy Name</th>
                    <th>Customer Tier</th>
                    <th>Product Scope</th>
                    <th>Standard %</th>
                    <th>Max %</th>
                    <th>Priority</th>
                    <th>Effective Period</th>
                    <th>Status</th>
                    <th style="text-align:right;">Actions</th>
                  </tr>
                </thead>
                <tbody id="discount-table-body">
                  <tr><td colspan="9" style="text-align:center; padding: 2rem;"><span class="spinner spinner-teal"></span> Loading policies...</td></tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      `;

      // Filter events
      document.getElementById('discount-tier-filter').addEventListener('change', (e) => {
        discountFilter.customer_tier_id = e.target.value;
        this.loadPoliciesData(canWrite);
      });

      document.getElementById('discount-category-filter').addEventListener('change', (e) => {
        discountFilter.product_category_id = e.target.value;
        this.loadPoliciesData(canWrite);
      });

      document.getElementById('discount-status-filter').addEventListener('change', (e) => {
        discountFilter.is_active = e.target.value;
        this.loadPoliciesData(canWrite);
      });

      // Resolver Tool event
      document.getElementById('btn-run-resolver').addEventListener('click', () => {
        this.executeResolver();
      });

      if (canWrite) {
        document.getElementById('btn-add-discount-policy').addEventListener('click', () => {
          this.openDiscountPolicyFormModal(null, canWrite);
        });
      }

      await this.loadPoliciesData(canWrite);
    },

    async executeResolver() {
      const tierId = document.getElementById('resolver-tier').value || null;
      const prodId = document.getElementById('resolver-prod').value || null;
      const resultBox = document.getElementById('resolver-result-box');
      const spinner = document.getElementById('resolver-spinner');
      const btnLabel = document.getElementById('resolver-btn-label');

      spinner.style.display = 'inline-block';
      btnLabel.textContent = 'Resolving...';

      try {
        const res = await global.DiscountPoliciesAPI.resolve({
          customer_tier_id: tierId,
          product_id: prodId
        });

        resultBox.style.display = 'block';

        if (!res || !res.applicable_policy) {
          resultBox.innerHTML = `
            <div class="alert alert-navy" style="margin-bottom:0;">
              <div>
                <strong>No Policy Applicable</strong>
                <div style="font-size:var(--font-size-xs);margin-top:2px;">No matching or fallback discount policy is configured for this combination. (Configuration result only)</div>
              </div>
            </div>
          `;
        } else {
          const p = res.applicable_policy;
          const tierName = p.customer_tier ? p.customer_tier.name : 'Global';
          const scopeName = p.product ? `Product: ${p.product.name} (${p.product.sku})` : (p.product_category ? `Category: ${p.product_category.name}` : 'All Products');

          resultBox.innerHTML = `
            <div class="alert alert-teal" style="margin-bottom:0; flex-direction:column; align-items:flex-start;">
              <div style="display:flex;align-items:center;justify-content:space-between;width:100%;margin-bottom:8px;">
                <span style="font-weight:700;font-size:var(--font-size-base);color:#0c675e;">Applicable: ${p.name}</span>
                <span class="badge badge-teal">Specificity: ${res.specificity_level || 'Tier Match'}</span>
              </div>
              <div class="key-value-list" style="width:100%;">
                <div class="key-value-item" style="border-color:rgba(25,181,165,0.2);">
                  <span class="key-label">Resolved Scope</span>
                  <span class="key-value">${tierName} · ${scopeName}</span>
                </div>
                <div class="key-value-item" style="border-color:rgba(25,181,165,0.2);">
                  <span class="key-label">Standard Reference Discount</span>
                  <span class="key-value" style="color:var(--color-teal);font-weight:700;">${p.standard_discount_pct}%</span>
                </div>
                <div class="key-value-item" style="border-color:rgba(25,181,165,0.2);">
                  <span class="key-label">Maximum Commercial Cap</span>
                  <span class="key-value" style="color:var(--color-coral);font-weight:700;">${p.max_discount_pct}%</span>
                </div>
                <div class="key-value-item" style="border-bottom:none;">
                  <span class="key-label">Priority Ranking</span>
                  <span class="key-value">${p.priority} (Lower = Higher precedence)</span>
                </div>
              </div>
              <div style="font-size:0.75rem;color:#0d6d63;margin-top:6px;font-style:italic;">
                * Configuration result only. Phase 3 quotation engine will evaluate margins and approval requirements.
              </div>
            </div>
          `;
        }
      } catch (err) {
        resultBox.style.display = 'block';
        resultBox.innerHTML = `<div class="alert alert-coral" style="margin-bottom:0;">${err.message || 'Resolution failed.'}</div>`;
      } finally {
        spinner.style.display = 'none';
        btnLabel.textContent = 'Resolve Policy';
      }
    },

    async loadPoliciesData(canWrite) {
      const tbody = document.getElementById('discount-table-body');
      try {
        const list = await global.DiscountPoliciesAPI.list(discountFilter);

        if (!list || list.length === 0) {
          tbody.innerHTML = `
            <tr>
              <td colspan="9">
                <div class="table-empty-state">
                  <h4 style="color:var(--color-navy);">No Discount Policies Found</h4>
                  <p style="font-size:var(--font-size-xs);">Configure standard and maximum commercial discount rules.</p>
                </div>
              </td>
            </tr>
          `;
          return;
        }

        let html = '';
        list.forEach(p => {
          const tierName = p.customer_tier ? p.customer_tier.name : '<span class="text-muted">Global</span>';
          let productScope = '<span class="text-muted">Global (All)</span>';
          if (p.product) {
            productScope = `<span class="scope-chip">SKU: ${p.product.sku}</span>`;
          } else if (p.product_category) {
            productScope = `<span class="scope-chip">Cat: ${p.product_category.name}</span>`;
          }

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
              <td>${productScope}</td>
              <td><strong style="color:var(--color-teal);">${p.standard_discount_pct}%</strong></td>
              <td><strong style="color:var(--color-coral);">${p.max_discount_pct}%</strong></td>
              <td><span class="badge badge-gray">${p.priority}</span></td>
              <td><span class="table-secondary-text">${effectivePeriod}</span></td>
              <td>${statusBadge}</td>
              <td style="text-align:right;">
                ${canWrite ? `<button class="btn btn-secondary btn-sm edit-discount-btn" data-id="${p.id}">Edit</button>` : '—'}
              </td>
            </tr>
          `;
        });

        tbody.innerHTML = html;

        tbody.querySelectorAll('.edit-discount-btn').forEach(btn => {
          btn.addEventListener('click', () => {
            const id = btn.getAttribute('data-id');
            const policy = list.find(x => x.id == id);
            if (policy) this.openDiscountPolicyFormModal(policy, canWrite);
          });
        });
      } catch (err) {
        tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding: 2rem; color: var(--color-coral);">${err.message || 'Failed to load discount policies.'}</td></tr>`;
      }
    },

    openDiscountPolicyFormModal(existingPolicy, canWrite) {
      const isEdit = Boolean(existingPolicy);
      const title = isEdit ? `Edit Discount Policy: ${existingPolicy.name}` : 'Add Discount Policy';

      let initialScopeType = 'global';
      if (existingPolicy?.product_id) initialScopeType = 'product';
      else if (existingPolicy?.product_category_id) initialScopeType = 'category';

      const fromVal = existingPolicy?.effective_from ? existingPolicy.effective_from.slice(0, 16) : '';
      const toVal = existingPolicy?.effective_to ? existingPolicy.effective_to.slice(0, 16) : '';

      const formHtml = `
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label" for="disc-form-name">Policy Name *</label>
            <input type="text" id="disc-form-name" class="form-input" required placeholder="e.g. Gold Tier Hardware Standard" value="${existingPolicy?.name || ''}" />
          </div>
          <div class="form-group">
            <label class="form-label" for="disc-form-tier">Customer Tier Scope</label>
            <select id="disc-form-tier" class="form-input">
              <option value="">Global (All Tiers)</option>
              ${tiersCache.map(t => `<option value="${t.id}" ${existingPolicy?.customer_tier_id == t.id ? 'selected' : ''}>${t.name}</option>`).join('')}
            </select>
          </div>
        </div>

        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label" for="disc-form-scope-type">Product Scope Type *</label>
            <select id="disc-form-scope-type" class="form-input">
              <option value="global" ${initialScopeType === 'global' ? 'selected' : ''}>Global (All Products)</option>
              <option value="category" ${initialScopeType === 'category' ? 'selected' : ''}>Specific Product Category</option>
              <option value="product" ${initialScopeType === 'product' ? 'selected' : ''}>Specific Product SKU</option>
            </select>
          </div>
          <div class="form-group" id="disc-scope-target-wrap">
            <!-- Dynamically populated based on scope type -->
          </div>
        </div>

        <div class="form-grid-3">
          <div class="form-group">
            <label class="form-label" for="disc-form-standard">Standard Discount % *</label>
            <input type="number" step="0.01" min="0" max="100" id="disc-form-standard" class="form-input" required value="${existingPolicy?.standard_discount_pct ?? '0.00'}" />
          </div>
          <div class="form-group">
            <label class="form-label" for="disc-form-max">Maximum Discount % *</label>
            <input type="number" step="0.01" min="0" max="100" id="disc-form-max" class="form-input" required value="${existingPolicy?.max_discount_pct ?? '0.00'}" />
          </div>
          <div class="form-group">
            <label class="form-label" for="disc-form-priority">Priority Ranking *</label>
            <input type="number" min="1" id="disc-form-priority" class="form-input" required value="${existingPolicy?.priority ?? 100}" />
            <div class="form-helper-text">Lower number = higher priority.</div>
          </div>
        </div>

        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label" for="disc-form-from">Effective From</label>
            <input type="datetime-local" id="disc-form-from" class="form-input" value="${fromVal}" />
          </div>
          <div class="form-group">
            <label class="form-label" for="disc-form-to">Effective To</label>
            <input type="datetime-local" id="disc-form-to" class="form-input" value="${toVal}" />
          </div>
        </div>

        <div class="form-group">
          <label class="form-toggle-wrap">
            <input type="checkbox" id="disc-form-active" ${existingPolicy ? (existingPolicy.is_active ? 'checked' : '') : 'checked'} />
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
          const name = document.getElementById('disc-form-name').value.trim();
          const tierVal = document.getElementById('disc-form-tier').value;
          const tier_id = tierVal ? parseInt(tierVal, 10) : null;
          const scopeType = document.getElementById('disc-form-scope-type').value;

          let category_id = null;
          let product_id = null;

          if (scopeType === 'category') {
            const catEl = document.getElementById('disc-form-cat');
            if (catEl && catEl.value) category_id = parseInt(catEl.value, 10);
          } else if (scopeType === 'product') {
            const prodEl = document.getElementById('disc-form-prod');
            if (prodEl && prodEl.value) product_id = parseInt(prodEl.value, 10);
          }

          const standard = document.getElementById('disc-form-standard').value.trim();
          const max = document.getElementById('disc-form-max').value.trim();
          const priority = parseInt(document.getElementById('disc-form-priority').value, 10);
          const fromInput = document.getElementById('disc-form-from').value;
          const toInput = document.getElementById('disc-form-to').value;
          const is_active = document.getElementById('disc-form-active').checked;

          if (!name || isNaN(priority)) {
            setErrorMessage('Please fill in policy name and valid priority.');
            throw new Error('Validation failed');
          }

          if (Number(standard) > Number(max)) {
            setErrorMessage('Standard discount cannot exceed maximum allowable discount.');
            throw new Error('Discount range validation failed');
          }

          const payload = {
            name,
            customer_tier_id: tier_id,
            product_category_id: category_id,
            product_id: product_id,
            standard_discount_pct: standard,
            max_discount_pct: max,
            priority,
            effective_from: fromInput ? new Date(fromInput).toISOString() : null,
            effective_to: toInput ? new Date(toInput).toISOString() : null,
            is_active
          };

          try {
            if (isEdit) {
              await global.DiscountPoliciesAPI.update(existingPolicy.id, payload);
              global.DealFlowUI.showToast(`Policy ${name} updated.`, 'teal');
            } else {
              await global.DiscountPoliciesAPI.create(payload);
              global.DealFlowUI.showToast(`Policy ${name} created.`, 'teal');
            }
            this.loadPoliciesData(canWrite);
          } catch (err) {
            setErrorMessage(err.message || 'Operation failed.');
            throw err;
          }
        }
      });

      // Handle dynamic scope dropdown rendering inside modal
      const updateScopeTarget = (type) => {
        const targetWrap = document.getElementById('disc-scope-target-wrap');
        if (!targetWrap) return;

        if (type === 'category') {
          targetWrap.innerHTML = `
            <label class="form-label" for="disc-form-cat">Select Product Category *</label>
            <select id="disc-form-cat" class="form-input" required>
              <option value="">Choose category...</option>
              ${categoriesCache.map(c => `<option value="${c.id}" ${existingPolicy?.product_category_id == c.id ? 'selected' : ''}>${c.name}</option>`).join('')}
            </select>
          `;
        } else if (type === 'product') {
          targetWrap.innerHTML = `
            <label class="form-label" for="disc-form-prod">Select Product SKU *</label>
            <select id="disc-form-prod" class="form-input" required>
              <option value="">Choose product...</option>
              ${productsCache.map(p => `<option value="${p.id}" ${existingPolicy?.product_id == p.id ? 'selected' : ''}>${p.name} (${p.sku})</option>`).join('')}
            </select>
          `;
        } else {
          targetWrap.innerHTML = `
            <label class="form-label">Scope Target</label>
            <div style="font-size:var(--font-size-sm);color:var(--color-text-secondary);padding-top:8px;">Applies universally across entire catalog.</div>
          `;
        }
      };

      document.getElementById('disc-form-scope-type')?.addEventListener('change', (e) => {
        updateScopeTarget(e.target.value);
      });

      updateScopeTarget(initialScopeType);
    }
  };

  global.DiscountPoliciesView = DiscountPoliciesView;
})(typeof window !== 'undefined' ? window : this);
