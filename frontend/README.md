# DealFlow360 — Frontend (Phase 1)

DealFlow360 is an Enterprise B2B Deal Management and Commercial Operations Platform.

This directory contains the **Phase 1 Vanilla JavaScript, HTML5, and CSS3** frontend application, designed to interface seamlessly with the FastAPI backend.

---

## 🎨 Locked Brand Identity & Design System

The visual design is built with the locked DealFlow360 enterprise color palette:

- **Deep Navy (`#172A46`)**: Sidebar, main headings, typography, dark container surfaces.
- **Teal (`#19B5A5`)**: Primary CTAs, active indicators, successful system health states, links.
- **Coral (`#F28C6B`)**: Warning indicators, errors, system disconnection alerts.
- **Off-white (`#F7F8FA`)**: Application background workspace.
- **White (`#FFFFFF`)**: Card surfaces, forms, panels.
- **Primary Text (`#172033`)**: High-contrast body copy and important values.

---

## 📁 Directory Structure

```
frontend/
├── index.html              # Authenticated workspace shell & Phase 1 dashboard
├── login.html              # Split-screen enterprise login page
├── README.md               # Frontend documentation & architecture guide
│
├── css/
│   ├── variables.css       # Design tokens & locked brand color palette
│   ├── base.css            # Base resets, typography, and utility classes
│   ├── components.css      # Buttons, cards, form inputs, badges, dropdowns, modals
│   ├── layout.css          # Login split-screen & app shell layout
│   └── responsive.css      # Tablet and mobile responsive rules
│
└── js/
    ├── config.js           # Centralized API_BASE_URL & storage configuration
    ├── api.js              # Centralized Fetch API client & health check callers
    ├── auth.js             # Token storage, auth guard, login & logout services
    ├── navigation.js       # Role-aware navigation definitions & role formatter
    ├── ui.js               # Modal dialogs, dropdowns, password toggles, and drawer controls
    └── app.js              # Dashboard initialization & live backend status integration
```

---

## 🚀 Running the Frontend Locally

1. **Ensure the backend is running:**
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

2. **Serve the frontend files:**
   You can serve the `frontend/` directory with any static server:
   ```bash
   # Option A: Python HTTP server
   cd frontend
   python -m http.server 3000

   # Option B: Node http-server / serve
   npx serve frontend
   ```
   Or open `frontend/login.html` directly in any modern browser.

3. **Configuring Backend URL:**
   If running FastAPI on a non-default host or port, configure `API_BASE_URL` in `frontend/js/config.js`:
   ```javascript
   const Config = {
     API_BASE_URL: 'http://127.0.0.1:8000',
     ...
   };
   ```

---

## 🔐 Phase 1 Authentication Flow

1. User visits `login.html`.
2. Form submits credentials to `POST /api/v1/auth/login`.
3. Backend returns signed JWT `access_token`.
4. Frontend stores `access_token` centrally via `DealFlowAuth.setAccessToken()`.
5. Frontend requests safe user profile via `GET /api/v1/auth/me` with `Authorization: Bearer <token>`.
6. User is redirected to `index.html` dashboard with role-aware navigation loaded.
7. Unauthenticated visits to `index.html` are intercepted by `DealFlowAuth.requireAuth()` and redirected to `login.html`.
8. Logging out clears the stored token and cached user profile.
