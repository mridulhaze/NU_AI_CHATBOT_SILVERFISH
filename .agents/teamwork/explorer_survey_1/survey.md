# Administrative & Solver Support Center UI Survey & Layout Mapping

**File**: `D:\projects\AI_CHAT_BOT\.agents\teamwork\explorer_survey_1\survey.md`  
**Author**: teamwork_preview_explorer (Explorer 1)  
**Date**: 2026-10-21  
**Target Codebase**: `static/index.html`, `static/`, `backend/`, `token_service/`  
**Integrity Mode**: Development / Read-Only Investigation  

---

## 1. Executive Summary

This survey provides an exhaustive structural, architectural, visual, and event-handling mapping of the **Administrative & Solver Support Center** in `static/index.html`. The goal of the upcoming refactor is to transform the existing cluttered, colorful, nested-modal support center into a clean, calm, Apple/Linear-inspired monochromatic interface featuring:
1. A **high-density data table** with subtle status badges, crisp typography, and generous whitespace.
2. A **slide-over inspection drawer** (sliding in smoothly from the right) that opens upon clicking any token row, displaying student details, service context, internal notes, and desk action controls.
3. Strict enforcement of **Solver Role Access Controls** (only Token Support Center tab, assigned desk tickets only, exactly 2 actions: `Solve` or `Send Back to Admin (Not Solved)`).
4. Full preservation of **Super Admin Controls** (department reassignments, trash management, soft delete & restore, system backup).
5. Application of Apple/Linear monochromatic design tokens (`--bg: #F5F5F7`, `--surface: #FFFFFF`, `--text: #1D1D1F`, `--text-secondary: #6E6E73`, `--hairline: rgba(0,0,0,0.08)`).

All existing DOM IDs, JavaScript functions, event listeners, and API endpoints have been mapped and analyzed, including an API route mismatch on `return-to-admin` that must be addressed during implementation.

---

## 2. Current Architecture & Layout Analysis

### 2.1 The Modal Container (`#admin-modal`)
- **Location**: `static/index.html` lines 1528–2970.
- **Structure**:
  - Backdrop: `fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 hidden flex items-center justify-center p-3 sm:p-6`
  - Container box: `bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-5xl h-[90vh] flex flex-col overflow-hidden`
- **Header Elements** (lines 1531–1565):
  - Brand badge: `NU` logo (currently `bg-emerald-800 text-white`)
  - Title: `Administrative & Solver Support Center`
  - User display: `#admin-user-display`
  - Role badge: `#admin-role-badge` (`SUPER_ADMIN`, `ADMIN`, `SOLVER`)
  - Department display: `#admin-dept-display`
  - Header actions:
    - `openDocumentaryModal()`: System & Operations Manual button (`bg-indigo-50 text-indigo-800`)
    - `toggleEmbedModal()`: Embed Widget button (`bg-slate-100 text-slate-700`)
    - `handleAdminLogout()`: Logout button (`bg-rose-50 text-rose-700`)
    - `toggleAdminModal()`: Close 'X' button
- **Tab Navigation Bar** (lines 1567–1622):
  - Interactive Bangla Hint Strip: `#global-tab-bangla-tip` with `#global-tab-bangla-text`
  - 8 Main Tabs:
    1. `#tab-btn-tokens`: Token Support Center (`#token-count-badge`)
    2. `#tab-btn-sitemap`: Website Structure Map
    3. `#tab-btn-ai-engine`: Autonomous AI Hub (6-in-1)
    4. `#tab-btn-qa-knowledge`: Q&A Knowledge Hub
    5. `#tab-btn-academic-static`: Academic Exam & Results Hub
    6. `#tab-btn-users`: User & Department Accounts
    7. `#tab-btn-logs`: Activity & Service Logs (`#log-count-badge`)
    8. `#tab-btn-backups`: System Backup & Restore

