/**
 * DealFlow360 — Phase 3 Quotation Intelligence & CPQ Builder View
 * Implements the 3-Zone enterprise deal workspace:
 * - Zone 1: Product Catalog selector
 * - Zone 2: Interactive Quotation lines, quantities, discounts, and order discount
 * - Zone 3: Deal Intelligence rail, risk reasons explainability, upsell recommendations,
 *           What-If simulation engine, and approval submission.
 */
(function (global) {
  'use strict';

  let currentQuote = null;
  let quoteId = null;
  let catalogProducts = [];
  let catalogCategories = [];
  let billingPlans = [];
  let isSaving = false;
  let saveDebounceTimer = null;

  async function render(container, params = {}) {
    quoteId = params.quoteId || (params.id ? parseInt(params.id, 10) : null);

    if (!quoteId && window.location.hash.includes('?')) {
      const qs = window.location.hash.split('?')[1];
      const searchParams = new URLSearchParams(qs);
      const qVal = searchParams.get('id') || searchParams.get('quoteId');
      if (qVal) quoteId = parseInt(qVal, 10);
    }
    if (!quoteId && window.location.search) {
      const searchParams = new URLSearchParams(window.location.search);
      const qVal = searchParams.get('id') || searchParams.get('quoteId');
      if (qVal) quoteId = parseInt(qVal, 10);
    }

    if (!quoteId) {
      container.innerHTML = `
        <div class="card animate-fade-in" style="text-align: center; padding: 60px 20px; max-width: 600px; margin: 40px auto;">
          <div style="width: 56px; height: 56px; border-radius: var(--radius-full); background: var(--color-navy-muted); color: var(--color-navy); display: flex; align-items: center; justify-content: center; margin: 0 auto var(--space-md);">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
          </div>
          <h3 style="font-size: var(--font-size-lg); color: var(--color-navy); margin-bottom: 8px;">No Quotation Selected</h3>
          <p style="color: var(--color-text-secondary); margin-bottom: var(--space-lg); font-size: var(--font-size-sm);">Select an existing quotation from your workspace list or create a new quotation to launch Deal Intelligence.</p>
          <div style="display: flex; gap: var(--space-md); justify-content: center; flex-wrap: wrap;">
            <button class="btn btn-primary" onclick="if(window.QuotationsView && typeof window.QuotationsView.openNewQuotationModal === 'function') { window.QuotationsView.openNewQuotationModal(); } else { window.DealFlowApp.switchView('quotations'); }">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
              <span>+ Create New Quotation</span>
            </button>
            <button class="btn btn-secondary" onclick="window.DealFlowApp.switchView('quotations');">Browse Quotations List</button>
          </div>
        </div>
      `;
      return;
    }


    container.innerHTML = `
      <div id="builder-main-wrapper" class="animate-fade-in">
        <div style="text-align: center; padding: 60px;"><span class="spinner spinner-teal"></span> Loading deal intelligence workspace...</div>
      </div>
    `;

    await loadInitialData();
  }

  async function loadInitialData() {
    try {
      const [quoteRes, prodRes, catRes, planRes] = await Promise.all([
        global.QuotationsAPI.get(quoteId),
        global.ProductsAPI.list({ limit: 100 }),
        global.ProductCategoriesAPI.list({ limit: 100 }),
        global.BillingPlansAPI.list({ limit: 100 })
      ]);

      if (!quoteRes.ok) {
        document.getElementById('builder-main-wrapper').innerHTML = `
          <div class="alert alert-coral" style="margin: 20px;">
            <span>Failed to load quotation: ${quoteRes.data?.detail || quoteRes.error || 'Quote not found'}</span>
          </div>
          <button class="btn btn-secondary" onclick="window.DealFlowApp.switchView('quotations');">Back to Quotations</button>
        `;
        return;
      }

      currentQuote = quoteRes.data;
      catalogProducts = prodRes.ok ? prodRes.data : [];
      catalogCategories = catRes.ok ? catRes.data : [];
      billingPlans = planRes.ok ? planRes.data : [];

      if (global.DealFlowWS) {
        if (typeof global.DealFlowWS.subscribeQuotation === 'function') {
          global.DealFlowWS.subscribeQuotation(quoteId);
        } else if (typeof global.DealFlowWS.subscribe === 'function') {
          global.DealFlowWS.subscribe(quoteId);
        }
      }

      renderWorkspace();
    } catch (err) {
      console.error('Error initializing quote builder:', err);
      document.getElementById('builder-main-wrapper').innerHTML = `
        <div class="alert alert-coral" style="margin: 20px;">
          <span>Error connecting to Quotation services.</span>
        </div>
      `;
    }
  }

  function isEditable() {
    return currentQuote && (currentQuote.status === 'DRAFT' || currentQuote.status === 'RETURNED_FOR_REVISION');
  }

  function renderWorkspace() {
    const wrapper = document.getElementById('builder-main-wrapper');
    if (!wrapper) return;

    const q = currentQuote;
    const editable = isEditable();
    const custName = q.customer ? q.customer.name : `Customer #${q.customer_id}`;
    const custTier = q.customer?.tier ? q.customer.tier.name : 'Standard';
    const repName = q.sales_rep ? q.sales_rep.full_name : `User #${q.sales_rep_id}`;

    wrapper.innerHTML = `
      <!-- Top Navigation & Actions Bar -->
      <div class="builder-topbar">
        <div class="builder-topbar-left">
          <button class="btn btn-secondary btn-sm" onclick="window.DealFlowApp.switchView('quotations');">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
            <span>Quotes</span>
          </button>
          <div class="builder-quote-title">
            <span>${q.quote_number}</span>
            ${formatStatusBadge(q.status)}
            <span id="save-status-indicator" style="font-size: 0.75rem; font-weight: normal; color: var(--color-text-muted); display: none;">Saving...</span>
          </div>
        </div>

        <div class="builder-topbar-actions">
          <!-- Recalculate Action -->
          <button id="btn-recalculate-quote" class="btn btn-secondary btn-sm" title="Refresh commercial evaluation from backend" ${!editable ? 'disabled' : ''}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
            <span>Recalculate</span>
          </button>

          <!-- What-If Simulator Action -->
          <button id="btn-open-whatif" class="btn btn-secondary btn-sm" style="color: var(--color-navy); font-weight: 600;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
            <span>What-If Simulator</span>
          </button>

          <!-- Audit Trail Action -->
          <button id="btn-open-audit" class="btn btn-secondary btn-sm" title="View quote activity audit timeline">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
            <span>Audit Trail</span>
          </button>

          <!-- Version History Action -->
          <button id="btn-view-versions" class="btn btn-secondary btn-sm" title="View quote version history and compare revisions">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20v-6M6 20V10M18 20V4"/></svg>
            <span>v${q.version_number || 1} Revisions</span>
          </button>

          <!-- Customer Negotiation & Messages Action -->
          <button id="btn-view-messages" class="btn btn-secondary btn-sm" title="Customer communication and negotiation messages">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
            <span>Messages / Negotiation</span>
          </button>

          <!-- Send to Customer (Only if APPROVED) -->
          ${q.status === 'APPROVED' ? `
            <button id="btn-send-to-customer" class="btn btn-teal btn-sm" style="font-weight: 700; box-shadow: 0 2px 6px rgba(13,148,136,0.25);">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
              <span>Send to Customer</span>
            </button>
          ` : ''}

          <!-- View Sales Order (Only if CUSTOMER_CONFIRMED) -->
          ${q.status === 'CUSTOMER_CONFIRMED' ? `
            <button id="btn-view-sales-order" class="btn btn-primary btn-sm" style="font-weight: 700; background: var(--color-navy); box-shadow: 0 2px 6px rgba(15,23,42,0.25);">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
              <span>View Sales Order</span>
            </button>
          ` : ''}

          <!-- Submit for Approval -->
          ${editable ? `
            <button id="btn-submit-quote" class="btn btn-primary btn-sm">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
              <span>Submit Quote</span>
            </button>
          ` : ''}

          <!-- Cancel Quote -->
          ${editable ? `
            <button id="btn-cancel-quote" class="btn btn-secondary btn-sm" style="color: var(--color-coral);" title="Cancel this draft quotation">
              <span>Cancel</span>
            </button>
          ` : ''}
        </div>
      </div>

      ${!editable ? `
        <div class="alert alert-navy" style="margin-bottom: var(--space-md); background: #EFF6FF; border-color: #BFDBFE; color: #1E40AF;">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
          <span>This quotation is currently locked in <strong>${formatStatusLabel(q.status)}</strong> status. Modifications are restricted to authorized reviewers.</span>
        </div>
      ` : ''}

      <!-- 3-Zone Workspace Grid -->
      <div class="builder-workspace-grid">
        <!-- Zone 1: Left Product Catalog -->
        <aside class="builder-catalog-panel">
          <div class="catalog-header">
            <h3>Product Catalogue</h3>
            <div class="input-wrapper" style="margin-bottom: var(--space-xs);">
              <input type="text" id="catalog-search-input" class="form-input" style="font-size: var(--font-size-xs); padding: 6px 8px;" placeholder="Search SKU or name..." />
            </div>
            <select id="catalog-category-filter" class="form-input" style="font-size: var(--font-size-xs); padding: 4px 6px;">
              <option value="">All Categories</option>
              ${catalogCategories.map(cat => `<option value="${cat.id}">${cat.name}</option>`).join('')}
            </select>
          </div>

          <div id="catalog-items-list" class="catalog-list">
            <!-- Rendered by renderCatalog() -->
          </div>
        </aside>

        <!-- Zone 2: Center Quotation Items & Lines -->
        <main class="builder-center-panel">
          <!-- Customer Info Header Strip -->
          <div class="customer-info-strip">
            <div class="info-strip-col">
              <label>Customer</label>
              <span>${custName}</span>
            </div>
            <div class="info-strip-col">
              <label>Customer Tier</label>
              <span>${custTier}</span>
            </div>
            <div class="info-strip-col">
              <label>Payment Terms</label>
              ${editable ? `
                <select id="header-payment-terms-select" class="form-input" style="padding: 2px 6px; font-size: var(--font-size-xs); height: 26px; font-weight: 600;">
                  <option value="0" ${q.payment_terms_days === 0 ? 'selected' : ''}>Due on Receipt (Net 0)</option>
                  <option value="15" ${q.payment_terms_days === 15 ? 'selected' : ''}>Net 15 Days</option>
                  <option value="30" ${q.payment_terms_days === 30 ? 'selected' : ''}>Net 30 Days</option>
                  <option value="45" ${q.payment_terms_days === 45 ? 'selected' : ''}>Net 45 Days</option>
                  <option value="60" ${q.payment_terms_days === 60 ? 'selected' : ''}>Net 60 Days</option>
                  <option value="90" ${q.payment_terms_days === 90 ? 'selected' : ''}>Net 90 Days</option>
                </select>
              ` : `<span>Net ${q.payment_terms_days} Days</span>`}
            </div>
            <div class="info-strip-col">
              <label>Owner / Sales Rep</label>
              <span>${repName}</span>
            </div>
          </div>

          <!-- Quotation Lines Table -->
          <div class="quote-lines-card">
            <div class="quote-lines-header">
              <h3>Quotation Products (${q.lines ? q.lines.length : 0})</h3>
              <span style="font-size: var(--font-size-xs); color: var(--color-text-secondary);">Currency: <strong>${q.currency}</strong></span>
            </div>

            <div style="overflow-x: auto;">
              <table class="lines-table">
                <thead>
                  <tr>
                    <th>Product / SKU</th>
                    <th>Billing Plan</th>
                    <th>List Price</th>
                    <th style="width: 110px;">Qty</th>
                    <th>Line Discount</th>
                    <th>Effective Disc</th>
                    <th>Net Line Total</th>
                    <th>Margin</th>
                    <th>Risk</th>
                    ${editable ? '<th style="width: 40px;"></th>' : ''}
                  </tr>
                </thead>
                <tbody id="quote-lines-tbody">
                  <!-- Rendered by renderQuoteLines() -->
                </tbody>
              </table>
            </div>
          </div>

          <!-- Order-Level Discount Bar -->
          <div class="order-discount-bar">
            <div>
              <div style="font-size: var(--font-size-sm); font-weight: 700; color: var(--color-navy); display: flex; align-items: center; gap: 6px;">
                <span>Order-Level Discount %</span>
                <span title="Order-level discount applies sequentially on top of line-level discounted totals." style="cursor: help; color: var(--color-text-muted);">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                </span>
              </div>
              <span style="font-size: var(--font-size-xs); color: var(--color-text-secondary);">Applies sequentially to all quote lines.</span>
            </div>

            <div style="display: flex; align-items: center; gap: var(--space-sm);">
              ${editable ? `
                <input type="number" id="order-discount-input" class="form-input" style="width: 90px; text-align: right; font-weight: 700;" value="${Number(q.order_discount_pct || 0).toFixed(2)}" min="0" max="100" step="0.5" />
                <span style="font-weight: 700; color: var(--color-navy);">%</span>
              ` : `
                <span style="font-size: var(--font-size-md); font-weight: 700; color: var(--color-navy);">${Number(q.order_discount_pct || 0).toFixed(2)}%</span>
              `}
            </div>
          </div>
        </main>

        <!-- Zone 3: Right Deal Intelligence Rail -->
        <aside class="builder-intel-panel">
          <!-- Commercial Intelligence Summary -->
          <div class="intel-summary-card">
            <div class="intel-summary-header">
              <span>Deal Intelligence</span>
              <span class="badge ${q.risk_level === 'GREEN' ? 'badge-teal' : 'badge-coral'}">Score: ${Number(q.blended_risk_score).toFixed(1)}</span>
            </div>

            <!-- Risk Banner with Explainability Trigger -->
            <div class="risk-level-banner risk-${q.risk_level}">
              <div style="display: flex; align-items: center; gap: 8px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                <span>Risk: <strong>${q.risk_level}</strong></span>
              </div>
              <button id="btn-show-risk-reasons" class="btn btn-secondary btn-sm" style="padding: 2px 6px; font-size: 0.7rem; background: var(--color-surface);">
                Why?
              </button>
            </div>

            <!-- Prominent Net Total -->
            <div class="intel-metric-big">
              <label>Net Quotation Total</label>
              <div class="val">${q.currency} ${Number(q.net_total).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            </div>

            <!-- Key Financial Key-Value Breakdown -->
            <div class="key-value-list" style="margin-bottom: var(--space-md);">
              <div class="key-value-item">
                <span class="key-label">Gross Subtotal</span>
                <span class="key-value">${q.currency} ${Number(q.gross_subtotal).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              </div>
              <div class="key-value-item">
                <span class="key-label">Total Discount Amount</span>
                <span class="key-value" style="color: var(--color-coral);">- ${q.currency} ${Number(q.discount_amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              </div>
              <div class="key-value-item">
                <span class="key-label">Effective Weighted Discount</span>
                <span class="key-value">${Number(q.weighted_effective_discount_pct).toFixed(2)}%</span>
              </div>
              <div class="key-value-item">
                <span class="key-label">Margin Amount</span>
                <span class="key-value">${q.currency} ${Number(q.margin_amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              </div>
              <div class="key-value-item">
                <span class="key-label">Commercial Margin %</span>
                <span class="key-value" style="font-weight: 700; color: ${Number(q.margin_pct) >= 15 ? 'var(--color-teal)' : (Number(q.margin_pct) >= 0 ? '#B45309' : 'var(--color-coral)')};">
                  ${Number(q.margin_pct).toFixed(2)}%
                </span>
              </div>
            </div>

            <!-- Submit Action -->
            ${editable ? `
              <button id="btn-intel-submit-quote" class="btn btn-primary btn-block">
                <span>Submit for Commercial Routing</span>
              </button>
            ` : ''}
          </div>

          <!-- Deal Health Intelligence Card (Phase 6 Part 1) -->
          <div class="card" style="padding: var(--space-md); margin-bottom: var(--space-md); border-top: 3px solid var(--color-teal);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-xs);">
              <span style="font-size: var(--font-size-xs); font-weight: 700; color: var(--color-navy); text-transform: uppercase; letter-spacing: 0.05em;">Deal Health</span>
              <span id="builder-health-badge"><span class="spinner spinner-teal" style="width: 12px; height: 12px;"></span></span>
            </div>
            <div id="builder-health-summary" style="font-size: var(--font-size-xs); color: var(--color-text-secondary); margin-bottom: var(--space-sm); line-height: 1.4;">
              Assessing risk signals...
            </div>
            <div style="display: flex; gap: var(--space-xs);">
              <button id="btn-builder-view-health" class="btn btn-secondary btn-sm" style="flex: 1; font-size: 0.7rem; padding: 4px 6px;">
                <span>View Full Health</span>
              </button>
              <button id="btn-builder-eval-health" class="btn btn-secondary btn-sm" style="font-size: 0.7rem; padding: 4px 6px;" title="Recalculate Deal Health">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
              </button>
            </div>
          </div>

          <!-- Upsell & Cross-Sell Recommendations Panel -->
          <div class="recommendations-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-xs);">
              <h4 style="font-size: var(--font-size-sm); color: var(--color-navy); margin: 0; font-weight: 700;">Recommended for this Deal</h4>
              <span class="badge badge-teal" style="font-size: 0.65rem;">AI / Rules</span>
            </div>
            <p style="font-size: 0.75rem; color: var(--color-text-secondary); margin-bottom: var(--space-xs);">
              Recommended products based on active items, customer tier affinity, and margin safeguards.
            </p>

            <div id="recommendations-container">
              <div style="text-align: center; padding: 12px; font-size: var(--font-size-xs); color: var(--color-text-muted);">
                <span class="spinner spinner-teal"></span> Loading recommendations...
              </div>
            </div>
          </div>
        </aside>
      </div>
    `;

    renderCatalog();
    renderQuoteLines();
    setupBuilderEvents();
    loadRecommendations();
    loadDealHealthWidget();
  }

  function renderCatalog() {
    const listEl = document.getElementById('catalog-items-list');
    if (!listEl) return;

    const searchVal = document.getElementById('catalog-search-input')?.value.toLowerCase().trim() || '';
    const catVal = document.getElementById('catalog-category-filter')?.value || '';
    const editable = isEditable();

    const filtered = catalogProducts.filter(p => {
      if (!p.is_active) return false;
      if (catVal && p.category_id !== parseInt(catVal, 10)) return false;
      if (searchVal) {
        return p.name.toLowerCase().includes(searchVal) || p.sku.toLowerCase().includes(searchVal);
      }
      return true;
    });

    if (filtered.length === 0) {
      listEl.innerHTML = `<div style="text-align: center; padding: 20px; color: var(--color-text-muted); font-size: var(--font-size-xs);">No products match filter</div>`;
      return;
    }

    listEl.innerHTML = filtered.map(p => `
      <div class="catalog-item-card">
        <div class="catalog-item-name">${p.name}</div>
        <div class="catalog-item-sku">SKU: ${p.sku}</div>
        <div class="catalog-item-footer">
          <span class="catalog-item-price">${p.currency} ${Number(p.list_price).toFixed(2)}</span>
          <button class="btn btn-secondary btn-sm btn-add-catalog-item" data-product-id="${p.id}" ${!editable ? 'disabled' : ''} style="padding: 2px 8px; font-size: 0.75rem;">
            <span>+ Add</span>
          </button>
        </div>
      </div>
    `).join('');

    listEl.querySelectorAll('.btn-add-catalog-item').forEach(btn => {
      btn.addEventListener('click', async () => {
        const prodId = parseInt(btn.dataset.productId, 10);
        await handleAddProductLine(prodId);
      });
    });
  }

  function renderQuoteLines() {
    const tbody = document.getElementById('quote-lines-tbody');
    if (!tbody) return;

    const q = currentQuote;
    const editable = isEditable();

    if (!q.lines || q.lines.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="${editable ? 10 : 9}" style="text-align: center; padding: 36px 12px; color: var(--color-text-muted);">
            <div style="font-weight: 600; margin-bottom: 4px;">No products added to this quotation</div>
            <div style="font-size: var(--font-size-xs);">Select products from the catalogue on the left to start building your quote.</div>
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = q.lines.map(line => {
      const prodName = line.product ? line.product.name : `Product #${line.product_id}`;
      const prodSku = line.product ? line.product.sku : '—';
      const marginVal = Number(line.margin_pct || 0);
      const marginColor = marginVal >= 15 ? 'var(--color-teal)' : (marginVal >= 0 ? '#B45309' : 'var(--color-coral)');
      const isUpsell = line.source_type === 'UPSELL';
      const stdDisc = line.standard_discount_pct_snapshot ? `${Number(line.standard_discount_pct_snapshot).toFixed(0)}%` : '—';
      const maxDisc = line.max_discount_pct_snapshot ? `${Number(line.max_discount_pct_snapshot).toFixed(0)}%` : '—';

      return `
        <tr data-line-id="${line.id}">
          <td>
            <div style="font-weight: 600; color: var(--color-navy);">${prodName}</div>
            <div style="font-family: monospace; font-size: 0.75rem; color: var(--color-text-secondary);">${prodSku}</div>
            ${isUpsell ? `<span class="source-tag source-tag-upsell">★ Recommended Upsell</span>` : ''}
          </td>
          <td>
            ${editable ? `
              <select class="form-input line-billing-plan-select" data-line-id="${line.id}" style="padding: 2px 4px; font-size: 0.75rem; width: 95px;">
                <option value="">One-Time</option>
                ${billingPlans.map(bp => `<option value="${bp.id}" ${line.billing_plan_id === bp.id ? 'selected' : ''}>${bp.name}</option>`).join('')}
              </select>
            ` : `
              <span style="font-size: 0.75rem;">${line.billing_plan ? line.billing_plan.name : 'One-Time'}</span>
            `}
          </td>
          <td style="font-family: monospace;">${q.currency} ${Number(line.unit_list_price).toFixed(2)}</td>
          <td>
            ${editable ? `
              <div class="qty-control">
                <button class="qty-btn btn-qty-minus" data-line-id="${line.id}">-</button>
                <input type="number" class="qty-input line-qty-input" data-line-id="${line.id}" value="${Number(line.quantity)}" min="1" step="1" />
                <button class="qty-btn btn-qty-plus" data-line-id="${line.id}">+</button>
              </div>
            ` : `
              <span style="font-weight: 600;">${Number(line.quantity)}</span>
            `}
          </td>
          <td>
            ${editable ? `
              <div class="discount-cell-wrapper">
                <div class="discount-input-row">
                  <input type="number" class="form-input discount-input line-discount-input" data-line-id="${line.id}" value="${Number(line.line_discount_pct || 0).toFixed(1)}" min="0" max="100" step="0.5" />
                  <span style="font-size: var(--font-size-xs);">%</span>
                </div>
                <div class="discount-limit-hint">Std: ${stdDisc} | Max: ${maxDisc}</div>
              </div>
            ` : `
              <span>${Number(line.line_discount_pct || 0).toFixed(1)}%</span>
            `}
          </td>
          <td style="font-size: var(--font-size-xs); font-weight: 600;">${Number(line.effective_discount_pct || 0).toFixed(1)}%</td>
          <td style="font-weight: 700; color: var(--color-navy);">${q.currency} ${Number(line.net_line_total).toFixed(2)}</td>
          <td style="font-weight: 600; color: ${marginColor};">${marginVal.toFixed(1)}%</td>
          <td>
            <span class="badge ${line.risk_level === 'GREEN' ? 'badge-teal' : 'badge-coral'}" style="font-size: 0.6875rem;">
              ${line.risk_level}
            </span>
          </td>
          ${editable ? `
            <td>
              <button class="btn btn-secondary btn-sm btn-delete-line" data-line-id="${line.id}" title="Remove item" style="padding: 4px 6px; color: var(--color-coral); border: none;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
            </td>
          ` : ''}
        </tr>
      `;
    }).join('');

    setupLineActionEvents();
  }

  function setupLineActionEvents() {
    // Quantity Buttons
    document.querySelectorAll('.btn-qty-minus').forEach(btn => {
      btn.addEventListener('click', () => {
        const lineId = parseInt(btn.dataset.lineId, 10);
        const input = document.querySelector(`.line-qty-input[data-line-id="${lineId}"]`);
        if (input) {
          const val = Math.max(1, parseInt(input.value, 10) - 1);
          input.value = val;
          debouncedUpdateLine(lineId, { quantity: val });
        }
      });
    });

    document.querySelectorAll('.btn-qty-plus').forEach(btn => {
      btn.addEventListener('click', () => {
        const lineId = parseInt(btn.dataset.lineId, 10);
        const input = document.querySelector(`.line-qty-input[data-line-id="${lineId}"]`);
        if (input) {
          const val = parseInt(input.value, 10) + 1;
          input.value = val;
          debouncedUpdateLine(lineId, { quantity: val });
        }
      });
    });

    // Quantity Direct Input
    document.querySelectorAll('.line-qty-input').forEach(input => {
      input.addEventListener('change', () => {
        const lineId = parseInt(input.dataset.lineId, 10);
        const val = Math.max(1, parseInt(input.value, 10) || 1);
        input.value = val;
        debouncedUpdateLine(lineId, { quantity: val });
      });
    });

    // Line Discount Input
    document.querySelectorAll('.line-discount-input').forEach(input => {
      input.addEventListener('change', () => {
        const lineId = parseInt(input.dataset.lineId, 10);
        const val = Math.min(100, Math.max(0, parseFloat(input.value) || 0.0));
        input.value = val.toFixed(1);
        debouncedUpdateLine(lineId, { line_discount_pct: val });
      });
    });

    // Billing Plan Select
    document.querySelectorAll('.line-billing-plan-select').forEach(select => {
      select.addEventListener('change', () => {
        const lineId = parseInt(select.dataset.lineId, 10);
        const val = select.value ? parseInt(select.value, 10) : null;
        debouncedUpdateLine(lineId, { billing_plan_id: val });
      });
    });

    // Delete Line Button
    document.querySelectorAll('.btn-delete-line').forEach(btn => {
      btn.addEventListener('click', async () => {
        const lineId = parseInt(btn.dataset.lineId, 10);
        if (confirm('Remove this product line from the quotation?')) {
          await handleDeleteLine(lineId);
        }
      });
    });
  }

  function setupBuilderEvents() {
    // Catalog Filtering
    const searchInput = document.getElementById('catalog-search-input');
    const catSelect = document.getElementById('catalog-category-filter');
    if (searchInput) searchInput.addEventListener('input', renderCatalog);
    if (catSelect) catSelect.addEventListener('change', renderCatalog);

    // Payment Terms Change
    const termsSelect = document.getElementById('header-payment-terms-select');
    if (termsSelect) {
      termsSelect.addEventListener('change', async () => {
        const termsVal = parseInt(termsSelect.value, 10);
        await handleUpdateHeader({ payment_terms_days: termsVal });
      });
    }

    // Order Discount Change
    const orderDiscInput = document.getElementById('order-discount-input');
    if (orderDiscInput) {
      orderDiscInput.addEventListener('change', async () => {
        const discVal = Math.min(100, Math.max(0, parseFloat(orderDiscInput.value) || 0.0));
        orderDiscInput.value = discVal.toFixed(2);
        await handleUpdateHeader({ order_discount_pct: discVal });
      });
    }

    // Recalculate Button
    document.getElementById('btn-recalculate-quote')?.addEventListener('click', async () => {
      try {
        const res = await global.QuotationsAPI.recalculate(quoteId);
        if (res.ok && res.data?.quotation) {
          currentQuote = res.data.quotation;
          renderWorkspace();
          global.DealFlowUI.toast('Quotation recalculated successfully.', 'teal');
        }
      } catch (err) {
        global.DealFlowUI.toast('Failed to recalculate quotation.', 'coral');
      }
    });

    // Risk Reasons Explanations
    document.getElementById('btn-show-risk-reasons')?.addEventListener('click', () => {
      showRiskReasonsModal();
    });

    // What-If Simulator
    document.getElementById('btn-open-whatif')?.addEventListener('click', () => {
      openWhatIfModal();
    });

    // Audit Trail
    document.getElementById('btn-open-audit')?.addEventListener('click', () => {
      openAuditTrailModal();
    });

    // Version History & Compare
    document.getElementById('btn-view-versions')?.addEventListener('click', () => {
      openVersionsModal();
    });

    // Customer Negotiation & Messages
    document.getElementById('btn-view-messages')?.addEventListener('click', () => {
      openMessagesDrawer();
    });

    // Send to Customer Action
    document.getElementById('btn-send-to-customer')?.addEventListener('click', async () => {
      if (confirm(`Send quotation ${currentQuote.quote_number} to customer for review?`)) {
        try {
          const res = await global.NegotiationAPI.sendToCustomer(quoteId);
          if (res.ok) {
            currentQuote = res.data;
            renderWorkspace();
            global.DealFlowUI.toast(`Quotation ${currentQuote.quote_number} sent to customer successfully.`, 'teal');
          } else {
            global.DealFlowUI.toast(res.data?.detail || 'Failed to send quotation to customer.', 'coral');
          }
        } catch (e) {
          global.DealFlowUI.toast('Network error sending quotation to customer.', 'coral');
        }
      }
    });

    // View Sales Order Action (CUSTOMER_CONFIRMED)
    document.getElementById('btn-view-sales-order')?.addEventListener('click', async () => {
      try {
        const res = await global.OrdersAPI.getByQuotation(quoteId);
        if (res.ok && res.data && res.data.id) {
          global.DealFlowApp.switchView('order-detail', { orderId: res.data.id });
        } else {
          global.DealFlowUI.toast('Sales order not found for this confirmed quotation.', 'navy');
        }
      } catch (err) {
        global.DealFlowUI.toast('Error locating sales order.', 'coral');
      }
    });

    // Submit Quote Button
    const submitBtn = document.getElementById('btn-submit-quote');
    const intelSubmitBtn = document.getElementById('btn-intel-submit-quote');
    if (submitBtn) submitBtn.addEventListener('click', handleSubmitQuote);
    if (intelSubmitBtn) intelSubmitBtn.addEventListener('click', handleSubmitQuote);

    // Cancel Quote Button
    document.getElementById('btn-cancel-quote')?.addEventListener('click', async () => {
      if (confirm('Are you sure you want to cancel this quotation? This cannot be undone.')) {
        try {
          const res = await global.QuotationsAPI.cancel(quoteId);
          if (res.ok) {
            currentQuote = res.data;
            renderWorkspace();
            global.DealFlowUI.toast('Quotation cancelled.', 'navy');
          } else {
            global.DealFlowUI.toast(res.data?.detail || 'Failed to cancel quotation.', 'coral');
          }
        } catch (e) {
          global.DealFlowUI.toast('Network error cancelling quote.', 'coral');
        }
      }
    });
  }

  function showSavingIndicator(show) {
    const indicator = document.getElementById('save-status-indicator');
    if (indicator) {
      indicator.style.display = show ? 'inline-block' : 'none';
    }
  }

  async function handleAddProductLine(productId) {
    showSavingIndicator(true);
    try {
      const payload = {
        product_id: productId,
        quantity: 1,
        line_discount_pct: 0.0
      };

      const res = await global.QuotationsAPI.addLine(quoteId, payload);
      showSavingIndicator(false);

      if (!res.ok) {
        global.DealFlowUI.toast(res.data?.detail || res.error || 'Failed to add product to quotation.', 'coral');
        return;
      }

      currentQuote = res.data;
      renderWorkspace();
      global.DealFlowUI.toast('Product line added.', 'teal');
    } catch (err) {
      showSavingIndicator(false);
      global.DealFlowUI.toast('Network error adding product.', 'coral');
    }
  }

  function debouncedUpdateLine(lineId, payload) {
    clearTimeout(saveDebounceTimer);
    showSavingIndicator(true);
    saveDebounceTimer = setTimeout(async () => {
      try {
        const res = await global.QuotationsAPI.updateLine(quoteId, lineId, payload);
        showSavingIndicator(false);
        if (!res.ok) {
          global.DealFlowUI.toast(res.data?.detail || res.error || 'Failed to update quotation line.', 'coral');
          return;
        }
        currentQuote = res.data;
        renderWorkspace();
      } catch (err) {
        showSavingIndicator(false);
        global.DealFlowUI.toast('Error updating line.', 'coral');
      }
    }, 400);
  }

  async function handleDeleteLine(lineId) {
    showSavingIndicator(true);
    try {
      const res = await global.QuotationsAPI.removeLine(quoteId, lineId);
      showSavingIndicator(false);
      if (!res.ok) {
        global.DealFlowUI.toast(res.data?.detail || res.error || 'Failed to delete line.', 'coral');
        return;
      }
      currentQuote = res.data;
      renderWorkspace();
      global.DealFlowUI.toast('Product line removed.', 'teal');
    } catch (err) {
      showSavingIndicator(false);
      global.DealFlowUI.toast('Network error deleting line.', 'coral');
    }
  }

  async function handleUpdateHeader(payload) {
    showSavingIndicator(true);
    try {
      const res = await global.QuotationsAPI.update(quoteId, payload);
      showSavingIndicator(false);
      if (!res.ok) {
        global.DealFlowUI.toast(res.data?.detail || res.error || 'Failed to update quotation header.', 'coral');
        return;
      }
      currentQuote = res.data;
      renderWorkspace();
    } catch (err) {
      showSavingIndicator(false);
      global.DealFlowUI.toast('Error updating quotation header.', 'coral');
    }
  }

  async function loadRecommendations() {
    const recContainer = document.getElementById('recommendations-container');
    if (!recContainer) return;

    try {
      const res = await global.QuotationsAPI.getRecommendations(quoteId);
      if (!res.ok) {
        recContainer.innerHTML = `<div style="font-size: 0.75rem; color: var(--color-text-muted); text-align: center; padding: 10px;">No recommendations available</div>`;
        return;
      }

      const recs = res.data || [];
      if (recs.length === 0) {
        recContainer.innerHTML = `
          <div style="font-size: 0.75rem; color: var(--color-text-muted); text-align: center; padding: 14px 8px; border: 1px dashed var(--color-border); border-radius: var(--radius-sm);">
            No eligible recommendations for this quotation.
          </div>
        `;
        return;
      }

      recContainer.innerHTML = recs.map(r => {
        const prodName = r.suggested_product ? r.suggested_product.name : `Product #${r.suggested_product_id}`;
        const editable = isEditable();

        return `
          <div class="recommendation-item">
            <div class="rec-title-row">
              <span class="rec-product-name">${prodName} (x${Number(r.recommended_qty)})</span>
              ${r.is_promoted ? `<span class="badge badge-teal" style="font-size: 0.6rem;">${r.promotion_label || 'Featured'}</span>` : ''}
            </div>
            <div class="rec-explanation">${r.explanation}</div>
            <div class="rec-impact-grid">
              <div>Incr. Rev: <strong>+$${Number(r.incremental_revenue).toFixed(2)}</strong></div>
              <div>Incr. Margin: <strong>+${Number(r.incremental_margin_pct).toFixed(1)}%</strong></div>
              <div>Projected Total: <strong>$${Number(r.projected_quote_net_total).toFixed(2)}</strong></div>
              <div>Projected Margin: <strong>${Number(r.projected_quote_margin_pct).toFixed(1)}%</strong></div>
            </div>
            ${editable ? `
              <div class="rec-actions">
                <button class="btn btn-primary btn-sm btn-add-recommendation" data-rule-id="${r.rule_id}" style="padding: 2px 8px; font-size: 0.75rem; flex: 1;">
                  + Add to Quote
                </button>
                <button class="btn btn-secondary btn-sm btn-dismiss-recommendation" data-rule-id="${r.rule_id}" style="padding: 2px 6px; font-size: 0.75rem;">
                  Dismiss
                </button>
              </div>
            ` : ''}
          </div>
        `;
      }).join('');

      recContainer.querySelectorAll('.btn-add-recommendation').forEach(btn => {
        btn.addEventListener('click', async () => {
          const ruleId = parseInt(btn.dataset.ruleId, 10);
          btn.disabled = true;
          try {
            const addRes = await global.QuotationsAPI.addRecommendation(quoteId, ruleId);
            if (addRes.ok) {
              currentQuote = addRes.data;
              renderWorkspace();
              global.DealFlowUI.toast('Recommendation added to quote!', 'teal');
            } else {
              global.DealFlowUI.toast(addRes.data?.detail || 'Failed to add recommendation.', 'coral');
              btn.disabled = false;
            }
          } catch (e) {
            btn.disabled = false;
            global.DealFlowUI.toast('Network error adding recommendation.', 'coral');
          }
        });
      });

      recContainer.querySelectorAll('.btn-dismiss-recommendation').forEach(btn => {
        btn.addEventListener('click', async () => {
          const ruleId = parseInt(btn.dataset.ruleId, 10);
          try {
            const disRes = await global.QuotationsAPI.dismissRecommendation(quoteId, ruleId);
            if (disRes.ok) {
              currentQuote = disRes.data;
              await loadRecommendations();
              global.DealFlowUI.toast('Recommendation dismissed.', 'navy');
            } else {
              global.DealFlowUI.toast(disRes.data?.detail || 'Failed to dismiss.', 'coral');
            }
          } catch (e) {
            global.DealFlowUI.toast('Network error dismissing recommendation.', 'coral');
          }
        });
      });
    } catch (err) {
      console.warn('Failed to load recommendations:', err);
    }
  }

  async function loadDealHealthWidget() {
    const badgeEl = document.getElementById('builder-health-badge');
    const summaryEl = document.getElementById('builder-health-summary');
    const viewBtn = document.getElementById('btn-builder-view-health');
    const evalBtn = document.getElementById('btn-builder-eval-health');

    if (!badgeEl || !summaryEl) return;

    viewBtn?.addEventListener('click', () => {
      global.DealFlowApp.switchView('deal-health', { quoteId: quoteId });
    });

    evalBtn?.addEventListener('click', async () => {
      evalBtn.disabled = true;
      badgeEl.innerHTML = `<span class="spinner spinner-teal" style="width: 12px; height: 12px;"></span>`;
      try {
        const evRes = await global.DealHealthAPI.evaluateQuotationHealth(quoteId);
        if (evRes.ok) {
          global.DealFlowUI.toast('Deal Health recalculated.', 'teal');
          await loadDealHealthWidget();
        } else {
          global.DealFlowUI.toast(evRes.data?.detail || 'Failed to recalculate health.', 'coral');
        }
      } catch (e) {
        global.DealFlowUI.toast('Error calculating health.', 'coral');
      } finally {
        evalBtn.disabled = false;
      }
    });

    try {
      if (!global.DealHealthAPI) return;
      const res = await global.DealHealthAPI.getQuotationHealth(quoteId);
      if (res.ok && res.data) {
        const h = res.data;
        const levelCls = h.health_level === 'HEALTHY' ? 'badge-teal' : (h.health_level === 'WATCH' ? 'badge-navy' : 'badge-coral');
        badgeEl.innerHTML = `<span class="badge ${levelCls}" style="font-weight: 700; font-size: 0.65rem;">${h.health_level} (${Number(h.health_score).toFixed(0)})</span>`;
        summaryEl.innerHTML = h.summary ? `<span>${h.summary}</span>` : `<span>Active Risk Signals: <strong>${h.signal_count || 0}</strong></span>`;
      } else {
        badgeEl.innerHTML = `<span class="badge badge-navy" style="font-size: 0.65rem;">Not Evaluated</span>`;
        summaryEl.innerHTML = `<span>Click recalculate to evaluate commercial deal health.</span>`;
      }
    } catch (e) {
      badgeEl.innerHTML = `<span class="badge badge-navy" style="font-size: 0.65rem;">—</span>`;
      summaryEl.innerHTML = `<span>Deal health data not available.</span>`;
    }
  }

  function showRiskReasonsModal() {
    const modal = document.getElementById('dealflow-modal-overlay');
    if (!modal) return;

    const reasons = currentQuote.risk_reasons || [];

    modal.innerHTML = `
      <div class="modal-dialog animate-fade-in" style="max-width: 600px;">
        <div class="modal-header">
          <div style="display: flex; align-items: center; gap: 8px;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--color-coral);"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            <h3 class="modal-title">Risk Evaluation & Explainability</h3>
          </div>
          <button class="modal-close" aria-label="Close" onclick="window.DealFlowUI.closeModal();">&times;</button>
        </div>
        <div class="modal-body" style="padding: 16px 20px;">
          <div style="margin-bottom: var(--space-md); font-size: var(--font-size-sm); color: var(--color-text-secondary);">
            DealFlow360 evaluates commercial policy compliance across each line item. Blended risk score: <strong>${Number(currentQuote.blended_risk_score).toFixed(1)}</strong> (${currentQuote.risk_level}).
          </div>

          ${reasons.length === 0 ? `
            <div class="alert alert-teal" style="background: var(--color-teal-light); border-color: var(--color-teal-border); color: var(--color-teal-hover);">
              <span>All quote lines comply with configured standard commercial policies. No policy violations detected.</span>
            </div>
          ` : `
            <div style="display: flex; flex-direction: column; gap: var(--space-sm);">
              ${reasons.map(r => `
                <div class="card" style="padding: var(--space-md); border-left: 4px solid ${r.severity === 'HIGH' ? 'var(--color-coral)' : '#F59E0B'};">
                  <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="font-weight: 700; font-size: var(--font-size-xs); color: var(--color-navy);">${r.code}</span>
                    <span class="badge ${r.severity === 'HIGH' ? 'badge-coral' : 'badge-navy'}" style="font-size: 0.65rem;">${r.severity}</span>
                  </div>
                  <div style="font-size: var(--font-size-sm); color: var(--color-text); margin-bottom: 6px;">${r.message}</div>
                  ${(r.actual_value !== null && r.threshold_value !== null) ? `
                    <div style="font-size: var(--font-size-xs); color: var(--color-text-secondary); background: var(--color-background); padding: 4px 8px; border-radius: var(--radius-sm);">
                      Actual: <strong>${Number(r.actual_value)}%</strong> | Policy Limit: <strong>${Number(r.threshold_value)}%</strong>
                    </div>
                  ` : ''}
                </div>
              `).join('')}
            </div>
          `}
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary btn-sm" onclick="window.DealFlowUI.closeModal();">Close</button>
        </div>
      </div>
    `;

    global.DealFlowUI.openModal();
  }

  function openWhatIfModal() {
    const modal = document.getElementById('dealflow-modal-overlay');
    if (!modal) return;

    const q = currentQuote;

    modal.innerHTML = `
      <div class="modal-dialog animate-fade-in" style="max-width: 800px;">
        <div class="modal-header">
          <div style="display: flex; align-items: center; gap: 8px;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--color-teal);"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            <h3 class="modal-title">What-If Deal Simulator</h3>
          </div>
          <button class="modal-close" aria-label="Close" onclick="window.DealFlowUI.closeModal();">&times;</button>
        </div>
        <div class="modal-body" style="padding: 16px 20px;">
          <div class="whatif-container">
            <div class="whatif-alert">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
              <span><strong>Preview only:</strong> Simulations run hypothetical calculations without modifying the live quotation.</span>
            </div>

            <!-- Hypothetical Inputs Grid -->
            <div class="card" style="padding: var(--space-md);">
              <h4 style="font-size: var(--font-size-xs); font-weight: 700; text-transform: uppercase; color: var(--color-navy); margin-bottom: var(--space-sm);">
                Simulate Parameter Overrides
              </h4>
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-md);">
                <div class="form-group" style="margin-bottom: 0;">
                  <label class="form-label">Simulated Order Discount %</label>
                  <input type="number" id="whatif-order-disc" class="form-input" value="${Number(q.order_discount_pct || 0).toFixed(2)}" min="0" max="100" step="0.5" />
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                  <label class="form-label">Simulated Payment Terms (Days)</label>
                  <input type="number" id="whatif-terms" class="form-input" value="${q.payment_terms_days || 30}" min="0" step="1" />
                </div>
              </div>

              ${q.lines && q.lines.length > 0 ? `
                <div style="margin-top: var(--space-md); border-top: 1px solid var(--color-border-light); padding-top: var(--space-sm);">
                  <div style="font-size: var(--font-size-xs); font-weight: 600; margin-bottom: var(--space-xs);">Line Item Overrides</div>
                  <div style="display: flex; flex-direction: column; gap: var(--space-xs);">
                    ${q.lines.map(l => `
                      <div style="display: grid; grid-template-columns: 2fr 1fr 1fr; gap: var(--space-sm); align-items: center; font-size: var(--font-size-xs);">
                        <span>${l.product ? l.product.name : 'Line #' + l.id}</span>
                        <div>
                          <input type="number" class="form-input whatif-line-qty" data-line-id="${l.id}" value="${Number(l.quantity)}" min="1" placeholder="Qty" style="font-size: 0.75rem; padding: 4px;" />
                        </div>
                        <div>
                          <input type="number" class="form-input whatif-line-disc" data-line-id="${l.id}" value="${Number(l.line_discount_pct || 0).toFixed(1)}" min="0" max="100" step="0.5" placeholder="Disc %" style="font-size: 0.75rem; padding: 4px;" />
                        </div>
                      </div>
                    `).join('')}
                  </div>
                </div>
              ` : ''}

              <div style="margin-top: var(--space-md); text-align: right;">
                <button id="btn-run-simulation" class="btn btn-primary btn-sm">
                  <span class="spinner" style="display: none;"></span>
                  <span>Run What-If Simulation</span>
                </button>
              </div>
            </div>

            <!-- Simulation Results Comparison -->
            <div id="whatif-results-area" style="display: none;">
              <!-- Rendered upon simulation calculation -->
            </div>
          </div>
        </div>
      </div>
    `;

    global.DealFlowUI.openModal();

    const runBtn = document.getElementById('btn-run-simulation');
    runBtn.addEventListener('click', async () => {
      runBtn.disabled = true;
      runBtn.querySelector('.spinner').style.display = 'inline-block';

      const simOrderDisc = parseFloat(document.getElementById('whatif-order-disc').value) || 0.0;
      const simTerms = parseInt(document.getElementById('whatif-terms').value, 10) || 30;

      const lineOverrides = [];
      document.querySelectorAll('.whatif-line-qty').forEach(input => {
        const lineId = parseInt(input.dataset.lineId, 10);
        const qty = parseFloat(input.value) || 1;
        const discInput = document.querySelector(`.whatif-line-disc[data-line-id="${lineId}"]`);
        const disc = discInput ? (parseFloat(discInput.value) || 0) : 0;
        lineOverrides.push({
          line_id: lineId,
          quantity: qty,
          line_discount_pct: disc
        });
      });

      const payload = {
        order_discount_pct: simOrderDisc,
        payment_terms_days: simTerms,
        line_overrides: lineOverrides.length > 0 ? lineOverrides : undefined
      };

      try {
        const res = await global.QuotationsAPI.runWhatIf(quoteId, payload);
        runBtn.disabled = false;
        runBtn.querySelector('.spinner').style.display = 'none';

        if (!res.ok) {
          global.DealFlowUI.toast(res.data?.detail || res.error || 'Simulation failed.', 'coral');
          return;
        }

        renderWhatIfResults(res.data);
      } catch (e) {
        runBtn.disabled = false;
        runBtn.querySelector('.spinner').style.display = 'none';
        global.DealFlowUI.toast('Network error running simulation.', 'coral');
      }
    });
  }

  function renderWhatIfResults(data) {
    const area = document.getElementById('whatif-results-area');
    if (!area) return;

    const b = data.before;
    const a = data.after;
    const c = data.changes;

    area.style.display = 'block';
    area.innerHTML = `
      <div class="card" style="padding: var(--space-md);">
        <h4 style="font-size: var(--font-size-xs); font-weight: 700; text-transform: uppercase; color: var(--color-navy); margin-bottom: var(--space-sm);">
          Simulation Impact Comparison
        </h4>

        <table class="whatif-comparison-table">
          <thead>
            <tr>
              <th>Metric</th>
              <th>Current (Saved)</th>
              <th>Simulated</th>
              <th>Delta / Change</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Net Total</strong></td>
              <td>$${Number(b.net_total).toFixed(2)}</td>
              <td style="font-weight: 700; color: var(--color-navy);">$${Number(a.net_total).toFixed(2)}</td>
              <td>
                <span class="delta-pill ${Number(c.net_total_delta) >= 0 ? 'delta-positive' : 'delta-negative'}">
                  ${Number(c.net_total_delta) >= 0 ? '+' : ''}$${Number(c.net_total_delta).toFixed(2)}
                </span>
              </td>
            </tr>
            <tr>
              <td><strong>Margin Amount</strong></td>
              <td>$${Number(b.margin_amount).toFixed(2)}</td>
              <td style="font-weight: 700;">$${Number(a.margin_amount).toFixed(2)}</td>
              <td>
                <span class="delta-pill ${Number(c.margin_amount_delta) >= 0 ? 'delta-positive' : 'delta-negative'}">
                  ${Number(c.margin_amount_delta) >= 0 ? '+' : ''}$${Number(c.margin_amount_delta).toFixed(2)}
                </span>
              </td>
            </tr>
            <tr>
              <td><strong>Margin %</strong></td>
              <td>${Number(b.margin_pct).toFixed(1)}%</td>
              <td style="font-weight: 700; color: ${Number(a.margin_pct) >= 15 ? 'var(--color-teal)' : 'var(--color-coral)'};">${Number(a.margin_pct).toFixed(1)}%</td>
              <td>
                <span class="delta-pill ${Number(c.margin_pct_delta) >= 0 ? 'delta-positive' : 'delta-negative'}">
                  ${Number(c.margin_pct_delta) >= 0 ? '+' : ''}${Number(c.margin_pct_delta).toFixed(1)}%
                </span>
              </td>
            </tr>
            <tr>
              <td><strong>Effective Discount</strong></td>
              <td>${Number(b.weighted_effective_discount_pct).toFixed(1)}%</td>
              <td style="font-weight: 700;">${Number(a.weighted_effective_discount_pct).toFixed(1)}%</td>
              <td>
                <span class="delta-pill delta-neutral">
                  ${(Number(a.weighted_effective_discount_pct) - Number(b.weighted_effective_discount_pct)).toFixed(1)}%
                </span>
              </td>
            </tr>
            <tr>
              <td><strong>Risk Score & Level</strong></td>
              <td>${b.risk_level} (${Number(b.blended_risk_score).toFixed(1)})</td>
              <td style="font-weight: 700; color: ${a.risk_level === 'GREEN' ? 'var(--color-teal)' : 'var(--color-coral)'};">${a.risk_level} (${Number(a.blended_risk_score).toFixed(1)})</td>
              <td>
                <span class="delta-pill ${Number(c.risk_score_delta) <= 0 ? 'delta-positive' : 'delta-negative'}">
                  ${Number(c.risk_score_delta) >= 0 ? '+' : ''}${Number(c.risk_score_delta).toFixed(1)} pts
                </span>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Approval Chain Impact -->
        <div class="approval-chain-preview">
          <div style="font-size: var(--font-size-xs); font-weight: 700; color: var(--color-navy); margin-bottom: 6px;">
            Projected Approval Requirement:
          </div>
          ${a.required_approval_roles.length === 0 ? `
            <div style="font-size: var(--font-size-xs); color: var(--color-teal); font-weight: 600;">✓ No approvals required (Auto-Approve)</div>
          ` : `
            <div style="display: flex; flex-direction: column; gap: 4px;">
              ${a.required_approval_roles.map((role, idx) => `
                <div class="chain-step">
                  <span class="badge badge-navy" style="font-size: 0.65rem;">Step ${idx + 1}</span>
                  <span>${global.DealFlowNav?.formatRole(role) || role}</span>
                </div>
              `).join('')}
            </div>
          `}
        </div>

        <div style="display: flex; justify-content: flex-end; gap: var(--space-sm); margin-top: var(--space-md);">
          <button class="btn btn-secondary btn-sm" onclick="window.DealFlowUI.closeModal();">Close</button>
          <button class="btn btn-primary btn-sm" onclick="window.DealFlowUI.closeModal(); global.DealFlowUI.toast('Apply changes in the quotation editor to save.', 'teal');">
            Apply Manually
          </button>
        </div>
      </div>
    `;
  }

  async function handleSubmitQuote() {
    if (!currentQuote) return;

    if (!currentQuote.lines || currentQuote.lines.length === 0) {
      global.DealFlowUI.toast('Cannot submit an empty quotation. Please add at least one product line.', 'coral');
      return;
    }

    if (!confirm(`Submit quotation ${currentQuote.quote_number} for commercial approval routing?`)) {
      return;
    }

    try {
      const res = await global.QuotationsAPI.submit(quoteId);
      if (!res.ok) {
        const errorDetail = res.data?.detail || res.error || 'Submission failed.';
        global.DealFlowUI.toast(errorDetail, 'coral');
        return;
      }

      const data = res.data;
      if (data.requires_approval) {
        const roles = (data.required_roles || []).map(r => global.DealFlowNav?.formatRole(r) || r).join(' → ');
        alert(`Quotation submitted successfully!\n\nRouting: Routed to ${roles} for approval review.`);
      } else {
        alert('Quotation submitted and automatically APPROVED! (Thresholds within standard policy limits)');
      }

      await loadInitialData();
    } catch (err) {
      global.DealFlowUI.toast('Network error submitting quotation.', 'coral');
    }
  }

  async function openAuditTrailModal() {
    const modal = document.getElementById('dealflow-modal-overlay');
    if (!modal) return;

    modal.innerHTML = `
      <div class="modal-dialog animate-fade-in" style="max-width: 620px;">
        <div class="modal-header">
          <div style="display: flex; align-items: center; gap: 8px;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--color-teal);"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            <h3 class="modal-title">Quotation Activity & Audit Trail</h3>
          </div>
          <button class="modal-close" aria-label="Close" onclick="window.DealFlowUI.closeModal();">&times;</button>
        </div>
        <div class="modal-body" style="padding: 16px 20px;">
          <div id="audit-trail-content">
            <div style="text-align: center; padding: 30px;"><span class="spinner spinner-teal"></span> Loading audit events...</div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary btn-sm" onclick="window.DealFlowUI.closeModal();">Close</button>
        </div>
      </div>
    `;

    global.DealFlowUI.openModal();

    try {
      const res = await global.QuotationsAPI.getAudit(quoteId);
      const content = document.getElementById('audit-trail-content');
      if (!content) return;

      if (!res.ok) {
        content.innerHTML = `<div class="alert alert-coral">Failed to load audit history.</div>`;
        return;
      }

      const events = res.data || [];
      if (events.length === 0) {
        content.innerHTML = `<div style="text-align: center; padding: 24px; color: var(--color-text-muted);">No audit events recorded yet.</div>`;
        return;
      }

      content.innerHTML = `
        <div class="audit-timeline">
          ${events.map(ev => {
            const timeStr = new Date(ev.created_at).toLocaleString();
            const actorName = ev.user ? ev.user.full_name : (ev.user_id ? `User #${ev.user_id}` : 'System');
            const actorRole = ev.user?.role?.name ? (global.DealFlowNav?.formatRole ? global.DealFlowNav.formatRole(ev.user.role.name) : ev.user.role.name) : 'User';

            return `
              <div class="audit-event-item">
                <div class="audit-dot"></div>
                <div class="audit-event-header">
                  <span class="audit-event-title">${formatEventType(ev.event_type)}</span>
                  <span class="audit-event-time">${timeStr}</span>
                </div>
                <div class="audit-event-actor">${actorName} (${actorRole})</div>
                ${ev.from_status && ev.to_status ? `
                  <div style="font-size: 0.75rem; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                    <span style="color: #64748b; font-weight: 500;">Status:</span>
                    <span class="badge badge-navy" style="font-size: 0.65rem;">${ev.from_status}</span>
                    <span style="color: #94a3b8;">&rarr;</span>
                    <span class="badge badge-teal" style="font-size: 0.65rem;">${ev.to_status}</span>
                  </div>
                ` : ''}
                ${ev.reason ? `<div class="audit-event-reason">Reason: ${ev.reason}</div>` : ''}
              </div>
            `;
          }).join('')}
        </div>
      `;
    } catch (e) {
      console.warn('Failed to fetch audit events:', e);
    }
  }

  // Open Internal Version History & Diff Modal
  async function openVersionsModal() {
    const overlay = document.getElementById('dealflow-modal-overlay');
    if (!overlay) return;

    overlay.innerHTML = `
      <div class="modal-dialog animate-fade-in" style="max-width: 800px; width: 90%;">
        <div class="modal-header">
          <div style="display: flex; align-items: center; gap: 8px;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--color-teal);"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
            <h3 class="modal-title">Quotation Revisions & Version Comparison</h3>
          </div>
          <button class="modal-close" aria-label="Close" onclick="window.DealFlowUI.closeModal();">&times;</button>
        </div>
        <div class="modal-body" id="ver-modal-body" style="padding: 16px 20px;">
          <div style="text-align: center; padding: 24px;"><span class="spinner spinner-teal"></span> Loading revision history...</div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary btn-sm" onclick="window.DealFlowUI.closeModal();">Close</button>
        </div>
      </div>
    `;
    global.DealFlowUI.openModal();

    try {
      const res = await global.NegotiationAPI.listVersions(quoteId);
      const versions = res.ok ? res.data : [];
      const body = document.getElementById('ver-modal-body');
      if (!body) return;

      if (!versions || versions.length === 0) {
        body.innerHTML = `<div style="text-align: center; padding: 20px; color: var(--color-text-muted);">No prior archived versions found. Current active version is v${currentQuote.version_number}.</div>`;
        return;
      }

      body.innerHTML = `
        <div style="margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between; background: var(--color-bg); padding: 12px 16px; border-radius: var(--radius-md);">
          <div>
            <strong>Current Active:</strong> Version ${currentQuote.version_number} &bull; ${currentQuote.currency} ${Number(currentQuote.net_total).toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
          <div style="display: flex; gap: 8px; align-items: center;">
            <label style="font-size: 0.8rem; font-weight: 600;">Compare with:</label>
            <select id="select-compare-ver" class="form-input" style="padding: 4px 8px; font-size: 0.8rem; width: 140px;">
              ${versions.map(v => `<option value="${v.version_number}">v${v.version_number} (${new Date(v.created_at).toLocaleDateString()})</option>`).join('')}
            </select>
            <button id="btn-run-compare" class="btn btn-secondary btn-sm">Compare Diff</button>
          </div>
        </div>

        <h4 style="font-size: 0.85rem; color: var(--color-navy); margin-bottom: 8px;">Archived Versions</h4>
        <div style="max-height: 200px; overflow-y: auto; border: 1px solid var(--color-border); border-radius: var(--radius-sm); margin-bottom: 16px;">
          <table class="data-table" style="font-size: 0.8rem;">
            <thead>
              <tr>
                <th>Version</th>
                <th>Status</th>
                <th>Net Total</th>
                <th>Margin %</th>
                <th>Archived At</th>
              </tr>
            </thead>
            <tbody>
              ${versions.map(v => `
                <tr>
                  <td><strong>v${v.version_number}</strong></td>
                  <td>${formatStatusBadge(v.status)}</td>
                  <td>${v.currency} ${Number(v.net_total).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                  <td>${Number(v.margin_pct).toFixed(1)}%</td>
                  <td>${new Date(v.created_at).toLocaleString()}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>

        <div id="version-diff-result-container"></div>
      `;

      document.getElementById('btn-run-compare')?.addEventListener('click', async () => {
        const fromV = parseInt(document.getElementById('select-compare-ver').value, 10);
        const toV = currentQuote.version_number;
        const diffCont = document.getElementById('version-diff-result-container');
        if (!diffCont) return;

        diffCont.innerHTML = `<div style="text-align:center; padding: 12px;"><span class="spinner spinner-teal"></span> Calculating version delta...</div>`;
        const diffRes = await global.NegotiationAPI.compareVersions(quoteId, fromV, toV);
        if (!diffRes.ok) {
          diffCont.innerHTML = `<div class="alert alert-coral">${diffRes.data?.detail || 'Failed to generate version diff.'}</div>`;
          return;
        }

        const d = diffRes.data;
        diffCont.innerHTML = `
          <div class="version-diff-card animate-fade-in" style="margin-top: 12px; border: 1px solid var(--color-border); border-radius: var(--radius-sm); padding: 12px; background: #FAFDFB;">
            <div style="font-weight: 700; color: var(--color-navy); font-size: 0.85rem; margin-bottom: 8px;">
              Delta Comparison: v${d.from_version} &rarr; v${d.to_version}
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 12px; font-size: 0.8rem;">
              <div style="background: white; padding: 8px; border-radius: 4px; border: 1px solid var(--color-border);">
                <div style="color: var(--color-text-secondary);">Net Total Delta</div>
                <div style="font-weight: 700; color: ${d.financial_diff?.net_total_diff < 0 ? 'var(--color-coral)' : 'var(--color-teal)'};">
                  ${d.financial_diff?.net_total_diff >= 0 ? '+' : ''}${d.financial_diff?.net_total_diff?.toFixed(2)}
                </div>
              </div>
              <div style="background: white; padding: 8px; border-radius: 4px; border: 1px solid var(--color-border);">
                <div style="color: var(--color-text-secondary);">Discount Delta</div>
                <div style="font-weight: 700; color: var(--color-navy);">
                  ${d.financial_diff?.order_discount_diff >= 0 ? '+' : ''}${d.financial_diff?.order_discount_diff?.toFixed(2)}%
                </div>
              </div>
              <div style="background: white; padding: 8px; border-radius: 4px; border: 1px solid var(--color-border);">
                <div style="color: var(--color-text-secondary);">Margin Delta</div>
                <div style="font-weight: 700; color: ${d.financial_diff?.margin_diff < 0 ? 'var(--color-coral)' : 'var(--color-teal)'};">
                  ${d.financial_diff?.margin_diff >= 0 ? '+' : ''}${d.financial_diff?.margin_diff?.toFixed(2)}%
                </div>
              </div>
            </div>
            ${d.line_diffs && d.line_diffs.length > 0 ? `
              <div style="font-size: 0.75rem; color: var(--color-text-secondary);">
                <strong>Modified Lines:</strong> ${d.line_diffs.map(l => `${l.product_name} (Qty: ${l.qty_old} &rarr; ${l.qty_new}, Disc: ${l.disc_old}% &rarr; ${l.disc_new}%)`).join('; ')}
              </div>
            ` : '<div style="font-size: 0.75rem; color: var(--color-text-muted);">No line-level differences between these versions.</div>'}
          </div>
        `;
      });
    } catch (e) {
      console.error(e);
    }
  }

  // Open Internal Messages / Negotiation Drawer
  async function openMessagesDrawer() {
    const backdrop = document.getElementById('dealflow-drawer-backdrop');
    const panel = document.getElementById('dealflow-drawer-panel');
    if (!panel || !backdrop) return;

    panel.innerHTML = `
      <div class="drawer-header">
        <div>
          <h3>Negotiation & Customer Messages</h3>
          <div style="font-size: 0.75rem; color: var(--color-text-secondary);">${currentQuote.quote_number} &bull; v${currentQuote.version_number}</div>
        </div>
        <button class="drawer-close-btn" id="btn-close-msg-drawer">&times;</button>
      </div>
      <div class="drawer-body" style="display: flex; flex-direction: column; height: calc(100% - 130px); padding: 16px;">
        <div id="drawer-messages-list" class="negotiation-chat-thread" style="flex: 1; overflow-y: auto; padding: 12px; background: #F8FAFC; border-radius: var(--radius-md); margin-bottom: 12px;">
          <div style="text-align: center; padding: 20px;"><span class="spinner spinner-teal"></span> Loading conversation...</div>
        </div>
        <div class="negotiation-reply-box" style="background: white; border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 12px;">
          <textarea id="sales-reply-content" class="form-input" rows="3" placeholder="Type a message or response to customer..."></textarea>
          <div style="display: flex; justify-content: flex-end; margin-top: 8px;">
            <button id="btn-send-sales-reply" class="btn btn-primary btn-sm">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
              <span>Send Message</span>
            </button>
          </div>
        </div>
      </div>
    `;

    backdrop.classList.add('active');
    panel.classList.add('active');

    const closeDrawer = () => {
      backdrop.classList.remove('active');
      panel.classList.remove('active');
    };
    document.getElementById('btn-close-msg-drawer').onclick = closeDrawer;
    backdrop.onclick = closeDrawer;

    await loadMessagesIntoThread();

    document.getElementById('btn-send-sales-reply')?.addEventListener('click', async () => {
      const input = document.getElementById('sales-reply-content');
      const content = input?.value.trim();
      if (!content) return;

      input.disabled = true;
      try {
        const res = await global.NegotiationAPI.replyMessage(quoteId, {
          content: content,
          message_type: 'COMMENT'
        });
        input.disabled = false;
        if (res.ok) {
          input.value = '';
          await loadMessagesIntoThread();
          global.DealFlowUI.toast('Message sent to customer.', 'teal');
        } else {
          global.DealFlowUI.toast(res.data?.detail || 'Failed to send message.', 'coral');
        }
      } catch (e) {
        input.disabled = false;
        global.DealFlowUI.toast('Error sending message.', 'coral');
      }
    });
  }

  async function loadMessagesIntoThread() {
    const listEl = document.getElementById('drawer-messages-list');
    if (!listEl) return;

    try {
      const res = await global.DealFlowAPI.get(`/api/v1/quotations/${quoteId}/messages`);
      const msgs = res.ok ? res.data : [];

      if (!msgs || msgs.length === 0) {
        listEl.innerHTML = `<div style="text-align: center; padding: 24px; color: var(--color-text-muted); font-size: 0.8rem;">No messages exchanged yet. Use the box below to message the customer.</div>`;
        return;
      }

      listEl.innerHTML = msgs.map(m => {
        const isCustomer = m.sender_type === 'CUSTOMER' || m.sender?.role?.name === 'CUSTOMER';
        const senderLabel = isCustomer ? (m.sender ? m.sender.full_name : 'Customer') : (m.sender ? m.sender.full_name : 'Sales Representative');
        const timeStr = new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        return `
          <div class="chat-bubble-wrapper ${isCustomer ? 'chat-customer' : 'chat-rep'}" style="margin-bottom: 12px; display: flex; flex-direction: column; align-items: ${isCustomer ? 'flex-start' : 'flex-end'};">
            <div style="font-size: 0.7rem; color: var(--color-text-muted); margin-bottom: 2px;">
              ${senderLabel} &bull; ${timeStr} ${m.message_type === 'LINE_QUESTION' ? '<span class="badge badge-navy" style="font-size: 0.6rem;">Line Question</span>' : ''}
            </div>
            <div class="chat-bubble" style="max-width: 85%; padding: 8px 12px; border-radius: 10px; background: ${isCustomer ? '#EEF2F6' : 'var(--color-navy)'}; color: ${isCustomer ? 'var(--color-navy)' : 'white'}; font-size: 0.825rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
              ${m.content}
            </div>
          </div>
        `;
      }).join('');
      listEl.scrollTop = listEl.scrollHeight;
    } catch (e) {
      console.warn(e);
    }
  }

  function formatEventType(type) {
    const map = {
      'QUOTE_CREATED': 'Quotation Created',
      'LINE_ADDED': 'Product Line Added',
      'LINE_UPDATED': 'Line Item Modified',
      'LINE_REMOVED': 'Product Line Removed',
      'QUOTE_UPDATED': 'Header Discount / Terms Updated',
      'QUOTE_RECALCULATED': 'Manual Commercial Recalculation',
      'SUBMITTED_FOR_APPROVAL': 'Submitted for Approval Routing',
      'AUTO_APPROVED': 'Automatically Approved',
      'APPROVAL_REQUESTED': 'Approval Step Triggered',
      'STEP_APPROVED': 'Approval Step Approved',
      'STEP_REJECTED': 'Approval Step Rejected',
      'STEP_RETURNED': 'Returned for Revision',
      'QUOTE_CANCELLED': 'Quotation Cancelled',
      'RECOMMENDATION_ADDED': 'Upsell Recommendation Added',
      'RECOMMENDATION_DISMISSED': 'Recommendation Dismissed',
      'SENT_TO_CUSTOMER': 'Quotation Sent to Customer',
      'CUSTOMER_ACCEPTED': 'Customer Accepted Quotation',
      'CUSTOMER_CONFIRMED': 'Customer Confirmed Deal',
      'CUSTOMER_CHANGES_REQUESTED': 'Customer Requested Changes / Counteroffer',
      'COUNTER_OFFER_SUBMITTED': 'Counteroffer Submitted',
      'COUNTER_OFFER_ACCEPTED': 'Counteroffer Accepted',
      'COUNTER_OFFER_REJECTED': 'Counteroffer Rejected',
      'MESSAGE_SENT': 'Message Sent'
    };
    return map[type] || type;
  }

  function formatStatusLabel(status) {
    const map = {
      'DRAFT': 'Draft',
      'PENDING_MANAGER_APPROVAL': 'Pending Manager Approval',
      'PENDING_FINANCE_APPROVAL': 'Pending Finance Approval',
      'APPROVED': 'Approved',
      'SENT_TO_CUSTOMER': 'Sent to Customer',
      'CUSTOMER_CHANGES_REQUESTED': 'Customer Changes Requested',
      'REAPPROVAL_REQUIRED': 'Reapproval Required',
      'CUSTOMER_ACCEPTED': 'Customer Accepted',
      'CUSTOMER_CONFIRMED': 'Customer Confirmed',
      'RETURNED_FOR_REVISION': 'Returned for Revision',
      'REJECTED': 'Rejected',
      'CANCELLED': 'Cancelled'
    };
    return map[status] || status;
  }

  function formatStatusBadge(status) {
    const map = {
      'DRAFT': { label: 'Draft', cls: 'badge-navy' },
      'PENDING_MANAGER_APPROVAL': { label: 'Pending Manager Approval', cls: 'badge-coral' },
      'PENDING_FINANCE_APPROVAL': { label: 'Pending Finance Approval', cls: 'badge-coral' },
      'APPROVED': { label: 'Approved', cls: 'badge-teal' },
      'SENT_TO_CUSTOMER': { label: 'Sent to Customer', cls: 'badge-teal' },
      'CUSTOMER_CHANGES_REQUESTED': { label: 'Changes Requested', cls: 'badge-coral' },
      'REAPPROVAL_REQUIRED': { label: 'Reapproval Required', cls: 'badge-coral' },
      'CUSTOMER_ACCEPTED': { label: 'Customer Accepted', cls: 'badge-teal' },
      'CUSTOMER_CONFIRMED': { label: 'Customer Confirmed', cls: 'badge-teal' },
      'RETURNED_FOR_REVISION': { label: 'Returned for Revision', cls: 'badge-coral' },
      'REJECTED': { label: 'Rejected', cls: 'badge-coral' },
      'CANCELLED': { label: 'Cancelled', cls: 'badge-navy' }
    };
    const s = map[status] || { label: status, cls: 'badge-navy' };
    return `<span class="badge ${s.cls}">${s.label}</span>`;
  }

  global.QuotationBuilderView = {
    render: render
  };
})(typeof window !== 'undefined' ? window : this);
