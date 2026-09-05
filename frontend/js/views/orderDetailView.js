/**
 * DealFlow360 — Order Detail & Fulfillment Workspace Controller
 * The main operational screen for Phase 5 covering fulfillment split, inventory reservation,
 * shipments, hybrid billing, payments, and audit timeline.
 */
(function (global) {
  'use strict';

  let currentOrder = null;
  let orderId = null;
  let activeTab = 'overview';
  let fulfillmentPreview = null;
  let fulfillmentPlan = null;
  let backorders = [];
  let shipments = [];
  let invoices = [];
  let subscriptions = [];
  let auditEvents = [];
  let warehouses = [];

  async function render(container, params = {}) {
    orderId = params.orderId || (params.id ? parseInt(params.id, 10) : null);

    if (!orderId) {
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 40px;">
          <h3>No Order Selected</h3>
          <p style="color: var(--color-text-secondary); margin-bottom: 20px;">Please select an order from the Sales Orders list.</p>
          <button class="btn btn-primary" onclick="window.DealFlowApp.switchView('orders');">Back to Orders</button>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div id="order-detail-wrapper" class="animate-fade-in">
        <div style="text-align: center; padding: 60px;"><span class="spinner spinner-teal"></span> Loading sales order workspace...</div>
      </div>
    `;

    await loadInitialData();
  }

  async function loadInitialData() {
    try {
      const [orderRes, whRes] = await Promise.all([
        global.OrdersAPI.get(orderId),
        global.WarehousesAPI ? global.WarehousesAPI.list({ limit: 50 }) : Promise.resolve({ ok: true, data: [] })
      ]);

      if (!orderRes.ok) {
        document.getElementById('order-detail-wrapper').innerHTML = `
          <div class="alert alert-coral" style="margin: 20px;">
            <span>Failed to load sales order: ${orderRes.data?.detail || orderRes.error || 'Order not found'}</span>
          </div>
          <button class="btn btn-secondary" onclick="window.DealFlowApp.switchView('orders');">Back to Orders</button>
        `;
        return;
      }

      currentOrder = orderRes.data;
      warehouses = whRes.ok ? whRes.data : [];

      renderWorkspace();
    } catch (err) {
      console.error('Error initializing order detail:', err);
      document.getElementById('order-detail-wrapper').innerHTML = `
        <div class="alert alert-coral" style="margin: 20px;">
          <span>Error connecting to Order services.</span>
        </div>
      `;
    }
  }

  function renderWorkspace() {
    const wrapper = document.getElementById('order-detail-wrapper');
    if (!wrapper || !currentOrder) return;

    const o = currentOrder;
    const custName = o.customer ? o.customer.name : `Customer #${o.customer_id}`;
    const confirmedAt = o.customer_confirmed_at ? new Date(o.customer_confirmed_at).toLocaleString() : new Date(o.created_at).toLocaleString();

    wrapper.innerHTML = `
      <!-- Order Header Card -->
      <div class="order-detail-header">
        <div class="order-detail-top">
          <div>
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
              <button class="btn btn-secondary btn-sm" onclick="window.DealFlowApp.switchView('orders');" style="padding: 2px 8px; font-size: 0.75rem;">
                &larr; All Orders
              </button>
              ${formatOrderStatusBadge(o.status)}
            </div>
            <div class="order-number-title">
              <span>${o.order_number}</span>
            </div>
            <div class="order-customer-sub">
              ${custName} &bull; Payment Terms: <strong>Net ${o.payment_terms_days} Days</strong>
            </div>
          </div>

          <div style="text-align: right;">
            <div style="font-size: 0.75rem; color: var(--color-text-secondary); text-transform: uppercase; font-weight: 600;">Net Order Total</div>
            <div style="font-size: 1.75rem; font-weight: 800; color: var(--color-navy); font-family: monospace;">
              ${o.currency} ${Number(o.net_total).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div style="font-size: 0.75rem; color: var(--color-text-muted); margin-top: 2px;">Confirmed ${confirmedAt}</div>
          </div>
        </div>

        <!-- Traceability Ribbon -->
        <div class="traceability-ribbon">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          <span>Created from confirmed commercial agreement:</span>
          <span>Source Quotation: <strong class="traceability-link" id="link-view-source-quote">#${o.quotation_id}</strong></span>
          <span>Confirmed Revision: <strong>v${o.confirmed_quote_version_id || 1}</strong></span>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <div class="order-tabs-nav">
        <button class="order-tab-btn ${activeTab === 'overview' ? 'active' : ''}" data-tab="overview">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>
          <span>Overview & Items</span>
        </button>
        <button class="order-tab-btn ${activeTab === 'fulfillment' ? 'active' : ''}" data-tab="fulfillment">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
          <span>Fulfillment & Split</span>
        </button>
        <button class="order-tab-btn ${activeTab === 'shipments' ? 'active' : ''}" data-tab="shipments">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="16" height="13" x="2" y="5" rx="2"/><path d="M16 8h4l3 3v5h-7V8z"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>
          <span>Shipments</span>
        </button>
        <button class="order-tab-btn ${activeTab === 'billing' ? 'active' : ''}" data-tab="billing">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>
          <span>Hybrid Billing & Subscriptions</span>
        </button>
        <button class="order-tab-btn ${activeTab === 'payments' ? 'active' : ''}" data-tab="payments">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
          <span>Payments</span>
        </button>
        <button class="order-tab-btn ${activeTab === 'audit' ? 'active' : ''}" data-tab="audit">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 14 14"></polyline></svg>
          <span>Order Audit</span>
        </button>
      </div>

      <!-- Tab Content Area -->
      <div id="order-tab-content" class="animate-fade-in">
        <!-- Rendered by renderActiveTab() -->
      </div>
    `;

    setupHeaderEvents();
    renderActiveTab();
  }

  function setupHeaderEvents() {
    const linkQuote = document.getElementById('link-view-source-quote');
    linkQuote?.addEventListener('click', () => {
      window.DealFlowApp.switchView('quotation-builder', { quoteId: currentOrder.quotation_id });
    });

    document.querySelectorAll('.order-tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.order-tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeTab = btn.dataset.tab;
        renderActiveTab();
      });
    });
  }

  async function renderActiveTab() {
    const container = document.getElementById('order-tab-content');
    if (!container) return;

    switch (activeTab) {
      case 'overview':
        renderOverviewTab(container);
        break;
      case 'fulfillment':
        await renderFulfillmentTab(container);
        break;
      case 'shipments':
        await renderShipmentsTab(container);
        break;
      case 'billing':
        await renderBillingTab(container);
        break;
      case 'payments':
        await renderPaymentsTab(container);
        break;
      case 'audit':
        await renderAuditTab(container);
        break;
    }
  }

  /* ==========================================================================
     TAB 1: Overview & Items
     ========================================================================== */
  function renderOverviewTab(container) {
    const o = currentOrder;

    container.innerHTML = `
      <!-- Financial Summary Cards -->
      <div class="order-summary-grid">
        <div class="order-summary-card">
          <label>Gross Subtotal</label>
          <div class="val">${o.currency} ${Number(o.gross_subtotal).toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
        </div>
        <div class="order-summary-card">
          <label>Total Discounts</label>
          <div class="val" style="color: var(--color-coral);">- ${o.currency} ${Number(o.discount_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
        </div>
        <div class="order-summary-card">
          <label>Net Total</label>
          <div class="val" style="color: var(--color-teal);">${o.currency} ${Number(o.net_total).toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
        </div>
        <div class="order-summary-card">
          <label>Commercial Margin</label>
          <div class="val">${Number(o.margin_pct).toFixed(1)}% <span style="font-size: 0.75rem; color: var(--color-text-secondary);">(${o.currency} ${Number(o.margin_amount).toFixed(2)})</span></div>
        </div>
      </div>

      <!-- Order Lines Table -->
      <div class="card" style="padding: 0; overflow: hidden; margin-bottom: var(--space-lg);">
        <div style="padding: var(--space-md) var(--space-lg); border-bottom: 1px solid var(--color-border); display: flex; justify-content: space-between; align-items: center;">
          <h3 style="margin: 0; font-size: var(--font-size-md); color: var(--color-navy);">Order Lines (${o.lines ? o.lines.length : 0})</h3>
          <span style="font-size: var(--font-size-xs); color: var(--color-text-secondary);">Snapshot from confirmed revision</span>
        </div>

        <div style="overflow-x: auto;">
          <table class="data-table">
            <thead>
              <tr>
                <th>Product / SKU</th>
                <th>Billing Type</th>
                <th>List Price</th>
                <th>Qty</th>
                <th>Discount %</th>
                <th>Net Total</th>
                <th>Margin</th>
              </tr>
            </thead>
            <tbody>
              ${o.lines && o.lines.length > 0 ? o.lines.map(l => `
                <tr>
                  <td>
                    <div style="font-weight: 600; color: var(--color-navy);">${l.product_name_snapshot}</div>
                    <div style="font-family: monospace; font-size: 0.75rem; color: var(--color-text-secondary);">${l.product_sku_snapshot}</div>
                  </td>
                  <td>
                    <span class="badge ${l.billing_type === 'RECURRING' ? 'badge-teal' : 'badge-navy'}" style="font-size: 0.7rem;">
                      ${l.billing_type === 'RECURRING' ? 'Recurring Subscription' : 'One-Time'}
                    </span>
                  </td>
                  <td style="font-family: monospace;">${o.currency} ${Number(l.unit_list_price).toFixed(2)}</td>
                  <td style="font-weight: 700;">${Number(l.quantity)}</td>
                  <td>${Number(l.effective_discount_pct || l.line_discount_pct || 0).toFixed(1)}%</td>
                  <td style="font-family: monospace; font-weight: 700;">${o.currency} ${Number(l.net_line_total).toFixed(2)}</td>
                  <td style="color: ${Number(l.margin_pct) >= 15 ? 'var(--color-teal)' : '#B45309'}; font-weight: 600;">
                    ${Number(l.margin_pct).toFixed(1)}%
                  </td>
                </tr>
              `).join('') : `
                <tr><td colspan="7" style="text-align: center; padding: 24px;">No items found in this order.</td></tr>
              `}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  /* ==========================================================================
     TAB 2: Fulfillment & Multi-Warehouse Split
     ========================================================================== */
  async function renderFulfillmentTab(container) {
    container.innerHTML = `<div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Loading live fulfillment split and inventory status...</div>`;

    try {
      const [prevRes, planRes, backRes] = await Promise.all([
        global.FulfillmentAPI.preview(orderId),
        global.FulfillmentAPI.getPlan(orderId),
        global.FulfillmentAPI.listBackorders(orderId)
      ]);

      fulfillmentPreview = prevRes.ok ? prevRes.data : null;
      fulfillmentPlan = planRes.ok ? planRes.data : null;
      backorders = backRes.ok ? backRes.data : [];

      renderFulfillmentContent(container);
    } catch (err) {
      console.error('Error loading fulfillment:', err);
      container.innerHTML = `<div class="alert alert-coral">Failed to load fulfillment data.</div>`;
    }
  }

  function renderFulfillmentContent(container) {
    const o = currentOrder;
    const prev = fulfillmentPreview;
    const plan = fulfillmentPlan;
    const hasBackorders = backorders.some(b => b.status === 'OPEN' || b.status === 'PARTIALLY_RESOLVED');

    // Group allocations by warehouse
    const allocationsByWh = {};
    const allocSource = (plan && plan.allocations && plan.allocations.length > 0) ? plan.allocations : (prev ? prev.allocations : []);

    allocSource.forEach(item => {
      const whId = item.warehouse_id;
      if (!allocationsByWh[whId]) {
        allocationsByWh[whId] = [];
      }
      allocationsByWh[whId].push(item);
    });

    const isReserved = plan && (plan.status === 'CONFIRMED' || plan.status === 'RESERVED' || plan.status === 'ACTIVE');

    container.innerHTML = `
      <!-- Backorder Alert Banner if needed -->
      ${hasBackorders ? `
        <div class="backorder-alert-panel animate-fade-in">
          <div>
            <div class="backorder-alert-title">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
              <span>Operational Attention: Backorder Active</span>
            </div>
            <div class="backorder-alert-sub">
              One or more product lines have inventory shortages. Required stock will be fulfilled as soon as warehouse supplies replenish.
            </div>
          </div>
          <button id="btn-consolidate-backorders" class="btn btn-primary btn-sm" style="background: var(--color-coral); border-color: var(--color-coral);">
            Consolidate Remaining Backorder
          </button>
        </div>
      ` : ''}

      <!-- Fulfillment Overview Card -->
      <div class="fulfillment-overview-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-md); flex-wrap: wrap; gap: var(--space-md);">
          <div>
            <h3 style="margin: 0; color: var(--color-navy); font-size: var(--font-size-md);">
              Multi-Warehouse Fulfillment Plan
              <span class="badge ${isReserved ? 'badge-teal' : 'badge-navy'}" style="margin-left: 8px;">
                ${isReserved ? 'Inventory Reserved' : 'System Recommendation Preview'}
              </span>
            </h3>
            <p style="margin: 2px 0 0; font-size: var(--font-size-xs); color: var(--color-text-secondary);">
              Optimized warehouse split minimizing total physical shipments and freight costs.
            </p>
          </div>

          <div style="display: flex; gap: var(--space-xs);">
            ${!isReserved ? `
              <button id="btn-accept-split" class="btn btn-teal btn-sm" style="font-weight: 700;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
                <span>Accept Suggested Split</span>
              </button>
            ` : ''}
            <button id="btn-manual-override" class="btn btn-secondary btn-sm" style="color: var(--color-navy);">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              <span>Manual Override</span>
            </button>
          </div>
        </div>

        <!-- Explainable AI/Rule Recommendation Banner -->
        ${prev && prev.explanation ? `
          <div class="fulfillment-explain-banner">
            <strong>System Recommendation Logic:</strong> ${prev.explanation}
          </div>
        ` : ''}

        <!-- Warehouse Split Cards -->
        <div class="warehouse-split-grid">
          ${Object.keys(allocationsByWh).map(whId => {
            const items = allocationsByWh[whId];
            const wh = warehouses.find(w => w.id === parseInt(whId, 10));
            const whName = wh ? wh.name : (items[0]?.warehouse_code || `Warehouse #${whId}`);
            const whCode = wh ? wh.code : (items[0]?.warehouse_code || 'WH');

            return `
              <div class="warehouse-card">
                <div class="warehouse-card-header">
                  <div>
                    <span class="warehouse-title">${whName}</span>
                    <span class="badge badge-navy" style="font-size: 0.65rem; margin-left: 6px;">${whCode}</span>
                  </div>
                  <span style="font-size: 0.75rem; font-weight: 700; color: var(--color-teal);">1 Shipment</span>
                </div>

                <div style="margin-bottom: var(--space-sm);">
                  ${items.map(item => {
                    const line = o.lines ? o.lines.find(l => l.id === (item.sales_order_line_id || item.order_line_id)) : null;
                    const prodName = line ? line.product_name_snapshot : `Product #${item.product_id || item.sales_order_line_id}`;
                    const qty = item.allocated_quantity || item.allocated_qty || item.quantity || 0;

                    return `
                      <div class="warehouse-item-row">
                        <span style="color: var(--color-navy); font-weight: 600;">${prodName}</span>
                        <span style="font-family: monospace; font-weight: 700; background: #EEF2F6; padding: 2px 6px; border-radius: 4px;">
                          ${Number(qty)} units
                        </span>
                      </div>
                    `;
                  }).join('')}
                </div>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;

    setupFulfillmentEvents();
  }

  function setupFulfillmentEvents() {
    // Accept Suggested Split
    document.getElementById('btn-accept-split')?.addEventListener('click', async () => {
      if (confirm('Accept this warehouse allocation and reserve live inventory?')) {
        try {
          const res = await global.FulfillmentAPI.accept(orderId);
          if (res.ok) {
            global.DealFlowUI.toast('Fulfillment plan accepted and inventory reserved.', 'teal');
            await loadInitialData();
            await renderFulfillmentTab(document.getElementById('order-tab-content'));
          } else {
            global.DealFlowUI.toast(res.data?.detail || 'Failed to accept fulfillment plan.', 'coral');
          }
        } catch (e) {
          global.DealFlowUI.toast('Network error accepting fulfillment plan.', 'coral');
        }
      }
    });

    // Manual Override Modal
    document.getElementById('btn-manual-override')?.addEventListener('click', () => {
      openManualOverrideModal();
    });

    // Consolidate Backorders
    document.getElementById('btn-consolidate-backorders')?.addEventListener('click', async () => {
      try {
        const res = await global.FulfillmentAPI.consolidateBackorders(orderId);
        if (res.ok) {
          global.DealFlowUI.toast('Backorders consolidated with available stock.', 'teal');
          await loadInitialData();
          await renderFulfillmentTab(document.getElementById('order-tab-content'));
        } else {
          global.DealFlowUI.toast(res.data?.detail || 'No new stock available to consolidate backorders.', 'coral');
        }
      } catch (e) {
        global.DealFlowUI.toast('Network error consolidating backorders.', 'coral');
      }
    });
  }

  function openManualOverrideModal() {
    const overlay = document.getElementById('dealflow-modal-overlay');
    if (!overlay || !currentOrder) return;

    const o = currentOrder;

    overlay.innerHTML = `
      <div class="modal-card" style="max-width: 750px; width: 90%;">
        <div class="modal-header">
          <h3>Manual Warehouse Allocation Override</h3>
          <button class="modal-close-btn" id="btn-close-override-modal">&times;</button>
        </div>
        <div class="modal-body">
          <div class="alert alert-navy" style="font-size: 0.75rem; margin-bottom: 16px;">
            Manual overrides are validated against live inventory before reservation. If stock is insufficient, remaining units will move to backorder.
          </div>

          <div style="max-height: 350px; overflow-y: auto;">
            <table class="data-table" style="font-size: 0.8rem;">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Required Qty</th>
                  <th>Warehouse Target</th>
                  <th>Allocate Qty</th>
                </tr>
              </thead>
              <tbody id="override-lines-tbody">
                ${o.lines.map((line, idx) => `
                  <tr data-line-id="${line.id}">
                    <td>
                      <strong>${line.product_name_snapshot}</strong>
                      <div style="font-size: 0.7rem; color: var(--color-text-secondary);">${line.product_sku_snapshot}</div>
                    </td>
                    <td style="font-weight: 700;">${Number(line.quantity)}</td>
                    <td>
                      <select class="form-input override-wh-select" data-line-id="${line.id}" style="padding: 4px 6px; font-size: 0.75rem;">
                        ${warehouses.map(w => `<option value="${w.id}">${w.name} (${w.code})</option>`).join('')}
                      </select>
                    </td>
                    <td>
                      <input type="number" class="form-input override-qty-input" data-line-id="${line.id}" value="${Number(line.quantity)}" min="1" max="${Number(line.quantity)}" style="width: 75px; padding: 4px 6px; font-size: 0.75rem; font-weight: 700;" />
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>

          <div style="display: flex; justify-content: flex-end; gap: 8px; margin-top: 20px;">
            <button class="btn btn-secondary btn-sm" id="btn-cancel-override">Cancel</button>
            <button class="btn btn-primary btn-sm" id="btn-submit-override">Submit Manual Split</button>
          </div>
        </div>
      </div>
    `;

    overlay.classList.add('active');

    const closeModal = () => overlay.classList.remove('active');
    document.getElementById('btn-close-override-modal').onclick = closeModal;
    document.getElementById('btn-cancel-override').onclick = closeModal;

    document.getElementById('btn-submit-override').onclick = async () => {
      const allocations = [];
      const rows = document.querySelectorAll('#override-lines-tbody tr');

      rows.forEach(row => {
        const lineId = parseInt(row.dataset.lineId, 10);
        const whSelect = row.querySelector('.override-wh-select');
        const qtyInput = row.querySelector('.override-qty-input');

        if (whSelect && qtyInput) {
          allocations.push({
            order_line_id: lineId,
            warehouse_id: parseInt(whSelect.value, 10),
            quantity: parseFloat(qtyInput.value)
          });
        }
      });

      try {
        const res = await global.FulfillmentAPI.manualOverride(orderId, allocations);
        if (res.ok) {
          closeModal();
          global.DealFlowUI.toast('Manual warehouse allocation applied successfully.', 'teal');
          await loadInitialData();
          await renderFulfillmentTab(document.getElementById('order-tab-content'));
        } else {
          global.DealFlowUI.toast(res.data?.detail || 'Manual allocation failed. Please verify inventory.', 'coral');
        }
      } catch (e) {
        global.DealFlowUI.toast('Network error submitting manual override.', 'coral');
      }
    };
  }

  /* ==========================================================================
     TAB 3: Shipments
     ========================================================================== */
  async function renderShipmentsTab(container) {
    container.innerHTML = `<div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Loading shipments...</div>`;

    try {
      const res = await global.ShipmentsAPI.list(orderId);
      shipments = res.ok ? res.data : [];

      renderShipmentsContent(container);
    } catch (err) {
      container.innerHTML = `<div class="alert alert-coral">Failed to load shipments.</div>`;
    }
  }

  function renderShipmentsContent(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-md);">
        <div>
          <h3 style="margin: 0; color: var(--color-navy); font-size: var(--font-size-md);">Physical Shipments (${shipments.length})</h3>
          <p style="margin: 2px 0 0; font-size: var(--font-size-xs); color: var(--color-text-secondary);">
            Warehouse dispatch and tracking management.
          </p>
        </div>

        <button id="btn-generate-shipments" class="btn btn-primary btn-sm">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
          <span>Generate Shipments</span>
        </button>
      </div>

      ${shipments.length === 0 ? `
        <div class="card" style="text-align: center; padding: 48px; color: var(--color-text-muted);">
          <div style="font-weight: 600; margin-bottom: 4px;">No Shipments Generated Yet</div>
          <p style="font-size: var(--font-size-xs); margin-bottom: 16px;">Click 'Generate Shipments' to bundle allocated warehouse inventory into dispatch records.</p>
        </div>
      ` : `
        <div class="shipments-grid">
          ${shipments.map(s => {
            const whName = s.warehouse ? s.warehouse.name : `Warehouse #${s.warehouse_id}`;
            const isShipped = s.status === 'SHIPPED' || s.status === 'DELIVERED';
            const isDelivered = s.status === 'DELIVERED';

            return `
              <div class="shipment-card animate-fade-in" data-shipment-id="${s.id}">
                <div>
                  <div class="shipment-header">
                    <span class="shipment-number">${s.shipment_number}</span>
                    <span class="badge ${isDelivered ? 'badge-teal' : (isShipped ? 'badge-navy' : 'badge-coral')}">
                      ${s.status}
                    </span>
                  </div>

                  <div class="shipment-meta-row">
                    <span>Dispatch Origin:</span>
                    <strong>${whName}</strong>
                  </div>
                  <div class="shipment-meta-row">
                    <span>Estimated Cost:</span>
                    <strong>$${Number(s.estimated_cost || 0).toFixed(2)}</strong>
                  </div>
                  ${s.shipped_at ? `
                    <div class="shipment-meta-row">
                      <span>Shipped Date:</span>
                      <span>${new Date(s.shipped_at).toLocaleString()}</span>
                    </div>
                  ` : ''}
                </div>

                <div class="shipment-actions">
                  ${!isShipped ? `
                    <button class="btn btn-teal btn-sm btn-mark-shipped" data-shipment-id="${s.id}">
                      Mark Shipped
                    </button>
                  ` : ''}
                  ${isShipped && !isDelivered ? `
                    <button class="btn btn-secondary btn-sm btn-mark-delivered" data-shipment-id="${s.id}">
                      Mark Delivered
                    </button>
                  ` : ''}
                </div>
              </div>
            `;
          }).join('')}
        </div>
      `}

      <!-- Inventory Movement Progression Visualizer -->
      <div class="inventory-flow-box">
        <h4 style="margin: 0; font-size: var(--font-size-xs); text-transform: uppercase; color: var(--color-navy); font-weight: 700;">
          Inventory Movement Protocol
        </h4>
        <div class="inventory-flow-steps">
          <div class="flow-step-card">
            <div class="flow-step-title">1. Allocation</div>
            <div class="flow-step-val" style="color: var(--color-navy);">Stock Identified</div>
          </div>
          <div class="flow-step-card">
            <div class="flow-step-title">2. Reservation</div>
            <div class="flow-step-val" style="color: var(--color-teal);">Reserved &bull; On-Hand Held</div>
          </div>
          <div class="flow-step-card">
            <div class="flow-step-title">3. Dispatch (Ship)</div>
            <div class="flow-step-val" style="color: var(--color-coral);">On-Hand & Reserved Decrement</div>
          </div>
          <div class="flow-step-card">
            <div class="flow-step-title">4. Delivery</div>
            <div class="flow-step-val" style="color: var(--color-teal);">Confirmed Closed</div>
          </div>
        </div>
      </div>
    `;

    setupShipmentEvents();
  }

  function setupShipmentEvents() {
    // Generate Shipments
    document.getElementById('btn-generate-shipments')?.addEventListener('click', async () => {
      try {
        const res = await global.ShipmentsAPI.generate(orderId);
        if (res.ok) {
          global.DealFlowUI.toast('Shipments generated from fulfillment plan.', 'teal');
          await renderShipmentsTab(document.getElementById('order-tab-content'));
        } else {
          global.DealFlowUI.toast(res.data?.detail || 'Failed to generate shipments.', 'coral');
        }
      } catch (e) {
        global.DealFlowUI.toast('Network error generating shipments.', 'coral');
      }
    });

    // Mark Shipped
    document.querySelectorAll('.btn-mark-shipped').forEach(btn => {
      btn.addEventListener('click', async () => {
        const shpId = parseInt(btn.dataset.shipmentId, 10);
        if (confirm('Mark this shipment as shipped? Reserved stock will be decremented from physical warehouse inventory.')) {
          try {
            const res = await global.ShipmentsAPI.ship(orderId, shpId);
            if (res.ok) {
              global.DealFlowUI.toast('Shipment dispatched and stock decremented.', 'teal');
              await renderShipmentsTab(document.getElementById('order-tab-content'));
            } else {
              global.DealFlowUI.toast(res.data?.detail || 'Failed to mark shipment shipped.', 'coral');
            }
          } catch (e) {
            global.DealFlowUI.toast('Network error updating shipment.', 'coral');
          }
        }
      });
    });

    // Mark Delivered
    document.querySelectorAll('.btn-mark-delivered').forEach(btn => {
      btn.addEventListener('click', async () => {
        const shpId = parseInt(btn.dataset.shipmentId, 10);
        try {
          const res = await global.ShipmentsAPI.deliver(orderId, shpId);
          if (res.ok) {
            global.DealFlowUI.toast('Shipment delivered successfully.', 'teal');
            await renderShipmentsTab(document.getElementById('order-tab-content'));
          } else {
            global.DealFlowUI.toast(res.data?.detail || 'Failed to mark shipment delivered.', 'coral');
          }
        } catch (e) {
          global.DealFlowUI.toast('Network error updating shipment.', 'coral');
        }
      });
    });
  }

  /* ==========================================================================
     TAB 4: Hybrid Billing & Subscriptions
     ========================================================================== */
  async function renderBillingTab(container) {
    container.innerHTML = `<div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Loading hybrid billing and subscriptions...</div>`;

    try {
      const [invRes, subRes] = await Promise.all([
        global.InvoicesAPI.list({ sales_order_id: orderId }),
        global.SubscriptionsAPI.list({ sales_order_id: orderId })
      ]);

      invoices = invRes.ok ? invRes.data : [];
      subscriptions = subRes.ok ? subRes.data : [];

      renderBillingContent(container);
    } catch (err) {
      container.innerHTML = `<div class="alert alert-coral">Failed to load billing information.</div>`;
    }
  }

  function renderBillingContent(container) {
    container.innerHTML = `
      <div class="hybrid-billing-container">
        <!-- Section 1: One-Time Invoices -->
        <div class="billing-card-section">
          <div>
            <div class="billing-section-header">
              <span class="billing-section-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                <span>One-Time Invoices (${invoices.length})</span>
              </span>
              <span class="badge badge-navy" style="font-size: 0.65rem;">Direct / Upfront</span>
            </div>

            ${invoices.length === 0 ? `
              <div style="text-align: center; padding: 24px; color: var(--color-text-muted); font-size: var(--font-size-xs);">
                No one-time invoices issued for this order.
              </div>
            ` : invoices.map(inv => `
              <div style="background: #F8FAFC; border: 1px solid var(--color-border); border-radius: var(--radius-sm); padding: 12px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                  <span style="font-family: monospace; font-weight: 700; color: var(--color-navy);">${inv.invoice_number}</span>
                  <span class="badge ${inv.status === 'PAID' ? 'badge-teal' : (inv.status === 'PARTIALLY_PAID' ? 'badge-coral' : 'badge-navy')}">
                    ${inv.status}
                  </span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: var(--font-size-xs); color: var(--color-text-secondary); margin-bottom: 2px;">
                  <span>Total Amount:</span>
                  <strong>${inv.currency} ${Number(inv.total_amount).toFixed(2)}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: var(--font-size-xs); color: var(--color-text-secondary);">
                  <span>Balance Due:</span>
                  <strong style="color: ${Number(inv.balance_due) > 0 ? 'var(--color-coral)' : 'var(--color-teal)'};">${inv.currency} ${Number(inv.balance_due).toFixed(2)}</strong>
                </div>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Section 2: Recurring Subscriptions -->
        <div class="billing-card-section">
          <div>
            <div class="billing-section-header">
              <span class="billing-section-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                <span>Recurring Subscriptions (${subscriptions.length})</span>
              </span>
              <span class="badge badge-teal" style="font-size: 0.65rem;">Active MRR</span>
            </div>

            ${subscriptions.length === 0 ? `
              <div style="text-align: center; padding: 24px; color: var(--color-text-muted); font-size: var(--font-size-xs);">
                No recurring SaaS / Support subscriptions in this order.
              </div>
            ` : subscriptions.map(sub => `
              <div style="background: #F8FAFC; border: 1px solid var(--color-border); border-radius: var(--radius-sm); padding: 12px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                  <span style="font-family: monospace; font-weight: 700; color: var(--color-navy);">${sub.subscription_number}</span>
                  <span class="badge ${sub.status === 'ACTIVE' ? 'badge-teal' : 'badge-coral'}">${sub.status}</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: var(--font-size-xs); color: var(--color-text-secondary); margin-bottom: 2px;">
                  <span>Monthly Recurring Revenue:</span>
                  <strong>${sub.currency} ${Number(sub.monthly_recurring_revenue || sub.unit_price).toFixed(2)}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: var(--font-size-xs); color: var(--color-text-secondary);">
                  <span>Next Billing Date:</span>
                  <span>${new Date(sub.next_billing_date).toLocaleDateString()}</span>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  }

  /* ==========================================================================
     TAB 5: Payments
     ========================================================================== */
  async function renderPaymentsTab(container) {
    container.innerHTML = `<div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Loading payments...</div>`;

    try {
      const invRes = await global.InvoicesAPI.list({ sales_order_id: orderId });
      invoices = invRes.ok ? invRes.data : [];

      const totalInvoiced = invoices.reduce((sum, i) => sum + Number(i.total_amount), 0);
      const totalPaid = invoices.reduce((sum, i) => sum + Number(i.paid_amount), 0);
      const totalBalance = invoices.reduce((sum, i) => sum + Number(i.balance_due), 0);
      const pctPaid = totalInvoiced > 0 ? (totalPaid / totalInvoiced) * 100 : 0;

      container.innerHTML = `
        <div class="card" style="margin-bottom: var(--space-lg);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-md); flex-wrap: wrap; gap: var(--space-md);">
            <div>
              <h3 style="margin: 0; color: var(--color-navy); font-size: var(--font-size-md);">Payment Progress & Outstanding Balance</h3>
              <p style="margin: 2px 0 0; font-size: var(--font-size-xs); color: var(--color-text-secondary);">
                ${currentOrder.currency} ${totalPaid.toFixed(2)} paid of ${currentOrder.currency} ${totalInvoiced.toFixed(2)} total invoiced (${pctPaid.toFixed(0)}%)
              </p>
            </div>

            <button id="btn-record-order-payment" class="btn btn-primary btn-sm">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
              <span>Record Payment</span>
            </button>
          </div>

          <div class="payment-progress-bar-wrapper">
            <div class="payment-progress-fill" style="width: ${Math.min(100, pctPaid)}%;"></div>
          </div>

          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-md); text-align: center; margin-top: var(--space-md);">
            <div style="background: #F8FAFC; padding: 10px; border-radius: var(--radius-sm);">
              <label style="font-size: 0.7rem; color: var(--color-text-muted); display: block;">Total Invoiced</label>
              <strong style="color: var(--color-navy);">${currentOrder.currency} ${totalInvoiced.toFixed(2)}</strong>
            </div>
            <div style="background: #F0FDF4; padding: 10px; border-radius: var(--radius-sm);">
              <label style="font-size: 0.7rem; color: var(--color-text-muted); display: block;">Total Received</label>
              <strong style="color: var(--color-teal);">${currentOrder.currency} ${totalPaid.toFixed(2)}</strong>
            </div>
            <div style="background: #EFF6FF; padding: 10px; border-radius: var(--radius-sm);">
              <label style="font-size: 0.7rem; color: var(--color-text-muted); display: block;">Balance Outstanding</label>
              <strong style="color: #1E40AF;">${currentOrder.currency} ${totalBalance.toFixed(2)}</strong>
            </div>
          </div>
        </div>
      `;

      document.getElementById('btn-record-order-payment')?.addEventListener('click', () => {
        window.DealFlowApp.switchView('payments');
      });
    } catch (err) {
      container.innerHTML = `<div class="alert alert-coral">Failed to load payment summary.</div>`;
    }
  }

  /* ==========================================================================
     TAB 6: Order Audit Timeline
     ========================================================================== */
  async function renderAuditTab(container) {
    container.innerHTML = `<div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Loading audit timeline...</div>`;

    try {
      const res = await global.OrdersAPI.getAudit(orderId);
      auditEvents = res.ok ? res.data : [];

      if (auditEvents.length === 0) {
        container.innerHTML = `<div class="card" style="text-align: center; padding: 40px; color: var(--color-text-muted);">No audit events recorded for this order.</div>`;
        return;
      }

      container.innerHTML = `
        <div class="card">
          <h3 style="margin-bottom: var(--space-md); font-size: var(--font-size-md); color: var(--color-navy);">
            Order Lifecycle Audit Trail
          </h3>

          <div class="audit-timeline">
            ${auditEvents.map(ev => {
              const actorName = ev.actor_user ? ev.actor_user.full_name : (ev.actor_user_id ? `User #${ev.actor_user_id}` : 'System');
              const timeStr = new Date(ev.created_at).toLocaleString();

              return `
                <div class="audit-event-item" style="padding-left: 20px; position: relative; margin-bottom: 16px; border-left: 2px solid var(--color-border);">
                  <div style="position: absolute; left: -6px; top: 0; width: 10px; height: 10px; border-radius: 50%; background: var(--color-teal);"></div>
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                    <strong style="color: var(--color-navy); font-size: 0.85rem;">${formatAuditEventType(ev.event_type)}</strong>
                    <span style="font-size: 0.7rem; color: var(--color-text-muted);">${timeStr}</span>
                  </div>
                  <div style="font-size: 0.75rem; color: var(--color-text-secondary);">${actorName}</div>
                  ${ev.to_status ? `
                    <div style="font-size: 0.75rem; margin-top: 2px;">
                      Status Transition: <span class="badge badge-teal" style="font-size: 0.65rem;">${ev.to_status}</span>
                    </div>
                  ` : ''}
                  ${ev.reason ? `<div style="font-size: 0.75rem; color: var(--color-text-muted); margin-top: 2px;">Reason: ${ev.reason}</div>` : ''}
                </div>
              `;
            }).join('')}
          </div>
        </div>
      `;
    } catch (e) {
      container.innerHTML = `<div class="alert alert-coral">Failed to load audit events.</div>`;
    }
  }

  function formatOrderStatusBadge(status) {
    const map = {
      'FULFILLMENT': { label: 'In Fulfillment', cls: 'badge-coral' },
      'PARTIALLY_FULFILLED': { label: 'Partially Fulfilled', cls: 'badge-coral' },
      'BACKORDERED': { label: 'Backordered', cls: 'badge-coral' },
      'FULFILLED': { label: 'Fulfilled', cls: 'badge-teal' },
      'BILLED': { label: 'Billed', cls: 'badge-navy' },
      'PARTIALLY_PAID': { label: 'Partially Paid', cls: 'badge-coral' },
      'PAID': { label: 'Paid', cls: 'badge-teal' },
      'ACTIVE_SUBSCRIPTION': { label: 'Active Subscription', cls: 'badge-teal' },
      'CLOSED': { label: 'Closed', cls: 'badge-navy' },
      'CANCELLED': { label: 'Cancelled', cls: 'badge-navy' }
    };
    const s = map[status] || { label: status, cls: 'badge-navy' };
    return `<span class="badge ${s.cls}">${s.label}</span>`;
  }

  function formatAuditEventType(type) {
    const map = {
      'ORDER_CREATED': 'Sales Order Created from Confirmed Quote',
      'FULFILLMENT_ALLOCATED': 'Fulfillment Allocation Plan Generated',
      'INVENTORY_RESERVED': 'Inventory Reserved Across Warehouses',
      'MANUAL_OVERRIDE_APPLIED': 'Manual Fulfillment Override Applied',
      'BACKORDER_CREATED': 'Backorder Shortage Recorded',
      'BACKORDER_CONSOLIDATED': 'Backorder Consolidating Stock Available',
      'SHIPMENT_GENERATED': 'Shipment Batch Generated',
      'SHIPMENT_SHIPPED': 'Shipment Dispatched & Inventory Decremented',
      'SHIPMENT_DELIVERED': 'Shipment Delivered',
      'BILLING_INITIALIZED': 'Billing Invoices & Subscriptions Initialized',
      'INVOICE_ISSUED': 'Invoice Issued',
      'PAYMENT_RECORDED': 'Customer Payment Recorded',
      'SUBSCRIPTION_MODIFIED': 'Subscription Quantity Modified',
      'SUBSCRIPTION_CANCELLED': 'Subscription Cancelled'
    };
    return map[type] || type;
  }

  global.OrderDetailView = {
    render: render
  };
})(typeof window !== 'undefined' ? window : this);