### 2.2 Token Support Center Tab Content (`#tab-content-tokens`)
- **Location**: lines 1628–1682.
- **Filters Toolbar** (lines 1630–1659):
  - `#admin-token-search`: Text input for searching token ID, student name, problem, reg no.
  - `#admin-token-status-filter`: Dropdown with `ALL`, `PENDING`, `ASSIGNED`, `PROCESSING`, `SOLVED`, `CLOSED`, `REJECTED`, `TRASH` (`#opt-trash-filter`).
  - `#admin-token-service-filter`: Dropdown populated dynamically via `loadServiceTypes()`.
  - Filter button: `onclick="loadAdminTokens()"`
  - Refresh button: `onclick="loadAdminTokens()"`
  - + New Token button: `onclick="openTokenModal()"`
- **Table Container** (lines 1661–1681):
  - Table header (`thead`): Token ID, Service, Problem Summary, Status, Solver, Created Date, Action
  - Table body: `<tbody id="admin-tokens-tbody">`
- **Current Row Rendering (`loadAdminTokens()` lines 5160–5200)**:
  - Table rows render with thick borders and noisy saturated status badges:
    - `PENDING`: `bg-amber-100 text-amber-800`
    - `ASSIGNED`: `bg-purple-100 text-purple-800`
    - `PROCESSING`: `bg-blue-100 text-blue-800`
    - `SOLVED`: `bg-emerald-100 text-emerald-800`
    - `CLOSED`: `bg-slate-100 text-slate-800`
    - `REJECTED`: `bg-rose-100 text-rose-800`
  - Action column:
    - If `t.is_deleted`: Restore button (`restoreAdminToken('${t.token_id}')`)
    - Else: Manage button (`openAdminManageToken('${t.token_id}')`) + Trash button for Super Admin (`deleteAdminToken('${t.token_id}')`)

### 2.3 Existing Manage Token View (`#admin-manage-token-modal`)
- **Location**: lines 2972–3141.
- **Current UX Problem**: It is implemented as a **nested, centered popup modal** (`z-[60] fixed inset-0 flex items-center justify-center`) that completely obscures the support center table underneath. When handling multiple tokens, opening and closing this window creates visual fatigue and breaks workflow continuity.
- **Inner Structure**:
  - Header: Dark slate bar (`bg-slate-900`) with `#adm-token-id` in amber.
  - **Card 1: Student & Problem Context** (lines 2989–3026):
    - Subgrid: `#adm-user-name`, `#adm-user-phone`, `#adm-reg-no`, `#adm-service`, `#adm-date`, `#adm-status-badge`.
    - Problem description: `#adm-problem`.
  - **Card 2: Action & Solver Controls** (lines 3028–3128):
    - Admin Controls (`#adm-admin-controls-panel`):
      - Desk assignment select: `#adm-solver-select` with `onchange="submitAssignToken()"`
      - Status select: `#adm-status-select` with `submitStatusUpdate()`
    - Solver Assignment Banner (`#solver-assignment-notice`):
      - Displays `#solver-desk-name-display` with lock indicator (`🔒 Re-assignment is managed only by Administrator`).
    - Action 1: Record Official Resolution / Mark Solved:
      - 4 quick templates: `setAdminSolveTemplate(...)`
      - Textarea: `#adm-solve-message`
      - Button: `submitSolveToken()`
    - Action 2: Solver Return to Admin (Not Solved):
      - Input: `#solver-return-reason-input`
      - Button: `submitReturnToAdmin()`
  - **Card 3: Internal Admin Notes (Private)** (lines 3130–3138):
    - Input: `#adm-note-input`
    - Button: `saveAdminNoteOnly()`
  - Close button: `closeAdminManageTokenModal()`

---

## 3. Role-Based Access Control Audit

### 3.1 Super Admin (`SUPER_ADMIN`)
- **Tab Access**: Full access to all 8 tabs (`tokens`, `sitemap`, `ai_engine`, `qa_knowledge`, `academic_static`, `users`, `logs`, `backups`).
- **Token Filtering**: Access to all department tokens and all statuses.
- **Trash Management**:
  - Can view soft-deleted tokens via `#opt-trash-filter` (`value="TRASH"`).
  - Can soft-delete any token via `deleteAdminToken(tokenId)` (calls `POST /api/token/admin/{token_id}/delete`).
  - Can restore soft-deleted tokens via `restoreAdminToken(tokenId)` (calls `POST /api/token/admin/{token_id}/restore`).
