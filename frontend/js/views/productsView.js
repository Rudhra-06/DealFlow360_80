/**
 * DealFlow360 — Products & Product Categories View Controller
 */
(function (global) {
  'use strict';

  let currentTab = 'products'; // 'products' or 'categories'
  let productsFilter = { search: '', category_id: '', is_active: '', limit: 20, offset: 0 };
  let categoriesFilter = { is_active: '', limit: 20, offset: 0 };
  let categoriesCache = [];

  const ProductsView = {
    async render(container, initialTab = 'products') {
      currentTab = initialTab || 'products';
      const currentUser = global.DealFlowAuth.getCurrentUser();
      const roleName = currentUser?.role?.name || 'ADMIN';
      const canWriteProduct = ['ADMIN', 'FINANCE_OPERATIONS'].includes(roleName.toUpperCase());
      const canWriteCategory = ['ADMIN', 'FINANCE_OPERATIONS'].includes(roleName.toUpperCase());

      container.innerHTML = `
        <div class="view-header animate-fade-in">
          <div class="tabs-nav">
            <button class="tab-btn ${currentTab === 'products' ? 'active' : ''}" id="tab-btn-products">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
              <span>Products Catalog</span>
            </button>
            <button class="tab-btn ${currentTab === 'categories' ? 'active' : ''}" id="tab-btn-categories">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 9h16M4 15h16M10 3L8 21M16 3l-2 18"/></svg>
              <span>Product Categories</span>
            </button>
          </div>

          <div id="products-subview-content"></div>
        </div>
      `;

      document.getElementById('tab-btn-products').addEventListener('click', () => {
        currentTab = 'products';
        this.render(container, 'products');
      });

      document.getElementById('tab-btn-categories').addEventListener('click', () => {
        currentTab = 'categories';
        this.render(container, 'categories');
      });

      const subviewContainer = document.getElementById('products-subview-content');

      try {
        categoriesCache = await global.ProductCategoriesAPI.list({ limit: 100 });
      } catch (e) {
        categoriesCache = [];
      }

      if (currentTab === 'products') {
        await this.renderProductsTab(subviewContainer, canWriteProduct);
      } else {
        await this.renderCategoriesTab(subviewContainer, canWriteCategory);
      }
    },

    async renderProductsTab(container, canWrite) {
      container.innerHTML = `
        <div class="filter-toolbar">
          <div class="filter-group-left">
            <div class="search-input-wrap">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input type="text" id="prod-search" class="form-input" placeholder="Search by SKU or name..." value="${productsFilter.search}" />
            </div>

            <select id="prod-category-filter" class="filter-select">
              <option value="">All Categories</option>
              ${categoriesCache.map(c => `<option value="${c.id}" ${productsFilter.category_id == c.id ? 'selected' : ''}>${c.name}</option>`).join('')}
            </select>

            <select id="prod-status-filter" class="filter-select">
              <option value="">All Statuses</option>
              <option value="true" ${productsFilter.is_active === 'true' ? 'selected' : ''}>Active</option>
              <option value="false" ${productsFilter.is_active === 'false' ? 'selected' : ''}>Inactive</option>
            </select>
          </div>

          <div>
            ${canWrite ? `
              <button class="btn btn-primary btn-sm" id="btn-add-product">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                <span>Add Product</span>
              </button>
            ` : ''}
          </div>
        </div>

        <div class="table-card">
          <div class="table-responsive">
            <table class="data-table">
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Product Name</th>
                  <th>Category</th>
                  <th>List Price</th>
                  <th>Cost Price</th>
                  <th>Unit</th>
                  <th>Status</th>
                  <th style="text-align:right;">Actions</th>
                </tr>
              </thead>
              <tbody id="products-table-body">
                <tr><td colspan="8" style="text-align:center; padding: 2rem;"><span class="spinner spinner-teal"></span> Loading products...</td></tr>
              </tbody>
            </table>
          </div>
          <div class="table-pagination">
            <span id="prod-pagination-info">Showing records</span>
            <div class="pagination-controls">
              <button class="btn btn-secondary btn-sm" id="prod-prev-btn" disabled>Previous</button>
              <button class="btn btn-secondary btn-sm" id="prod-next-btn">Next</button>
            </div>
          </div>
        </div>
      `;

      let searchTimeout = null;
      document.getElementById('prod-search').addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
          productsFilter.search = e.target.value.trim();
          productsFilter.offset = 0;
          this.loadProductsData(canWrite);
        }, 300);
      });

      document.getElementById('prod-category-filter').addEventListener('change', (e) => {
        productsFilter.category_id = e.target.value;
        productsFilter.offset = 0;
        this.loadProductsData(canWrite);
      });

      document.getElementById('prod-status-filter').addEventListener('change', (e) => {
        productsFilter.is_active = e.target.value;
        productsFilter.offset = 0;
        this.loadProductsData(canWrite);
      });

      document.getElementById('prod-prev-btn').addEventListener('click', () => {
        if (productsFilter.offset >= productsFilter.limit) {
          productsFilter.offset -= productsFilter.limit;
          this.loadProductsData(canWrite);
        }
      });

      document.getElementById('prod-next-btn').addEventListener('click', () => {
        productsFilter.offset += productsFilter.limit;
        this.loadProductsData(canWrite);
      });

      if (canWrite) {
        document.getElementById('btn-add-product').addEventListener('click', () => {
          this.openProductFormModal(null, canWrite);
        });
      }

      await this.loadProductsData(canWrite);
    },

    async loadProductsData(canWrite) {
      const tbody = document.getElementById('products-table-body');
      const prevBtn = document.getElementById('prod-prev-btn');
      const nextBtn = document.getElementById('prod-next-btn');
      const infoEl = document.getElementById('prod-pagination-info');

      try {
        const list = await global.ProductsAPI.list(productsFilter);

        if (!list || list.length === 0) {
          tbody.innerHTML = `
            <tr>
              <td colspan="8">
                <div class="table-empty-state">
                  <div class="table-empty-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
                  </div>
                  <h4 style="color:var(--color-navy);">No Products Found</h4>
                  <p style="font-size:var(--font-size-xs);">Try adjusting your category filter or search keywords.</p>
                </div>
              </td>
            </tr>
          `;
          if (infoEl) infoEl.textContent = `Page ${Math.floor(productsFilter.offset / productsFilter.limit) + 1}`;
          if (prevBtn) prevBtn.disabled = productsFilter.offset === 0;
          if (nextBtn) nextBtn.disabled = true;
          return;
        }

        let html = '';
        list.forEach(p => {
          const categoryName = p.category ? p.category.name : '—';
          const listPrice = `${p.currency} ${Number(p.list_price || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
          const costPrice = `${p.currency} ${Number(p.cost_price || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
          const statusBadge = p.is_active
            ? `<span class="badge badge-teal"><span class="status-dot status-dot-teal"></span>Active</span>`
            : `<span class="badge badge-gray"><span class="status-dot status-dot-gray"></span>Inactive</span>`;

          html += `
            <tr data-prod-id="${p.id}" style="cursor:pointer;">
              <td><span class="table-code">${p.sku}</span></td>
              <td><span class="table-primary-text">${p.name}</span></td>
              <td><span class="badge badge-navy">${categoryName}</span></td>
              <td><span style="font-weight:600; color:var(--color-navy);">${listPrice}</span></td>
              <td><span class="table-secondary-text">${costPrice}</span></td>
              <td>${p.unit_of_measure}</td>
              <td>${statusBadge}</td>
              <td style="text-align:right;" onclick="event.stopPropagation();">
                <button class="btn btn-ghost btn-sm view-prod-btn" data-id="${p.id}">View</button>
                ${canWrite ? `<button class="btn btn-secondary btn-sm edit-prod-btn" data-id="${p.id}">Edit</button>` : ''}
              </td>
            </tr>
          `;
        });

        tbody.innerHTML = html;

        tbody.querySelectorAll('tr').forEach(row => {
          row.addEventListener('click', () => {
            const id = row.getAttribute('data-prod-id');
            const prod = list.find(x => x.id == id);
            if (prod) ProductsView.openProductDetailsDrawer(prod, canWrite);
          });
        });

        tbody.querySelectorAll('.view-prod-btn').forEach(btn => {
          btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = btn.getAttribute('data-id');
            const prod = list.find(x => x.id == id);
            if (prod) ProductsView.openProductDetailsDrawer(prod, canWrite);
          });
        });

        tbody.querySelectorAll('.edit-prod-btn').forEach(btn => {
          btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = btn.getAttribute('data-id');
            const prod = list.find(x => x.id == id);
            if (prod) ProductsView.openProductFormModal(prod, canWrite);
          });
        });

        const page = Math.floor(productsFilter.offset / productsFilter.limit) + 1;
        if (infoEl) infoEl.textContent = `Page ${page} (${list.length} products)`;
        if (prevBtn) prevBtn.disabled = productsFilter.offset === 0;
        if (nextBtn) nextBtn.disabled = list.length < productsFilter.limit;
      } catch (err) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding: 2rem; color: var(--color-coral);">${err.message || 'Failed to load products.'}</td></tr>`;
      }
    },

    async openProductDetailsDrawer(prod, canWrite) {
      const categoryName = prod.category ? prod.category.name : 'None';
      const listPrice = `${prod.currency} ${Number(prod.list_price || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      const costPrice = `${prod.currency} ${Number(prod.cost_price || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

      // Fetch real inventory stock for this product
      let stockHtml = '<div style="font-size:var(--font-size-xs);color:var(--color-text-secondary);">Loading warehouse stock...</div>';

      const contentHtml = `
        <div>
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
            <div class="user-avatar" style="width:48px;height:48px;font-size:16px;background:var(--color-navy);">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
            </div>
            <div>
              <h3 style="color:var(--color-navy);margin-bottom:2px;">${prod.name}</h3>
              <span class="table-code">${prod.sku}</span>
            </div>
          </div>

          <div class="drawer-section-title">Pricing & Category</div>
          <div class="key-value-list">
            <div class="key-value-item">
              <span class="key-label">Product Category</span>
              <span class="key-value"><span class="badge badge-navy">${categoryName}</span></span>
            </div>
            <div class="key-value-item">
              <span class="key-label">List Price</span>
              <span class="key-value" style="color:var(--color-teal);">${listPrice}</span>
            </div>
            <div class="key-value-item">
              <span class="key-label">Cost Price</span>
              <span class="key-value">${costPrice}</span>
            </div>
            <div class="key-value-item">
              <span class="key-label">Unit of Measure</span>
              <span class="key-value">${prod.unit_of_measure}</span>
            </div>
            <div class="key-value-item">
              <span class="key-label">Status</span>
              <span class="key-value">
                ${prod.is_active ? '<span class="badge badge-teal"><span class="status-dot status-dot-teal"></span>Active</span>' : '<span class="badge badge-gray">Inactive</span>'}
              </span>
            </div>
          </div>

          <div class="drawer-section-title" style="margin-top:20px;">Description</div>
          <p style="font-size:var(--font-size-sm);color:var(--color-text);">${prod.description || 'No description provided.'}</p>

          <div class="drawer-section-title" style="margin-top:20px;">Warehouse Stock Availability</div>
          <div id="drawer-product-stock-container">${stockHtml}</div>
        </div>
      `;

      const footerHtml = canWrite ? `
        <button class="btn btn-secondary btn-sm" id="drawer-edit-prod-btn">Edit Product</button>
      ` : '';

      global.DealFlowUI.showDrawer({
        title: 'Product Catalog Details',
        contentHtml,
        footerHtml
      });

      if (canWrite) {
        document.getElementById('drawer-edit-prod-btn')?.addEventListener('click', () => {
          document.getElementById('dealflow-drawer-backdrop')?.click();
          this.openProductFormModal(prod, canWrite);
        });
      }

      // Load stock asynchronously
      try {
        const invList = await global.InventoryAPI.list({ product_id: prod.id });
        const container = document.getElementById('drawer-product-stock-container');
        if (container) {
          if (!invList || invList.length === 0) {
            container.innerHTML = `<div style="font-size:var(--font-size-xs);color:var(--color-text-muted);">No warehouse stock records configured for this product.</div>`;
          } else {
            let invHtml = '<div class="key-value-list">';
            invList.forEach(inv => {
              const whName = inv.warehouse ? inv.warehouse.name : `Warehouse #${inv.warehouse_id}`;
              invHtml += `
                <div class="key-value-item">
                  <span class="key-label">${whName}</span>
                  <span class="key-value">
                    <span style="font-weight:600;">${inv.available_qty}</span> avail 
                    <span style="color:var(--color-text-muted);font-size:var(--font-size-xs);">(${inv.on_hand_qty} on-hand, ${inv.reserved_qty} reserved)</span>
                  </span>
                </div>
              `;
            });
            invHtml += '</div>';
            container.innerHTML = invHtml;
          }
        }
      } catch (e) {
        const container = document.getElementById('drawer-product-stock-container');
        if (container) container.innerHTML = `<div style="font-size:var(--font-size-xs);color:var(--color-coral);">Unable to load inventory.</div>`;
      }
    },

    openProductFormModal(existingProduct, canWrite) {
      const isEdit = Boolean(existingProduct);
      const title = isEdit ? `Edit Product: ${existingProduct.sku}` : 'Add New Product';

      const activeCategories = categoriesCache.filter(c => c.is_active || (existingProduct && c.id === existingProduct.category_id));

      const formHtml = `
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label" for="prod-form-sku">SKU Code *</label>
            <input type="text" id="prod-form-sku" class="form-input" required placeholder="e.g. SKU-1001" value="${existingProduct?.sku || ''}" />
          </div>
          <div class="form-group">
            <label class="form-label" for="prod-form-name">Product Name *</label>
            <input type="text" id="prod-form-name" class="form-input" required placeholder="e.g. Enterprise Server Blade" value="${existingProduct?.name || ''}" />
          </div>
        </div>

        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label" for="prod-form-category">Product Category *</label>
            <select id="prod-form-category" class="form-input" required>
              <option value="">Select Category...</option>
              ${activeCategories.map(c => `<option value="${c.id}" ${existingProduct?.category_id == c.id ? 'selected' : ''}>${c.name}</option>`).join('')}
            </select>
          </div>
          <div class="form-group">
            <label class="form-label" for="prod-form-unit">Unit of Measure *</label>
            <input type="text" id="prod-form-unit" class="form-input" required placeholder="EA, BOX, UNIT, HR" value="${existingProduct?.unit_of_measure || 'EA'}" />
          </div>
        </div>

        <div class="form-grid-3">
          <div class="form-group">
            <label class="form-label" for="prod-form-list-price">List Price *</label>
            <input type="number" step="0.01" min="0" id="prod-form-list-price" class="form-input" required value="${existingProduct?.list_price ?? '0.00'}" />
          </div>
          <div class="form-group">
            <label class="form-label" for="prod-form-cost-price">Cost Price *</label>
            <input type="number" step="0.01" min="0" id="prod-form-cost-price" class="form-input" required value="${existingProduct?.cost_price ?? '0.00'}" />
          </div>
          <div class="form-group">
            <label class="form-label" for="prod-form-currency">Currency (3 Letters) *</label>
            <input type="text" id="prod-form-currency" class="form-input" maxlength="3" required placeholder="USD" value="${existingProduct?.currency || 'USD'}" />
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="prod-form-desc">Description</label>
          <textarea id="prod-form-desc" class="form-input" style="height:60px;" placeholder="Product specifications and commercial overview">${existingProduct?.description || ''}</textarea>
        </div>

        <div class="form-group">
          <label class="form-toggle-wrap">
            <input type="checkbox" id="prod-form-active" ${existingProduct ? (existingProduct.is_active ? 'checked' : '') : 'checked'} />
            <span style="font-size:var(--font-size-sm);font-weight:500;">Active in Catalog</span>
          </label>
        </div>
      `;

      global.DealFlowUI.showFormModal({
        title,
        size: 'lg',
        formHtml,
        submitLabel: isEdit ? 'Update Product' : 'Create Product',
        onSubmit: async (form, setErrorMessage) => {
          const sku = document.getElementById('prod-form-sku').value.trim();
          const name = document.getElementById('prod-form-name').value.trim();
          const category_id = parseInt(document.getElementById('prod-form-category').value, 10);
          const unit = document.getElementById('prod-form-unit').value.trim();
          const list_price = document.getElementById('prod-form-list-price').value.trim();
          const cost_price = document.getElementById('prod-form-cost-price').value.trim();
          const currency = document.getElementById('prod-form-currency').value.trim().toUpperCase();
          const desc = document.getElementById('prod-form-desc').value.trim() || null;
          const is_active = document.getElementById('prod-form-active').checked;

          if (!sku || !name || isNaN(category_id) || !unit) {
            setErrorMessage('Please fill in all required product fields.');
            throw new Error('Validation failed');
          }

          const payload = {
            sku,
            name,
            category_id,
            unit_of_measure: unit,
            list_price,
            cost_price,
            currency,
            description: desc,
            is_active
          };

          try {
            if (isEdit) {
              await global.ProductsAPI.update(existingProduct.id, payload);
              global.DealFlowUI.showToast(`Product ${sku} updated.`, 'teal');
            } else {
              await global.ProductsAPI.create(payload);
              global.DealFlowUI.showToast(`Product ${sku} created.`, 'teal');
            }
            this.loadProductsData(canWrite);
          } catch (err) {
            setErrorMessage(err.message || 'Operation failed.');
            throw err;
          }
        }
      });
    },

    // Categories Tab
    async renderCategoriesTab(container, canWrite) {
      container.innerHTML = `
        <div class="filter-toolbar">
          <div class="filter-group-left">
            <select id="cat-status-filter" class="filter-select">
              <option value="">All Statuses</option>
              <option value="true" ${categoriesFilter.is_active === 'true' ? 'selected' : ''}>Active</option>
              <option value="false" ${categoriesFilter.is_active === 'false' ? 'selected' : ''}>Inactive</option>
            </select>
          </div>

          <div>
            ${canWrite ? `
              <button class="btn btn-primary btn-sm" id="btn-add-category">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                <span>Add Category</span>
              </button>
            ` : ''}
          </div>
        </div>

        <div class="table-card">
          <div class="table-responsive">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Category Name</th>
                  <th>Description</th>
                  <th>Status</th>
                  <th>Updated</th>
                  <th style="text-align:right;">Actions</th>
                </tr>
              </thead>
              <tbody id="categories-table-body">
                <tr><td colspan="5" style="text-align:center; padding: 2rem;"><span class="spinner spinner-teal"></span> Loading categories...</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      `;

      document.getElementById('cat-status-filter').addEventListener('change', (e) => {
        categoriesFilter.is_active = e.target.value;
        this.loadCategoriesData(canWrite);
      });

      if (canWrite) {
        document.getElementById('btn-add-category').addEventListener('click', () => {
          this.openCategoryFormModal(null, canWrite);
        });
      }

      await this.loadCategoriesData(canWrite);
    },

    async loadCategoriesData(canWrite) {
      const tbody = document.getElementById('categories-table-body');
      try {
        const list = await global.ProductCategoriesAPI.list(categoriesFilter);
        categoriesCache = list;

        if (!list || list.length === 0) {
          tbody.innerHTML = `
            <tr>
              <td colspan="5">
                <div class="table-empty-state">
                  <h4 style="color:var(--color-navy);">No Product Categories</h4>
                  <p style="font-size:var(--font-size-xs);">Create product categories to organize items in your commercial catalog.</p>
                </div>
              </td>
            </tr>
          `;
          return;
        }

        let html = '';
        list.forEach(c => {
          const statusBadge = c.is_active
            ? `<span class="badge badge-teal"><span class="status-dot status-dot-teal"></span>Active</span>`
            : `<span class="badge badge-gray">Inactive</span>`;

          html += `
            <tr>
              <td><span class="table-primary-text">${c.name}</span></td>
              <td><span class="table-secondary-text">${c.description || '—'}</span></td>
              <td>${statusBadge}</td>
              <td><span style="font-size:var(--font-size-xs);">${new Date(c.updated_at).toLocaleDateString()}</span></td>
              <td style="text-align:right;">
                ${canWrite ? `<button class="btn btn-secondary btn-sm edit-cat-btn" data-id="${c.id}">Edit</button>` : '—'}
              </td>
            </tr>
          `;
        });

        tbody.innerHTML = html;

        tbody.querySelectorAll('.edit-cat-btn').forEach(btn => {
          btn.addEventListener('click', () => {
            const id = btn.getAttribute('data-id');
            const cat = list.find(x => x.id == id);
            if (cat) this.openCategoryFormModal(cat, canWrite);
          });
        });
      } catch (err) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 2rem; color: var(--color-coral);">${err.message || 'Failed to load categories.'}</td></tr>`;
      }
    },

    openCategoryFormModal(existingCategory, canWrite) {
      const isEdit = Boolean(existingCategory);
      const title = isEdit ? `Edit Category: ${existingCategory.name}` : 'Add Product Category';

      const formHtml = `
        <div class="form-group">
          <label class="form-label" for="cat-form-name">Category Name *</label>
          <input type="text" id="cat-form-name" class="form-input" required placeholder="e.g. Hardware, Cloud Services" value="${existingCategory?.name || ''}" />
        </div>

        <div class="form-group">
          <label class="form-label" for="cat-form-desc">Description</label>
          <textarea id="cat-form-desc" class="form-input" placeholder="Category classification details">${existingCategory?.description || ''}</textarea>
        </div>

        <div class="form-group">
          <label class="form-toggle-wrap">
            <input type="checkbox" id="cat-form-active" ${existingCategory ? (existingCategory.is_active ? 'checked' : '') : 'checked'} />
            <span style="font-size:var(--font-size-sm);font-weight:500;">Active Category</span>
          </label>
        </div>
      `;

      global.DealFlowUI.showFormModal({
        title,
        size: 'md',
        formHtml,
        submitLabel: isEdit ? 'Update Category' : 'Create Category',
        onSubmit: async (form, setErrorMessage) => {
          const name = document.getElementById('cat-form-name').value.trim();
          const desc = document.getElementById('cat-form-desc').value.trim() || null;
          const is_active = document.getElementById('cat-form-active').checked;

          if (!name) {
            setErrorMessage('Category name is required.');
            throw new Error('Validation error');
          }

          const payload = { name, description: desc, is_active };

          try {
            if (isEdit) {
              await global.ProductCategoriesAPI.update(existingCategory.id, payload);
              global.DealFlowUI.showToast(`Category ${name} updated.`, 'teal');
            } else {
              await global.ProductCategoriesAPI.create(payload);
              global.DealFlowUI.showToast(`Category ${name} created.`, 'teal');
            }
            this.loadCategoriesData(canWrite);
          } catch (err) {
            setErrorMessage(err.message || 'Operation failed.');
            throw err;
          }
        }
      });
    }
  };

  global.ProductsView = ProductsView;
})(typeof window !== 'undefined' ? window : this);
