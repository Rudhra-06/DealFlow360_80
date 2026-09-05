/**
 * DealFlow360 — Customers & Customer Tiers View Controller
 */
(function (global) {
  'use strict';

  let currentTab = 'customers'; // 'customers' or 'tiers'
  let customersFilter = { search: '', tier_id: '', is_active: '', limit: 20, offset: 0 };
  let tiersFilter = { is_active: '', limit: 20, offset: 0 };
  let tiersCache = [];

  const CustomersView = {
    async render(container, initialTab = 'customers') {
      currentTab = initialTab || 'customers';
      const currentUser = global.DealFlowAuth.getCurrentUser();
      const roleName = currentUser?.role?.name || 'ADMIN';
      const canWriteCustomer = ['ADMIN', 'SALES_REP', 'SALES_MANAGER'].includes(roleName.toUpperCase());
      const canWriteTier = ['ADMIN', 'SALES_MANAGER'].includes(roleName.toUpperCase());

      container.innerHTML = `
        <div class="view-header animate-fade-in">
          <div class="tabs-nav">
            <button class="tab-btn ${currentTab === 'customers' ? 'active' : ''}" id="tab-btn-customers">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
              <span>Customers</span>
            </button>
            <button class="tab-btn ${currentTab === 'tiers' ? 'active' : ''}" id="tab-btn-tiers">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
              <span>Customer Tiers</span>
            </button>
          </div>

          <div id="subview-content"></div>
        </div>
      `;

      document.getElementById('tab-btn-customers').addEventListener('click', () => {
        currentTab = 'customers';
        this.render(container, 'customers');
      });

      document.getElementById('tab-btn-tiers').addEventListener('click', () => {
        currentTab = 'tiers';
        this.render(container, 'tiers');
      });

      const subviewContainer = document.getElementById('subview-content');

      // Preload active tiers for dropdowns
      try {
        tiersCache = await global.CustomerTiersAPI.list({ limit: 100 });
      } catch (e) {
        tiersCache = [];
      }

      if (currentTab === 'customers') {
        await this.renderCustomersTab(subviewContainer, canWriteCustomer);
      } else {
        await this.renderTiersTab(subviewContainer, canWriteTier);
      }
    },

    async renderCustomersTab(container, canWrite) {
      container.innerHTML = `
        <div class="filter-toolbar">
          <div class="filter-group-left">
            <div class="search-input-wrap">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input type="text" id="cust-search" class="form-input" placeholder="Search by name or code..." value="${customersFilter.search}" />
            </div>

            <select id="cust-tier-filter" class="filter-select">
              <option value="">All Tiers</option>
              ${tiersCache.map(t => `<option value="${t.id}" ${customersFilter.tier_id == t.id ? 'selected' : ''}>${t.name}</option>`).join('')}
            </select>

            <select id="cust-status-filter" class="filter-select">
              <option value="">All Statuses</option>
              <option value="true" ${customersFilter.is_active === 'true' ? 'selected' : ''}>Active</option>
              <option value="false" ${customersFilter.is_active === 'false' ? 'selected' : ''}>Inactive</option>
            </select>
          </div>

          <div>
            ${canWrite ? `
              <button class="btn btn-primary btn-sm" id="btn-add-customer">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                <span>Add Customer</span>
              </button>
            ` : ''}
          </div>
        </div>

        <div class="table-card">
          <div class="table-responsive">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Customer Name</th>
                  <th>Tier</th>
                  <th>Email</th>
                  <th>Payment Terms</th>
                  <th>Credit Limit</th>
                  <th>Status</th>
                  <th style="text-align:right;">Actions</th>
                </tr>
              </thead>
              <tbody id="customers-table-body">
                <tr><td colspan="8" style="text-align:center; padding: 2rem;"><span class="spinner spinner-teal"></span> Loading customers...</td></tr>
              </tbody>
            </table>
          </div>
          <div class="table-pagination">
            <span id="cust-pagination-info">Showing records</span>
            <div class="pagination-controls">
              <button class="btn btn-secondary btn-sm" id="cust-prev-btn" disabled>Previous</button>
              <button class="btn btn-secondary btn-sm" id="cust-next-btn">Next</button>
            </div>
          </div>
        </div>
      `;

      // Filter events
      let searchTimeout = null;
      document.getElementById('cust-search').addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
          customersFilter.search = e.target.value.trim();
          customersFilter.offset = 0;
          this.loadCustomersData(canWrite);
        }, 300);
      });

      document.getElementById('cust-tier-filter').addEventListener('change', (e) => {
        customersFilter.tier_id = e.target.value;
        customersFilter.offset = 0;
        this.loadCustomersData(canWrite);
      });

      document.getElementById('cust-status-filter').addEventListener('change', (e) => {
        customersFilter.is_active = e.target.value;
        customersFilter.offset = 0;
        this.loadCustomersData(canWrite);
      });

      document.getElementById('cust-prev-btn').addEventListener('click', () => {
        if (customersFilter.offset >= customersFilter.limit) {
          customersFilter.offset -= customersFilter.limit;
          this.loadCustomersData(canWrite);
        }
      });

      document.getElementById('cust-next-btn').addEventListener('click', () => {
        customersFilter.offset += customersFilter.limit;
        this.loadCustomersData(canWrite);
      });

      if (canWrite) {
        document.getElementById('btn-add-customer').addEventListener('click', () => {
          this.openCustomerFormModal(null, canWrite);
        });
      }

      await this.loadCustomersData(canWrite);
    },

    async loadCustomersData(canWrite) {
      const tbody = document.getElementById('customers-table-body');
      const prevBtn = document.getElementById('cust-prev-btn');
      const nextBtn = document.getElementById('cust-next-btn');
      const infoEl = document.getElementById('cust-pagination-info');

      try {
        const list = await global.CustomersAPI.list(customersFilter);
        
        if (!list || list.length === 0) {
          tbody.innerHTML = `
            <tr>
              <td colspan="8">
                <div class="table-empty-state">
                  <div class="table-empty-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
                  </div>
                  <h4 style="color:var(--color-navy);">No Customers Found</h4>
                  <p style="font-size:var(--font-size-xs);">Try adjusting filters or search terms.</p>
                </div>
              </td>
            </tr>
          `;
          if (infoEl) infoEl.textContent = `Page ${Math.floor(customersFilter.offset / customersFilter.limit) + 1}`;
          if (prevBtn) prevBtn.disabled = customersFilter.offset === 0;
          if (nextBtn) nextBtn.disabled = true;
          return;
        }

        let html = '';
        list.forEach(c => {
          const tierName = c.tier ? c.tier.name : '—';
          const creditFormatted = `${c.currency || 'USD'} ${Number(c.credit_limit || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
          const statusBadge = c.is_active
            ? `<span class="badge badge-teal"><span class="status-dot status-dot-teal"></span>Active</span>`
            : `<span class="badge badge-gray"><span class="status-dot status-dot-gray"></span>Inactive</span>`;

          html += `
            <tr data-cust-id="${c.id}" style="cursor:pointer;">
              <td><span class="table-code">${c.customer_code}</span></td>
              <td><span class="table-primary-text">${c.name}</span></td>
              <td><span class="badge badge-navy">${tierName}</span></td>
              <td><span class="table-secondary-text">${c.email || '—'}</span></td>
              <td>${c.default_payment_terms_days} days</td>
              <td><span style="font-weight:600;">${creditFormatted}</span></td>
              <td>${statusBadge}</td>
              <td style="text-align:right;" onclick="event.stopPropagation();">
                <button class="btn btn-ghost btn-sm view-cust-btn" data-id="${c.id}" title="View Details">View</button>
                ${canWrite ? `<button class="btn btn-secondary btn-sm edit-cust-btn" data-id="${c.id}" title="Edit Customer">Edit</button>` : ''}
              </td>
            </tr>
          `;
        });

        tbody.innerHTML = html;

        // Row click -> View Details Drawer
        tbody.querySelectorAll('tr').forEach(row => {
          row.addEventListener('click', async () => {
            const id = row.getAttribute('data-cust-id');
            if (id) {
              const cust = list.find(x => x.id == id);
              if (cust) CustomersView.openCustomerDetailsDrawer(cust, canWrite);
            }
          });
        });

        tbody.querySelectorAll('.view-cust-btn').forEach(btn => {
          btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = btn.getAttribute('data-id');
            const cust = list.find(x => x.id == id);
            if (cust) CustomersView.openCustomerDetailsDrawer(cust, canWrite);
          });
        });

        tbody.querySelectorAll('.edit-cust-btn').forEach(btn => {
          btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = btn.getAttribute('data-id');
            const cust = list.find(x => x.id == id);
            if (cust) CustomersView.openCustomerFormModal(cust, canWrite);
          });
        });

        const page = Math.floor(customersFilter.offset / customersFilter.limit) + 1;
        if (infoEl) infoEl.textContent = `Page ${page} (${list.length} records shown)`;
        if (prevBtn) prevBtn.disabled = customersFilter.offset === 0;
        if (nextBtn) nextBtn.disabled = list.length < customersFilter.limit;
      } catch (err) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding: 2rem; color: var(--color-coral);">${err.message || 'Failed to load customers.'}</td></tr>`;
      }
    },

    openCustomerDetailsDrawer(cust, canWrite) {
      const tierName = cust.tier ? cust.tier.name : 'None';
      const creditFormatted = `${cust.currency || 'USD'} ${Number(cust.credit_limit || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

      const contentHtml = `
        <div>
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
            <div class="user-avatar" style="width:48px;height:48px;font-size:16px;background:var(--color-navy);">
              ${global.DealFlowUI.getInitials(cust.name)}
            </div>
            <div>
              <h3 style="color:var(--color-navy);margin-bottom:2px;">${cust.name}</h3>
              <span class="table-code">${cust.customer_code}</span>
            </div>
          </div>

          <div class="drawer-section-title">Commercial Profile</div>
          <div class="key-value-list">
            <div class="key-value-item">
              <span class="key-label">Customer Tier</span>
              <span class="key-value"><span class="badge badge-navy">${tierName}</span></span>
            </div>
            <div class="key-value-item">
              <span class="key-label">Credit Limit</span>
              <span class="key-value">${creditFormatted}</span>
            </div>
            <div class="key-value-item">
              <span class="key-label">Payment Terms</span>
              <span class="key-value">${cust.default_payment_terms_days} days</span>
            </div>
            <div class="key-value-item">
              <span class="key-label">Currency</span>
              <span class="key-value">${cust.currency}</span>
            </div>
            <div class="key-value-item">
              <span class="key-label">Account Status</span>
              <span class="key-value">
                ${cust.is_active ? '<span class="badge badge-teal"><span class="status-dot status-dot-teal"></span>Active</span>' : '<span class="badge badge-gray">Inactive</span>'}
              </span>
            </div>
          </div>

          <div class="drawer-section-title" style="margin-top:20px;">Contact & Addresses</div>
          <div class="key-value-list">
            <div class="key-value-item">
              <span class="key-label">Email</span>
              <span class="key-value">${cust.email || '—'}</span>
            </div>
            <div class="key-value-item">
              <span class="key-label">Phone</span>
              <span class="key-value">${cust.phone || '—'}</span>
            </div>
            <div class="key-value-item" style="flex-direction:column;align-items:flex-start;">
              <span class="key-label">Billing Address</span>
              <span style="font-size:var(--font-size-sm);color:var(--color-text);margin-top:4px;">${cust.billing_address || '—'}</span>
            </div>
            <div class="key-value-item" style="flex-direction:column;align-items:flex-start;">
              <span class="key-label">Shipping Address</span>
              <span style="font-size:var(--font-size-sm);color:var(--color-text);margin-top:4px;">${cust.shipping_address || '—'}</span>
            </div>
          </div>
        </div>
      `;

      const footerHtml = canWrite ? `
        <button class="btn btn-secondary btn-sm" id="drawer-edit-cust-btn">Edit Customer</button>
      ` : '';

      global.DealFlowUI.showDrawer({
        title: 'Customer Master Details',
        contentHtml,
        footerHtml
      });

      if (canWrite) {
        document.getElementById('drawer-edit-cust-btn')?.addEventListener('click', () => {
          document.getElementById('dealflow-drawer-backdrop')?.click();
          this.openCustomerFormModal(cust, canWrite);
        });
      }
    },

    openCustomerFormModal(existingCustomer, canWrite) {
      const isEdit = Boolean(existingCustomer);
      const title = isEdit ? `Edit Customer: ${existingCustomer.customer_code}` : 'Add New Customer';

      const activeTiers = tiersCache.filter(t => t.is_active || (existingCustomer && t.id === existingCustomer.tier_id));

      const formHtml = `
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label" for="cust-form-code">Customer Code *</label>
            <input type="text" id="cust-form-code" class="form-input" required placeholder="e.g. CUST-001" value="${existingCustomer?.customer_code || ''}" />
          </div>
          <div class="form-group">
            <label class="form-label" for="cust-form-name">Customer Name *</label>
            <input type="text" id="cust-form-name" class="form-input" required placeholder="e.g. Acme Corporation" value="${existingCustomer?.name || ''}" />
          </div>
        </div>

        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label" for="cust-form-email">Email Address</label>
            <input type="email" id="cust-form-email" class="form-input" placeholder="procurement@acme.com" value="${existingCustomer?.email || ''}" />
          </div>
          <div class="form-group">
            <label class="form-label" for="cust-form-phone">Phone</label>
            <input type="text" id="cust-form-phone" class="form-input" placeholder="+1-555-0199" value="${existingCustomer?.phone || ''}" />
          </div>
        </div>

        <div class="form-grid-3">
          <div class="form-group">
            <label class="form-label" for="cust-form-tier">Customer Tier *</label>
            <select id="cust-form-tier" class="form-input" required>
              <option value="">Select Tier...</option>
              ${activeTiers.map(t => `<option value="${t.id}" ${existingCustomer?.tier_id == t.id ? 'selected' : ''}>${t.name}</option>`).join('')}
            </select>
          </div>
          <div class="form-group">
            <label class="form-label" for="cust-form-terms">Payment Terms (Days) *</label>
            <input type="number" id="cust-form-terms" class="form-input" min="0" required value="${existingCustomer?.default_payment_terms_days ?? 30}" />
          </div>
          <div class="form-group">
            <label class="form-label" for="cust-form-credit">Credit Limit *</label>
            <input type="number" step="0.01" min="0" id="cust-form-credit" class="form-input" required value="${existingCustomer?.credit_limit ?? '0.00'}" />
          </div>
        </div>

        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label" for="cust-form-currency">Currency (3 Letters) *</label>
            <input type="text" id="cust-form-currency" class="form-input" maxlength="3" required placeholder="USD" value="${existingCustomer?.currency || 'USD'}" />
          </div>
          <div class="form-group" style="justify-content:center;">
            <label class="form-toggle-wrap">
              <input type="checkbox" id="cust-form-active" ${existingCustomer ? (existingCustomer.is_active ? 'checked' : '') : 'checked'} />
              <span style="font-size:var(--font-size-sm);font-weight:500;">Active Account</span>
            </label>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="cust-form-billing">Billing Address</label>
          <textarea id="cust-form-billing" class="form-input" style="height:60px;">${existingCustomer?.billing_address || ''}</textarea>
        </div>

        <div class="form-group">
          <label class="form-label" for="cust-form-shipping">Shipping Address</label>
          <textarea id="cust-form-shipping" class="form-input" style="height:60px;">${existingCustomer?.shipping_address || ''}</textarea>
        </div>
      `;

      global.DealFlowUI.showFormModal({
        title,
        size: 'lg',
        formHtml,
        submitLabel: isEdit ? 'Update Customer' : 'Create Customer',
        onSubmit: async (form, setErrorMessage) => {
          const code = document.getElementById('cust-form-code').value.trim();
          const name = document.getElementById('cust-form-name').value.trim();
          const email = document.getElementById('cust-form-email').value.trim() || null;
          const phone = document.getElementById('cust-form-phone').value.trim() || null;
          const tier_id = parseInt(document.getElementById('cust-form-tier').value, 10);
          const payment_terms = parseInt(document.getElementById('cust-form-terms').value, 10);
          const credit_limit = document.getElementById('cust-form-credit').value.trim();
          const currency = document.getElementById('cust-form-currency').value.trim().toUpperCase();
          const is_active = document.getElementById('cust-form-active').checked;
          const billing_address = document.getElementById('cust-form-billing').value.trim() || null;
          const shipping_address = document.getElementById('cust-form-shipping').value.trim() || null;

          if (!code || !name || isNaN(tier_id)) {
            setErrorMessage('Please fill in all required fields (Code, Name, Tier).');
            throw new Error('Validation failed');
          }

          const payload = {
            customer_code: code,
            name: name,
            email: email,
            phone: phone,
            tier_id: tier_id,
            default_payment_terms_days: payment_terms,
            credit_limit: credit_limit,
            currency: currency,
            billing_address: billing_address,
            shipping_address: shipping_address,
            is_active: is_active
          };

          try {
            if (isEdit) {
              await global.CustomersAPI.update(existingCustomer.id, payload);
              global.DealFlowUI.showToast(`Customer ${code} updated successfully.`, 'teal');
            } else {
              await global.CustomersAPI.create(payload);
              global.DealFlowUI.showToast(`Customer ${code} created successfully.`, 'teal');
            }
            this.loadCustomersData(canWrite);
          } catch (err) {
            setErrorMessage(err.message || 'Operation failed.');
            throw err;
          }
        }
      });
    },

    // Customer Tiers Tab
    async renderTiersTab(container, canWrite) {
      container.innerHTML = `
        <div class="filter-toolbar">
          <div class="filter-group-left">
            <select id="tier-status-filter" class="filter-select">
              <option value="">All Statuses</option>
              <option value="true" ${tiersFilter.is_active === 'true' ? 'selected' : ''}>Active</option>
              <option value="false" ${tiersFilter.is_active === 'false' ? 'selected' : ''}>Inactive</option>
            </select>
          </div>

          <div>
            ${canWrite ? `
              <button class="btn btn-primary btn-sm" id="btn-add-tier">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                <span>Add Customer Tier</span>
              </button>
            ` : ''}
          </div>
        </div>

        <div class="table-card">
          <div class="table-responsive">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Tier Name</th>
                  <th>Description</th>
                  <th>Status</th>
                  <th>Updated</th>
                  <th style="text-align:right;">Actions</th>
                </tr>
              </thead>
              <tbody id="tiers-table-body">
                <tr><td colspan="5" style="text-align:center; padding: 2rem;"><span class="spinner spinner-teal"></span> Loading tiers...</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      `;

      document.getElementById('tier-status-filter').addEventListener('change', (e) => {
        tiersFilter.is_active = e.target.value;
        this.loadTiersData(canWrite);
      });

      if (canWrite) {
        document.getElementById('btn-add-tier').addEventListener('click', () => {
          this.openTierFormModal(null, canWrite);
        });
      }

      await this.loadTiersData(canWrite);
    },

    async loadTiersData(canWrite) {
      const tbody = document.getElementById('tiers-table-body');
      try {
        const list = await global.CustomerTiersAPI.list(tiersFilter);
        tiersCache = list;

        if (!list || list.length === 0) {
          tbody.innerHTML = `
            <tr>
              <td colspan="5">
                <div class="table-empty-state">
                  <h4 style="color:var(--color-navy);">No Customer Tiers</h4>
                  <p style="font-size:var(--font-size-xs);">Configure master customer tiers like Gold, Silver, Bronze.</p>
                </div>
              </td>
            </tr>
          `;
          return;
        }

        let html = '';
        list.forEach(t => {
          const statusBadge = t.is_active
            ? `<span class="badge badge-teal"><span class="status-dot status-dot-teal"></span>Active</span>`
            : `<span class="badge badge-gray">Inactive</span>`;

          html += `
            <tr>
              <td><span class="table-primary-text">${t.name}</span></td>
              <td><span class="table-secondary-text">${t.description || '—'}</span></td>
              <td>${statusBadge}</td>
              <td><span style="font-size:var(--font-size-xs);">${new Date(t.updated_at).toLocaleDateString()}</span></td>
              <td style="text-align:right;">
                ${canWrite ? `<button class="btn btn-secondary btn-sm edit-tier-btn" data-id="${t.id}">Edit</button>` : '—'}
              </td>
            </tr>
          `;
        });

        tbody.innerHTML = html;

        tbody.querySelectorAll('.edit-tier-btn').forEach(btn => {
          btn.addEventListener('click', () => {
            const id = btn.getAttribute('data-id');
            const tier = list.find(x => x.id == id);
            if (tier) this.openTierFormModal(tier, canWrite);
          });
        });
      } catch (err) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 2rem; color: var(--color-coral);">${err.message || 'Failed to load customer tiers.'}</td></tr>`;
      }
    },

    openTierFormModal(existingTier, canWrite) {
      const isEdit = Boolean(existingTier);
      const title = isEdit ? `Edit Customer Tier: ${existingTier.name}` : 'Add Customer Tier';

      const formHtml = `
        <div class="form-group">
          <label class="form-label" for="tier-form-name">Tier Name *</label>
          <input type="text" id="tier-form-name" class="form-input" required placeholder="e.g. GOLD, PLATINUM" value="${existingTier?.name || ''}" />
        </div>

        <div class="form-group">
          <label class="form-label" for="tier-form-desc">Description</label>
          <textarea id="tier-form-desc" class="form-input" placeholder="Commercial tier benefits and eligibility">${existingTier?.description || ''}</textarea>
        </div>

        <div class="form-group">
          <label class="form-toggle-wrap">
            <input type="checkbox" id="tier-form-active" ${existingTier ? (existingTier.is_active ? 'checked' : '') : 'checked'} />
            <span style="font-size:var(--font-size-sm);font-weight:500;">Active Tier</span>
          </label>
          <div class="form-helper-text">CustomerTier is a master classification. Discount limits are configured under Discount Policies.</div>
        </div>
      `;

      global.DealFlowUI.showFormModal({
        title,
        size: 'md',
        formHtml,
        submitLabel: isEdit ? 'Update Tier' : 'Create Tier',
        onSubmit: async (form, setErrorMessage) => {
          const name = document.getElementById('tier-form-name').value.trim();
          const desc = document.getElementById('tier-form-desc').value.trim() || null;
          const is_active = document.getElementById('tier-form-active').checked;

          if (!name) {
            setErrorMessage('Tier name is required.');
            throw new Error('Validation error');
          }

          const payload = { name, description: desc, is_active };

          try {
            if (isEdit) {
              await global.CustomerTiersAPI.update(existingTier.id, payload);
              global.DealFlowUI.showToast(`Tier ${name} updated.`, 'teal');
            } else {
              await global.CustomerTiersAPI.create(payload);
              global.DealFlowUI.showToast(`Tier ${name} created.`, 'teal');
            }
            this.loadTiersData(canWrite);
          } catch (err) {
            setErrorMessage(err.message || 'Operation failed.');
            throw err;
          }
        }
      });
    }
  };

  global.CustomersView = CustomersView;
})(typeof window !== 'undefined' ? window : this);
