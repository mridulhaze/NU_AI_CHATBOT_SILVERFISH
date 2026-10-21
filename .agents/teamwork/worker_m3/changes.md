# Code Changes Summary - Milestone 3

## 1. Backend Return-to-Admin Schema Alignment (`backend/models/schemas.py`)
- **Location**: Lines 160-164
- **Modification**: Updated `TokenReturnRequest` Pydantic model to allow optional fields for both `reason` (as requested by PROJECT.md § Interface Contracts) and `return_reason` (legacy/alternate), as well as `token_id` and `solver_name`.
```python
class TokenReturnRequest(BaseModel):
    token_id: Optional[str] = None
    reason: Optional[str] = None
    return_reason: Optional[str] = None
    solver_name: Optional[str] = None
```
- **Rationale**: Eliminates `AttributeError` and FastAPI 422 Unprocessable Entity errors when frontend callers submit `{ reason, solver_name }` while URL routes supply `token_id`.

## 2. Admin Router Return-to-Admin Handler (`backend/api/admin_routes.py`)
- **Location**: Lines 168-185
- **Modification**: 
  - Added robust resolution of `solver_name = payload.solver_name or user.get("full_name") or user.get("username")`.
  - Added fallback handling for `reason = payload.reason or payload.return_reason or "Returned to admin"`.
  - Cleaned up extraneous `TokenReturnRequest` type token in `solve_token_endpoint` signature line.
```python
@router.post("/tokens/{token_id}/return-to-admin")
def return_token_to_admin_endpoint(
    token_id: str,
    payload: TokenReturnRequest,
    user: dict = Depends(require_roles([Role.SOLVER, Role.ADMIN, Role.SUPER_ADMIN]))
):
    service = get_token_domain_service()
    solver_name = payload.solver_name or user.get("full_name") or user.get("username")
    reason = payload.reason or payload.return_reason or "Returned to admin"
    ok, msg = service.return_to_admin(
        token_id=token_id.strip().upper(),
        reason=reason,
        solver_name=solver_name,
        changed_by=user.get("username", "SOLVER")
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}
```

## 3. Monochromatic Theme & Dark Mode Unification (`static/index.html` & `static/chat.html`)
- **Variables Harmonized**:
  - Light Mode:
    - `--bg: #F5F5F7`
    - `--surface: #FFFFFF`
    - `--text: #1D1D1F`
    - `--text-secondary: #6E6E73`
    - `--hairline: rgba(0, 0, 0, 0.08)`
  - Dark Mode:
    - `--bg: #1C1C1E`
    - `--surface: #2C2C2E`
    - `--text: #F5F5F7`
    - `--hairline: rgba(255, 255, 255, 0.10)`
- **Drawer & Table Dark Adaptivity in `static/index.html`**:
  - Slide-over drawer `#admin-drawer-panel`:
    `[data-theme="dark"] #admin-drawer-panel { background: #2C2C2E; color: #F5F5F7; border-color: rgba(255,255,255,0.10); }`
  - Drawer header and sub-containers adapt to `#242426` and `#1C1C1E`.
  - Textarea, text inputs, and select elements adapt with dark backgrounds and subtle hairline borders.
  - Table `<thead>`, `<th>`, and `<td>` borders adapt to `rgba(255, 255, 255, 0.10)` and header background `#242426`.
  - Added `data-theme="light"` to `<html>` root with `@media (prefers-color-scheme: dark)` system detection support.
