# Milestone 1 Changes: Administrative & Solver Support Center Redesign

**Worker**: worker_m1  
**Target File**: `static/index.html`  
**Date**: 2026-10-21  

---

## 1. Monochromatic Apple / Linear Design System
- Added `:root` design tokens in `<style>` (lines 545–557):
  - `--bg: #F5F5F7` (Apple canvas neutral)
  - `--surface: #FFFFFF` (pure white surface for cards and drawer)
  - `--surface-subtle: #FAFAFA` (subtle header and panel surface)
  - `--text: #1D1D1F` (crisp near-black primary text)
  - `--text-secondary: #6E6E73` (Apple secondary muted text)
  - `--text-tertiary: #86868B` (micro metadata text)
  - `--hairline: rgba(0, 0, 0, 0.08)` (1px boundary divider)
  - `--hairline-subtle: rgba(0, 0, 0, 0.04)` (row hairpins)
  - `--accent: #1D1D1F` & `--accent-hover: #000000`
  - `--focus-ring: rgba(0, 113, 227, 0.4)`

## 2. High-Density Data Table & Monochromatic Toolbar
- Redesigned `#tab-content-tokens` filters toolbar with clean monochromatic inputs, status selector, and buttons.
- Updated `<thead>` to 6 dense, well-spaced columns:
  1. `Token ID & Time` (Token ID and creation timestamp)
  2. `Student Info` (Name, Phone number, and Registration number)
  3. `Service & Desk` (Service category and assigned solver department)
  4. `Problem` (Truncated problem statement with title tooltip)
  5. `Status` (Subtle muted badge with 6px dot indicator)
  6. `Actions` (Manage button, Restore button, Super Admin Trash button)
- Introduced `getMonochromeStatusBadge(status)` function using soft tints (`bg-*-500/10`) and dot pips (`bg-*-500/600`).
- Made entire `<tr>` clickable with `onclick="openAdminManageToken('${tokenId}')"` for instant drawer opening.
- Attached `event.stopPropagation()` to row action buttons (`restoreAdminToken`, `deleteAdminToken`, `openAdminManageToken`) to prevent bubbling conflicts.
- Updated empty state and error state to `colspan="6"`.

## 3. Slide-Over Inspection Drawer Architecture
- Restructured `#admin-manage-token-modal` from a centered popup into a slide-over drawer:
  - Slide panel (`#admin-drawer-panel`): `fixed top-0 right-0 h-full w-full max-w-xl bg-white border-l border-[rgba(0,0,0,0.08)] shadow-2xl transform translate-x-full transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] z-[60] flex flex-col`.
  - Translucent backdrop overlay (`#admin-drawer-backdrop`) with `onclick="closeAdminManageTokenModal()"` for click-outside dismissal.
  - Header: Token ID, creation date, service indicator, status badge, and close button (`closeAdminManageTokenModal()`).
  - Section 1 (Student & Service Context): `#adm-user-name`, `#adm-user-phone`, `#adm-reg-no`, `#adm-service`, `#adm-date`, `#adm-status-badge`, `#adm-problem`.
  - Section 2 (Desk Controls): `#adm-admin-controls-panel` (`#adm-solver-select`, `#adm-status-select`) for Admin vs `#solver-assignment-notice` (`#solver-desk-name-display`) for Solver.
  - Section 3 (Desk Action Controls): Action 1: Solve (`#adm-solve-message`, `submitSolveToken()`, with 4 quick template chips) and Action 2: Solver Return to Admin (`#solver-return-reason-input`, `submitReturnToAdmin()`).
  - Section 4 (Internal Notes): `#adm-note-input`, `saveAdminNoteOnly()`.
- Added smooth slide animation trigger in `openAdminManageToken()` and slide-out with timeout in `closeAdminManageTokenModal()`.
- Added global `Escape` key event listener for drawer dismissal.

## 4. Strict Solver Role Access Control
- In `openAdminDashboardUI()`, ensured all 7 non-token admin tabs (`tab-btn-sitemap`, `tab-btn-ai-engine`, `tab-btn-qa-knowledge`, `tab-btn-academic-static`, `tab-btn-users`, `tab-btn-logs`, `tab-btn-backups`) are strictly hidden (`display = "none"`) when `user.role === 'SOLVER'`.
- In `switchAdminTab()`, forced tab to `"tokens"` if a solver attempts to navigate to any other tab.
- In `openAdminManageToken()`, desk reassignment controls (`#adm-admin-controls-panel`) remain hidden for solvers, displaying read-only `#solver-assignment-notice` banner instead.
- Solvers are limited exclusively to 2 actions: `Solve` or `Send Back to Admin (Not Solved)`.

## 5. Return-to-Admin API Bug Fix
- In `submitReturnToAdmin()`, updated the target endpoint:
  - Before: `${API_BASE}/api/token/admin/${currentAdminSelectedTokenId}/return-to-admin` (which returned 404).
  - After: `${API_BASE}/api/v1/admin/tokens/${currentAdminSelectedTokenId}/return-to-admin` matching `backend/api/admin_routes.py` line 163.
  - Payload preserved: `{"reason": reason, "solver_name": solverName}` with Bearer JWT authorization.

## 6. Super Admin Controls Preservation
- Preserved `deleteAdminToken(tokenId)` (`POST /api/token/admin/${tokenId}/delete`).
- Preserved `restoreAdminToken(tokenId)` (`POST /api/token/admin/${tokenId}/restore`).
- Preserved `#opt-trash-filter` dropdown filter option (`value="TRASH"`).

## 7. DOM ID Preservation
All existing DOM IDs and event handlers preserved without renaming or deletion.