- **Assignment & Actions**: Full rights to reassign solvers (`#adm-solver-select`), manually update status (`#adm-status-select`), mark solved, and write private notes.

### 3.2 Department Solver (`SOLVER`)
- **Tab Access**:
  - **Strictly restricted to Token Support Center tab only**.
  - In `openAdminDashboardUI()`, all other tab buttons must be hidden (`display: none`).
  - In `switchAdminTab(tab)`, if `isSolver && tab !== "tokens"`, tab is forcibly redirected to `"tokens"`.
- **Token Filtering**:
  - Query parameters automatically appended in `loadAdminTokens()`:
    `department=${user.department}&solver_name=${user.full_name}&role=SOLVER`.
  - Backend enforces department desk isolation so solvers only see their assigned tickets.
- **Desk Actions (Strictly Two Actions)**:
  1. **Action 1: Solve**:
     - Submits official resolution message (`#adm-solve-message`).
     - Calls `submitSolveToken()`.
     - Marks token as `SOLVED` and auto-indexes solution into secondary AI knowledge.
  2. **Action 2: Send Back to Admin (Not Solved)**:
     - Submits reason/guidance request (`#solver-return-reason-input`).
     - Calls `submitReturnToAdmin()`.
     - Transitions token status back to `PENDING` with reason logged in history and admin note.
  - **Prohibited Action**:
    - Reassignment controls are hidden (`#adm-admin-controls-panel` hidden, `#solver-assignment-notice` displayed).
    - Solvers CANNOT reassign tokens to another desk.

---

## 4. API Endpoints & Critical Bug Discovery

### 4.1 Registered FastAPI Routes
A complete inspection of FastAPI route registrations reveals:

| Endpoint Path | Method | File | Purpose |
|---|---|---|---|
| `/api/token/services` | GET | `token_service/routes.py` | List active service types |
| `/api/token/admin/tokens` | GET | `token_service/routes.py` | Search & list tokens with filters |
| `/api/token/admin/solvers` | GET | `token_service/routes.py` | List solvers/departments |
| `/api/token/admin/{token_id}` | GET | `token_service/routes.py` | Full admin token detail |
| `/api/token/admin/{token_id}/assign` | POST | `token_service/routes.py` | Assign solver desk |
| `/api/token/admin/{token_id}/status` | POST | `token_service/routes.py` | Update status & admin notes |
| `/api/token/admin/{token_id}/solve` | POST | `token_service/routes.py` | Mark token solved with message |
| `/api/token/admin/{token_id}/delete` | POST | `token_service/routes.py` | Super admin soft-delete (Trash) |
| `/api/token/admin/{token_id}/restore` | POST | `token_service/routes.py` | Super admin restore token |
| `/api/v1/admin/tokens/{token_id}/return-to-admin` | POST | `backend/api/admin_routes.py` | Solver return to admin |

### 4.2 ⚠️ Critical Bug Discovered in Existing `submitReturnToAdmin()`
- **Current Code in `static/index.html` (line 5281)**:
  ```javascript
  const res = await fetch(`${API_BASE}/api/token/admin/${currentAdminSelectedTokenId}/return-to-admin`, {
    method: "POST", ...
  });
  ```
- **Backend Observation**:
  - `/api/token/admin/{token_id}/return-to-admin` does NOT exist in `token_service/routes.py`!
  - The actual implemented route in FastAPI is:
    `POST /api/v1/admin/tokens/{token_id}/return-to-admin` (in `backend/api/admin_routes.py` line 163).
