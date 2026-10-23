"""
National University Bangladesh - Academic Examination Information Service
Handles structured administrative examination information lifecycle and 
student chatbot query grounding with small modern nice looking vertical cards.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta, date
import re
from backend.models.schemas import ChatResponse, SourceCitation
from db.sql_store import get_sql_store

BD_TZ = timezone(timedelta(hours=6))

BN_TO_EN_DIGITS = str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789')
EN_TO_BN_DIGITS = str.maketrans('0123456789', '০১২৩৪৫৬৭৮৯')

BN_MONTHS = {
    'জানুয়ারি': 1, 'জানুয়ারি': 1, 'ফেব্রুয়ারি': 2, 'ফেব্রুয়ারি': 2,
    'মার্চ': 3, 'এপ্রিল': 4, 'মে': 5, 'জুন': 6,
    'জুলাই': 7, 'আগস্ট': 8, 'সেপ্টেম্বর': 9, 'অক্টোবর': 10,
    'নভেম্বর': 11, 'ডিসেম্বর': 12
}

def to_bn_digits(s: Any) -> str:
    """Converts ASCII digits to Bengali digits."""
    return str(s).translate(EN_TO_BN_DIGITS)

def get_bd_now() -> datetime:
    """Returns the current datetime in Bangladesh Standard Time (UTC+6)."""
    return datetime.now(BD_TZ)

def parse_date_str(val: Optional[str]) -> Optional[date]:
    """
    Parses various date strings (e.g. '15 May 2024', '10 Jan 2025 - 20 Jan 2025',
    '15-05-2024', '2025-06-20', Bengali numerals/months) into a date object.
    """
    if not val or not isinstance(val, str):
        return None
    s = val.translate(BN_TO_EN_DIGITS).strip()
    if not s or s.lower() in ['n/a', 'none', 'তথ্য এখনো প্রকাশ করা হয়নি।', 'নাই', 'বাতিল', 'অপেক্ষমাণ']:
        return None
    if s.startswith('http://') or s.startswith('https://'):
        return None

    # Handle range (e.g. '10 Jan 2025 - 20 Jan 2025' or '10 Jan to 20 Jan 2025')
    if ' - ' in s:
        s = s.split(' - ')[-1].strip()
    elif ' হতে ' in s:
        s = s.split(' হতে ')[-1].strip()
    elif ' to ' in s.lower():
        s = re.split(r'\s+to\s+', s, flags=re.I)[-1].strip()

    formats = [
        '%d %B %Y', '%d %b %Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y',
        '%B %d, %Y', '%b %d, %Y', '%d.%m.%Y'
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass

    for bn, m in BN_MONTHS.items():
        if bn in val:
            nums = re.findall(r'\d+', val.translate(BN_TO_EN_DIGITS))
            if len(nums) >= 2:
                day = int(nums[0])
                year = int(nums[-1]) if len(nums[-1]) == 4 else int(nums[1])
                try:
                    return datetime(year, m, day).date()
                except ValueError:
                    pass
    return None

def format_user_facing_date(val: Optional[str], parsed: Optional[date]) -> str:
    """
    Normalizes user-facing dates into DD-MM-YYYY format when parsed,
    or falls back cleanly to the admin-entered string.
    """
    if parsed:
        return parsed.strftime("%d-%m-%Y")
    if val and not val.startswith("http"):
        return val.strip()
    return "তথ্য নেই"

def evaluate_milestone_status(
    milestone_id: str,
    raw_val: Optional[str],
    record: Dict[str, Any],
    today_bd: date
) -> Tuple[str, str, bool, str]:
    """
    Intelligent status evaluation for academic examination milestones.
    Returns: (status_label_bn, status_type, is_completed, status_description_bn)

    Statuses:
    - 'সম্পন্ন' (completed): Confirmed completion explicitly verified
    - 'আজ' (today): Confirmed scheduled date is today in Bangladesh Standard Time
    - 'আসন্ন' (upcoming): Scheduled date or deadline is in the future
    - 'তারিখ অতিক্রান্ত' (passed_unconfirmed): Date has passed, but completion is NOT explicitly confirmed
    - 'প্রকাশিত' (published): Result or official document confirmed published
    - 'অপেক্ষমাণ' (pending): Expected event not yet confirmed
    - 'তথ্য নেই' (no_info): Administrator has not supplied date or info
    - 'প্রযোজ্য নয়' (not_applicable): Not applicable to this program/part
    """
    raw_clean = (raw_val or "").strip()

    # 1. Results Published status
    if milestone_id == "results_published":
        val = (record.get("results_published") or "").strip().lower()
        if val in ["yes", "true", "1", "হ্যাঁ", "সম্পন্ন", "প্রকাশিত"]:
            return ("প্রকাশিত", "published", True, "জাতীয় বিশ্ববিদ্যালয় কর্তৃক ফলাফল আনুষ্ঠানিকভাবে প্রকাশ করা হয়েছে।")
        elif val in ["no", "false", "0", "না"]:
            return ("অপেক্ষমাণ", "pending", False, "ফলাফল প্রকাশের অপেক্ষায় রয়েছে।")
        return ("তথ্য নেই", "no_info", False, "ফলাফল প্রকাশের তথ্য এখনো প্রশাসনিকভাবে এন্ট্রি করা হয়নি।")

    # 2. Documents Printed status
    if milestone_id == "documents_printed":
        val = (record.get("documents_printed") or "").strip().lower()
        if val in ["yes", "true", "1", "হ্যাঁ", "সম্পন্ন"]:
            return ("সম্পন্ন", "completed", True, "সনদ ও মূল মার্কশিট মুদ্রণ ও প্রস্তুতকরণ সম্পন্ন হয়েছে।")
        elif val in ["no", "false", "0", "না"]:
            return ("অপেক্ষমাণ", "pending", False, "সনদ বা মার্কশিট মুদ্রণের প্রক্রিয়া অপেক্ষমাণ।")
        return ("তথ্য নেই", "no_info", False, "মুদ্রণ সংক্রান্ত তথ্য এখনো হালনাগাদ করা হয়নি।")

    # 3. Routine Publication
    if milestone_id == "routine_publication_date":
        if raw_clean.startswith("http://") or raw_clean.startswith("https://"):
            return ("প্রকাশিত", "published", True, "পরীক্ষার অফিসিয়াল সময়সূচি/রুটিন প্রকাশিত হয়েছে এবং লিঙ্ক সংযুক্ত আছে।")
        p_date = parse_date_str(raw_clean)
        if p_date:
            if p_date == today_bd:
                return ("আজ", "today", False, "আজ রুটিন প্রকাশিত হওয়ার নির্ধারিত তারিখ।")
            elif p_date > today_bd:
                return ("আসন্ন", "upcoming", False, f"রুটিন প্রকাশের নির্ধারিত তারিখ: {p_date.strftime('%d-%m-%Y')}।")
            else:
                return ("তারিখ অতিক্রান্ত", "passed_unconfirmed", False, f"রুটিন প্রকাশের নির্ধারিত তারিখ ({p_date.strftime('%d-%m-%Y')}) অতিক্রান্ত হয়েছে, তবে রুটিন লিঙ্ক এখনো হালনাগাদ করা হয়নি।")
        if raw_clean:
            return ("অপেক্ষমাণ", "pending", False, raw_clean)
        return ("তথ্য নেই", "no_info", False, "রুটিনের নির্ধারিত তারিখ এন্ট্রি করা হয়নি।")

    # 4. Standard Date-based Milestones
    if not raw_clean or raw_clean.lower() in ["n/a", "none", "তথ্য নেই", "নাই", "বাতিল", "অপেক্ষমাণ", "তথ্য এখনো প্রকাশ করা হয়নি।"]:
        return ("তথ্য নেই", "no_info", False, "প্রশাসনিকভাবে এই তারিখের তথ্য এখনো প্রদান করা হয়নি।")

    p_date = parse_date_str(raw_clean)
    if not p_date:
        return ("অপেক্ষমাণ", "pending", False, raw_clean)

    if p_date == today_bd:
        return ("আজ", "today", False, "আজকের জন্য নির্ধারিত কার্যক্রম/সময়সীমা।")
    elif p_date > today_bd:
        return ("আসন্ন", "upcoming", False, f"নির্ধারিত তারিখ/সময়সীমা ভবিষ্যতে রয়েছে ({p_date.strftime('%d-%m-%Y')})।")
    else:
        # CRITICAL ACCURACY RULE:
        # Never mark a milestone as completed merely because its date is in the past!
        return ("তারিখ অতিক্রান্ত", "passed_unconfirmed", False, f"নির্ধারিত তারিখ ({p_date.strftime('%d-%m-%Y')}) অতিক্রান্ত হয়েছে। নিশ্চিত সমাপ্তি প্রশাসনিকভাবে অপেক্ষমাণ।")

def get_academic_exam_years(
    program_type: str,
    part: Optional[str] = None,
    semester: Optional[str] = None,
    course_name: Optional[str] = None
) -> List[str]:
    """
    Retrieves all distinct examination years available in SQLite for a given program and part.
    """
    sql_store = get_sql_store()
    records = sql_store.lookup_academic_exam_info(
        program_type=program_type,
        part=part,
        semester=semester,
        course_name=course_name
    )
    years = {str(r.get("examination_year")).strip() for r in records if r.get("examination_year")}
    def _extract_year_num(y: str) -> int:
        nums = re.findall(r'\d+', y)
        return int(nums[0]) if nums else 0
    return sorted(list(years), key=_extract_year_num, reverse=True)

def build_academic_milestone_timeline(
    record: Optional[Dict[str, Any]],
    available_years: Optional[List[str]] = None,
    program_type: Optional[str] = None,
    part: Optional[str] = None,
    semester: Optional[str] = None,
    course_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Builds the interactive 5-phase examination milestone timeline & progress tracker
    grounded strictly in SQLite database records.
    """
    today_bd = get_bd_now().date()
    rec = record or {}

    prog = rec.get("program_type") or program_type or "Honours"
    prog_cfg = PROGRAM_CONFIG.get(prog, {})
    prog_bn = rec.get("program_type_name") or prog_cfg.get("bn_name", prog)

    p_part = rec.get("part") or part or "Part 1"
    part_bn = prog_cfg.get("part_labels", {}).get(p_part, p_part) if p_part and p_part != "N/A" else ""

    p_sem = rec.get("semester") or semester or ""
    p_course = rec.get("course_name") or course_name or ""
    exam_year = str(rec.get("examination_year") or "").strip()

    # Determine heading
    heading_parts = [prog_bn]
    if part_bn:
        heading_parts.append(part_bn)
    if p_course and p_course != "N/A":
        heading_parts.append(f"({p_course})")
    if p_sem and p_sem != "N/A":
        heading_parts.append(f"সেমিস্টার: {to_bn_digits(p_sem)}")

    heading = " ".join(heading_parts) + " — পরীক্ষা বিষয়ক অগ্রগতি"
    subheading = f"পরীক্ষার বছর: {to_bn_digits(exam_year)}" if exam_year else "পরীক্ষার সময়সূচি ও অগ্রগতি"

    # Define the 5 phases with their milestones
    phase_defs = [
        {
            "phase_id": 1,
            "title_bn": "ইনকোর্স ও ফরম পূরণ",
            "title_en": "Incourse & Form Fill-up",
            "icon": "📝",
            "milestone_specs": [
                {
                    "id": "incourse_exam",
                    "title_bn": "ইনকোর্স পরীক্ষা",
                    "field": "incourse_exam_date",
                    "category": "academic"
                },
                {
                    "id": "incourse_marks_deadline",
                    "title_bn": "ইনকোর্স নম্বর জমার শেষ তারিখ",
                    "field": "incourse_marks_deadline",
                    "category": "deadline"
                },
                {
                    "id": "form_fillup_start",
                    "title_bn": "ফরম পূরণ শুরু",
                    "field": "form_fillup_start_date",
                    "category": "portal"
                },
                {
                    "id": "form_fillup_deadline",
                    "title_bn": "ফরম পূরণের শেষ তারিখ",
                    "field": "form_fillup_deadline",
                    "category": "deadline"
                }
            ]
        },
        {
            "phase_id": 2,
            "title_bn": "পরীক্ষা",
            "title_en": "Examination",
            "icon": "📋",
            "milestone_specs": [
                {
                    "id": "routine_publication_date",
                    "title_bn": "রুটিন প্রকাশ",
                    "field": "routine_publication_date",
                    "category": "routine"
                },
                {
                    "id": "admit_card_date",
                    "title_bn": "প্রবেশপত্র প্রকাশ বা প্রাপ্তি",
                    "field": "admit_card_date",
                    "category": "portal"
                },
                {
                    "id": "exam_date",
                    "title_bn": "পরীক্ষার তারিখ (শুরু)",
                    "field": "exam_date",
                    "category": "exam"
                },
                {
                    "id": "last_exam_date",
                    "title_bn": "শেষ পরীক্ষা",
                    "field": "last_exam_date",
                    "category": "exam"
                },
                {
                    "id": "practical_marks_start_date",
                    "title_bn": "ব্যবহারিক নম্বর জমা শুরু",
                    "field": "practical_marks_start_date",
                    "category": "academic"
                },
                {
                    "id": "practical_marks_deadline",
                    "title_bn": "ব্যবহারিক নম্বর জমার শেষ তারিখ",
                    "field": "practical_marks_deadline",
                    "category": "deadline"
                }
            ]
        },
        {
            "phase_id": 3,
            "title_bn": "ফলাফল",
            "title_en": "Results",
            "icon": "📊",
            "milestone_specs": [
                {
                    "id": "probable_result_date",
                    "title_bn": "সম্ভাব্য ফলাফল প্রকাশ",
                    "field": "probable_result_date",
                    "category": "result"
                },
                {
                    "id": "actual_result_date",
                    "title_bn": "প্রকৃত ফলাফল প্রকাশ",
                    "field": "actual_result_date",
                    "category": "result"
                },
                {
                    "id": "results_published",
                    "title_bn": "ফলাফল প্রকাশের স্থিতি",
                    "field": "results_published",
                    "category": "confirmation"
                }
            ]
        },
        {
            "phase_id": 4,
            "title_bn": "পুনঃনিরীক্ষণ",
            "title_en": "Re-scrutiny",
            "icon": "🔍",
            "milestone_specs": [
                {
                    "id": "rescrutiny_start_date",
                    "title_bn": "পুনঃনিরীক্ষণ আবেদনের শুরু",
                    "field": "rescrutiny_start_date",
                    "category": "rescrutiny"
                },
                {
                    "id": "rescrutiny_deadline",
                    "title_bn": "পুনঃনিরীক্ষণ আবেদনের শেষ তারিখ",
                    "field": "rescrutiny_deadline",
                    "category": "deadline"
                },
                {
                    "id": "rescrutiny_result_date",
                    "title_bn": "পুনঃনিরীক্ষণের ফলাফল প্রকাশ",
                    "field": "rescrutiny_result_date",
                    "category": "result"
                }
            ]
        },
        {
            "phase_id": 5,
            "title_bn": "সনদ ও মার্কশিট",
            "title_en": "Certificate & Marksheet",
            "icon": "🎓",
            "milestone_specs": [
                {
                    "id": "document_printing_date",
                    "title_bn": "সার্টিফিকেট/মার্কশিট মুদ্রণের তারিখ",
                    "field": "document_printing_date",
                    "category": "printing"
                },
                {
                    "id": "documents_printed",
                    "title_bn": "মুদ্রণ সম্পন্ন হয়েছে কি না",
                    "field": "documents_printed",
                    "category": "confirmation"
                }
            ]
        }
    ]

    # Status badge styling helper
    badge_styles = {
        "completed": "bg-emerald-50 text-emerald-700 border-emerald-200",
        "published": "bg-blue-50 text-blue-700 border-blue-200",
        "today": "bg-sky-500 text-white font-bold animate-pulse shadow-sm",
        "upcoming": "bg-amber-50 text-amber-700 border-amber-200",
        "passed_unconfirmed": "bg-orange-50 text-orange-700 border-orange-200",
        "pending": "bg-purple-50 text-purple-700 border-purple-200",
        "no_info": "bg-slate-100 text-slate-500 border-slate-200",
        "not_applicable": "bg-gray-100 text-gray-400 border-gray-200"
    }

    total_milestones = 0
    completed_milestones = 0
    upcoming_milestones = 0
    passed_unconfirmed_milestones = 0
    missing_milestones = 0
    today_milestones = 0

    evaluated_phases = []

    for p_def in phase_defs:
        phase_milestones = []
        phase_completed_count = 0

        for m_spec in p_def["milestone_specs"]:
            m_id = m_spec["id"]
            field = m_spec["field"]
            raw_val = str(rec.get(field) or "").strip()

            p_date = parse_date_str(raw_val)
            formatted_date = format_user_facing_date(raw_val, p_date)
            status_label, status_type, is_comp, desc = evaluate_milestone_status(m_id, raw_val, rec, today_bd)

            # Determine relevant portal links for this milestone
            links = []
            if m_id in ["results_published", "actual_result_date", "probable_result_date"]:
                res_url = rec.get("revaluation_result_url") or "https://results.nu.ac.bd/"
                cw_url = rec.get("college_wise_result_url") or "http://103.113.200.68/nu-app/search.php"
                links.append({"title": "অনলাইন ফলাফল পোর্টাল", "url": res_url, "icon": "📊"})
                links.append({"title": "কলেজভিত্তিক ফলাফল অনুসন্ধান", "url": cw_url, "icon": "🏫"})
            elif m_id in ["rescrutiny_start_date", "rescrutiny_deadline", "rescrutiny_result_date"]:
                res_url = rec.get("revaluation_result_url") or "https://results.nu.ac.bd/"
                links.append({"title": "পুনঃনিরীক্ষণ আবেদন ও ফলাফল", "url": res_url, "icon": "🔍"})
                links.append({"title": "সোনালী সেবা ফি পেমেন্ট পোর্টাল", "url": "http://103.113.200.68/nu-app/", "icon": "💳"})
            elif m_id == "routine_publication_date":
                if raw_val.startswith("http://") or raw_val.startswith("https://"):
                    links.append({"title": "অফিসিয়াল রুটিন ডাউনলোড (PDF/ওয়েব)", "url": raw_val, "icon": "📥"})
                links.append({"title": "পরীক্ষা সংক্রান্ত নোটিশ বোর্ড", "url": rec.get("source_url") or "https://www.nu.ac.bd/recent-news-notice.php", "icon": "📢"})
            elif m_id in ["form_fillup_start", "form_fillup_deadline"]:
                links.append({"title": "ইএমএস ফরম পূরণ পোর্টাল", "url": "http://ems.nu.ac.bd/", "icon": "📝"})
                links.append({"title": "শিক্ষার্থী সেবা পোর্টাল", "url": "http://103.113.200.68/nu-app/", "icon": "🎓"})
            elif m_id in ["document_printing_date", "documents_printed"]:
                links.append({"title": "অনলাইন সার্টিফিকেট/ট্রান্সক্রিপ্ট আবেদন", "url": "http://103.113.200.68/nu-app/", "icon": "🎓"})

            # Counts
            total_milestones += 1
            if is_comp:
                completed_milestones += 1
                phase_completed_count += 1
            elif status_type == "today":
                today_milestones += 1
            elif status_type == "upcoming":
                upcoming_milestones += 1
            elif status_type == "passed_unconfirmed":
                passed_unconfirmed_milestones += 1
            elif status_type == "no_info":
                missing_milestones += 1

            phase_milestones.append({
                "id": m_id,
                "title_bn": m_spec["title_bn"],
                "category": m_spec["category"],
                "raw_value": raw_val,
                "formatted_date": formatted_date,
                "status_label": status_label,
                "status_type": status_type,
                "badge_class": badge_styles.get(status_type, badge_styles["no_info"]),
                "is_completed": is_comp,
                "description": desc,
                "links": links
            })

        # Phase status
        phase_status = "pending"
        if phase_completed_count == len(phase_milestones) and len(phase_milestones) > 0:
            phase_status = "completed"
        elif any(m["status_type"] in ["today", "upcoming", "passed_unconfirmed"] or m["is_completed"] for m in phase_milestones):
            phase_status = "in_progress"

        evaluated_phases.append({
            "phase_id": p_def["phase_id"],
            "title_bn": p_def["title_bn"],
            "title_en": p_def["title_en"],
            "icon": p_def["icon"],
            "phase_status": phase_status,
            "completed_count": phase_completed_count,
            "total_count": len(phase_milestones),
            "milestones": phase_milestones
        })

    progress_pct = round((completed_milestones / total_milestones) * 100) if total_milestones > 0 else 0

    return {
        "record_id": rec.get("id"),
        "program_type": prog,
        "program_type_name": prog_bn,
        "part": p_part,
        "part_name_bn": part_bn,
        "semester": p_sem,
        "course_name": p_course,
        "examination_year": exam_year,
        "available_years": available_years or [exam_year] if exam_year else [],
        "heading": heading,
        "subheading": subheading,
        "updated_at": rec.get("updated_at") or "",
        "summary": {
            "total_milestones": total_milestones,
            "completed_milestones": completed_milestones,
            "upcoming_milestones": upcoming_milestones,
            "passed_unconfirmed_milestones": passed_unconfirmed_milestones,
            "missing_milestones": missing_milestones,
            "today_milestones": today_milestones,
            "progress_percentage": progress_pct,
            "progress_text": f"{to_bn_digits(completed_milestones)} / {to_bn_digits(total_milestones)} ধাপ নিশ্চিত সম্পন্ন ({to_bn_digits(progress_pct)}%)",
            "disclaimer": "তথ্যসূত্র: জাতীয় বিশ্ববিদ্যালয় পরীক্ষা নিয়ন্ত্রণ দপ্তর ও প্রশাসনিক পোর্টাল। তারিখ ও সময়সূচি পরিবর্তনশীল।"
        },
        "phases": evaluated_phases,
        "official_portals": [
            {"title": "ফলাফল আর্কাইভ পোর্টাল", "url": rec.get("revaluation_result_url") or "https://results.nu.ac.bd/", "icon": "📊"},
            {"title": "কলেজভিত্তিক ফলাফল অনুসন্ধান", "url": rec.get("college_wise_result_url") or "http://103.113.200.68/nu-app/search.php", "icon": "🏫"},
            {"title": "শিক্ষার্থী অনলাইন সেবা (সার্টিফিকেট/মার্কশিট/সংশোধন)", "url": "http://103.113.200.68/nu-app/", "icon": "🎓"},
            {"title": "ভর্তি বিষয়ক পোর্টাল", "url": "http://app11.nu.edu.bd/", "icon": "🎯"},
            {"title": "ইএমএস ফরম পূরণ পোর্টাল", "url": "http://ems.nu.ac.bd/", "icon": "📝"},
            {"title": "পরীক্ষা নিয়ন্ত্রণ সার্কুলার ও নোটিশ", "url": rec.get("source_url") or "https://www.nu.ac.bd/recent-news-notice.php", "icon": "📢"}
        ],
        "remarks": rec.get("remarks") or ""
    }


