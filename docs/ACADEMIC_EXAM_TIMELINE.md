# National University Bangladesh — Interactive Academic Examination Milestone Timeline & Tracker

## 1. Overview
The **Interactive Academic Examination Milestone Timeline & Progress Tracker** is an advanced, student-facing academic workflow tracker grounded strictly in administrative examination records stored in SQLite (`academic_exam_information` table in `data/nu_assistant.db`).

The timeline provides transparency across the 5 canonical examination phases of the National University of Bangladesh without fabricating or guessing dates.

---

## 2. Navigation Flow & Placement
The tracker is seamlessly integrated into the left column of [`static/chat.html`](file:///d:/projects/AI_CHAT_BOT/static/chat.html) while keeping the right-hand FAQ forum panel visible on desktop (70% : 30% layout):
1. **Student opens the main chat page.**
2. **Student clicks an exam card** (e.g. `অনার্স পরীক্ষা`, `ডিগ্রি পরীক্ষা`, `মাস্টার্স পরীক্ষা`, `প্রফেশনাল পরীক্ষা`).
3. An Apple-style program/part picker modal appears (`#exam-part-modal`).
4. **Student selects a part/year** (e.g. `অনার্স ১ম বর্ষ`, `অনার্স ২য় বর্ষ`, `অনার্স ৩য় বর্ষ`, `অনার্স ৪র্থ বর্ষ`).
5. The application retrieves the matching examination record from SQLite via `/api/v1/academic-exams/lookup`.
6. The dedicated `#timeline-view` opens in the left column displaying:
   - Breadcrumb navigation (`← মূল মেনু / অনার্স পরীক্ষা / ১ম বর্ষ`)
   - Program & Part titles with Bengali numerals
   - Multi-year switcher pills (`📅 ২০২৫ (চলতি)`, `📅 ২০২৪`)
   - Compact progress overview (confirmed completed, upcoming, passed unconfirmed, missing info, progress %)
   - 5-Phase interactive stepper (`ইনকোর্স ও ফরম পূরণ`, `পরীক্ষা`, `ফলাফল`, `পুনঃনিরীক্ষণ`, `সনদ ও মার্কশিট`)
   - Milestone cards with intelligent status indicators
   - Direct official portal links (`results.nu.ac.bd`, `103.113.200.68/nu-app/`, `ems.nu.ac.bd`, `app11.nu.edu.bd`)
7. **Student clicks any milestone card** to open the **Milestone Detail Modal** (`#milestone-detail-modal`) with date formatted in `DD-MM-YYYY`, status explanation, direct action links, and one-click "Ask AI" chat query injection.

---

## 3. The 5 Academic Phases & Milestones

### Phase 1 — ইনকোর্স ও ফরম পূরণ (Incourse & Form Fill-up)
- **ইনকোর্স পরীক্ষা** (`incourse_exam_date`)
- **ইনকোর্স নম্বর জমার শেষ তারিখ** (`incourse_marks_deadline`)
- **ফরম পূরণ শুরু** (`form_fillup_start_date`)
- **ফরম পূরণের শেষ তারিখ** (`form_fillup_deadline`)

### Phase 2 — পরীক্ষা (Examination)
- **রুটিন প্রকাশ** (`routine_publication_date`) — detects direct PDF/web links
- **প্রবেশপত্র প্রকাশ বা প্রাপ্তি** (`admit_card_date`)
- **পরীক্ষার তারিখ (শুরু)** (`exam_date`)
- **শেষ পরীক্ষা** (`last_exam_date`)
- **ব্যবহারিক নম্বর জমা শুরু** (`practical_marks_start_date`)
- **ব্যবহারিক নম্বর জমার শেষ তারিখ** (`practical_marks_deadline`)

### Phase 3 — ফলাফল (Results)
- **সম্ভাব্য ফলাফল প্রকাশ** (`probable_result_date`)
- **প্রকৃত ফলাফল প্রকাশ** (`actual_result_date`)
- **ফলাফল প্রকাশের স্থিতি** (`results_published` == 'Yes' / 'No')

### Phase 4 — পুনঃনিরীক্ষণ (Re-scrutiny)
- **পুনঃনিরীক্ষণ আবেদনের শুরু** (`rescrutiny_start_date`)
- **পুনঃনিরীক্ষণ আবেদনের শেষ তারিখ** (`rescrutiny_deadline`)
- **পুনঃনিরীক্ষণের ফলাফল প্রকাশ** (`rescrutiny_result_date`)

### Phase 5 — সনদ ও মার্কশিট (Certificate & Marksheet)
- **সার্টিফিকেট/মার্কশিট মুদ্রণের তারিখ** (`document_printing_date`)
- **মুদ্রণ সম্পন্ন হয়েছে কি না** (`documents_printed` == 'Yes' / 'No')

---

## 4. Intelligent Milestone Status Evaluation & Accuracy Rules

Every milestone displays an understandable status indicator grounded in real dates:
- **সম্পন্ন** (`completed` — green): Confirmed completion explicitly verified (e.g. `documents_printed == 'Yes'`).
- **আজ** (`today` — sky blue with pulse animation): Confirmed scheduled date falls on the current Bangladesh calendar date (`UTC+6`).
- **আসন্ন** (`upcoming` — amber): A scheduled date or deadline is in the future.
- **তারিখ অতিক্রান্ত** (`passed_unconfirmed` — orange): **Critical Rule:** Never mark a milestone as completed merely because its date is in the past! If a scheduled date has passed without administrative confirmation, it is marked as `তারিখ অতিক্রান্ত`.
- **প্রকাশিত** (`published` — blue): An official result or document has been confirmed as published (e.g. `results_published == 'Yes'`, or routine URL is provided and valid).
- **অপেক্ষমাণ** (`pending` — purple): Expected event or result not yet confirmed.
- **তথ্য নেই** (`no_info` — slate): The administrator has not supplied the necessary date or information.

---

## 5. API Endpoints
- `GET /api/v1/academic-exams/years?program_type=Honours&part=Part 1`: Returns available examination years from SQLite.
- `GET /api/v1/academic-exams/lookup?program_type=Honours&examination_year=2025&part=Part 1`: Returns examination record, formatted markdown card, and the computed 5-phase timeline with progress overview.
- `GET /api/v1/academic-exams/{record_id}`: Returns record and timeline by ID.

---

## 6. Test Suite
Verified via `pytest tests/test_academic_timeline.py`:
- 100% pass on critical accuracy rules (past date != completed).
- 100% pass on confirmed completion flags.
- 100% pass on today/upcoming date evaluations.
- 100% pass on API endpoints and multi-year switcher.