- **Impact**: Any solver attempting to return a token to admin currently triggers a 404 Not Found error.
- **Solution during UI Refactor**:
  In `submitReturnToAdmin()`, target the valid endpoint:
  ```javascript
  const res = await fetch(`${API_BASE}/api/v1/admin/tokens/${currentAdminSelectedTokenId}/return-to-admin`, ...);
  ```
  *(Or optionally alias the route in backend if needed; the frontend endpoint fix is direct and clean).*

---

## 5. Apple / Linear Monochromatic Design System

### 5.1 Design Tokens Specification
To replace the noisy multi-colored UI, the following CSS design variables must be introduced:

```css
:root {
  --bg: #F5F5F7;               /* Apple neutral canvas */
  --surface: #FFFFFF;          /* Pure white card & drawer background */
  --surface-subtle: #FAFAFA;   /* Subtle header/panel background */
  --text: #1D1D1F;             /* Crisp near-black primary text */
  --text-secondary: #6E6E73;   /* Apple muted secondary text */
  --text-tertiary: #86868B;    /* Micro metadata & timestamp text */
  --hairline: rgba(0, 0, 0, 0.08); /* 1px crisp divider */
  --hairline-subtle: rgba(0, 0, 0, 0.04);
  --accent: #1D1D1F;           /* Restrained monochromatic primary */
  --accent-hover: #000000;
  --focus-ring: rgba(0, 113, 227, 0.4); /* Subtle Apple blue focus ring */
}
```

### 5.2 Status Badge Treatment (Subtle Muted Tints with Micro-Pips)
Instead of high-saturation solid pills (`bg-purple-100 text-purple-800`), use soft neutral backgrounds with a 6px status dot (Linear style):

| Status | Badge Background | Text Color | Dot Color | Icon / Visual |
|---|---|---|---|---|
| `PENDING` | `bg-amber-500/10` | `text-amber-900` | `bg-amber-500` | 6px amber dot |
| `ASSIGNED` | `bg-indigo-500/10` | `text-indigo-900` | `bg-indigo-500` | 6px indigo dot |
| `PROCESSING` | `bg-blue-500/10` | `text-blue-900` | `bg-blue-500` | 6px blue dot |
| `SOLVED` | `bg-emerald-500/10` | `text-emerald-900` | `bg-emerald-600` | 6px emerald dot |
| `CLOSED` | `bg-slate-500/10` | `text-slate-800` | `bg-slate-400` | 6px slate dot |
| `REJECTED` | `bg-rose-500/10` | `text-rose-900` | `bg-rose-500` | 6px rose dot |
| `TRASH` | `bg-rose-500/10` | `text-rose-900` | `bg-rose-600` | 🗑️ trash icon |

---

## 6. Slide-Over Inspection Drawer Architecture

### 6.1 DOM Structure Proposal
Replace the existing centered `#admin-manage-token-modal` with a slide-over drawer:

