/**
 * DealFlow360 — UI Utilities & Interactivity
 * Handles dropdowns, modals, toasts, password toggles, and responsive drawer interactions.
 */
(function (global) {
  'use strict';

  const UI = {
    /**
     * Compute 2-letter initials from user full name.
     * @param {string} name
     * @returns {string}
     */
    getInitials(name) {
      if (!name || typeof name !== 'string') return 'DF';
      const parts = name.trim().split(/\s+/);
      if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    },

    /**
     * Bind password show/hide button to target input.
     * @param {HTMLButtonElement} toggleBtn
     * @param {HTMLInputElement} passwordInput
     */
    initPasswordToggle(toggleBtn, passwordInput) {
      if (!toggleBtn || !passwordInput) return;

      toggleBtn.addEventListener('click', (e) => {
        e.preventDefault();
        const isPassword = passwordInput.type === 'password';
        passwordInput.type = isPassword ? 'text' : 'password';
        toggleBtn.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
        
        // Update SVG icon
        toggleBtn.innerHTML = isPassword ? `
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
            <line x1="1" y1="1" x2="23" y2="23"/>
          </svg>
        ` : `
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
        `;
      });
    },

    /**
     * Setup user dropdown menu toggling and click outside handling.
     * @param {HTMLElement} triggerEl
     * @param {HTMLElement} menuEl
     */
    initUserDropdown(triggerEl, menuEl) {
      if (!triggerEl || !menuEl) return;

      function closeDropdown() {
        menuEl.classList.remove('show');
        triggerEl.setAttribute('aria-expanded', 'false');
      }

      function toggleDropdown(e) {
        e.stopPropagation();
        const isShown = menuEl.classList.contains('show');
        if (isShown) {
          closeDropdown();
        } else {
          menuEl.classList.add('show');
          triggerEl.setAttribute('aria-expanded', 'true');
        }
      }

      triggerEl.addEventListener('click', toggleDropdown);

      document.addEventListener('click', (e) => {
        if (!triggerEl.contains(e.target) && !menuEl.contains(e.target)) {
          closeDropdown();
        }
      });

      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && menuEl.classList.contains('show')) {
          closeDropdown();
          triggerEl.focus();
        }
      });
    },

    /**
     * Setup mobile sidebar toggle drawer.
     * @param {HTMLElement} toggleBtn
     * @param {HTMLElement} sidebarEl
     * @param {HTMLElement} backdropEl
     */
    initMobileSidebar(toggleBtn, sidebarEl, backdropEl) {
      if (!toggleBtn || !sidebarEl) return;

      function openSidebar() {
        sidebarEl.classList.add('open');
        if (backdropEl) backdropEl.classList.add('show');
      }

      function closeSidebar() {
        sidebarEl.classList.remove('open');
        if (backdropEl) backdropEl.classList.remove('show');
      }

      toggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (sidebarEl.classList.contains('open')) {
          closeSidebar();
        } else {
          openSidebar();
        }
      });

      if (backdropEl) {
        backdropEl.addEventListener('click', closeSidebar);
      }
    },

    /**
     * Show Coming Soon modal dialog.
     * @param {string} title
     * @param {string} description
     */
    showComingSoonModal(title, description) {
      let modalOverlay = document.getElementById('dealflow-modal-overlay');
      if (!modalOverlay) {
        modalOverlay = document.createElement('div');
        modalOverlay.id = 'dealflow-modal-overlay';
        modalOverlay.className = 'modal-overlay';
        document.body.appendChild(modalOverlay);
      }

      modalOverlay.innerHTML = `
        <div class="modal-card" role="dialog" aria-modal="true" aria-labelledby="modal-title">
          <div class="card-header">
            <div style="display:flex;align-items:center;gap:8px;">
              <span class="badge badge-teal">Phase Roadmap</span>
              <h3 id="modal-title" class="card-title">${title}</h3>
            </div>
            <button class="btn btn-ghost btn-sm" id="modal-close-btn" aria-label="Close modal">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
          <div class="card-body">
            <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: var(--space-md);">
              ${description || 'This module is scheduled for future release in upcoming DealFlow360 development phases.'}
            </p>
            <div class="alert alert-navy" style="margin-bottom:0;">
              <svg class="alert-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
              <span>Phase 1 establishes authentication, visual identity, and RBAC-aware workspace architecture.</span>
            </div>
          </div>
          <div class="card-footer" style="display:flex;justify-content:flex-end;">
            <button class="btn btn-primary btn-sm" id="modal-confirm-btn">Understood</button>
          </div>
        </div>
      `;

      modalOverlay.classList.add('show');

      const closeHandler = () => {
        modalOverlay.classList.remove('show');
      };

      document.getElementById('modal-close-btn')?.addEventListener('click', closeHandler);
      document.getElementById('modal-confirm-btn')?.addEventListener('click', closeHandler);
      
      modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) closeHandler();
      });
    },

    /**
     * Show Account Profile modal.
     * @param {object} user
     */
    showProfileModal(user) {
      if (!user) return;
      let modalOverlay = document.getElementById('dealflow-modal-overlay');
      if (!modalOverlay) {
        modalOverlay = document.createElement('div');
        modalOverlay.id = 'dealflow-modal-overlay';
        modalOverlay.className = 'modal-overlay';
        document.body.appendChild(modalOverlay);
      }

      const roleName = user.role ? user.role.name : 'ADMIN';
      const formattedRole = global.DealFlowNav ? global.DealFlowNav.formatRole(roleName) : roleName;

      modalOverlay.innerHTML = `
        <div class="modal-card" role="dialog" aria-modal="true" aria-labelledby="profile-modal-title">
          <div class="card-header">
            <h3 id="profile-modal-title" class="card-title">User Account Profile</h3>
            <button class="btn btn-ghost btn-sm" id="profile-modal-close-btn" aria-label="Close modal">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
          <div class="card-body">
            <div style="display:flex;align-items:center;gap:16px;margin-bottom:20px;">
              <div class="user-avatar" style="width:52px;height:52px;font-size:18px;">
                ${this.getInitials(user.full_name)}
              </div>
              <div>
                <h4 style="color:var(--color-navy);margin-bottom:2px;">${user.full_name || 'Authenticated User'}</h4>
                <p style="font-size:var(--font-size-xs);">${user.email}</p>
              </div>
            </div>

            <div class="key-value-list">
              <div class="key-value-item">
                <span class="key-label">User ID</span>
                <span class="key-value">#${user.id}</span>
              </div>
              <div class="key-value-item">
                <span class="key-label">Assigned Role</span>
                <span class="key-value"><span class="badge badge-navy">${formattedRole}</span></span>
              </div>
              <div class="key-value-item">
                <span class="key-label">Account Status</span>
                <span class="key-value"><span class="badge badge-teal"><span class="status-dot status-dot-teal"></span>${user.is_active ? 'Active' : 'Inactive'}</span></span>
              </div>
              <div class="key-value-item">
                <span class="key-label">Authentication Method</span>
                <span class="key-value">JWT Bearer Token (HS256)</span>
              </div>
              <div class="key-value-item">
                <span class="key-label">Created At</span>
                <span class="key-value">${user.created_at ? new Date(user.created_at).toLocaleString() : 'N/A'}</span>
              </div>
            </div>
          </div>
          <div class="card-footer" style="display:flex;justify-content:flex-end;">
            <button class="btn btn-secondary btn-sm" id="profile-modal-dismiss-btn">Close</button>
          </div>
        </div>
      `;

      modalOverlay.classList.add('show');

      const closeHandler = () => {
        modalOverlay.classList.remove('show');
      };

      document.getElementById('profile-modal-close-btn')?.addEventListener('click', closeHandler);
      document.getElementById('profile-modal-dismiss-btn')?.addEventListener('click', closeHandler);

      modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) closeHandler();
      });
    }
  };

  global.DealFlowUI = UI;
})(typeof window !== 'undefined' ? window : this);