STATIC_CITATIONS = [
    SourceCitation(title="জাতীয় বিশ্ববিদ্যালয় ফলাফল ও পুনর্নিরীক্ষণ পোর্টাল", url="https://results.nu.ac.bd/", date="ফলাফল আর্কাইভ"),
    SourceCitation(title="কলেজভিত্তিক ফলাফল ও তথ্য অনুসন্ধান", url="http://103.113.200.68/nu-app/search.php", date="ERP ফলাফল সার্ভার"),
    SourceCitation(title="পরীক্ষা নিয়ন্ত্রণ দপ্তর ও অফিসিয়াল নোটিশ বোর্ড", url="https://www.nu.ac.bd/recent-news-notice.php", date="অফিসিয়াল সার্কুলার")
]

PROGRAM_CONFIG = {
    "Honours": {
        "bn_name": "অনার্স",
        "parts": ["Part 1", "Part 2", "Part 3", "Part 4"],
        "part_labels": {
            "Part 1": "১ম বর্ষ",
            "Part 2": "২য় বর্ষ",
            "Part 3": "৩য় বর্ষ",
            "Part 4": "৪র্থ বর্ষ"
        }
    },
    "Degree Pass": {
        "bn_name": "ডিগ্রি পাস",
        "parts": ["Part 1", "Part 2", "Part 3"],
        "part_labels": {
            "Part 1": "১ম বর্ষ",
            "Part 2": "২য় বর্ষ",
            "Part 3": "৩য় বর্ষ"
        }
    },
    "Master's": {
        "bn_name": "মাস্টার্স",
        "parts": ["Final", "Preliminary", "N/A"],
        "part_labels": {
            "Final": "শেষ পর্ব",
            "Preliminary": "প্রিলিমিনারি",
            "N/A": "মাস্টার্স কোর্স"
        }
    },
    "Professional": {
        "bn_name": "প্রফেশনাল কোর্স",
        "parts": ["Part 1", "Part 2", "Part 3", "Part 4"],
        "part_labels": {
            "Part 1": "১ম বর্ষ",
            "Part 2": "২য় বর্ষ",
            "Part 3": "৩য় বর্ষ",
            "Part 4": "৪র্থ বর্ষ"
        },
        "part_semesters": {
            "Part 1": ["Semester 1", "Semester 2"],
            "Part 2": ["Semester 3", "Semester 4"],
            "Part 3": ["Semester 5", "Semester 6"],
            "Part 4": ["Semester 7", "Semester 8"]
        }
    }
}