```html
<!-- Admin & Solver Manage Token Slide-Over Drawer -->
<div id="admin-manage-token-modal" class="fixed inset-0 z-[60] hidden overflow-hidden">
  <!-- Translucent Backdrop -->
  <div id="admin-drawer-backdrop" onclick="closeAdminManageTokenModal()" class="fixed inset-0 bg-black/20 backdrop-blur-[2px] transition-opacity duration-300"></div>

  <!-- Slide-Over Inspection Pane (from Right) -->
  <div id="admin-drawer-panel" class="fixed top-0 right-0 h-full w-full max-w-md sm:max-w-xl bg-white shadow-2xl border-l border-[rgba(0,0,0,0.08)] flex flex-col transform translate-x-full transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] overflow-hidden">
    
    <!-- Drawer Header -->
    <div class="px-6 py-4 border-b border-[rgba(0,0,0,0.08)] flex items-center justify-between bg-[#FAFAFA] shrink-0">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-[#1D1D1F] text-white flex items-center justify-center font-bold text-xs tracking-wider">NU</div>
        <div>
          <div class="flex items-center gap-2">
            <h3 class="text-sm font-semibold text-[#1D1D1F]">Token <span id="adm-token-id" class="font-mono">NU-2026-000000</span></h3>
            <span id="adm-status-badge" class="px-2 py-0.5 rounded text-[10px] font-medium">PENDING</span>
          </div>
          <p class="text-[11px] text-[#6E6E73]" id="adm-service">Service Category</p>
        </div>
      </div>
      <button onclick="closeAdminManageTokenModal()" class="text-[#6E6E73] hover:text-[#1D1D1F] p-1.5 rounded-lg hover:bg-[rgba(0,0,0,0.05)] transition cursor-pointer">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
      </button>
    </div>

    <!-- Scrollable Drawer Body -->
    <div class="flex-1 overflow-y-auto p-6 space-y-6 text-xs text-[#1D1D1F] bg-[#FFFFFF]">
      
      <!-- Student & Problem Context -->
      <section class="space-y-3">
        <h4 class="text-[11px] font-bold uppercase tracking-wider text-[#6E6E73]">Student & Service Context</h4>
        <div class="grid grid-cols-2 gap-3 p-3.5 rounded-xl bg-[#F5F5F7] border border-[rgba(0,0,0,0.06)] text-[11px]">
          <div>
            <span class="text-[#6E6E73] block text-[10px]">Student Name:</span>
            <strong id="adm-user-name" class="text-[#1D1D1F] font-semibold">N/A</strong>
          </div>
          <div>
            <span class="text-[#6E6E73] block text-[10px]">Phone Number:</span>
            <strong id="adm-user-phone" class="text-[#1D1D1F] font-semibold">N/A</strong>
          </div>
          <div>
            <span class="text-[#6E6E73] block text-[10px]">Registration No:</span>
            <strong id="adm-reg-no" class="text-[#1D1D1F] font-semibold">N/A</strong>
          </div>
          <div>
            <span class="text-[#6E6E73] block text-[10px]">Submitted Date:</span>
            <span id="adm-date" class="text-[#6E6E73]">--</span>
          </div>
        </div>

        <div>
          <span class="text-[#6E6E73] text-[10px] font-bold uppercase tracking-wider block mb-1">Problem Description:</span>
          <div id="adm-problem" class="p-3.5 rounded-xl bg-[#FAFAFA] border border-[rgba(0,0,0,0.06)] text-[#1D1D1F] leading-relaxed"></div>
        </div>
      </section>

      <!-- Action & Solver Controls -->
      <section class="space-y-4 pt-4 border-t border-[rgba(0,0,0,0.08)]">
        
        <!-- Admin Controls Panel (Admin Only) -->
        <div id="adm-admin-controls-panel" class="space-y-3">
          <h4 class="text-[11px] font-bold uppercase tracking-wider text-[#6E6E73]">Administrative Desk Routing</h4>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="block text-[11px] font-medium text-[#6E6E73] mb-1">Assign Solver / Department</label>
              <select id="adm-solver-select" onchange="submitAssignToken()" class="w-full bg-[#FAFAFA] border border-[rgba(0,0,0,0.1)] rounded-lg p-2 text-xs text-[#1D1D1F] focus:outline-none focus:border-[#1D1D1F]">
                <option value="">-- Select Solver / Department --</option>
              </select>
            </div>
            <div>
              <label class="block text-[11px] font-medium text-[#6E6E73] mb-1">Update Status</label>
              <div class="flex gap-1.5">
                <select id="adm-status-select" class="flex-1 bg-[#FAFAFA] border border-[rgba(0,0,0,0.1)] rounded-lg p-2 text-xs text-[#1D1D1F] focus:outline-none focus:border-[#1D1D1F]">
                  <option value="PROCESSING">Processing</option>
                  <option value="SOLVED">Solved</option>
                  <option value="CLOSED">Closed</option>
                  <option value="REJECTED">Rejected</option>
                  <option value="PENDING">Pending</option>
                  <option value="ASSIGNED">Assigned</option>
                </select>
                <button onclick="submitStatusUpdate()" class="bg-[#1D1D1F] hover:bg-black text-white text-xs font-medium px-3 py-2 rounded-lg transition">Update</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Solver Assignment Banner (Solver Only) -->
        <div id="solver-assignment-notice" class="hidden p-3 rounded-xl bg-[#F5F5F7] border border-[rgba(0,0,0,0.06)] flex items-center justify-between">
          <div>
            <span class="text-[10px] text-[#6E6E73] block uppercase font-bold">Assigned Department Desk:</span>
            <strong id="solver-desk-name-display" class="text-xs text-[#1D1D1F] font-semibold">Department Desk</strong>
          </div>
          <span class="text-[10px] text-[#6E6E73] bg-white border border-[rgba(0,0,0,0.08)] px-2 py-0.5 rounded font-medium">
            🔒 Re-assignment managed by Admin
          </span>
        </div>

        <!-- Action 1: Solve -->
        <div class="space-y-2.5 pt-3">
          <label class="text-[11px] font-bold uppercase tracking-wider text-[#1D1D1F] flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span>Record Official Resolution (Mark Solved)</span>
          </label>
          
          <!-- Quick resolution chips -->
          <div class="flex flex-wrap gap-1.5">
            <button type="button" onclick="setAdminSolveTemplate('সোনালী সেবার পেমেন্ট ট্রানজেকশন যাচাই করে ডাটাবেজে পেমেন্ট সিনক্রোনাইজেশন সম্পন্ন করা হয়েছে এবং স্ট্যাটাস Paid করা হয়েছে।')" class="text-[10px] bg-[#F5F5F7] hover:bg-slate-200 text-[#1D1D1F] border border-[rgba(0,0,0,0.08)] px-2 py-1 rounded transition">💳 পেমেন্ট সিনক্রোনাইজেশন</button>
            <button type="button" onclick="setAdminSolveTemplate('ইএমএস (EMS) পোর্টালে শিক্ষার্থীর তথ্য ও পাসওয়ার্ড রিসেট করে সক্রিয় করা হয়েছে। নতুন পাসওয়ার্ড দিয়ে লগইন করুন।')" class="text-[10px] bg-[#F5F5F7] hover:bg-slate-200 text-[#1D1D1F] border border-[rgba(0,0,0,0.08)] px-2 py-1 rounded transition">💻 ইএমএস রিসেট</button>
            <button type="button" onclick="setAdminSolveTemplate('মূল সনদপত্র যাচাই ও প্রিন্ট সম্পন্ন হয়েছে। জাতীয় বিশ্ববিদ্যালয়ের সনদপত্র শাখা হতে মূল কপি সংগ্রহ করার জন্য অনুরোধ করা হলো।')" class="text-[10px] bg-[#F5F5F7] hover:bg-slate-200 text-[#1D1D1F] border border-[rgba(0,0,0,0.08)] px-2 py-1 rounded transition">📜 সনদ প্রস্তুত</button>
            <button type="button" onclick="setAdminSolveTemplate('উত্তরপত্র পুনঃনিরীক্ষণ বোর্ড কর্তৃক নিরীক্ষা সম্পন্ন হয়েছে এবং ফলাফল ডাটাবেজে হালনাগাদ করা হয়েছে।')" class="text-[10px] bg-[#F5F5F7] hover:bg-slate-200 text-[#1D1D1F] border border-[rgba(0,0,0,0.08)] px-2 py-1 rounded transition">🔍 পুনর্নিরীক্ষণ সম্পন্ন</button>
          </div>

          <textarea id="adm-solve-message" rows="3" placeholder="Write official student resolution..." class="w-full bg-[#FAFAFA] border border-[rgba(0,0,0,0.1)] rounded-lg p-3 text-xs text-[#1D1D1F] focus:outline-none focus:border-[#1D1D1F] resize-none"></textarea>

          <div class="flex items-center justify-between">
            <span class="text-[10px] text-[#6E6E73]">Visible publicly on Student Status Check</span>
            <button onclick="submitSolveToken()" class="bg-[#1D1D1F] hover:bg-black text-white text-xs font-semibold px-4 py-2 rounded-lg transition flex items-center gap-1.5 shadow-xs">
              <span>✓ Mark Solved</span>
            </button>
          </div>
        </div>

        <!-- Action 2: Send Back to Admin (Solver Only) -->
        <div class="space-y-2 pt-3 border-t border-[rgba(0,0,0,0.06)]">
          <label class="text-[11px] font-bold uppercase tracking-wider text-[#6E6E73] flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full bg-rose-500"></span>
            <span>Send Back to Admin (Not Solved / দিকনির্দেশনার জন্য ফেরত)</span>
          </label>
          <div class="flex gap-2">
            <input id="solver-return-reason-input" type="text" placeholder="নোট বা কারণ লিখুন..." class="flex-1 bg-[#FAFAFA] border border-[rgba(0,0,0,0.1)] rounded-lg p-2 text-xs text-[#1D1D1F] focus:outline-none focus:border-[#1D1D1F]" />
            <button onclick="submitReturnToAdmin()" class="bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold px-3 py-2 rounded-lg transition shrink-0">
              <span>↩️ Send Back</span>
            </button>
          </div>
        </div>
      </section>

      <!-- Internal Admin Notes (Private) -->
      <section class="space-y-2 pt-4 border-t border-[rgba(0,0,0,0.08)]">
        <h4 class="text-[11px] font-bold uppercase tracking-wider text-[#6E6E73]">Internal Administrative Notes (Private)</h4>
        <div class="flex gap-2">
          <input id="adm-note-input" type="text" placeholder="Private internal note..." class="flex-1 bg-[#FAFAFA] border border-[rgba(0,0,0,0.1)] rounded-lg p-2 text-xs text-[#1D1D1F] focus:outline-none focus:border-[#1D1D1F]" />
          <button onclick="saveAdminNoteOnly()" class="bg-[#F5F5F7] hover:bg-slate-200 text-[#1D1D1F] border border-[rgba(0,0,0,0.08)] text-xs font-medium px-3 py-2 rounded-lg transition">Save Note</button>
        </div>
      </section>
    </div>
  </div>
</div>
```

