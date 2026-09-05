/**
 * DealFlow360 — Settings & Commercial Configuration Hub
 */
(function (global) {
  'use strict';

  const SettingsView = {
    async render(container, onSwitchView) {
      const currentUser = global.DealFlowAuth.getCurrentUser();
      const roleName = currentUser?.role?.name || 'ADMIN';

      container.innerHTML = `
        <div class="view-header animate-fade-in">
          <div style="margin-bottom:var(--space-xl);">
            <h2>Settings & Commercial Configuration Hub</h2>
            <p>Centralized administration of master data classifications, discount rules, approval thresholds, and billing plans.</p>
          </div>

          <!-- Section 1: Master Data Configuration -->
          <div style="margin-bottom:var(--space-lg);">
            <h3 style="margin-bottom:var(--space-xs);">Master Data Classifications</h3>
            <p style="font-size:var(--font-size-xs);">Configure baseline hierarchies and physical facilities.</p>
          </div>

          <div class="capabilities-grid" style="margin-bottom:var(--space-2xl);">
            <!-- Customer Tiers Tile -->
            <div class="capability-card" style="cursor:pointer;" id="tile-customer-tiers">
              <div class="capability-header">
                <div class="capability-icon-wrap" style="background:var(--color-navy-muted);color:var(--color-navy);">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                </div>
                <span class="badge badge-teal">Active</span>
              </div>
              <h4 class="capability-title">Customer Tiers</h4>
              <p class="capability-desc">Define enterprise customer classifications (Gold, Silver, Bronze) for commercial policy scoping.</p>
              <div style="margin-top:var(--space-sm);">
                <button class="btn btn-secondary btn-sm">Configure Tiers &rarr;</button>
              </div>
            </div>

            <!-- Product Categories Tile -->
            <div class="capability-card" style="cursor:pointer;" id="tile-product-categories">
              <div class="capability-header">
                <div class="capability-icon-wrap" style="background:var(--color-navy-muted);color:var(--color-navy);">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 9h16M4 15h16M10 3L8 21M16 3l-2 18"/></svg>
                </div>
                <span class="badge badge-teal">Active</span>
              </div>
              <h4 class="capability-title">Product Categories</h4>
              <p class="capability-desc">Organize commercial catalog items into category groupings for portfolio management and discount rules.</p>
              <div style="margin-top:var(--space-sm);">
                <button class="btn btn-secondary btn-sm">Configure Categories &rarr;</button>
              </div>
            </div>

            <!-- Warehouses Tile -->
            <div class="capability-card" style="cursor:pointer;" id="tile-warehouses">
              <div class="capability-header">
                <div class="capability-icon-wrap" style="background:var(--color-navy-muted);color:var(--color-navy);">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
                </div>
                <span class="badge badge-teal">Active</span>
              </div>
              <h4 class="capability-title">Warehouses</h4>
              <p class="capability-desc">Manage physical storage facilities, regional hubs, and location addresses.</p>
              <div style="margin-top:var(--space-sm);">
                <button class="btn btn-secondary btn-sm">Configure Warehouses &rarr;</button>
              </div>
            </div>
          </div>

          <!-- Section 2: Commercial Policy Configuration -->
          <div style="margin-bottom:var(--space-lg);">
            <h3 style="margin-bottom:var(--space-xs);">Commercial Rules & Terms</h3>
            <p style="font-size:var(--font-size-xs);">Configure pricing boundaries, escalation triggers, and contract terms.</p>
          </div>

          <div class="capabilities-grid">
            <!-- Discount Policies Tile -->
            <div class="capability-card" style="cursor:pointer;" id="tile-discount-policies">
              <div class="capability-header">
                <div class="capability-icon-wrap" style="background:var(--color-teal-light);color:var(--color-teal);">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="9" y1="15" x2="15" y2="9"/><circle cx="9.5" cy="9.5" r=".5" fill="currentColor"/><circle cx="14.5" cy="14.5" r=".5" fill="currentColor"/></svg>
                </div>
                <span class="badge badge-teal">Live Rules</span>
              </div>
              <h4 class="capability-title">Discount Policies</h4>
              <p class="capability-desc">Set standard reference discounts and maximum commercial caps by tier, category, or product SKU with 6-tier precedence.</p>
              <div style="margin-top:var(--space-sm);">
                <button class="btn btn-secondary btn-sm">Configure Discount Policies &rarr;</button>
              </div>
            </div>

            <!-- Approval Policies Tile -->
            <div class="capability-card" style="cursor:pointer;" id="tile-approval-policies">
              <div class="capability-header">
                <div class="capability-icon-wrap" style="background:var(--color-teal-light);color:var(--color-teal);">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                </div>
                <span class="badge badge-teal">Live Rules</span>
              </div>
              <h4 class="capability-title">Approval Policies</h4>
              <p class="capability-desc">Configure discount thresholds, margin floors, and payment term triggers mapped to Sales Manager or Finance Operations.</p>
              <div style="margin-top:var(--space-sm);">
                <button class="btn btn-secondary btn-sm">Configure Approval Policies &rarr;</button>
              </div>
            </div>

            <!-- Billing Plans Tile -->
            <div class="capability-card" style="cursor:pointer;" id="tile-billing-plans">
              <div class="capability-header">
                <div class="capability-icon-wrap" style="background:var(--color-teal-light);color:var(--color-teal);">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>
                </div>
                <span class="badge badge-teal">Live Terms</span>
              </div>
              <h4 class="capability-title">Billing Plans</h4>
              <p class="capability-desc">Define standard commercial contract schedules (One-time, Monthly, Quarterly, Annual) and default payment due terms.</p>
              <div style="margin-top:var(--space-sm);">
                <button class="btn btn-secondary btn-sm">Configure Billing Plans &rarr;</button>
              </div>
            </div>
          </div>
        </div>
      `;

      // Event listeners for tiles
      document.getElementById('tile-customer-tiers')?.addEventListener('click', () => {
        if (typeof onSwitchView === 'function') onSwitchView('customers', 'tiers');
      });

      document.getElementById('tile-product-categories')?.addEventListener('click', () => {
        if (typeof onSwitchView === 'function') onSwitchView('products', 'categories');
      });

      document.getElementById('tile-warehouses')?.addEventListener('click', () => {
        if (typeof onSwitchView === 'function') onSwitchView('inventory', 'warehouses');
      });

      document.getElementById('tile-discount-policies')?.addEventListener('click', () => {
        if (typeof onSwitchView === 'function') onSwitchView('discount-policies');
      });

      document.getElementById('tile-approval-policies')?.addEventListener('click', () => {
        if (typeof onSwitchView === 'function') onSwitchView('approval-policies');
      });

      document.getElementById('tile-billing-plans')?.addEventListener('click', () => {
        if (typeof onSwitchView === 'function') onSwitchView('billing-plans');
      });
    }
  };

  global.SettingsView = SettingsView;
})(typeof window !== 'undefined' ? window : this);