PROFESSIONAL_BRANCHES = [
    {
        "branch_id": "eng_tech",
        "title": "Technology, Engineering & Physical Sciences",
        "title_bn": "প্রযুক্তি, প্রকৌশল ও বিজ্ঞান শাখা",
        "icon": "🔬",
        "badge_color": "bg-blue-600",
        "courses": [
            {
                "code": "CSE",
                "name": "B.Sc. in Computer Science & Engineering (CSE)",
                "name_bn": "কম্পিউটার সায়েন্স অ্যান্ড ইঞ্জিনিয়ারিং",
                "icon": "💻",
                "color_bg": "from-blue-50/70 to-white hover:from-blue-100 hover:to-blue-50",
                "border": "border-blue-200 hover:border-blue-500",
                "badge_bg": "bg-blue-600 text-white",
                "text_accent": "text-blue-700",
                "keywords": ["cse", "computer science", "কম্পিউটার সায়েন্স", "কম্পিউটার সায়েন্স", "সিএসই"]
            },
            {
                "code": "ECE",
                "name": "B.Sc. in Electronics & Communication Engineering (ECE)",
                "name_bn": "ইলেকট্রনিক্স অ্যান্ড কমিউনিকেশন ইঞ্জিনিয়ারিং",
                "icon": "📡",
                "color_bg": "from-indigo-50/70 to-white hover:from-indigo-100 hover:to-indigo-50",
                "border": "border-indigo-200 hover:border-indigo-500",
                "badge_bg": "bg-indigo-600 text-white",
                "text_accent": "text-indigo-700",
                "keywords": ["ece", "electronics", "ইলেকট্রনিক্স", "ইসিই"]
            },
            {
                "code": "Aviation_Science",
                "name": "B.Sc. in Aeronautical & Aviation Science",
                "name_bn": "অ্যারোনটিক্যাল অ্যান্ড এভিয়েশন সায়েন্স",
                "icon": "✈️",
                "color_bg": "from-sky-50/70 to-white hover:from-sky-100 hover:to-sky-50",
                "border": "border-sky-200 hover:border-sky-500",
                "badge_bg": "bg-sky-600 text-white",
                "text_accent": "text-sky-700",
                "keywords": ["aeronautical", "aviation science", "এভিয়েশন সায়েন্স", "এভিয়েশন সায়েন্স", "অ্যারোনটিক্যাল"]
            }
        ]
    },
    {
        "branch_id": "textile_fashion",
        "title": "Textile, Apparel & Fashion Design",
        "title_bn": "টেক্সটাইল, অ্যাপারেল ও ফ্যাশন ডিজাইন শাখা",
        "icon": "🧵",
        "badge_color": "bg-emerald-600",
        "courses": [
            {
                "code": "TST",
                "name": "B.Sc. (Honours) in Textile Science & Technology (TST)",
                "name_bn": "টেক্সটাইল সায়েন্স অ্যান্ড টেকনোলজি",
                "icon": "👕",
                "color_bg": "from-emerald-50/70 to-white hover:from-emerald-100 hover:to-emerald-50",
                "border": "border-emerald-200 hover:border-emerald-500",
                "badge_bg": "bg-emerald-600 text-white",
                "text_accent": "text-emerald-700",
                "keywords": ["tst", "textile", "টেক্সটাইল", "টিএসটি"]
            },
            {
                "code": "AMT",
                "name": "B.Sc. in Apparel Manufacture & Technology (AMT)",
                "name_bn": "অ্যাপারেল ম্যানুফ্যাকচার অ্যান্ড টেকনোলজি",
                "icon": "🧵",
                "color_bg": "from-teal-50/70 to-white hover:from-teal-100 hover:to-teal-50",
                "border": "border-teal-200 hover:border-teal-500",
                "badge_bg": "bg-teal-600 text-white",
                "text_accent": "text-teal-700",
                "keywords": ["amt", "apparel", "অ্যাপারেল", "এএমটি"]
            },
            {
                "code": "FDT",
                "name": "B.Sc. in Fashion Design & Technology (FDT)",
                "name_bn": "ফ্যাশন ডিজাইন অ্যান্ড টেকনোলজি",
                "icon": "👗",
                "color_bg": "from-rose-50/70 to-white hover:from-rose-100 hover:to-rose-50",
                "border": "border-rose-200 hover:border-rose-500",
                "badge_bg": "bg-rose-600 text-white",
                "text_accent": "text-rose-700",
                "keywords": ["fdt", "fashion design", "ফ্যাশন ডিজাইন", "এফডিটি"]
            },
            {
                "code": "KMT",
                "name": "B.Sc. in Knitwear Manufacture & Technology (KMT)",
                "name_bn": "নিটওয়্যার ম্যানুফ্যাকচার অ্যান্ড টেকনোলজি",
                "icon": "🧶",
                "color_bg": "from-orange-50/70 to-white hover:from-orange-100 hover:to-orange-50",
                "border": "border-orange-200 hover:border-orange-500",
                "badge_bg": "bg-orange-600 text-white",
                "text_accent": "text-orange-700",
                "keywords": ["kmt", "knitwear", "নিটওয়্যার", "নিটওয়্যার", "কেএমটি"]
            }
        ]
    },
    {
        "branch_id": "business_mgmt",
        "title": "Business & Management",
        "title_bn": "ব্যবসায় ও ব্যবস্থাপনা শাখা",
        "icon": "💼",
        "badge_color": "bg-amber-600",
        "courses": [
            {
                "code": "BBA",
                "name": "BBA (Bachelor of Business Administration)",
                "name_bn": "ব্যাচেলর অব বিজনেস অ্যাডমিনিস্ট্রেশন (বিবিএ)",
                "icon": "📊",
                "color_bg": "from-amber-50/70 to-white hover:from-amber-100 hover:to-amber-50",
                "border": "border-amber-200 hover:border-amber-500",
                "badge_bg": "bg-amber-600 text-white",
                "text_accent": "text-amber-700",
                "keywords": ["bba", "বিবিএ", "business administration"]
            },
            {
                "code": "BBA_Aviation",
                "name": "BBA in Aviation Management",
                "name_bn": "এভিয়েশন ম্যানেজমেন্টে বিবিএ",
                "icon": "🛫",
                "color_bg": "from-yellow-50/70 to-white hover:from-yellow-100 hover:to-yellow-50",
                "border": "border-yellow-200 hover:border-yellow-500",
                "badge_bg": "bg-yellow-600 text-white",
                "text_accent": "text-yellow-700",
                "keywords": ["aviation management", "এভিয়েশন ম্যানেজমেন্ট", "এভিয়েশন ম্যানেজমেন্ট"]
            },
            {
                "code": "THM",
                "name": "Tourism & Hospitality Management (THM)",
                "name_bn": "ট্যুরিজম অ্যান্ড হসপিটালিটি ম্যানেজমেন্ট",
                "icon": "🏨",
                "color_bg": "from-lime-50/70 to-white hover:from-lime-100 hover:to-lime-50",
                "border": "border-lime-200 hover:border-lime-500",
                "badge_bg": "bg-lime-600 text-white",
                "text_accent": "text-lime-700",
                "keywords": ["thm", "tourism", "hospitality", "ট্যুরিজম", "হসপিটালিটি"]
            }
        ]
    },
    {
        "branch_id": "edu_media_arts",
        "title": "Education, Media & Arts",
        "title_bn": "শিক্ষা, মিডিয়া ও চারুকলা শাখা",
        "icon": "🎨",
        "badge_color": "bg-purple-600",
        "courses": [
            {
                "code": "BEd",
                "name": "Bachelor of Education (B.Ed. Honours)",
                "name_bn": "ব্যাচেলর অব এডুকেশন (বিএড)",
                "icon": "📚",
                "color_bg": "from-purple-50/70 to-white hover:from-purple-100 hover:to-purple-50",
                "border": "border-purple-200 hover:border-purple-500",
                "badge_bg": "bg-purple-600 text-white",
                "text_accent": "text-purple-700",
                "keywords": ["b.ed", "bed", "বিএড", "ব্যাচেলর অব এডুকেশন"]
            },
            {
                "code": "BFA",
                "name": "Bachelor of Fine Arts (BFA Honours)",
                "name_bn": "ব্যাচেলর অব ফাইন আর্টস (চারুকলা)",
                "icon": "🎨",
                "color_bg": "from-violet-50/70 to-white hover:from-violet-100 hover:to-violet-50",
                "border": "border-violet-200 hover:border-violet-500",
                "badge_bg": "bg-violet-600 text-white",
                "text_accent": "text-violet-700",
                "keywords": ["bfa", "fine arts", "চারুকলা", "বিএফএ"]
            },
            {
                "code": "TMS",
                "name": "Theatre & Media Studies (TMS)",
                "name_bn": "থিয়েটার অ্যান্ড মিডিয়া স্টাডিজ",
                "icon": "🎬",
                "color_bg": "from-fuchsia-50/70 to-white hover:from-fuchsia-100 hover:to-fuchsia-50",
                "border": "border-fuchsia-200 hover:border-fuchsia-500",
                "badge_bg": "bg-fuchsia-600 text-white",
                "text_accent": "text-fuchsia-700",
                "keywords": ["tms", "theatre", "media studies", "থিয়েটার", "থিয়েটার", "মিডিয়া স্টাডিজ", "মিডিয়া স্টাডিজ"]
            }
        ]
    },
    {
        "branch_id": "diploma_masters",
        "title": "Post-Graduate & Professional Diploma Programs",
        "title_bn": "ডিপ্লোমা ও স্নাতকোত্তর কোর্স",
        "icon": "📜",
        "badge_color": "bg-slate-700",
        "courses": [
            {
                "code": "MEd",
                "name": "Master of Education (M.Ed.)",
                "name_bn": "মাস্টার অব এডুকেশন",
                "icon": "🎓",
                "color_bg": "from-slate-50/70 to-white hover:from-slate-100 hover:to-slate-50",
                "border": "border-slate-200 hover:border-slate-500",
                "badge_bg": "bg-slate-700 text-white",
                "text_accent": "text-slate-800",
                "keywords": ["m.ed", "med", "এমএড", "মাস্টার অব এডুকেশন"]
            },
            {
                "code": "MSEd",
                "name": "Master of Special Education (MSEd)",
                "name_bn": "মাস্টার অব স্পেশাল এডুকেশন",
                "icon": "🧩",
                "color_bg": "from-cyan-50/70 to-white hover:from-cyan-100 hover:to-cyan-50",
                "border": "border-cyan-200 hover:border-cyan-500",
                "badge_bg": "bg-cyan-700 text-white",
                "text_accent": "text-cyan-800",
                "keywords": ["msed", "special education", "স্পেশাল এডুকেশন"]
            },
            {
                "code": "MPEd",
                "name": "Master of Physical Education (MPEd)",
                "name_bn": "মাস্টার অব ফিজিক্যাল এডুকেশন",
                "icon": "⚽",
                "color_bg": "from-emerald-50/70 to-white hover:from-emerald-100 hover:to-emerald-50",
                "border": "border-emerald-200 hover:border-emerald-500",
                "badge_bg": "bg-emerald-700 text-white",
                "text_accent": "text-emerald-800",
                "keywords": ["mped", "physical education", "ফিজিক্যাল এডুকেশন"]
            },
            {
                "code": "PGD_LIS",
                "name": "Post Graduate Diploma in Library & Information Science",
                "name_bn": "ডিপ্লোমা ইন লাইব্রেরি অ্যান্ড ইনফরমেশন সায়েন্স",
                "icon": "📖",
                "color_bg": "from-teal-50/70 to-white hover:from-teal-100 hover:to-teal-50",
                "border": "border-teal-200 hover:border-teal-500",
                "badge_bg": "bg-teal-700 text-white",
                "text_accent": "text-teal-800",
                "keywords": ["library science", "লাইব্রেরি", "লাইব্রেরী", "pgd-lis", "lis"]
            },
            {
                "code": "PGD_Sports",
                "name": "Post Graduate Diploma in Sports Science",
                "name_bn": "স্নাতকোত্তর ডিপ্লোমা ইন স্পোর্টস সায়েন্স",
                "icon": "🏆",
                "color_bg": "from-blue-50/70 to-white hover:from-blue-100 hover:to-blue-50",
                "border": "border-blue-200 hover:border-blue-500",
                "badge_bg": "bg-blue-700 text-white",
                "text_accent": "text-blue-800",
                "keywords": ["sports science", "স্পোর্টস সায়েন্স", "স্পোর্টস সায়েন্স", "pgd sports"]
            }
        ]
    }
]