### 6.2 Animation & Interaction Handlers
- **Smooth Slide-In**:
  ```javascript
  async function openAdminManageToken(tokenId) {
    currentAdminSelectedTokenId = tokenId;
    await loadSolversList();
    const modal = document.getElementById("admin-manage-token-modal");
    const drawer = document.getElementById("admin-drawer-panel");
    if (modal) modal.classList.remove("hidden");
    if (drawer) {
      setTimeout(() => drawer.classList.remove("translate-x-full"), 10);
    }
    // populate fields via fetch(`${API_BASE}/api/token/admin/${tokenId}`)...
  }
  ```
- **Smooth Slide-Out**:
  ```javascript
  function closeAdminManageTokenModal() {
    const drawer = document.getElementById("admin-drawer-panel");
    const modal = document.getElementById("admin-manage-token-modal");
    if (drawer) {
      drawer.classList.add("translate-x-full");
      setTimeout(() => {
        if (modal) modal.classList.add("hidden");
        currentAdminSelectedTokenId = null;
      }, 300);
    } else {
      if (modal) modal.classList.add("hidden");
      currentAdminSelectedTokenId = null;
    }
  }
  ```
- **Keyboard Listener**:
  Pressing `Escape` while `#admin-manage-token-modal` is active calls `closeAdminManageTokenModal()`.

