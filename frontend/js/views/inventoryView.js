/**
 * DealFlow360 — Inventory Overview & Warehouses View Controller
 */
(function (global) {
  'use strict';

  let currentTab = 'inventory'; // 'inventory' or 'warehouses'
  let inventoryFilter = { warehouse_id: '', product_id: '', limit: 20, offset: 0 };
  let warehousesFilter = { is_active: '', limit: 20, offset: 0 };
  let warehousesCache = [];
  let productsCache = [];

  const InventoryView = {
    async render(container, initialTab = 'inventory') {
      currentTab = initialTab || 'inventory';
      const currentUser = global.DealFlowAuth.getCurrentUser();
      const roleName = currentUser?.role?.name || 'ADMIN';
      const canWrite = ['ADMIN', 'FINANCE_OPERATIONS'].includes(roleName.toUpperCase());

      container.innerHTML = `
        <div class="view-header animate-fade-in">
          <div class="tabs-nav">
            <button class="tab-btn ${currentTab === 'inventory' ? 'active' : ''}" id="tab-btn-inventory">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
              <span>Inventory Stock Overview</span>
            </button>
            <button class="tab-btn ${currentTab === 'warehouses' ? 'active' : ''}" id="tab-btn-warehouses">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
              <span>Warehouses</span>
            </button>
          </div>

          <div id="inventory-subview-content"></div>
        </div>
      `;

      document.getElementById('tab-btn-inventory').addEventListener('click', () => {
        currentTab = 'inventory';
        this.render(container, 'inventory');
      });

      document.getElementById('tab-btn-warehouses').addEventListener('click', () => {
        currentTab = 'warehouses';
        this.render(container, 'warehouses');
      });

      const subviewContainer = document.getElementById('inventory-subview-content');

      try {
        [warehousesCache, productsCache] = await Promise.all([
          global.WarehousesAPI.list({ limit: 100 }),
          global.ProductsAPI.list({ limit: 100 })
        ]);
      } catch (e) {
        warehousesCache = [];
        productsCache = [];
      }

      if (currentTab === 'inventory') {
        await this.renderInventoryTab(subviewContainer, canWrite);
      } else {
        await this.renderWarehousesTab(subviewContainer, canWrite);
      }
    },

    async renderInventoryTab(container, canWrite) {
      container.innerHTML = `
        <div class="filter-toolbar">
          <div class="filter-group-left">
            <select id="inv-warehouse-filter" class="filter-select">
              <option value="">All Warehouses</option>
              ${warehousesCache.map(w => `<option value="${w.id}" ${inventoryFilter.warehouse_id == w.id ? 'selected' : ''}>${w.name} (${w.code})</option>`).join('')}
            </select>

            <select id="inv-product-filter" class="filter-select">
              <option value="">All Products</option>
              ${productsCache.map(p => `<option value="${p.id}" ${inventoryFilter.product_id == p.id ? 'selected' : ''}>${p.name} (${p.sku})</option>`).join('')}
            </select>
          </div>

          <div>
            ${canWrite ? `
              <button class="btn btn-primary btn-sm" id="btn-add-inventory">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                <span>Add Stock Record</span>
              </button>
            ` : ''}
          </div>
        </div>

        <div class="table-card">
          <div class="table-responsive">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Product SKU</th>
                  <th>Product Name</th>
                  <th>Warehouse</th>
                  <th>On Hand</th>
                  <th>Reserved</th>
                  <th>Available</th>
                  <th>Reorder Level</th>
                  <th>Stock Status</th>
                  <th style="text-align:right;">Actions</th>
                </tr>
              </thead>
              <tbody id="inventory-table-body">
                <tr><td colspan="9" style="text-align:center; padding: 2rem;"><span class="spinner spinner-teal"></span> Loading inventory...</td></tr>
              </tbody>
            </table>
          </div>
          <div class="table-pagination">
            <span id="inv-pagination-info">Showing records</span>
            <div class="pagination-controls">
              <button class="btn btn-secondary btn-sm" id="inv-prev-btn" disabled>Previous</button>
              <button class="btn btn-secondary btn-sm" id="inv-next-btn">Next</button>
            </div>
          </div>
        </div>
      `;

      document.getElementById('inv-warehouse-filter').addEventListener('change', (e) => {
        inventoryFilter.warehouse_id = e.target.value;
        inventoryFilter.offset = 0;
        this.loadInventoryData(canWrite);
      });

      document.getElementById('inv-product-filter').addEventListener('change', (e) => {
        inventoryFilter.product_id = e.target.value;
        inventoryFilter.offset = 0;
        this.loadInventoryData(canWrite);
      });

      document.getElementById('inv-prev-btn').addEventListener('click', () => {
        if (inventoryFilter.offset >= inventoryFilter.limit) {
          inventoryFilter.offset -= inventoryFilter.limit;
          this.loadInventoryData(canWrite);
        }
      });

      document.getElementById('inv-next-btn').addEventListener('click', () => {
        inventoryFilter.offset += inventoryFilter.limit;
        this.loadInventoryData(canWrite);
      });

      if (canWrite) {
        document.getElementById('btn-add-inventory').addEventListener('click', () => {
          this.openInventoryCreateModal(canWrite);
        });
      }

      await this.loadInventoryData(canWrite);
    },

    async loadInventoryData(canWrite) {
      const tbody = document.getElementById('inventory-table-body');
      const prevBtn = document.getElementById('inv-prev-btn');
      const nextBtn = document.getElementById('inv-next-btn');
      const infoEl = document.getElementById('inv-pagination-info');

      try {
        const list = await global.InventoryAPI.list(inventoryFilter);

        if (!list || list.length === 0) {
          tbody.innerHTML = `
            <tr>
              <td colspan="9">
                <div class="table-empty-state">
                  <div class="table-empty-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
                  </div>
                  <h4 style="color:var(--color-navy);">No Inventory Records</h4>
                  <p style="font-size:var(--font-size-xs);">No stock allocations found for the selected filters.</p>
                </div>
              </td>
            </tr>
          `;
          if (infoEl) infoEl.textContent = `Page ${Math.floor(inventoryFilter.offset / inventoryFilter.limit) + 1}`;
          if (prevBtn) prevBtn.disabled = inventoryFilter.offset === 0;
          if (nextBtn) nextBtn.disabled = true;
          return;
        }

        let html = '';
        list.forEach(inv => {
          const sku = inv.product ? inv.product.sku : `Prod #${inv.product_id}`;
          const prodName = inv.product ? inv.product.name : '—';
          const whName = inv.warehouse ? inv.warehouse.name : `WH #${inv.warehouse_id}`;
          const avail = Number(inv.available_qty);
          const reorder = Number(inv.reorder_level);

          let statusBadge = `<span class="badge badge-teal"><span class="status-dot status-dot-teal"></span>Healthy</span>`;
          if (avail === 0) {
            statusBadge = `<span class="badge badge-coral"><span class="status-dot status-dot-coral"></span>Out of Stock</span>`;
          } else if (avail <= reorder) {
            statusBadge = `<span class="badge badge-gray" style="border-color:#e0b252;color:#855b00;"><span class="status-dot" style="background-color:#e0b252;"></span>Low Stock</span>`;
          }

          html += `
            <tr>
              <td><span class="table-code">${sku}</span></td>
              <td><span class="table-primary-text">${prodName}</span></td>
              <td><span class="badge badge-navy">${whName}</span></td>
              <td><strong>${inv.on_hand_qty}</strong></td>
              <td><span class="text-muted">${inv.reserved_qty}</span></td>
              <td><strong style="color:var(--color-teal);">${inv.available_qty}</strong></td>
              <td>${inv.reorder_level}</td>
              <td>${statusBadge}</td>
              <td style="text-align:right;">
                ${canWrite ? `<button class="btn btn-secondary btn-sm edit-inv-btn" data-id="${inv.id}">Adjust Stock</button>` : '—'}
              </td>
            </tr>
          `;
        });

        tbody.innerHTML = html;

        tbody.querySelectorAll('.edit-inv-btn').forEach(btn => {
          btn.addEventListener('click', () => {
            const id = btn.getAttribute('data-id');
            const inv = list.find(x => x.id == id);
            if (inv) this.openInventoryEditModal(inv, canWrite);
          });
        });

        const page = Math.floor(inventoryFilter.offset / inventoryFilter.limit) + 1;
        if (infoEl) infoEl.textContent = `Page ${page} (${list.length} records)`;
        if (prevBtn) prevBtn.disabled = inventoryFilter.offset === 0;
        if (nextBtn) nextBtn.disabled = list.length < inventoryFilter.limit;
      } catch (err) {
        tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding: 2rem; color: var(--color-coral);">${err.message || 'Failed to load inventory.'}</td></tr>`;
      }
    },

    openInventoryCreateModal(canWrite) {
      const activeWarehouses = warehousesCache.filter(w => w.is_active);
      const activeProducts = productsCache.filter(p => p.is_active);

      const formHtml = `
        <div class="form-group">
          <label class="form-label" for="inv-form-wh">Warehouse *</label>
          <select id="inv-form-wh" class="form-input" required>
            <option value="">Select Warehouse...</option>
            ${activeWarehouses.map(w => `<option value="${w.id}">${w.name} (${w.code})</option>`).join('')}
          </select>
        </div>

        <div class="form-group">
          <label class="form-label" for="inv-form-prod">Product *</label>
          <select id="inv-form-prod" class="form-input" required>
            <option value="">Select Product...</option>
            ${activeProducts.map(p => `<option value="${p.id}">${p.name} (${p.sku})</option>`).join('')}
          </select>
        </div>

        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label" for="inv-form-onhand">On Hand Quantity *</label>
            <input type="number" step="0.001" min="0" id="inv-form-onhand" class="form-input" required value="0.000" />
          </div>
          <div class="form-group">
            <label class="form-label" for="inv-form-reorder">Reorder Level *</label>
            <input type="number" step="0.001" min="0" id="inv-form-reorder" class="form-input" required value="10.000" />
          </div>
        </div>

        <div class="alert alert-navy" style="margin-top:10px;">
          <svg class="alert-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
          <span>Reserved Quantity is managed automatically by commercial reservations and cannot be manually entered.</span>
        </div>
      `;

      global.DealFlowUI.showFormModal({
        title: 'Add New Inventory Stock Record',
        size: 'md',
        formHtml,
        submitLabel: 'Create Record',
        onSubmit: async (form, setErrorMessage) => {
          const warehouse_id = parseInt(document.getElementById('inv-form-wh').value, 10);
          const product_id = parseInt(document.getElementById('inv-form-prod').value, 10);
          const on_hand_qty = document.getElementById('inv-form-onhand').value.trim();
          const reorder_level = document.getElementById('inv-form-reorder').value.trim();

          if (isNaN(warehouse_id) || isNaN(product_id) || !on_hand_qty || !reorder_level) {
            setErrorMessage('Please fill in all fields.');
            throw new Error('Validation error');
          }

          const payload = {
            warehouse_id,
            product_id,
            on_hand_qty,
            reorder_level
          };

          try {
            await global.InventoryAPI.create(payload);
            global.DealFlowUI.showToast('Inventory record created.', 'teal');
            this.loadInventoryData(canWrite);
          } catch (err) {
            setErrorMessage(err.message || 'Operation failed.');
            throw err;
          }
        }
      });
    },

    openInventoryEditModal(inv, canWrite) {
      const sku = inv.product ? inv.product.sku : `#${inv.product_id}`;
      const whName = inv.warehouse ? inv.warehouse.name : `#${inv.warehouse_id}`;

      const formHtml = `
        <div class="key-value-list" style="margin-bottom:16px;">
          <div class="key-value-item">
            <span class="key-label">Product</span>
            <span class="key-value">${inv.product?.name || '—'} (${sku})</span>
          </div>
          <div class="key-value-item">
            <span class="key-label">Warehouse</span>
            <span class="key-value">${whName}</span>
          </div>
          <div class="key-value-item">
            <span class="key-label">Reserved Stock (Read-Only)</span>
            <span class="key-value"><span class="badge badge-navy">${inv.reserved_qty}</span></span>
          </div>
        </div>

        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label" for="inv-edit-onhand">On Hand Quantity *</label>
            <input type="number" step="0.001" min="${inv.reserved_qty}" id="inv-edit-onhand" class="form-input" required value="${inv.on_hand_qty}" />
            <div class="form-helper-text">Cannot be lower than reserved stock (${inv.reserved_qty}).</div>
          </div>
          <div class="form-group">
            <label class="form-label" for="inv-edit-reorder">Reorder Level *</label>
            <input type="number" step="0.001" min="0" id="inv-edit-reorder" class="form-input" required value="${inv.reorder_level}" />
          </div>
        </div>
      `;

      global.DealFlowUI.showFormModal({
        title: `Adjust Inventory: ${sku}`,
        size: 'md',
        formHtml,
        submitLabel: 'Update Stock',
        onSubmit: async (form, setErrorMessage) => {
          const on_hand_qty = document.getElementById('inv-edit-onhand').value.trim();
          const reorder_level = document.getElementById('inv-edit-reorder').value.trim();

          if (Number(on_hand_qty) < Number(inv.reserved_qty)) {
            setErrorMessage('On-hand quantity cannot be lower than currently reserved stock.');
            throw new Error('Reserved stock validation error');
          }

          const payload = { on_hand_qty, reorder_level };

          try {
            await global.InventoryAPI.update(inv.id, payload);
            global.DealFlowUI.showToast('Inventory stock updated.', 'teal');
            this.loadInventoryData(canWrite);
          } catch (err) {
            setErrorMessage(err.message || 'Operation failed.');
            throw err;
          }
        }
      });
    },

    // Warehouses Tab
    async renderWarehousesTab(container, canWrite) {
      container.innerHTML = `
        <div class="filter-toolbar">
          <div class="filter-group-left">
            <select id="wh-status-filter" class="filter-select">
              <option value="">All Statuses</option>
              <option value="true" ${warehousesFilter.is_active === 'true' ? 'selected' : ''}>Active</option>
              <option value="false" ${warehousesFilter.is_active === 'false' ? 'selected' : ''}>Inactive</option>
            </select>
          </div>

          <div>
            ${canWrite ? `
              <button class="btn btn-primary btn-sm" id="btn-add-warehouse">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                <span>Add Warehouse</span>
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
                  <th>Warehouse Name</th>
                  <th>Location</th>
                  <th>Address</th>
                  <th>Status</th>
                  <th style="text-align:right;">Actions</th>
                </tr>
              </thead>
              <tbody id="warehouses-table-body">
                <tr><td colspan="6" style="text-align:center; padding: 2rem;"><span class="spinner spinner-teal"></span> Loading warehouses...</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      `;

      document.getElementById('wh-status-filter').addEventListener('change', (e) => {
        warehousesFilter.is_active = e.target.value;
        this.loadWarehousesData(canWrite);
      });

      if (canWrite) {
        document.getElementById('btn-add-warehouse').addEventListener('click', () => {
          this.openWarehouseFormModal(null, canWrite);
        });
      }

      await this.loadWarehousesData(canWrite);
    },

    async loadWarehousesData(canWrite) {
      const tbody = document.getElementById('warehouses-table-body');
      try {
        const list = await global.WarehousesAPI.list(warehousesFilter);
        warehousesCache = list;

        if (!list || list.length === 0) {
          tbody.innerHTML = `
            <tr>
              <td colspan="6">
                <div class="table-empty-state">
                  <h4 style="color:var(--color-navy);">No Warehouses Found</h4>
                  <p style="font-size:var(--font-size-xs);">Register physical warehouse facilities to track multi-location inventory.</p>
                </div>
              </td>
            </tr>
          `;
          return;
        }

        let html = '';
        list.forEach(w => {
          const statusBadge = w.is_active
            ? `<span class="badge badge-teal"><span class="status-dot status-dot-teal"></span>Active</span>`
            : `<span class="badge badge-gray">Inactive</span>`;

          html += `
            <tr>
              <td><span class="table-code">${w.code}</span></td>
              <td><span class="table-primary-text">${w.name}</span></td>
              <td>${w.location || '—'}</td>
              <td><span class="table-secondary-text">${w.address || '—'}</span></td>
              <td>${statusBadge}</td>
              <td style="text-align:right;">
                ${canWrite ? `<button class="btn btn-secondary btn-sm edit-wh-btn" data-id="${w.id}">Edit</button>` : '—'}
              </td>
            </tr>
          `;
        });

        tbody.innerHTML = html;

        tbody.querySelectorAll('.edit-wh-btn').forEach(btn => {
          btn.addEventListener('click', () => {
            const id = btn.getAttribute('data-id');
            const wh = list.find(x => x.id == id);
            if (wh) this.openWarehouseFormModal(wh, canWrite);
          });
        });
      } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 2rem; color: var(--color-coral);">${err.message || 'Failed to load warehouses.'}</td></tr>`;
      }
    },

    openWarehouseFormModal(existingWarehouse, canWrite) {
      const isEdit = Boolean(existingWarehouse);
      const title = isEdit ? `Edit Warehouse: ${existingWarehouse.code}` : 'Add New Warehouse';

      const formHtml = `
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label" for="wh-form-code">Warehouse Code *</label>
            <input type="text" id="wh-form-code" class="form-input" required placeholder="e.g. WH-EAST-01" value="${existingWarehouse?.code || ''}" />
          </div>
          <div class="form-group">
            <label class="form-label" for="wh-form-name">Warehouse Name *</label>
            <input type="text" id="wh-form-name" class="form-input" required placeholder="e.g. Central Logistics Hub" value="${existingWarehouse?.name || ''}" />
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="wh-form-location">Region / Location</label>
          <input type="text" id="wh-form-location" class="form-input" placeholder="e.g. North America - East" value="${existingWarehouse?.location || ''}" />
        </div>

        <div class="form-group">
          <label class="form-label" for="wh-form-address">Physical Facility Address</label>
          <textarea id="wh-form-address" class="form-input" style="height:60px;">${existingWarehouse?.address || ''}</textarea>
        </div>

        <div class="form-group">
          <label class="form-toggle-wrap">
            <input type="checkbox" id="wh-form-active" ${existingWarehouse ? (existingWarehouse.is_active ? 'checked' : '') : 'checked'} />
            <span style="font-size:var(--font-size-sm);font-weight:500;">Active Facility</span>
          </label>
        </div>
      `;

      global.DealFlowUI.showFormModal({
        title,
        size: 'md',
        formHtml,
        submitLabel: isEdit ? 'Update Warehouse' : 'Create Warehouse',
        onSubmit: async (form, setErrorMessage) => {
          const code = document.getElementById('wh-form-code').value.trim();
          const name = document.getElementById('wh-form-name').value.trim();
          const location = document.getElementById('wh-form-location').value.trim() || null;
          const address = document.getElementById('wh-form-address').value.trim() || null;
          const is_active = document.getElementById('wh-form-active').checked;

          if (!code || !name) {
            setErrorMessage('Code and Name are required.');
            throw new Error('Validation failed');
          }

          const payload = { code, name, location, address, is_active };

          try {
            if (isEdit) {
              await global.WarehousesAPI.update(existingWarehouse.id, payload);
              global.DealFlowUI.showToast(`Warehouse ${code} updated.`, 'teal');
            } else {
              await global.WarehousesAPI.create(payload);
              global.DealFlowUI.showToast(`Warehouse ${code} created.`, 'teal');
            }
            this.loadWarehousesData(canWrite);
          } catch (err) {
            setErrorMessage(err.message || 'Operation failed.');
            throw err;
          }
        }
      });
    }
  };

  global.InventoryView = InventoryView;
})(typeof window !== 'undefined' ? window : this);