SEMESTERS_CONFIG = [
    {"num": "১ম", "ord": "1st", "value": "1st Semester", "label": "১ম সেমিস্টার"},
    {"num": "২য়", "ord": "2nd", "value": "2nd Semester", "label": "২য় সেমিস্টার"},
    {"num": "৩য়", "ord": "3rd", "value": "3rd Semester", "label": "৩য় সেমিস্টার"},
    {"num": "৪র্থ", "ord": "4th", "value": "4th Semester", "label": "৪র্থ সেমিস্টার"},
    {"num": "৫ম", "ord": "5th", "value": "5th Semester", "label": "৫ম সেমিস্টার"},
    {"num": "৬ষ্ঠ", "ord": "6th", "value": "6th Semester", "label": "৬ষ্ঠ সেমিস্টার"},
    {"num": "৭ম", "ord": "7th", "value": "7th Semester", "label": "৭ম সেমিস্টার"},
    {"num": "৮ম", "ord": "8th", "value": "8th Semester", "label": "৮ম সেমিস্টার"},
]

def find_professional_course(query: str) -> Optional[Dict[str, Any]]:
    q_low = query.lower()
    for branch in PROFESSIONAL_BRANCHES:
        for course in branch["courses"]:
            c_code = course["code"].lower()
            if re.search(r'(?:\b|_)' + re.escape(c_code) + r'(?:\b|_)', q_low):
                return course
            if any(kw in q_low for kw in course["keywords"]):
                return course
            if course["name"].lower() in q_low or course["name_bn"] in query:
                return course
    return None

def find_semester(query: str) -> Optional[str]:
    q_low = query.lower()
    sem_match = re.search(r"(\d+)(?:st|nd|rd|th)?\s*(?:semester|সেমিস্টার)", q_low)
    if sem_match:
        n = int(sem_match.group(1))
        if 1 <= n <= 8:
            ords = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th", 6: "6th", 7: "7th", 8: "8th"}
            return f"{ords.get(n, str(n)+'th')} Semester"

    bn_map = {
        "১ম সেমিস্টার": "1st Semester", "1st semester": "1st Semester",
        "২য় সেমিস্টার": "2nd Semester", "২য় সেমিস্টার": "2nd Semester", "2nd semester": "2nd Semester",
        "৩য় সেমিস্টার": "3rd Semester", "৩য় সেমিস্টার": "3rd Semester", "3rd semester": "3rd Semester",
        "৪র্থ সেমিস্টার": "4th Semester", "৪থ সেমিস্টার": "4th Semester", "4th semester": "4th Semester",
        "৫ম সেমিস্টার": "5th Semester", "5th semester": "5th Semester",
        "৬ষ্ঠ সেমিস্টার": "6th Semester", "6th semester": "6th Semester",
        "৭ম সেমিস্টার": "7th Semester", "7th semester": "7th Semester",
        "৮ম সেমিস্টার": "8th Semester", "8th semester": "8th Semester",
    }
    for k, v in bn_map.items():
        if k in q_low:
            return v
    return None

def render_professional_courses_selection_cards() -> str:
    html = '''<div class="my-2 space-y-3 font-sans text-left">
  <div class="p-3.5 bg-gradient-to-r from-teal-800 to-emerald-900 text-white rounded-2xl shadow-xs flex items-center justify-between">
    <div>
      <div class="text-[10px] uppercase tracking-wider text-teal-200 font-bold">জাতীয় বিশ্ববিদ্যালয় বাংলাদেশ (nu.ac.bd)</div>
      <h3 class="text-sm sm:text-base font-bold text-white mt-0.5">🎓 প্রফেশনাল পরীক্ষা — শাখা ও কোর্স নির্বাচন করুন</h3>
      <p class="text-[11px] text-teal-100">প্রথমে আপনার কাঙ্ক্ষিত কোর্স নির্বাচন করুন, এরপর সেমিস্টারভিত্তিক পরীক্ষার তথ্য দেখতে পাবেন:</p>
    </div>
    <span class="text-2xl">💼</span>
  </div>'''

    for branch in PROFESSIONAL_BRANCHES:
        html += f'''
  <div class="space-y-1.5 pt-1">
    <div class="flex items-center gap-1.5 px-1">
      <span class="text-sm">{branch["icon"]}</span>
      <h4 class="text-xs font-bold text-slate-800">{branch["title_bn"]} <span class="text-[10px] text-slate-500 font-normal">({branch["title"]})</span></h4>
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">'''

        for c in branch["courses"]:
            html += f'''
      <div onclick="sendQuickQuestion('{c["code"]} পরীক্ষা তথ্য')" class="group p-2.5 rounded-xl border {c["border"]} bg-gradient-to-b {c["color_bg"]} hover:shadow-md transition-all cursor-pointer flex items-center gap-2.5">
        <div class="w-8 h-8 rounded-lg {c["badge_bg"]} text-white flex items-center justify-center text-base shrink-0 shadow-2xs group-hover:scale-105 transition-transform">
          {c["icon"]}
        </div>
        <div class="min-w-0 flex-1 text-left">
          <div class="text-[10px] font-bold uppercase tracking-wider {c["text_accent"]}">{c["code"]}</div>
          <div class="font-bold text-slate-900 text-xs truncate group-hover:{c["text_accent"]} transition">{c["name_bn"]}</div>
          <div class="text-[10px] text-slate-500 truncate">{c["name"]}</div>
        </div>
        <span class="text-slate-400 group-hover:translate-x-0.5 transition-transform text-xs">➔</span>
      </div>'''

        html += '''
    </div>
  </div>'''

    html += '''</div>'''
    return html.strip()

def render_professional_semesters_cards(course: dict) -> str:
    html = f'''<div class="my-2 space-y-3 font-sans text-left">
  <div class="p-3.5 bg-gradient-to-r from-teal-800 to-cyan-900 text-white rounded-2xl shadow-xs flex items-center justify-between">
    <div>
      <div class="text-[10px] uppercase tracking-wider text-teal-200 font-bold">জাতীয় বিশ্ববিদ্যালয় প্রফেশনাল পরীক্ষা</div>
      <h3 class="text-sm sm:text-base font-bold text-white mt-0.5">{course["icon"]} {course["name"]}</h3>
      <p class="text-[11px] text-teal-100">{course["name_bn"]} — অনুগ্রহ করে কাঙ্ক্ষিত সেমিস্টার নির্বাচন করুন:</p>
    </div>
    <span class="text-2xl">{course["icon"]}</span>
  </div>

  <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5">'''

    for sem in SEMESTERS_CONFIG:
        html += f'''
    <div onclick="sendQuickQuestion('{course["code"]} {sem["label"]} পরীক্ষা বিষয়ক তথ্য')" class="group relative overflow-hidden bg-gradient-to-b from-teal-50/70 to-white hover:from-teal-100 hover:to-teal-50 border border-teal-200 hover:border-teal-500 p-3 rounded-2xl shadow-xs hover:shadow-md transition-all cursor-pointer flex flex-col items-center justify-between text-center gap-1.5 aspect-square sm:aspect-auto sm:min-h-[110px]">
      <div class="flex items-center justify-between w-full">
        <span class="text-sm">📌</span>
        <span class="text-[10px] font-bold bg-white/90 text-teal-800 px-2 py-0.5 rounded-full border border-teal-200/80">{sem["ord"]}</span>
      </div>
      <div class="w-9 h-9 rounded-xl bg-teal-600 text-white font-bold text-xs flex items-center justify-center shadow-xs group-hover:scale-110 transition-transform my-0.5">
        {sem["num"]}
      </div>
      <div>
        <h5 class="font-bold text-slate-900 text-xs group-hover:text-teal-700 transition leading-snug">{sem["label"]}</h5>
        <p class="text-[10px] text-slate-500">{sem["value"]}</p>
      </div>
    </div>'''

    html += '''
  </div>
</div>'''
    return html.strip()