---

## 7. Complete DOM ID & Event Inventory

| DOM ID | Element Type | Function / Event Handler | Preserved / Purpose |
|---|---|---|---|
| `admin-modal` | `div` (overlay) | `toggleAdminModal()` | Full support center modal container |
| `admin-user-display` | `span` | Displays user `full_name` or `username` | Header user identity |
| `admin-role-badge` | `span` | Displays `SUPER_ADMIN`, `ADMIN`, or `SOLVER` | Role indicator badge |
| `admin-dept-display` | `span` | Displays assigned department desk | Department context |
| `tab-btn-tokens` | `button` | `onclick="switchAdminTab('tokens')"` | Token Support Center tab button |
| `token-count-badge` | `span` | Updated with total count in `loadAdminTokens()` | Counter badge |
| `admin-token-search` | `input` | Debounced search or Enter key | Search input |
| `admin-token-status-filter` | `select` | `onchange="loadAdminTokens()"` | Status filter dropdown |
| `admin-token-service-filter` | `select` | `onchange="loadAdminTokens()"` | Service filter dropdown |
| `admin-tokens-tbody` | `tbody` | Populated in `loadAdminTokens()` | High-density data table rows |
| `admin-manage-token-modal` | `div` | Slide-over drawer container | Drawer backdrop & container |
| `admin-drawer-panel` | `div` | Slide-over right drawer | Transformed 60fps sliding panel |
| `adm-token-id` | `span` | Populated with `t.token_id` | Header token ID |
| `adm-status-badge` | `span` | Populated with `t.status` | Monochromatic status badge |
| `adm-user-name` | `strong` | Populated with `t.user_name` | Student name |
| `adm-user-phone` | `strong` | Populated with `t.user_phone` | Student phone |
| `adm-reg-no` | `strong` | Populated with `t.registration_no` | Student registration number |
| `adm-service` | `span` | Populated with `service_name (service_type)` | Service context |
| `adm-date` | `span` | Populated with `t.created_date` | Created date |
| `adm-problem` | `div` | Populated with `t.problem` | Student problem text |
| `adm-admin-controls-panel` | `div` | Shown for ADMIN, hidden for SOLVER | Assignment & status dropdowns |
| `adm-solver-select` | `select` | `onchange="submitAssignToken()"` | Department desk assignment |
| `adm-status-select` | `select` | `submitStatusUpdate()` | Status update |
| `solver-assignment-notice` | `div` | Shown for SOLVER, hidden for ADMIN | Read-only desk banner |
| `solver-desk-name-display` | `strong` | Displays assigned desk name | Desk name |
| `adm-solve-message` | `textarea` | Populated with `t.solve_message` | Resolution message |
| `submitSolveToken` | `button` | `onclick="submitSolveToken()"` | Save resolution & mark solved |
| `solver-return-reason-input` | `input` | Reason text for return to admin | Return reason input |
| `submitReturnToAdmin` | `button` | `onclick="submitReturnToAdmin()"` | Return to admin (Not Solved) |
| `adm-note-input` | `input` | Populated with `t.admin_note` | Private admin note input |
| `saveAdminNoteOnly` | `button` | `onclick="saveAdminNoteOnly()"` | Save private note |

