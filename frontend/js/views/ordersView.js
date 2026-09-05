/**
 * DealFlow360 — Orders View Controller
 * Renders the Sales Orders list and filterable operational dashboard.
 */
(function (global) {
  'use strict';

  let orders = [];
  let currentFilters = {
    status: '',
    search: ''
  };

  async function render(container) {
    container.innerHTML = `
      <div class="orders-page-wrapper animate-fade-in">
        <div class="page-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-md); flex-wrap: wrap; gap: var(--space-md);">
          <div>
            <h1 class="page-title" style="margin: 0;">Sales Orders</h1>
            <p class="page-subtitle" style="margin-top: 4px; color: var(--color-text-secondary); font-size: var(--font-size-sm);">
              Operations Hub &bull; Post-confirmation order execution, fulfillment, and revenue tracking.
            </p>
          </div>
          <div style="display: flex; gap: var(--space-sm);">
            <button id="btn-refresh-orders" class="btn btn-secondary btn-sm">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
              <span>Refresh</span>
            </button>
          </div>
        </div>

        <!-- Filters Strip -->
        <div class="card orders-filter-bar" style="padding: var(--space-md); margin-bottom: var(--space-md);">
          <div class="orders-filter-group">
            <div class="input-wrapper" style="min-width: 240px;">
              <input type="text" id="order-search-input" class="form-input" placeholder="Search Order # or Customer..." value="${currentFilters.search}">
            </div>
            <select id="order-status-filter" class="form-input" style="width: 180px;">
              <option value="">All Statuses</option>
              <option value="FULFILLMENT" ${currentFilters.status === 'FULFILLMENT' ? 'selected' : ''}>In Fulfillment</option>
              <option value="PARTIALLY_FULFILLED" ${currentFilters.status === 'PARTIALLY_FULFILLED' ? 'selected' : ''}>Partially Fulfilled</option>
              <option value="BACKORDERED" ${currentFilters.status === 'BACKORDERED' ? 'selected' : ''}>Backordered</option>
              <option value="FULFILLED" ${currentFilters.status === 'FULFILLED' ? 'selected' : ''}>Fulfilled</option>
              <option value="BILLED" ${currentFilters.status === 'BILLED' ? 'selected' : ''}>Billed</option>
              <option value="PARTIALLY_PAID" ${currentFilters.status === 'PARTIALLY_PAID' ? 'selected' : ''}>Partially Paid</option>
              <option value="PAID" ${currentFilters.status === 'PAID' ? 'selected' : ''}>Paid</option>
              <option value="ACTIVE_SUBSCRIPTION" ${currentFilters.status === 'ACTIVE_SUBSCRIPTION' ? 'selected' : ''}>Active Subscription</option>
              <option value="CLOSED" ${currentFilters.status === 'CLOSED' ? 'selected' : ''}>Closed</option>
              <option value="CANCELLED" ${currentFilters.status === 'CANCELLED' ? 'selected' : ''}>Cancelled</option>
            </select>
          </div>
          <div id="order-count-badge" style="font-size: var(--font-size-xs); color: var(--color-text-secondary); font-weight: 600;">
            Loading orders...
          </div>
        </div>

        <!-- Orders Table Card -->
        <div class="card" style="padding: 0; overflow: hidden;">
          <div id="orders-table-container" style="overflow-x: auto;">
            <div style="text-align: center; padding: 40px;"><span class="spinner spinner-teal"></span> Loading sales orders...</div>
          </div>
        </div>
      </div>
    `;

    setupEvents(container);
    await loadOrders();
  }

  function setupEvents(container) {
    const searchInput = container.querySelector('#order-search-input');
    const statusFilter = container.querySelector('#order-status-filter');
    const refreshBtn = container.querySelector('#btn-refresh-orders');

    let debounceTimer;
    searchInput?.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        currentFilters.search = searchInput.value.trim();
        renderOrdersTable();
      }, 250);
    });

    statusFilter?.addEventListener('change', async () => {
      currentFilters.status = statusFilter.value;
      await loadOrders();
    });

    refreshBtn?.addEventListener('click', async () => {
      await loadOrders();
      global.DealFlowUI.toast('Sales orders refreshed.', 'teal');
    });
  }

  async function loadOrders() {
    try {
      const res = await global.OrdersAPI.list({
        status: currentFilters.status || undefined,
        limit: 100
      });

      if (!res.ok) {
        document.getElementById('orders-table-container').innerHTML = `
          <div class="alert alert-coral" style="margin: 20px;">
            <span>Failed to load sales orders: ${res.data?.detail || res.error || 'Server error'}</span>
          </div>
        `;
        return;
      }

      orders = res.data || [];
      renderOrdersTable();
    } catch (err) {
      console.error('Error loading orders:', err);
      document.getElementById('orders-table-container').innerHTML = `
        <div class="alert alert-coral" style="margin: 20px;">
          <span>Error connecting to Orders services.</span>
        </div>
      `;
    }
  }

  function renderOrdersTable() {
    const container = document.getElementById('orders-table-container');
    const countBadge = document.getElementById('order-count-badge');
    if (!container) return;

    let filtered = orders;
    if (currentFilters.search) {
      const q = currentFilters.search.toLowerCase();
      filtered = filtered.filter(o =>
        o.order_number.toLowerCase().includes(q) ||
        (o.customer && o.customer.name.toLowerCase().includes(q))
      );
    }

    if (countBadge) {
      countBadge.textContent = `Showing ${filtered.length} of ${orders.length} orders`;
    }

    if (filtered.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 48px; color: var(--color-text-muted);">
          <div style="font-weight: 600; margin-bottom: 4px; font-size: var(--font-size-md);">No Sales Orders Found</div>
          <p style="font-size: var(--font-size-xs); margin: 0;">Confirmed quotations will automatically appear here as active orders.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <table class="data-table">
        <thead>
          <tr>
            <th>Order Number</th>
            <th>Customer</th>
            <th>Source Quotation</th>
            <th>Confirmed Version</th>
            <th>Net Total</th>
            <th>Fulfillment & Billing Status</th>
            <th>Confirmed At</th>
            <th style="text-align: right;">Action</th>
          </tr>
        </thead>
        <tbody>
          ${filtered.map(o => {
            const custName = o.customer ? o.customer.name : `Customer #${o.customer_id}`;
            const confirmedAt = o.customer_confirmed_at ? new Date(o.customer_confirmed_at).toLocaleDateString() : new Date(o.created_at).toLocaleDateString();

            return `
              <tr data-order-id="${o.id}">
                <td>
                  <a href="#" class="order-link-btn" data-order-id="${o.id}" style="font-family: monospace; font-weight: 700; color: var(--color-navy); text-decoration: underline;">
                    ${o.order_number}
                  </a>
                </td>
                <td style="font-weight: 600; color: var(--color-navy);">${custName}</td>
                <td>
                  <span class="badge badge-navy" style="font-size: 0.75rem; font-family: monospace;">
                    Quote #${o.quotation_id}
                  </span>
                </td>
                <td>
                  <span class="badge badge-teal" style="font-size: 0.75rem;">
                    v${o.confirmed_quote_version_id ? o.confirmed_quote_version_id : 1}
                  </span>
                </td>
                <td style="font-family: monospace; font-weight: 700;">
                  ${o.currency} ${Number(o.net_total).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </td>
                <td>
                  ${formatOrderStatusBadge(o.status)}
                </td>
                <td style="font-size: var(--font-size-xs); color: var(--color-text-secondary);">
                  ${confirmedAt}
                </td>
                <td style="text-align: right;">
                  <button class="btn btn-secondary btn-sm btn-open-order" data-order-id="${o.id}" style="padding: 4px 10px; font-size: 0.75rem;">
                    <span>Open Order</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"></polyline></svg>
                  </button>
                </td>
              </tr>
            `;
          }).join('')}
        </tbody>
      </table>
    `;

    container.querySelectorAll('.btn-open-order, .order-link-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const orderId = parseInt(btn.dataset.orderId, 10);
        window.DealFlowApp.switchView('order-detail', { orderId: orderId });
      });
    });
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

  global.OrdersView = {
    render: render
  };
})(typeof window !== 'undefined' ? window : this);