def render_program_selection_cards(program_type: str) -> str:
    """
    Renders small modern nice looking vertical cards for selecting specific parts / years
    when a student clicks or asks for an exam category (e.g. অনার্স পরীক্ষা বিষয়ক তথ্য).
    """
    if program_type == "Honours":
        title = "জাতীয় বিশ্ববিদ্যালয় — অনার্স পরীক্ষা বিষয়ক তথ্য"
        category_icon = "📘"
        grid_cols_class = "grid grid-cols-2 sm:grid-cols-4 gap-2.5"
        cards = [
            {
                "icon": "📘",
                "num": "১ম",
                "part_badge": "Part 1",
                "title": "অনার্স ১ম বর্ষ পরীক্ষা বিষয়ক তথ্য",
                "sub": "ইনকোর্স • ফরম পূরণ • পরীক্ষার রুটিন • ফলাফল • সনদ",
                "query": "অনার্স ১ম বর্ষ পরীক্ষা বিষয়ক তথ্য",
                "color_bg": "from-blue-50/70 to-white hover:from-blue-100 hover:to-blue-50",
                "border": "border-blue-200 hover:border-blue-500",
                "badge_bg": "bg-blue-600 text-white",
                "text_accent": "text-blue-700"
            },
            {
                "icon": "📘",
                "num": "২য়",
                "part_badge": "Part 2",
                "title": "অনার্স ২য় বর্ষ পরীক্ষা বিষয়ক তথ্য",
                "sub": "ইনকোর্স • ফরম পূরণ • পরীক্ষার রুটিন • ফলাফল • সনদ",
                "query": "অনার্স ২য় বর্ষ পরীক্ষা বিষয়ক তথ্য",
                "color_bg": "from-blue-50/70 to-white hover:from-blue-100 hover:to-blue-50",
                "border": "border-blue-200 hover:border-blue-500",
                "badge_bg": "bg-blue-600 text-white",
                "text_accent": "text-blue-700"
            },
            {
                "icon": "📘",
                "num": "৩য়",
                "part_badge": "Part 3",
                "title": "অনার্স ৩য় বর্ষ পরীক্ষা বিষয়ক তথ্য",
                "sub": "ইনকোর্স • ফরম পূরণ • পরীক্ষার রুটিন • ফলাফল • সনদ",
                "query": "অনার্স ৩য় বর্ষ পরীক্ষা বিষয়ক তথ্য",
                "color_bg": "from-blue-50/70 to-white hover:from-blue-100 hover:to-blue-50",
                "border": "border-blue-200 hover:border-blue-500",
                "badge_bg": "bg-blue-600 text-white",
                "text_accent": "text-blue-700"
            },
            {
                "icon": "📘",
                "num": "৪র্থ",
                "part_badge": "Part 4",
                "title": "অনার্স ৪থ বর্ষ পরীক্ষা বিষয়ক তথ্য",
                "sub": "ইনকোর্স • ফরম পূরণ • পরীক্ষার রুটিন • ফলাফল • সনদ",
                "query": "অনার্স ৪থ বর্ষ পরীক্ষা বিষয়ক তথ্য",
                "color_bg": "from-blue-50/70 to-white hover:from-blue-100 hover:to-blue-50",
                "border": "border-blue-200 hover:border-blue-500",
                "badge_bg": "bg-blue-600 text-white",
                "text_accent": "text-blue-700"
            }
        ]
    elif program_type == "Degree Pass":
        title = "জাতীয় বিশ্ববিদ্যালয় — ডিগ্রি পরীক্ষা বিষয়ক তথ্য"
        category_icon = "📗"
        grid_cols_class = "grid grid-cols-1 sm:grid-cols-3 gap-2.5"
        cards = [
            {
                "icon": "📗",
                "num": "১ম",
                "part_badge": "Part 1",
                "title": "ডিগ্রি ১ম বর্ষ পরীক্ষা বিষয়ক তথ্য",
                "sub": "ইনকোর্স • ফরম পূরণ • পরীক্ষার রুটিন • ফলাফল • সনদ",
                "query": "ডিগ্রি ১ম বর্ষ পরীক্ষা বিষয়ক তথ্য",
                "color_bg": "from-indigo-50/70 to-white hover:from-indigo-100 hover:to-indigo-50",
                "border": "border-indigo-200 hover:border-indigo-500",
                "badge_bg": "bg-indigo-600 text-white",
                "text_accent": "text-indigo-700"
            },
            {
                "icon": "📗",
                "num": "২য়",
                "part_badge": "Part 2",
                "title": "ডিগ্রি ২য় বর্ষ পরীক্ষা বিষয়ক তথ্য",
                "sub": "ইনকোর্স • ফরম পূরণ • পরীক্ষার রুটিন • ফলাফল • সনদ",
                "query": "ডিগ্রি ২য় বর্ষ পরীক্ষা বিষয়ক তথ্য",
                "color_bg": "from-indigo-50/70 to-white hover:from-indigo-100 hover:to-indigo-50",
                "border": "border-indigo-200 hover:border-indigo-500",
                "badge_bg": "bg-indigo-600 text-white",
                "text_accent": "text-indigo-700"
            },
            {
                "icon": "📗",
                "num": "৩য়",
                "part_badge": "Part 3",
                "title": "ডিগ্রি ৩য় বর্ষ পরীক্ষা বিষয়ক তথ্য",
                "sub": "ইনকোর্স • ফরম পূরণ • পরীক্ষার রুটিন • ফলাফল • সনদ",
                "query": "ডিগ্রি ৩য় বর্ষ পরীক্ষা বিষয়ক তথ্য",
                "color_bg": "from-indigo-50/70 to-white hover:from-indigo-100 hover:to-indigo-50",
                "border": "border-indigo-200 hover:border-indigo-500",
                "badge_bg": "bg-indigo-600 text-white",
                "text_accent": "text-indigo-700"
            }
        ]
    elif program_type == "Master's":
        title = "জাতীয় বিশ্ববিদ্যালয় — মাস্টার্স পরীক্ষা বিষয়ক তথ্য"
        category_icon = "📙"
        grid_cols_class = "grid grid-cols-1 sm:grid-cols-2 gap-2.5"
        cards = [
            {
                "icon": "📙",
                "num": "শেষ",
                "part_badge": "Final",
                "title": "মাস্টার্স শেষ পর্ব পরীক্ষা বিষয়ক তথ্য",
                "sub": "ইনকোর্স • ফরম পূরণ • পরীক্ষার রুটিন • ফলাফল • সনদ",
                "query": "মাস্টার্স শেষ পর্ব পরীক্ষা বিষয়ক তথ্য",
                "color_bg": "from-purple-50/70 to-white hover:from-purple-100 hover:to-purple-50",
                "border": "border-purple-200 hover:border-purple-500",
                "badge_bg": "bg-purple-600 text-white",
                "text_accent": "text-purple-700"
            },
            {
                "icon": "📙",
                "num": "প্রি",
                "part_badge": "Preliminary",
                "title": "মাস্টার্স প্রিলিমিনারি পরীক্ষা বিষয়ক তথ্য",
                "sub": "ইনকোর্স • ফরম পূরণ • পরীক্ষার রুটিন • ফলাফল • সনদ",
                "query": "মাস্টার্স প্রিলিমিনারি পরীক্ষা বিষয়ক তথ্য",
                "color_bg": "from-purple-50/70 to-white hover:from-purple-100 hover:to-purple-50",
                "border": "border-purple-200 hover:border-purple-500",
                "badge_bg": "bg-purple-600 text-white",
                "text_accent": "text-purple-700"
            }
        ]
    elif program_type == "Professional":
        return render_professional_courses_selection_cards()
    else:
        return ""

    cards_html = ""
    for c in cards:
        cards_html += f'''<div onclick="sendQuickQuestion('{c["query"]}')" class="group relative overflow-hidden bg-gradient-to-b {c["color_bg"]} border {c["border"]} p-3 rounded-2xl shadow-xs hover:shadow-md transition-all cursor-pointer flex flex-col items-center justify-between text-center gap-1.5 aspect-square sm:aspect-auto sm:min-h-[125px]">
  <div class="flex items-center justify-between w-full">
    <span class="text-base">{c["icon"]}</span>
    <span class="text-[10px] font-bold bg-white/90 text-slate-700 px-2 py-0.5 rounded-full border border-slate-200/80">{c["part_badge"]}</span>
  </div>
  <div class="w-9 h-9 rounded-xl {c["badge_bg"]} font-bold text-xs flex items-center justify-center shadow-xs group-hover:scale-110 transition-transform my-0.5">
    {c["num"]}
  </div>
  <div>
    <h4 class="font-bold text-slate-900 text-xs sm:text-sm group-hover:{c["text_accent"]} transition leading-tight">{c["title"]}</h4>
    <p class="text-[10px] text-slate-500 mt-0.5 line-clamp-1">{c["sub"]}</p>
  </div>
  <div class="text-[11px] font-bold {c["text_accent"]} flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
    <span>সময়সূচি ও ফলাফল</span>
    <span>➔</span>
  </div>
</div>'''

    wrapper = f'''<div class="my-2 space-y-2 text-left font-sans">
  <div class="p-3 rounded-2xl bg-gradient-to-r from-slate-900 to-slate-800 text-white flex items-center justify-between shadow-xs">
    <div class="flex items-center gap-2">
      <span class="text-lg">{category_icon}</span>
      <div>
        <h3 class="text-xs sm:text-sm font-bold text-white leading-tight">{title}</h3>
        <p class="text-[10px] text-slate-300">তথ্য দেখতে নিচের যেকোনো বর্ষ বা পর্বে ক্লিক করুন</p>
      </div>
    </div>
    <button onclick="sendQuickQuestion('মূল মেনু')" class="text-xs bg-white/20 hover:bg-white/30 text-white border border-white/30 px-2.5 py-1 rounded-xl font-bold transition flex items-center gap-1 cursor-pointer">
      <span>🏠</span>
      <span>মূল মেনু</span>
    </button>
  </div>
  <div class="{grid_cols_class}">
    {cards_html}
  </div>
</div>'''
    return wrapper.strip()


def get_milestone_badge_class(status_type: str) -> str:
    """Returns subtle muted Apple-style badge classes matching monochromatic theme."""
    if status_type == "completed":
        return "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border-emerald-200/60 dark:border-emerald-800/60"
    if status_type == "published":
        return "bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border-blue-200/60 dark:border-blue-800/60"
    if status_type == "today":
        return "bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border-amber-200/60 dark:border-amber-800/60"
    if status_type == "passed_unconfirmed":
        return "bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border-rose-200/60 dark:border-rose-800/60"
    if status_type == "upcoming":
        return "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200/60 dark:border-slate-700/60"
    return "bg-slate-50 dark:bg-slate-800/50 text-slate-400 dark:text-slate-500 border-slate-200/40 dark:border-slate-700/40"