---

## 8. Verification & Test Plan

1. **Python Domain Test Suite**:
   Execute:
   ```bash
   .venv\Scripts\python.exe -m pytest tests/test_token_service_domain.py -v
   ```
   Must pass 100% (4/4 tests passed).
2. **FAQ Forum Test Suite**:
   Execute:
   ```bash
   .venv\Scripts\python.exe -m pytest tests/test_faq_forum.py -v
   ```
   Must pass 100% (6/6 tests passed).
3. **Solver Access Control Verification**:
   - Log in as Solver (e.g. `solver_ict` or `solver_accounts`).
   - Confirm only `Token Support Center` tab is visible.
   - Confirm desk reassignment is disabled.
   - Confirm both `Solve` and `Send Back to Admin` work flawlessly.
4. **Super Admin Controls Verification**:
   - Log in as `admin` (`SUPER_ADMIN`).
   - Confirm full tab access.
   - Confirm soft-delete moves ticket to Trash.
   - Filter by Trash, confirm Restore recovers ticket.

---

## 9. Conclusion

The Administrative & Solver Support Center in `static/index.html` is primed for the Apple/Linear monochromatic redesign. The existing JavaScript logic cleanly maps to the slide-over drawer pattern without breaking any DOM IDs, event handlers, or database schemas. Addressing the `return-to-admin` API endpoint path will simultaneously fix a dormant routing bug while providing a modern, calm, and hyper-responsive support workspace.
