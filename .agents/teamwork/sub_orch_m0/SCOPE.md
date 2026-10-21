# Scope: Milestone 0 — E2E Testing Track

## Mission
Design and implement the comprehensive opaque-box E2E test suite in `tests/test_e2e_ui_redesign.py` covering Support Center and FAQ Panel UI contracts, Solver/Admin RBAC isolation, official URLs, and theme tokens. Publish `TEST_READY.md` upon completion.

## Architecture & Boundaries
- Owned files: `tests/test_e2e_ui_redesign.py`, `TEST_READY.md`
- Referenced files: `PROJECT.md`, `TEST_INFRA.md`, `ORIGINAL_REQUEST.md`, `AGENTS.md`
- Target test command: `.venv\Scripts\python.exe -m pytest tests/test_e2e_ui_redesign.py -v`

## Feature Coverage Matrix (Tiers 1-4)
1. High-Density Token Table & Badges (Tier 1: >=5, Tier 2: >=5, Tier 3: pairwise, Tier 4: scenario)
2. Slide-over Inspection Drawer (Tier 1: >=5, Tier 2: >=5, Tier 3: pairwise, Tier 4: scenario)
3. Solver Role Desk Isolation & Actions (Tier 1: >=5, Tier 2: >=5, Tier 3: pairwise, Tier 4: scenario)
4. Super Admin Trash & Backup Controls (Tier 1: >=5, Tier 2: >=5, Tier 3: pairwise, Tier 4: scenario)
5. Return-to-Admin Route Integrity (Tier 1: >=5, Tier 2: >=5, Tier 3: pairwise, Tier 4: scenario)
6. FAQ Accordion & Category Pills (Tier 1: >=5, Tier 2: >=5, Tier 3: pairwise, Tier 4: scenario)
7. FAQ Action Controls (Like, Ask AI, Copy) (Tier 1: >=5, Tier 2: >=5, Tier 3: pairwise, Tier 4: scenario)
8. Dynamic 70%/30% Split Layout (Tier 1: >=5, Tier 2: >=5, Tier 3: pairwise, Tier 4: scenario)
9. Monochromatic Design Tokens & Dark Mode (Tier 1: >=5, Tier 2: >=5, Tier 3: pairwise, Tier 4: scenario)
10. Official Portal URLs (Student Services, Admission, EMS, forbidden deprecated links) (Tier 1: >=5, Tier 2: >=5, Tier 3: pairwise, Tier 4: scenario)

## Completion Criteria
1. `tests/test_e2e_ui_redesign.py` created and runnable via pytest.
2. All tests pass with exit code 0.
3. `TEST_READY.md` published at project root (`D:\projects\AI_CHAT_BOT\TEST_READY.md`) detailing runner command, tier breakdown, and feature checklist.