def render_exam_card_timeline_bar(item: Dict[str, Any]) -> str:
    """
    Renders an Apple-inspired horizontal milestone timeline with a slim progress bar track,
    neat circular nodes (১ to ৬ or ✓), bold typography, minimalist dates, and subtle status badges.
    Contains no boxy step cards or alternating connector sticks.
    """
    today_bd = get_bd_now().date()

    # 1. Incourse
    incourse_raw = (item.get("incourse_exam_date") or item.get("incourse_marks_deadline") or "").strip()
    status_1, type_1, comp_1, desc_1 = evaluate_milestone_status("incourse_exam_date", incourse_raw, item, today_bd)
    date_1 = format_user_facing_date(incourse_raw, parse_date_str(incourse_raw))

    # 2. Form fillup
    form_raw = (item.get("form_fillup_deadline") or item.get("form_fillup_start_date") or "").strip()
    status_2, type_2, comp_2, desc_2 = evaluate_milestone_status("form_fillup_deadline", form_raw, item, today_bd)
    date_2 = format_user_facing_date(form_raw, parse_date_str(form_raw))

    # 3. Routine & Admit Card
    routine_raw = (item.get("routine_publication_date") or item.get("admit_card_date") or "").strip()
    status_3, type_3, comp_3, desc_3 = evaluate_milestone_status("routine_publication_date", routine_raw, item, today_bd)
    date_3 = "রুটিন প্রকাশিত" if routine_raw.startswith("http") else format_user_facing_date(routine_raw, parse_date_str(routine_raw))

    # 4. Exam period
    exam_raw = (item.get("exam_date") or item.get("last_exam_date") or "").strip()
    status_4, type_4, comp_4, desc_4 = evaluate_milestone_status("exam_date", exam_raw, item, today_bd)
    date_4 = format_user_facing_date(exam_raw, parse_date_str(exam_raw))

    # 5. Results
    pub_flag = (item.get("results_published") or "").strip().lower()
    res_comp = pub_flag in ["yes", "true", "1", "হ্যাঁ", "সম্পন্ন", "প্রকাশিত"]
    res_raw = (item.get("actual_result_date") or item.get("probable_result_date") or "").strip()
    if res_comp:
        status_5, type_5, comp_5, desc_5 = "প্রকাশিত", "published", True, "ফলাফল আনুষ্ঠানিকভাবে প্রকাশ করা হয়েছে।"
    else:
        status_5, type_5, comp_5, desc_5 = evaluate_milestone_status("probable_result_date", res_raw, item, today_bd)
    date_5 = format_user_facing_date(res_raw, parse_date_str(res_raw)) if res_raw else ("প্রকাশিত" if res_comp else "অপেক্ষমাণ")

    # 6. Certificates & Marksheet
    doc_flag = (item.get("documents_printed") or "").strip().lower()
    doc_comp = doc_flag in ["yes", "true", "1", "হ্যাঁ", "সম্পন্ন"]
    doc_raw = (item.get("document_printing_date") or "").strip()
    if doc_comp:
        status_6, type_6, comp_6, desc_6 = "সম্পন্ন", "completed", True, "মূল মার্কশিট ও সনদ মুদ্রণ সম্পন্ন হয়েছে।"
    else:
        status_6, type_6, comp_6, desc_6 = evaluate_milestone_status("document_printing_date", doc_raw, item, today_bd)
    date_6 = format_user_facing_date(doc_raw, parse_date_str(doc_raw)) if doc_raw else ("সম্পন্ন" if doc_comp else "অপেক্ষমাণ")

    milestones = [
        {
            "id": "1",
            "title": "ইনকোর্স পরীক্ষা",
            "sub": "ইনকোর্স ও নম্বর জমা",
            "date": date_1,
            "status": status_1,
            "type": type_1,
            "comp": comp_1,
            "badge_class": get_milestone_badge_class(type_1)
        },
        {
            "id": "2",
            "title": "ফরম পূরণ",
            "sub": "অনলাইন ফরম ও ফি",
            "date": date_2,
            "status": status_2,
            "type": type_2,
            "comp": comp_2,
            "badge_class": get_milestone_badge_class(type_2)
        },
        {
            "id": "3",
            "title": "রুটিন ও প্রবেশপত্র",
            "sub": "সময়সূচি ও এডমিট কার্ড",
            "date": date_3,
            "status": status_3,
            "type": type_3,
            "comp": comp_3,
            "badge_class": get_milestone_badge_class(type_3)
        },
        {
            "id": "4",
            "title": "মূল পরীক্ষা",
            "sub": "তত্ত্বীয় ও ব্যবহারিক পরীক্ষা",
            "date": date_4,
            "status": status_4,
            "type": type_4,
            "comp": comp_4,
            "badge_class": get_milestone_badge_class(type_4)
        },
        {
            "id": "5",
            "title": "ফলাফল প্রকাশ",
            "sub": "ফলাফল ও পুনঃনিরীক্ষণ",
            "date": date_5,
            "status": status_5,
            "type": type_5,
            "comp": comp_5,
            "badge_class": get_milestone_badge_class(type_5)
        },
        {
            "id": "6",
            "title": "সনদ ও মার্কশিট",
            "sub": "মূল মার্কশিট ও সনদ বিতরণ",
            "date": date_6,
            "status": status_6,
            "type": type_6,
            "comp": comp_6,
            "badge_class": get_milestone_badge_class(type_6)
        }
    ]

    completed_count = sum(1 for m in milestones if m["comp"])
    if doc_comp:
        progress_pct = 100
        track_fill_pct = 100
    elif res_comp:
        progress_pct = 83
        track_fill_pct = 83
    elif comp_4 or (type_4 in ["today", "passed_unconfirmed"]):
        progress_pct = 66
        track_fill_pct = 66
    elif comp_3 or routine_raw.startswith("http") or (type_3 in ["today", "passed_unconfirmed"]):
        progress_pct = 50
        track_fill_pct = 50
    elif comp_2 or (type_2 in ["today", "passed_unconfirmed"]):
        progress_pct = 33
        track_fill_pct = 33
    elif comp_1 or (type_1 in ["today", "passed_unconfirmed"]):
        progress_pct = 20
        track_fill_pct = 20
    else:
        progress_pct = 10
        track_fill_pct = 10

    # In a 6-node grid, the first node center is at 8.33% and the last is at 91.67%.
    # The total span between node 1 and node 6 is 83.34%.
    effective_track_pct = round((track_fill_pct / 100.0) * 83.34, 1)

    bn_numerals = ["১", "২", "৩", "৪", "৫", "৬"]
    node_cols = []
    detail_cols = []
    for idx, m in enumerate(milestones):
        bn_num = bn_numerals[idx]
        is_comp = m["comp"]
        is_today = (m["type"] == "today")
        icon = "✓" if is_comp else bn_num

        if is_comp:
            node_style = "bg-emerald-600 text-white border-2 border-white dark:border-slate-800 shadow-2xs"
        elif is_today:
            node_style = "bg-amber-500 text-white ring-4 ring-amber-200 dark:ring-amber-900/60 animate-pulse border-2 border-white dark:border-slate-800 shadow-2xs"
        elif m["type"] == "published":
            node_style = "bg-blue-600 text-white border-2 border-white dark:border-slate-800 shadow-2xs"
        elif m["type"] == "passed_unconfirmed":
            node_style = "bg-rose-500 text-white border-2 border-white dark:border-slate-800 shadow-2xs"
        elif m["type"] == "upcoming":
            node_style = "bg-slate-700 dark:bg-slate-300 text-white dark:text-slate-900 border-2 border-white dark:border-slate-800 shadow-2xs"
        else:
            node_style = "bg-slate-300 dark:bg-slate-600 text-slate-600 dark:text-slate-300 border-2 border-white dark:border-slate-800 shadow-2xs"

        node_cols.append(
            f'<div class="flex items-center justify-center">'
            f'<div class="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold transition hover:scale-110 cursor-default {node_style}" title="{m["title"]}: {m["date"]} ({m["status"]})">{icon}</div>'
            f'</div>'
        )

        detail_cols.append(
            f'<div class="flex flex-col items-center text-center px-1">'
            f'<div class="text-[12px] sm:text-[13px] font-bold text-slate-900 dark:text-white tracking-tight leading-snug">{m["title"]}</div>'
            f'<div class="text-[10px] sm:text-[11px] font-medium text-slate-500 dark:text-slate-400 mt-1 truncate max-w-full">{m["date"]}</div>'
            f'<div class="mt-1.5"><span class="inline-block text-[9.5px] px-2 py-0.5 rounded-full font-medium border {m["badge_class"]}">{m["status"]}</span></div>'
            f'<div class="text-[9.5px] text-slate-400 dark:text-slate-500 mt-1 truncate max-w-full">{m["sub"]}</div>'
            f'</div>'
        )

    node_row_html = "".join(node_cols)
    detail_cols_html = "".join(detail_cols)

    timeline_html = (
        f'<div class="bg-[var(--surface)] dark:bg-[#2C2C2E] border border-slate-200/80 dark:border-white/10 rounded-2xl p-4 shadow-2xs">'
        f'<div class="flex items-center justify-between pb-2.5 mb-3 border-b border-slate-200/60 dark:border-white/10 flex-wrap gap-2">'
        f'<div class="flex items-center gap-2">'
        f'<span class="w-6 h-6 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-xs font-bold">📈</span>'
        f'<div>'
        f'<h4 class="text-xs sm:text-sm font-bold text-slate-900 dark:text-white tracking-tight">পরীক্ষা মাইলস্টোন টাইমলাইন ও অগ্রগতি</h4>'
        f'<p class="text-[10px] text-slate-500 dark:text-slate-400">একাডেমিক ক্যালেন্ডার ও ধাপভিত্তিক বিবরণ</p>'
        f'</div>'
        f'</div>'
        f'<div class="flex items-center gap-1.5 text-xs font-semibold">'
        f'<span class="px-2.5 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 border border-emerald-200/70 dark:border-emerald-800/60">অগ্রগতি: {progress_pct}%</span>'
        f'<span class="px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200/70 dark:border-slate-700/60 text-[11px]">{to_bn_digits(completed_count)} / ৬ ধাপ সম্পন্ন</span>'
        f'</div>'
        f'</div>'
        f'<div class="overflow-x-auto thin-scrollbar pb-1 pt-1">'
        f'<div class="min-w-[620px] px-1 py-1">'
        f'<div class="relative flex items-center mb-3">'
        f'<div class="absolute left-[8.33%] right-[8.33%] h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full"></div>'
        f'<div class="absolute left-[8.33%] h-1.5 bg-gradient-to-r from-emerald-500 via-teal-500 to-indigo-600 rounded-full transition-all duration-500" style="width: {effective_track_pct}%;"></div>'
        f'<div class="relative w-full grid grid-cols-6 z-10">{node_row_html}</div>'
        f'</div>'
        f'<div class="grid grid-cols-6 gap-2 text-center">{detail_cols_html}</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    return timeline_html

def format_exam_card_markdown(item: Dict[str, Any]) -> str:
    """
    Renders an official Academic Examination Card as Small Modern Nice Looking Vertical Cards.
    Empty fields display neutral notice 'তথ্য এখনো প্রকাশ করা হয়নি।'
    """
    prog = item.get("program_type", "Honours")
    prog_safe = str(prog).replace("'", "\\'")
    prog_safe = str(prog).replace("'", "\\'")
    course_name = item.get("course_name") or ""
    prog_bn = item.get("program_type_name") or PROGRAM_CONFIG.get(prog, {}).get("bn_name", prog)
    year = item.get("examination_year") or "নির্ধারিত হয়নি"
    part = item.get("part", "N/A")
    sem = item.get("semester", "N/A")

    title_parts = [prog_bn]
    if prog == "Professional":
        prof_c = find_professional_course(course_name or part)
        if prof_c:
            title_parts.append(f"{prof_c['name_bn']} ({prof_c['code']})")
        elif course_name:
            title_parts.append(course_name)
        elif part and part != "N/A":
            title_parts.append(part)
        if sem and sem != "N/A":
            title_parts.append(f"সেমিস্টার: {sem}")
    else:
        if part and part != "N/A":
            part_bn = PROGRAM_CONFIG.get(prog, {}).get("part_labels", {}).get(part, part)
            title_parts.append(part_bn)
        if sem and sem != "N/A":
            title_parts.append(f"সেমিস্টার: {sem}")

    header = " — ".join(title_parts)
    neutral = "তথ্য এখনো প্রকাশ করা হয়নি।"

    # Section Values
    incourse_date = item.get("incourse_exam_date") or neutral
    incourse_deadline = item.get("incourse_marks_deadline") or neutral
    form_start = item.get("form_fillup_start_date") or ""
    form_deadline = item.get("form_fillup_deadline") or neutral
    form_fillup_display = f"{form_start} হতে {form_deadline}" if form_start and form_deadline != neutral else form_deadline

    exam_date = item.get("exam_date") or neutral
    routine = item.get("routine_publication_date") or neutral
    admit_card = item.get("admit_card_date") or neutral
    last_exam = item.get("last_exam_date") or neutral
    practical_start = item.get("practical_marks_start_date") or ""
    practical_deadline = item.get("practical_marks_deadline") or neutral
    practical_display = f"{practical_start} হতে {practical_deadline}" if practical_start and practical_deadline != neutral else practical_deadline

    prob_result = item.get("probable_result_date") or neutral
    actual_result = item.get("actual_result_date") or neutral
    res_pub = item.get("results_published", "No")
    is_pub_yes = str(res_pub).lower() in ["yes", "true", "1", "হ্যাঁ"]
    pub_badge_text = "✅ ফলাফল প্রকাশিত" if is_pub_yes else "⏳ ফল এখনও প্রকাশিত হয়নি"
    pub_badge_class = "bg-emerald-500/20 text-emerald-200 border border-emerald-400/30" if is_pub_yes else "bg-amber-500/20 text-amber-200 border border-amber-400/30"

    rescrutiny_start = item.get("rescrutiny_start_date") or ""
    rescrutiny_deadline = item.get("rescrutiny_deadline") or neutral
    rescrutiny_apply_display = f"{rescrutiny_start} হতে {rescrutiny_deadline}" if rescrutiny_start and rescrutiny_deadline != neutral else rescrutiny_deadline
    rescrutiny_result = item.get("rescrutiny_result_date") or neutral

    doc_printing = item.get("document_printing_date") or neutral
    doc_printed = item.get("documents_printed", "No")
    is_doc_yes = str(doc_printed).lower() in ["yes", "true", "1", "হ্যাঁ"]
    printed_badge_text = "✅ মুদ্রণ সম্পন্ন ও বিতরণ চলছে" if is_doc_yes else "⏳ মুদ্রণ অপেক্ষমান"
    printed_badge_class = "text-emerald-700 bg-emerald-50 border-emerald-200" if is_doc_yes else "text-slate-600 bg-slate-100 border-slate-200"

    reval_link = item.get("revaluation_result_url") or "https://results.nu.ac.bd/"
    college_link = item.get("college_wise_result_url") or "http://103.113.200.68/nu-app/search.php"
    remarks = item.get("remarks") or ""

    routine_display = f'<a href="{routine}" target="_blank" class="text-blue-600 hover:underline font-bold inline-flex items-center gap-1">রুটিন দেখুন ↗</a>' if routine.startswith("http") else routine

    remarks_html = ""
    if remarks:
        remarks_html = f'''<div class="bg-amber-50 border border-amber-200 rounded-xl p-3 shadow-2xs">
  <div class="flex items-center gap-2 text-amber-800 font-bold text-xs pb-1 mb-1 border-b border-amber-200/60">
    <span>💡</span>
    <span>বিশেষ নির্দেশনা / দ্রষ্টব্য</span>
  </div>
  <p class="text-xs text-amber-900 leading-relaxed">{remarks}</p>
</div>'''

    # Deterministic timeline ID for collapsible container
    rec_id = str(item.get("id") or "")
    prog_id = str(item.get("program_type") or "")
    year_id = str(item.get("examination_year") or "")
    part_id = str(item.get("part") or "")
    hash_seed = f"{rec_id}_{prog_id}_{year_id}_{part_id}"
    raw_hash = abs(hash(hash_seed)) % 1000000
    clean_prog = re.sub(r'[^a-zA-Z0-9]', '', prog_id) or "exam"
    timeline_id = f"timeline-collapse-{clean_prog}-{raw_hash}"

    toggle_timeline_btn_html = (
        f'<div class="pt-1 pb-0.5">'
        f'<button type="button" '
        f'onclick="if(window.toggleExamTimeline){{window.toggleExamTimeline(\'{timeline_id}\', this);}}else{{var el=document.getElementById(\'{timeline_id}\');if(el){{var isH=el.classList.toggle(\'hidden\');var lbl=this.querySelector(\'.timeline-toggle-label\');var ic=this.querySelector(\'.timeline-toggle-icon\');if(lbl)lbl.textContent=isH?\'📊 পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন\':\'📊 পরীক্ষার টাইমলাইন ও ধাপসমূহ লুকান\';if(ic)ic.textContent=isH?\'↓\':\'↑\';this.setAttribute(\'aria-expanded\', !isH);}}}}" '
        f'class="w-full py-2.5 px-4 rounded-xl border border-slate-200/80 dark:border-white/10 bg-slate-50 hover:bg-slate-100 dark:bg-slate-800/80 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200 text-xs font-semibold shadow-2xs hover:shadow-xs transition-all flex items-center justify-between cursor-pointer group" '
        f'aria-expanded="false">'
        f'<span class="flex items-center gap-2">'
        f'<span class="timeline-toggle-label font-bold text-slate-800 dark:text-slate-200">📊 পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন</span>'
        f'</span>'
        f'<span class="timeline-toggle-icon text-xs text-slate-500 dark:text-slate-400 group-hover:text-slate-800 dark:group-hover:text-slate-200 font-bold transition-transform">↓</span>'
        f'</button>'
        f'</div>'
    )

    timeline_container_html = (
        f'<div id="{timeline_id}" class="hidden transition-all duration-300">'
        f'{render_exam_card_timeline_bar(item)}'
        f'</div>'
    )

    html_cards = f'''<div class="my-2 space-y-2.5 text-left font-sans">
  <!-- Header Card -->
  <div class="p-3.5 rounded-2xl bg-gradient-to-r from-blue-900 via-indigo-900 to-blue-950 text-white shadow-xs border border-blue-800">
    <div class="flex items-center justify-between flex-wrap gap-2">
      <div>
        <div class="text-[10px] tracking-wider uppercase text-blue-200 font-semibold flex items-center gap-1.5">
          <span>🏛️</span>
          <span>জাতীয় বিশ্ববিদ্যালয় বাংলাদেশ</span>
        </div>
        <h3 class="text-base font-bold text-white mt-0.5 flex items-center gap-1.5">
          <span>🎓</span>
          <span>{header} — পরীক্ষা বিষয়ক তথ্য</span>
        </h3>
      </div>
      <div class="flex items-center gap-1.5 flex-wrap">
        <span class="text-xs bg-white/15 text-white font-semibold px-2.5 py-1 rounded-full border border-white/20">
          পরীক্ষার বছর: <strong>{year}</strong>
        </span>
        <span class="text-xs px-2.5 py-1 rounded-full font-semibold {pub_badge_class}">
          {pub_badge_text}
        </span>
      </div>
    </div>
  </div>

  <!-- On-Demand Collapsible Timeline -->
  {toggle_timeline_btn_html}
  {timeline_container_html}

  <!-- Small Modern Vertical Cards Grid -->
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">

    <!-- Card 1: 📝 ইনকোর্স ও ফরম পূরণ -->
    <div class="bg-white border border-slate-200 rounded-xl p-3 shadow-2xs hover:shadow-xs transition">
      <div class="flex items-center gap-2 pb-1.5 mb-2 border-b border-slate-100 text-indigo-700 font-bold text-xs">
        <span class="w-6 h-6 rounded-lg bg-indigo-50 flex items-center justify-center text-sm">📝</span>
        <span>ইনকোর্স ও ফরম পূরণ</span>
      </div>
      <div class="space-y-1.5 text-xs">
        <div class="flex justify-between items-start gap-2">
          <span class="text-slate-500 shrink-0">ইনকোর্স পরীক্ষা:</span>
          <span class="font-semibold text-slate-800 text-right">{incourse_date}</span>
        </div>
        <div class="flex justify-between items-start gap-2">
          <span class="text-slate-500 shrink-0">ইনকোর্স নম্বর শেষ সময়:</span>
          <span class="font-semibold text-slate-800 text-right">{incourse_deadline}</span>
        </div>
        <div class="flex justify-between items-start gap-2">
          <span class="text-slate-500 shrink-0">ফরম পূরণ সময়সীমা:</span>
          <span class="font-semibold text-slate-800 text-right">{form_fillup_display}</span>
        </div>
      </div>
    </div>

    <!-- Card 2: 📅 পরীক্ষা ও রুটিনের সময়সূচি -->
    <div class="bg-white border border-slate-200 rounded-xl p-3 shadow-2xs hover:shadow-xs transition">
      <div class="flex items-center gap-2 pb-1.5 mb-2 border-b border-slate-100 text-blue-700 font-bold text-xs">
        <span class="w-6 h-6 rounded-lg bg-blue-50 flex items-center justify-center text-sm">📅</span>
        <span>পরীক্ষা ও রুটিনের সময়সূচি</span>
      </div>
      <div class="space-y-1.5 text-xs">
        <div class="flex justify-between items-start gap-2">
          <span class="text-slate-500 shrink-0">পরীক্ষা শুরুর তারিখ:</span>
          <span class="font-semibold text-blue-900 text-right">{exam_date}</span>
        </div>
        <div class="flex justify-between items-start gap-2">
          <span class="text-slate-500 shrink-0">রুটিন প্রকাশ:</span>
          <span class="font-semibold text-blue-700 text-right">{routine_display}</span>
        </div>
        <div class="flex justify-between items-start gap-2">
          <span class="text-slate-500 shrink-0">প্রবেশপত্র (Admit Card):</span>
          <span class="font-semibold text-slate-800 text-right">{admit_card}</span>
        </div>
        <div class="flex justify-between items-start gap-2">
          <span class="text-slate-500 shrink-0">তত্ত্বীয় শেষ পরীক্ষা:</span>
          <span class="font-semibold text-slate-800 text-right">{last_exam}</span>
        </div>
        <div class="flex justify-between items-start gap-2">
          <span class="text-slate-500 shrink-0">ব্যবহারিক নম্বর শেষ সময়:</span>
          <span class="font-semibold text-slate-800 text-right">{practical_display}</span>
        </div>
      </div>
    </div>

    <!-- Card 3: 📊 ফলাফল ও পুনর্নিরীক্ষণ -->
    <div class="bg-white border border-slate-200 rounded-xl p-3 shadow-2xs hover:shadow-xs transition">
      <div class="flex items-center gap-2 pb-1.5 mb-2 border-b border-slate-100 text-emerald-700 font-bold text-xs">
        <span class="w-6 h-6 rounded-lg bg-emerald-50 flex items-center justify-center text-sm">📊</span>
        <span>ফলাফল ও পুনর্নিরীক্ষণ</span>
      </div>
      <div class="space-y-1.5 text-xs">
        <div class="flex justify-between items-start gap-2">
          <span class="text-slate-500 shrink-0">সম্ভাব্য ফল প্রকাশ:</span>
          <span class="font-semibold text-slate-800 text-right">{prob_result}</span>
        </div>
        <div class="flex justify-between items-start gap-2">
          <span class="text-slate-500 shrink-0">প্রকৃত ফল প্রকাশের তারিখ:</span>
          <span class="font-semibold text-emerald-800 text-right">{actual_result}</span>
        </div>
        <div class="flex justify-between items-start gap-2">
          <span class="text-slate-500 shrink-0">ফলাফল প্রকাশিত:</span>
          <span class="font-semibold text-right">{pub_badge_text}</span>
        </div>
        <div class="flex justify-between items-start gap-2">
          <span class="text-slate-500 shrink-0">পুনর্নিরীক্ষণ আবেদন:</span>
          <span class="font-semibold text-slate-800 text-right">{rescrutiny_apply_display}</span>
        </div>
        <div class="flex justify-between items-start gap-2">
          <span class="text-slate-500 shrink-0">পুনর্নিরীক্ষণের ফল:</span>
          <span class="font-semibold text-slate-800 text-right">{rescrutiny_result}</span>
        </div>
      </div>
    </div>

    <!-- Card 4: 📜 সনদ ও মার্কশিট -->
    <div class="bg-white border border-slate-200 rounded-xl p-3 shadow-2xs hover:shadow-xs transition">
      <div class="flex items-center gap-2 pb-1.5 mb-2 border-b border-slate-100 text-purple-700 font-bold text-xs">
        <span class="w-6 h-6 rounded-lg bg-purple-50 flex items-center justify-center text-sm">📜</span>
        <span>সনদ ও মার্কশিট বিতরণ</span>
      </div>
      <div class="space-y-1.5 text-xs">
        <div class="flex justify-between items-start gap-2">
          <span class="text-slate-500 shrink-0">মুদ্রণের তারিখ:</span>
          <span class="font-semibold text-slate-800 text-right">{doc_printing}</span>
        </div>
        <div class="flex justify-between items-start gap-2">
          <span class="text-slate-500 shrink-0">মুদ্রণ স্ট্যাটাস:</span>
          <span class="font-semibold {printed_badge_class} px-2 py-0.5 rounded text-[11px] border">{printed_badge_text}</span>
        </div>
      </div>
    </div>

  </div>

  {remarks_html}

  <!-- Card 5: 🔗 সরাসরি পোর্টাল লিংকসমূহ -->
  <div class="bg-slate-50 border border-slate-200 rounded-xl p-3 flex flex-wrap items-center justify-between gap-2 text-xs">
    <div class="flex items-center gap-2 flex-wrap">
      <span class="font-bold text-slate-700 flex items-center gap-1.5">
        <span>🔗</span>
        <span>অফিসিয়াল পোর্টাল:</span>
      </span>
      <button onclick="openTimelineView('{prog_safe}', '{part}', '{year}', '{course_name}', '{sem}')" class="bg-[#DC2626] hover:bg-[#B91C1C] text-white font-semibold px-3 py-1 rounded-lg text-xs shadow-2xs transition inline-flex items-center gap-1 cursor-pointer">
        <span>📅 টাইমলাইন ও অগ্রগতি দেখুন</span>
        <span>→</span>
      </button>
    </div>
    <div class="flex flex-wrap gap-1.5">
      <a href="{reval_link}" target="_blank" class="bg-white hover:bg-blue-50 text-blue-700 border border-blue-200 px-2.5 py-1 rounded-lg font-semibold transition shadow-2xs inline-flex items-center gap-1">
        <span>ফলাফল পোর্টাল</span>
        <span>↗</span>
      </a>
      <a href="{college_link}" target="_blank" class="bg-white hover:bg-indigo-50 text-indigo-700 border border-indigo-200 px-2.5 py-1 rounded-lg font-semibold transition shadow-2xs inline-flex items-center gap-1">
        <span>কলেজ রেজাল্ট</span>
        <span>↗</span>
      </a>
      <a href="https://www.nu.ac.bd/recent-news-notice.php" target="_blank" class="bg-white hover:bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-1 rounded-lg font-semibold transition shadow-2xs inline-flex items-center gap-1">
        <span>নোটিশ বোর্ড</span>
        <span>↗</span>
      </a>
    </div>
  </div>
</div>'''
    return html_cards.strip()

def render_empty_exam_card(header_title: str, exam_year: Optional[str] = None) -> str:
    """
    Renders clean modern alert card when exam info is not yet published in database.
    """
    year_str = f"পরীক্ষার সাল: **`{exam_year}`**" if exam_year else "উক্ত শিক্ষাবর্ষ"
    return f'''<div class="my-2 space-y-2.5 text-left font-sans">
  <div class="p-4 rounded-2xl bg-amber-50/80 border border-amber-200 shadow-2xs">
    <div class="flex items-center gap-2 text-amber-800 font-bold text-sm mb-1.5">
      <span>⚠️</span>
      <span>{header_title} — তথ্য এখনো প্রকাশ করা হয়নি।</span>
    </div>
    <p class="text-xs text-slate-700 leading-relaxed">
      {year_str}-এর জন্য পরীক্ষা নিয়ন্ত্রণ দপ্তর কর্তৃক স্থানীয় ডাটাবেজে এখনও কোনো সময়সূচি বা ফলাফল অন্তর্ভুক্ত করা হয়নি।
    </p>
    <div class="mt-3 pt-2.5 border-t border-amber-200/60 flex flex-wrap items-center justify-between gap-2 text-xs">
      <span class="text-slate-500 text-[11px]">অফিসিয়াল পোর্টালসমূহ চেক করুন:</span>
      <div class="flex flex-wrap gap-1.5">
        <a href="https://www.nu.ac.bd/recent-news-notice.php" target="_blank" class="bg-white hover:bg-amber-100/50 text-amber-900 border border-amber-300 px-2 py-0.5 rounded font-semibold transition">নোটিশ বোর্ড ↗</a>
        <a href="https://results.nu.ac.bd/" target="_blank" class="bg-white hover:bg-amber-100/50 text-amber-900 border border-amber-300 px-2 py-0.5 rounded font-semibold transition">ফলাফল পোর্টাল ↗</a>
      </div>
    </div>
  </div>
</div>'''.strip()

def process_academic_exam_query(query: str) -> Optional[ChatResponse]:
    """
    Resolves natural language queries for academic examination milestones.
    Grounds all answers in local SQLite database records with small modern nice looking vertical cards.
    """
    q = query.lower().strip()
    store = get_sql_store()

    # Step 1: Detect Professional Course or Program Category
    prof_course = find_professional_course(q)
    program_type = None

    if prof_course:
        program_type = "Professional"
    elif any(k in q for k in ["অনার্স", "honours", "hons"]):
        program_type = "Honours"
    elif any(k in q for k in ["ডিগ্রি", "ডিগ্রী", "degree"]):
        program_type = "Degree Pass"
    elif any(k in q for k in ["মাস্টার্স", "মাস্টাস", "master"]):
        program_type = "Master's"
    elif any(k in q for k in ["প্রফেশনাল", "professional"]):
        program_type = "Professional"

    if not program_type:
        return None

    # Step 2: Handle Professional Flow specifically
    if program_type == "Professional":
        # If no specific course selected, show the 5 branches and 18 courses
        if not prof_course:
            cards_reply = render_professional_courses_selection_cards()
            suggested_chips = ["CSE পরীক্ষা তথ্য", "BBA পরীক্ষা তথ্য", "TST পরীক্ষা তথ্য", "B.Ed পরীক্ষা তথ্য", "🏠 মূল মেনু"]
            return ChatResponse(
                reply=cards_reply,
                citations=STATIC_CITATIONS,
                intent="ACADEMIC_EXAM_INFO",
                skill_used="academic_exam_service",
                suggested_chips=suggested_chips
            )

        # Course is identified! Check if semester is specified
        prof_sem = find_semester(q)
        if not prof_sem:
            # Show the 8 semesters cards for this specific course
            cards_reply = render_professional_semesters_cards(prof_course)
            suggested_chips = [
                f"{prof_course['code']} ১ম সেমিস্টার",
                f"{prof_course['code']} ২য় সেমিস্টার",
                f"{prof_course['code']} ৩য় সেমিস্টার",
                f"{prof_course['code']} ৪র্থ সেমিস্টার",
                "🏠 মূল মেনু"
            ]
            return ChatResponse(
                reply=cards_reply,
                citations=STATIC_CITATIONS,
                intent="ACADEMIC_EXAM_INFO",
                skill_used="academic_exam_service",
                suggested_chips=suggested_chips
            )

        # Specific course + semester selected! Detect exam year if provided
        exam_year = None
        year_match = re.search(r"\b(202[3-9]|203[0-5])\b", q)
        if year_match:
            exam_year = year_match.group(1)
        else:
            bn_to_en = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
            trans_q = q.translate(bn_to_en)
            year_match_bn = re.search(r"\b(202[3-9]|203[0-5])\b", trans_q)
            if year_match_bn:
                exam_year = year_match_bn.group(1)

        # Lookup in SQLite database
        records = store.lookup_academic_exam_info(
            program_type="Professional",
            examination_year=exam_year,
            part=prof_course["code"],
            semester=prof_sem,
            course_name=prof_course["code"]
        )

        header_title = f"প্রফেশনাল {prof_course['name_bn']} ({prof_course['code']}) — সেমিস্টার: {prof_sem}"

        if records:
            distinct_years = sorted(list({r["examination_year"] for r in records}), reverse=True)
            reply = ""
            if not exam_year and len(distinct_years) > 1:
                most_recent_year = distinct_years[0]
                recent_record = [r for r in records if r["examination_year"] == most_recent_year][0]
                p_code = prof_course["code"]
                year_buttons = "".join([f'<button onclick="sendQuickQuestion(\'{p_code} {prof_sem} {y} পরীক্ষা\')" class="bg-blue-50 text-blue-800 border border-blue-200 hover:bg-blue-100 px-3 py-1 rounded-full text-xs font-semibold cursor-pointer transition">📅 {y} পরীক্ষার তথ্য</button> ' for y in distinct_years[1:]])
                reply += f'''<div class="mt-2.5 p-2.5 bg-slate-100 rounded-xl border border-slate-200 text-xs text-slate-700 flex items-center justify-between flex-wrap gap-2">
  <span>ℹ️ <strong>অন্যান্য শিক্ষাবর্ষের তথ্য:</strong></span>
  <div class="flex flex-wrap gap-1.5">{year_buttons}</div>
</div>'''
            else:
                for rec in records:
                    reply += format_exam_card_markdown(rec) + "\n\n"

            suggested_chips = [f"{prof_course['code']} পরীক্ষা তথ্য", "🎓 প্রফেশনাল কোর্স তালিকা", "📅 পরীক্ষার রুটিন", "🏠 মূল মেনু"]
            return ChatResponse(
                reply=reply.strip(),
                citations=STATIC_CITATIONS,
                intent="ACADEMIC_EXAM_INFO",
                skill_used="academic_exam_service",
                suggested_chips=suggested_chips[:5]
            )
        else:
            empty_reply = render_empty_exam_card(header_title, exam_year)
            return ChatResponse(
                reply=empty_reply,
                citations=STATIC_CITATIONS,
                intent="ACADEMIC_EXAM_INFO",
                skill_used="academic_exam_service",
                suggested_chips=[f"{prof_course['code']} পরীক্ষা তথ্য", "🎓 প্রফেশনাল কোর্স তালিকা", "📅 পরীক্ষার রুটিন", "🏠 মূল মেনু"]
            )

    # Step 3: Detect Part / Year for Honours / Degree Pass / Master's
    part = None
    if any(k in q for k in ["১ম বর্ষ", "১ম পর্ব", "1st year", "part 1", "পার্ট ১"]):
        part = "Part 1"
    elif any(k in q for k in ["২য় বর্ষ", "২য় বর্ষ", "২য় পর্ব", "২য় পর্ব", "2nd year", "part 2", "পার্ট ২"]):
        part = "Part 2"
    elif any(k in q for k in ["৩য় বর্ষ", "৩য় বর্ষ", "৩য় পর্ব", "৩য় পর্ব", "3rd year", "part 3", "পার্ট ৩"]):
        part = "Part 3"
    elif any(k in q for k in ["৪র্থ বর্ষ", "৪থ বর্ষ", "৪র্থ পর্ব", "৪থ পর্ব", "4th year", "part 4", "পার্ট ৪"]):
        part = "Part 4"
    elif any(k in q for k in ["প্রিলিমিনারি", "preliminary"]):
        part = "Preliminary"
    elif any(k in q for k in ["শেষ পর্ব", "final"]):
        part = "Final"

    semester = "N/A"

    # Step 4: Detect Specific Examination Year if provided
    exam_year = None
    year_match = re.search(r"\b(202[3-9]|203[0-5])\b", q)
    if year_match:
        exam_year = year_match.group(1)
    else:
        # Check Bengali digits (e.g. ২০২৪, ২০২৫)
        bn_to_en = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
        trans_q = q.translate(bn_to_en)
        year_match_bn = re.search(r"\b(202[3-9]|203[0-5])\b", trans_q)
        if year_match_bn:
            exam_year = year_match_bn.group(1)

    # Step 5: If no specific part requested, show the small modern vertical cards
    if not part:
        cards_reply = render_program_selection_cards(program_type)

        suggested_chips = []
        if program_type == "Honours":
            suggested_chips = ["অনার্স ১ম বর্ষ পরীক্ষা বিষয়ক তথ্য", "অনার্স ২য় বর্ষ পরীক্ষা বিষয়ক তথ্য", "অনার্স ৩য় বর্ষ পরীক্ষা বিষয়ক তথ্য", "অনার্স ৪থ বর্ষ পরীক্ষা বিষয়ক তথ্য"]
        elif program_type == "Degree Pass":
            suggested_chips = ["ডিগ্রি ১ম বর্ষ পরীক্ষা বিষয়ক তথ্য", "ডিগ্রি ২য় বর্ষ পরীক্ষা বিষয়ক তথ্য", "ডিগ্রি ৩য় বর্ষ পরীক্ষা বিষয়ক তথ্য"]
        elif program_type == "Master's":
            suggested_chips = ["মাস্টার্স শেষ পর্ব পরীক্ষা বিষয়ক তথ্য", "মাস্টার্স প্রিলিমিনারি পরীক্ষা বিষয়ক তথ্য"]
        elif program_type == "Professional":
            suggested_chips = ["প্রফেশনাল পার্ট ১ পরীক্ষা বিষয়ক তথ্য", "প্রফেশনাল পার্ট ২ পরীক্ষা বিষয়ক তথ্য", "প্রফেশনাল পার্ট ৩ পরীক্ষা বিষয়ক তথ্য", "প্রফেশনাল পার্ট ৪ পরীক্ষা বিষয়ক তথ্য"]
        suggested_chips.append("🏠 মূল মেনু")

        return ChatResponse(
            reply=cards_reply,
            citations=STATIC_CITATIONS,
            intent="ACADEMIC_EXAM_INFO",
            skill_used="academic_exam_service",
            suggested_chips=suggested_chips[:5]
        )

    # Step 6: Specific Part or Semester requested -> Query SQLite Database
    records = store.lookup_academic_exam_info(
        program_type=program_type,
        examination_year=exam_year,
        part=part,
        semester=semester
    )

    prog_bn = PROGRAM_CONFIG.get(program_type, {}).get("bn_name", program_type)
    part_bn = PROGRAM_CONFIG.get(program_type, {}).get("part_labels", {}).get(part, part) if part else ""
    header_title = f"{prog_bn} {part_bn}" if part_bn else prog_bn
    if semester and semester != "N/A":
        header_title += f" (সেমিস্টার: {semester})"

    if records:
        distinct_years = sorted(list({r["examination_year"] for r in records}), reverse=True)
        reply = ""

        # If user did not specify year and multiple exist, display the most recent and offer year selector
        if not exam_year and len(distinct_years) > 1:
            most_recent_year = distinct_years[0]
            recent_record = [r for r in records if r["examination_year"] == most_recent_year][0]
            reply += format_exam_card_markdown(recent_record)
            
            # Year switcher buttons
            year_buttons = "".join([f'<button onclick="sendQuickQuestion(\'{part or program_type} {y} পরীক্ষা\')" class="bg-blue-50 text-blue-800 border border-blue-200 hover:bg-blue-100 px-3 py-1 rounded-full text-xs font-semibold cursor-pointer transition">📅 {y} পরীক্ষার তথ্য</button> ' for y in distinct_years[1:]])
            reply += f'''<div class="mt-2.5 p-2.5 bg-slate-100 rounded-xl border border-slate-200 text-xs text-slate-700 flex items-center justify-between flex-wrap gap-2">
  <span>ℹ️ <strong>অন্যান্য শিক্ষাবর্ষের তথ্য:</strong></span>
  <div class="flex flex-wrap gap-1.5">{year_buttons}</div>
</div>'''
        else:
            for rec in records:
                reply += format_exam_card_markdown(rec) + "\n\n"

        suggested_chips = []
        for y in distinct_years:
            suggested_chips.append(f"{part or program_type} {y}")
        suggested_chips.extend(["📅 পরীক্ষার রুটিন", "🏠 মূল মেনু"])

        return ChatResponse(
            reply=reply.strip(),
            citations=STATIC_CITATIONS,
            intent="ACADEMIC_EXAM_INFO",
            skill_used="academic_exam_service",
            suggested_chips=suggested_chips[:5]
        )
    else:
        # No database record yet
        empty_reply = render_empty_exam_card(header_title, exam_year)
        return ChatResponse(
            reply=empty_reply,
            citations=STATIC_CITATIONS,
            intent="ACADEMIC_EXAM_INFO",
            skill_used="academic_exam_service",
            suggested_chips=["অনার্স পরীক্ষা বিষয়ক তথ্য", "ডিগ্রি পরীক্ষা বিষয়ক তথ্য", "📅 পরীক্ষার রুটিন", "🏠 মূল মেনু"]
        )
