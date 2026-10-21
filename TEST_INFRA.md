# E2E Test Infra: National University Bangladesh AI Assistant UI Redesign

## Test Philosophy
- Opaque-box & contract-driven verification derived from ORIGINAL_REQUEST.md and AGENTS.md.
- Verification covers UI contracts, DOM IDs, role isolation, API routes, URL authenticity, and test suite pass rates.
- Methodology: Category-Partition + Boundary Value Analysis + Pairwise Combinatorial + Real-World Workload Testing.

## Feature Inventory & Test Coverage Matrix
| # | Feature | Source (requirement) | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|---|---------|---------------------|:------:|:------:|:------:|:------:|
| 1 | High-density Token Table & Badges | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 2 | Slide-Over Inspection Drawer | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 3 | Solver Role Desk Isolation & Actions | ORIGINAL_REQUEST §R3 & AGENTS.md | 5 | 5 | ✓ | ✓ |
| 4 | Super Admin Trash & Backup | ORIGINAL_REQUEST §R3 & AGENTS.md | 5 | 5 | ✓ | ✓ |
| 5 | Return-to-Admin Route Integrity | Survey Explorer 1 | 5 | 5 | ✓ | ✓ |
| 6 | Sleek FAQ Accordion & Search | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 7 | Horizontal Category Scroll Pills | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 8 | FAQ Action Controls (Like, Ask AI, Copy) | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 9 | Dynamic 70%/30% Split Layout | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 10 | Monochromatic Tokens & Dark Mode | ORIGINAL_REQUEST §R1, R2 | 5 | 5 | ✓ | ✓ |
| 11 | Official Portal URLs Verification | AGENTS.md | 5 | 5 | ✓ | ✓ |

## Test Architecture
- **Test Runner**: Pytest via `.venv\Scripts\python.exe -m pytest tests/test_e2e_ui_redesign.py -v`
- **Pass/Fail Semantics**: 100% tests must pass (exit code 0, 0 failures).
- **Target Test File**: `tests/test_e2e_ui_redesign.py`

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Solver Workflow: Login as Accounts Solver -> View only Accounts tickets -> Click ticket to open drawer -> Solve ticket -> Verify status updated | F1, F2, F3, F10 | High |
| 2 | Solver Return Workflow: Login as ICT Solver -> Open ticket -> Return to admin with note -> Verify correct /api/v1/admin route | F2, F3, F5, F10 | High |
| 3 | Student FAQ Discovery: Search query in chat FAQ -> Debounced filter -> Click category hashtag pill -> Expand accordion -> Copy answer -> Ask AI in chat | F6, F7, F8, F9, F10 | High |
| 4 | Super Admin Governance: View all desks -> Soft-delete invalid ticket -> Restore from trash -> Verify audit and permissions | F1, F3, F4 | High |
| 5 | Portal Link Authenticity: Verify all student service, admission, and EMS URLs match official IP/domains without deprecated links | F11 | Medium |

## Coverage Thresholds
- Tier 1: Feature Coverage (≥5 tests per primary capability)
- Tier 2: Boundary & Corner Cases (empty states, invalid roles, long notes, missing fields)
- Tier 3: Pairwise Cross-Feature Interactions
- Tier 4: Real-World Workload Scenarios
