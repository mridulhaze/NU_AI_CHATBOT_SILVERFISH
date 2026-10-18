"""
Smart Subject-Wise & Date-Wise Notice Filtering Service for National University Bangladesh (nu.ac.bd)

Capabilities:
1. Intent & Entity Extraction:
   - Subjects / Courses: LLB, CSE, BBA, Degree, Honours, Masters, B.Ed, B.P.Ed, MBA, AMT, KMT, FDT, ECE, THM, Fazil, Kamil, Economics, Botany, Physics, etc.
   - Actions / Categories: Form Fill-up (ফরম পূরণ), Exam Routine (রুটিন / সময়সূচি), Result (ফলাফল), Practical/Viva (ব্যবহারিক / ইনকোর্স), Admission (ভর্তি), Re-scrutiny (খাতা চ্যালেঞ্জ), Center List (কেন্দ্র তালিকা).
   - Years & Sessions: 2024, 2025, 2026, ২০২০-২০২৬, 2021-22, 2022-23, 2023-24.
   - Semesters & Years of Study: 1st-8th Semester, 1st-4th Year, Part-1/2, Final Year.
2. Smart SQL Query Generation & Subject Isolation:
   - Queries SQLite `notices` across title, published_date, and raw_text.
   - Enforces STRICT subject-isolation (prevents dumping CSE or BBA notices when LLB is requested).
3. Fallback & Formatting:
   - Returns ONLY relevant subject notices when found.
   - If subject requested but no notices exist, returns polite, subject-specific fallback without dumping unrelated notices.
   - If general notice requested, returns latest chronological notices.
"""

import re
import sqlite3
import logging
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from backend.models import SourceCitation, ChatResponse

logger = logging.getLogger("NU_NOTICE_SERVICE")

# Path to database
DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "nu_assistant.db"

# Strict Official Portals
PORTAL_RECENT_NOTICES = "https://www.nu.ac.bd/recent-news-notice.php"
PORTAL_EXAM_NOTICES = "https://www.nu.ac.bd/examination-notice.php"
PORTAL_ADMISSION_NOTICES = "https://www.nu.ac.bd/admission-notice.php"
PORTAL_EMS = "http://ems.nu.ac.bd/"

# Bengali to English digit mapping
BN_TO_EN_DIGITS = {
    '০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4',
    '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9'
}
EN_TO_BN_DIGITS = {v: k for k, v in BN_TO_EN_DIGITS.items()}

BN_MONTH_MAP = {
    'জানুয়ারি': 'January', 'জানুয়ারি': 'January',
    'ফেব্রুয়ারি': 'February', 'ফেব্রুয়ারি': 'February',
    'মার্চ': 'March',
    'এপ্রিল': 'April',
    'মে': 'May',
    'জুন': 'June',
    'জুলাই': 'July',
    'আগস্ট': 'August', 'অগাস্ট': 'August',
    'সেপ্টেম্বর': 'September',
    'অক্টোবর': 'October',
    'নভেম্বর': 'November',
    'ডিসেম্বর': 'December'
}

def to_en_digits(text: str) -> str:
    return "".join(BN_TO_EN_DIGITS.get(ch, ch) for ch in str(text or ""))

def to_bn_digits(text: str) -> str:
    return "".join(EN_TO_BN_DIGITS.get(ch, ch) for ch in str(text or ""))

def parse_notice_date(date_str: str, title_str: str = "", url_str: str = "") -> datetime:
    """
    Robust date parser converting diverse Bengali, English, and URL date formats
    into a standardized datetime for accurate chronological sorting.
    """
    default_date = datetime(2000, 1, 1)
    raw = str(date_str or "").strip()
    
    # Replace Bengali digits and Bengali month names
    normalized = to_en_digits(raw)
    for bn_m, en_m in BN_MONTH_MAP.items():
        normalized = normalized.replace(bn_m, en_m)
    
    # Direct datetime parsing patterns
    date_patterns = [
        "%B %d, %Y",       # August 23, 2026
        "%B %d %Y",        # August 23 2026
        "%b %d, %Y",       # Aug 23, 2026
        "%b %d %Y",        # Aug 23 2026
        "%d %B %Y",        # 23 August 2026
        "%d %b %Y",        # 23 Aug 2026
        "%d %B, %Y",       # 23 August, 2026
        "%Y-%m-%d",        # 2026-08-25
        "%d/%m/%Y",        # 25/08/2026
        "%m/%d/%Y",        # 08/25/2026
        "%d.%m.%Y",        # 23.08.2026
        "%d-%m-%Y",        # 23-08-2026
        "%Y/%m/%d",        # 2026/08/25
        "%Y.%m.%d",        # 2026.08.25
    ]
    
    clean_str = re.sub(r"[,\.]", " ", normalized).strip()
    for pat in date_patterns:
        for s in [normalized, clean_str, re.sub(r"\s+", " ", normalized)]:
            try:
                return datetime.strptime(s.strip(), pat)
            except ValueError:
                pass

    # Extract date from pub_date in URL: e.g. pub_date_23082026 or pub_date_06.01.2016
    if url_str:
        m_url = re.search(r"pub_date_(\d{2})(\d{2})(\d{4})", url_str)
        if m_url:
            d, m, y = int(m_url.group(1)), int(m_url.group(2)), int(m_url.group(3))
            try:
                return datetime(y, m, d)
            except ValueError:
                pass
        m_url_dot = re.search(r"pub_date_(\d{2})\.(\d{2})\.(\d{4})", url_str)
        if m_url_dot:
            d, m, y = int(m_url_dot.group(1)), int(m_url_dot.group(2)), int(m_url_dot.group(3))
            try:
                return datetime(y, m, d)
            except ValueError:
                pass
        m_url_path = re.search(r"/uploads/(\d{4})/(\d{2})/", url_str)
        if m_url_path:
            y, m = int(m_url_path.group(1)), int(m_url_path.group(2))
            return datetime(y, m, 1)

    # Extract 4-digit year from date_str or title_str
    combined = normalized + " " + to_en_digits(title_str)
    year_match = re.search(r"\b(20[12][0-9])\b", combined)
    if year_match:
        y = int(year_match.group(1))
        month_idx = 1
        for idx, m_name in enumerate(["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"], 1):
            if m_name in combined.lower():
                month_idx = idx
                break
        return datetime(y, month_idx, 1)

    return default_date

# --- Academic Subjects & Courses Taxonomy ---
SUBJECT_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "id": "LLB",
        "display_name_bn": "এলএলবি (আইন)",
        "display_name_en": "LL.B (Law)",
        "keywords": [
            r"\bllb\b", r"\bll\.b\b", r"\bll\s+b\b", r"\bl\.l\.b\b",
            r"এলএলবি", r"এল\.এল\.বি", r"এল\.\s*এল\.\s*বি", r"এল\s*এল\s*বি",
            r"\blaw\b", r"আইন\s*বিভাগ", r"আইন\s*কোর্স", r"আইন\s*অনুষদ"
        ],
        "sql_patterns": ["%LLB%", "%LL.B%", "%এলএলবি%", "%এল.এল.বি%", "%এল. এল. বি%", "%আইন বিভাগ%", "%আইন কোর্স%", "%আইন অনুষদ%"]
    },
    {
        "id": "CSE",
        "display_name_bn": "সিএসই (কম্পিউটার সায়েন্স এন্ড ইঞ্জিনিয়ারিং)",
        "display_name_en": "CSE (Computer Science & Engineering)",
        "keywords": [
            r"\bcse\b", r"\bc\.s\.e\b", r"সিএসই", r"সি\.এস\.ই",
            r"কম্পিউটার\s*সায়েন্স", r"কম্পিউটার\s*সায়েন্স", r"computer\s*science"
        ],
        "sql_patterns": ["%CSE%", "%সিএসই%", "%কম্পিউটার সায়েন্স%", "%কম্পিউটার সায়েন্স%", "%Computer Science%"]
    },
    {
        "id": "BBA",
        "display_name_bn": "বিবিএ (প্রফেশনাল)",
        "display_name_en": "BBA (Professional)",
        "keywords": [
            r"\bbba\b", r"\bb\.b\.a\b", r"বিবিএ", r"বিবিএ\s*\(প্রফেশনাল\)",
            r"ব্যবসা\s*প্রশাসন", r"business\s*administration"
        ],
        "sql_patterns": ["%BBA%", "%বিবিএ%", "%ব্যবসা প্রশাসন%"]
    },
    {
        "id": "DEGREE",
        "display_name_bn": "ডিগ্রি (পাস) ও সার্টিফিকেট কোর্স",
        "display_name_en": "Degree (Pass)",
        "keywords": [
            r"\bdegree\b", r"\bdegree\s*pass\b", r"ডিগ্রি", r"ডিগ্রী",
            r"ডিগ্রি\s*পাস", r"ডিগ্রী\s*পাস", r"ডিগ্রী\s*\(পাস\)", r"ডিগ্রি\s*\(পাস\)"
        ],
        "sql_patterns": ["%ডিগ্রি%", "%ডিগ্রী%", "%Degree%"]
    },
    {
        "id": "HONOURS",
        "display_name_bn": "অনার্স (স্নাতক সম্মান)",
        "display_name_en": "Honours",
        "keywords": [
            r"\bhonours\b", r"\bhonors\b", r"\bhons\b", r"অনার্স", r"স্নাতক\s*সম্মান"
        ],
        "sql_patterns": ["%অনার্স%", "%Honours%", "%Honors%"]
    },
    {
        "id": "MASTERS",
        "display_name_bn": "মাস্টার্স (স্নাতকোত্তর)",
        "display_name_en": "Masters",
        "keywords": [
            r"\bmasters\b", r"\bmaster's\b", r"\bm\.a\b", r"\bm\.s\.c\b",
            r"মাস্টার্স", r"স্নাতকোত্তর", r"প্রিলিমিনারি\s*মাস্টার্স", r"মাস্টার্স\s*ফাইনাল"
        ],
        "sql_patterns": ["%মাস্টার্স%", "%Masters%", "%স্নাতকোত্তর%"]
    },
    {
        "id": "BED",
        "display_name_bn": "বিএড (অনার্স / প্রফেশনাল)",
        "display_name_en": "B.Ed",
        "keywords": [
            r"\bbed\b", r"\bb\.ed\b", r"বিএড", r"বি\.এড", r"বি\s*এড", r"শিক্ষা\s*স্নাতক"
        ],
        "sql_patterns": ["%B.Ed%", "%বিএড%", "%বি.এড%"]
    },
    {
        "id": "BPED_MPED",
        "display_name_bn": "বিপিএড / এমপিএড (শারীরিক শিক্ষা)",
        "display_name_en": "B.P.Ed / M.P.Ed",
        "keywords": [
            r"\bbped\b", r"\bb\.p\.ed\b", r"বিপিএড", r"বি\.পি\.এড",
            r"\bmped\b", r"\bm\.p\.ed\b", r"এমপিএড", r"এম\.পি\.এড",
            r"শারীরিক\s*শিক্ষা", r"physical\s*education"
        ],
        "sql_patterns": ["%বিপিএড%", "%এমপিএড%", "%BPED%", "%MPED%"]
    },
    {
        "id": "MBA",
        "display_name_bn": "এমবিএ (প্রফেশনাল)",
        "display_name_en": "MBA",
        "keywords": [
            r"\bmba\b", r"\bm\.b\.a\b", r"এমবিএ", r"এম\.বি\.এ"
        ],
        "sql_patterns": ["%MBA%", "%এমবিএ%"]
    },
    {
        "id": "BSC_PROF_AMT_KMT_FDT_ECE",
        "display_name_bn": "বিএসসি প্রফেশনাল (AMT / KMT / FDT / ECE)",
        "display_name_en": "B.Sc Professional (AMT/KMT/FDT/ECE)",
        "keywords": [
            r"\bamt\b", r"\bkmt\b", r"\bfdt\b", r"\bece\b",
            r"অ্যাপারেল", r"নিটওয়্যার", r"ফ্যাশন\s*ডিজাইন", r"ইলেক্ট্রনিক্স"
        ],
        "sql_patterns": ["%AMT%", "%KMT%", "%FDT%", "%ECE%"]
    },
    {
        "id": "THM",
        "display_name_bn": "ট্যুরিজম এন্ড হসপিটালিটি ম্যানেজমেন্ট (THM)",
        "display_name_en": "Tourism & Hospitality (THM)",
        "keywords": [
            r"\bthm\b", r"ট্যুরিজম", r"হসপিটালিটি", r"tourism"
        ],
        "sql_patterns": ["%THM%", "%ট্যুরিজম%", "%Tourism%"]
    },
    {
        "id": "FAZIL_KAMIL",
        "display_name_bn": "ফাজিল / কামিল",
        "display_name_en": "Fazil / Kamil",
        "keywords": [
            r"\bfazil\b", r"ফাজিল", r"\bkamil\b", r"কামিল"
        ],
        "sql_patterns": ["%ফাজিল%", "%Fazil%", "%কামিল%", "%Kamil%"]
    },
    {
        "id": "BOTANY",
        "display_name_bn": "উদ্ভিদ বিজ্ঞান বিভাগ",
        "display_name_en": "Botany",
        "keywords": [r"\bbotany\b", r"উদ্ভিদ\s*বিজ্ঞান", r"উদ্ভিদবিদ্যা", r"বোটানি"],
        "sql_patterns": ["%উদ্ভিদ বিজ্ঞান%", "%উদ্ভিদবিদ্যা%", "%Botany%"]
    },
    {
        "id": "ZOOLOGY",
        "display_name_bn": "প্রাণী বিদ্যা বিভাগ",
        "display_name_en": "Zoology",
        "keywords": [r"\bzoology\b", r"প্রাণী\s*বিদ্যা", r"প্রাণিবিদ্যা", r"জুলোজি"],
        "sql_patterns": ["%প্রাণী বিদ্যা%", "%প্রাণিবিদ্যা%", "%Zoology%"]
    },
    {
        "id": "PHYSICS",
        "display_name_bn": "পদার্থ বিজ্ঞান বিভাগ",
        "display_name_en": "Physics",
        "keywords": [r"\bphysics\b", r"পদার্থ\s*বিজ্ঞান", r"পদার্থবিজ্ঞান", r"পদার্থবিদ্যা", r"ফিজিক্স"],
        "sql_patterns": ["%পদার্থ বিজ্ঞান%", "%পদার্থবিজ্ঞান%", "%পদার্থবিদ্যা%", "%Physics%"]
    },
    {
        "id": "CHEMISTRY",
        "display_name_bn": "রসায়ন বিভাগ",
        "display_name_en": "Chemistry",
        "keywords": [r"\bchemistry\b", r"রসায়ন", r"রসায়ন", r"রসায়নবিদ্যা", r"কেমিস্ট্রি"],
        "sql_patterns": ["%রসায়ন%", "%রসায়ন%", "%Chemistry%"]
    },
    {
        "id": "MATHEMATICS",
        "display_name_bn": "গণিত বিভাগ",
        "display_name_en": "Mathematics",
        "keywords": [r"\bmath\b", r"\bmathematics\b", r"গণিত", r"ম্যাথ", r"ম্যাথমেটিক্স"],
        "sql_patterns": ["%গণিত%", "%Mathematics%", "%Math%"]
    },
    {
        "id": "ECONOMICS",
        "display_name_bn": "অর্থনীতি বিভাগ",
        "display_name_en": "Economics",
        "keywords": [r"\beconomics\b", r"অর্থনীতি", r"ইকোনমিক্স"],
        "sql_patterns": ["%অর্থনীতি%", "%Economics%"]
    },
    {
        "id": "ACCOUNTING",
        "display_name_bn": "হিসাববিজ্ঞান বিভাগ",
        "display_name_en": "Accounting",
        "keywords": [r"\baccounting\b", r"হিসাববিজ্ঞান", r"হিসাব\s*বিজ্ঞান", r"অ্যাকাউন্টিং", r"একাউন্টিং"],
        "sql_patterns": ["%হিসাববিজ্ঞান%", "%হিসাব বিজ্ঞান%", "%Accounting%"]
    },
    {
        "id": "MANAGEMENT",
        "display_name_bn": "ব্যবস্থাপনা বিভাগ",
        "display_name_en": "Management",
        "keywords": [r"\bmanagement\b", r"ব্যবস্থাপনা", r"ম্যানেজমেন্ট"],
        "sql_patterns": ["%ব্যবস্থাপনা%", "%Management%"]
    },
    {
        "id": "FINANCE",
        "display_name_bn": "ফিন্যান্স ও ব্যাংকিং বিভাগ",
        "display_name_en": "Finance & Banking",
        "keywords": [r"\bfinance\b", r"ফিন্যান্স", r"ফাইন্যান্স", r"অর্থায়ন", r"ব্যাংকিং"],
        "sql_patterns": ["%ফিন্যান্স%", "%ফাইন্যান্স%", "%Finance%", "%Banking%"]
    },
    {
        "id": "MARKETING",
        "display_name_bn": "মার্কেটিং বিভাগ",
        "display_name_en": "Marketing",
        "keywords": [r"\bmarketing\b", r"মার্কেটিং"],
        "sql_patterns": ["%মার্কেটিং%", "%Marketing%"]
    },
    {
        "id": "POLITICAL_SCIENCE",
        "display_name_bn": "রাষ্ট্রবিজ্ঞান বিভাগ",
        "display_name_en": "Political Science",
        "keywords": [r"political\s*science", r"রাষ্ট্রবিজ্ঞান", r"পলিটিক্যাল\s*সায়েন্স", r"পলিটিকাল\s*সায়েন্স"],
        "sql_patterns": ["%রাষ্ট্রবিজ্ঞান%", "%Political Science%"]
    },
    {
        "id": "SOCIOLOGY",
        "display_name_bn": "সমাজবিজ্ঞান বিভাগ",
        "display_name_en": "Sociology",
        "keywords": [r"\bsociology\b", r"সমাজবিজ্ঞান", r"সোসিওলজি"],
        "sql_patterns": ["%সমাজবিজ্ঞান%", "%Sociology%"]
    },
    {
        "id": "SOCIAL_WORK",
        "display_name_bn": "সমাজকর্ম বিভাগ",
        "display_name_en": "Social Work",
        "keywords": [r"social\s*work", r"সমাজকর্ম", r"সোশ্যাল\s*ওয়ার্ক", r"সোশাল\s*ওয়ার্ক"],
        "sql_patterns": ["%সমাজকর্ম%", "%Social Work%"]
    },
    {
        "id": "ISLAMIC_HISTORY",
        "display_name_bn": "ইসলামের ইতিহাস ও সংস্কৃতি",
        "display_name_en": "Islamic History",
        "keywords": [r"islamic\s*history", r"ইসলামের\s*ইতিহাস", r"ইসলামিক\s*ইতিহাস"],
        "sql_patterns": ["%ইসলামের ইতিহাস%", "%ইসলামিক ইতিহাস%", "%Islamic History%"]
    },
    {
        "id": "ISLAMIC_STUDIES",
        "display_name_bn": "ইসলামিক স্টাডিজ বিভাগ",
        "display_name_en": "Islamic Studies",
        "keywords": [r"islamic\s*studies", r"ইসলামিক\s*স্টাডিজ", r"ইসলাম\s*শিক্ষা"],
        "sql_patterns": ["%ইসলামিক স্টাডিজ%", "%ইসলাম শিক্ষা%", "%Islamic Studies%"]
    },
    {
        "id": "GEOGRAPHY",
        "display_name_bn": "ভূগোল ও পরিবেশ বিভাগ",
        "display_name_en": "Geography & Environment",
        "keywords": [r"\bgeography\b", r"ভূগোল", r"জিওগ্রাফি", r"পরিবেশ\s*বিজ্ঞান"],
        "sql_patterns": ["%ভূগোল%", "%Geography%"]
    },
    {
        "id": "PSYCHOLOGY",
        "display_name_bn": "মনোবিজ্ঞান বিভাগ",
        "display_name_en": "Psychology",
        "keywords": [r"\bpsychology\b", r"মনোবিজ্ঞান", r"সাইকোলজি"],
        "sql_patterns": ["%মনোবিজ্ঞান%", "%Psychology%"]
    },
    {
        "id": "STATISTICS",
        "display_name_bn": "পরিসংখ্যান বিভাগ",
        "display_name_en": "Statistics",
        "keywords": [r"\bstatistics\b", r"পরিসংখ্যান", r"স্ট্যাটিস্টিকস"],
        "sql_patterns": ["%পরিসংখ্যান%", "%Statistics%"]
    },
    {
        "id": "SOIL_SCIENCE",
        "display_name_bn": "মৃত্তিকা বিজ্ঞান বিভাগ",
        "display_name_en": "Soil Science",
        "keywords": [r"soil\s*science", r"মৃত্তিকা\s*বিজ্ঞান"],
        "sql_patterns": ["%মৃত্তিকা বিজ্ঞান%", "%Soil Science%"]
    },
    {
        "id": "HOME_ECONOMICS",
        "display_name_bn": "গার্হস্থ্য অর্থনীতি",
        "display_name_en": "Home Economics",
        "keywords": [r"home\s*economics", r"গার্হস্থ্য\s*অর্থনীতি", r"গার্হস্থ্য"],
        "sql_patterns": ["%গার্হস্থ্য অর্থনীতি%", "%Home Economics%"]
    },
    {
        "id": "BANGLA_DEPT",
        "display_name_bn": "বাংলা বিভাগ",
        "display_name_en": "Bangla Department",
        "keywords": [r"বাংলা\s*বিভাগ", r"বাংলা\s*বিষয়", r"বাংলা\s*কোর্স", r"bangla\s*department"],
        "sql_patterns": ["%বাংলা বিভাগ%", "%Bangla Department%"]
    },
    {
        "id": "ENGLISH_DEPT",
        "display_name_bn": "ইংরেজি বিভাগ",
        "display_name_en": "English Department",
        "keywords": [r"ইংরেজি\s*বিভাগ", r"ইংরেজী\s*বিভাগ", r"ইংরেজি\s*বিষয়", r"english\s*department"],
        "sql_patterns": ["%ইংরেজি বিভাগ%", "%English Department%"]
    }
]

# --- Action / Category Taxonomy ---
ACTION_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "id": "FORM_FILLUP",
        "display_name_bn": "ফরম পূরণ সংক্রান্ত বিজ্ঞপ্তি",
        "display_name_en": "Form Fill-up Notice",
        "keywords": [
            r"form\s*fill\s*up", r"form\s*fill-up", r"formfillup", r"form\s*fill", r"form\s*filla",
            r"ফরম\s*পূরণ", r"ফরমপূরণ", r"আবেদন\s*ফরম", r"আবেদনপত্র\s*পূরণ", r"ফরম\s*ফিলাপ", r"ফিলাপ"
        ],
        "sql_patterns": ["%ফরম পূরণ%", "%ফরমপূরণ%", "%আবেদনফরম%", "%ফরম পূরণের%", "%form fill%"]
    },
    {
        "id": "ROUTINE",
        "display_name_bn": "পরীক্ষার রুটিন ও সময়সূচি",
        "display_name_en": "Exam Routine & Schedule",
        "keywords": [
            r"routine", r"schedule", r"time\s*table", r"exam\s*date",
            r"রুটিন", r"সময়সূচি", r"সময়সূচী", r"সময়সূচি", r"সময়সূচী", r"পরীক্ষার\s*তারিখ"
        ],
        "sql_patterns": ["%সময়সূচি%", "%সময়সূচি%", "%সময়সূচী%", "%সময়সূচী%", "%রুটিন%", "%Routine%", "%Schedule%"]
    },
    {
        "id": "RESULT",
        "display_name_bn": "পরীক্ষার ফলাফল",
        "display_name_en": "Exam Result",
        "keywords": [
            r"result", r"grade", r"cgpa", r"gpa", r"ফলাফল", r"রেজাল্ট", r"ফল\s*প্রকাশ"
        ],
        "sql_patterns": ["%ফলাফল%", "%রেজাল্ট%", "%Result%"]
    },
    {
        "id": "PRACTICAL",
        "display_name_bn": "ব্যবহারিক ও ইনকোর্স পরীক্ষা",
        "display_name_en": "Practical & Incourse Exam",
        "keywords": [
            r"practical", r"viva", r"incourse",
            r"ব্যবহারিক", r"ব্যাবহারিক", r"ইনকোর্স", r"মৌখিক"
        ],
        "sql_patterns": ["%ব্যবহারিক%", "%ব্যাবহারিক%", "%ইনকোর্স%", "%Practical%"]
    },
    {
        "id": "ADMISSION",
        "display_name_bn": "ভর্তি সংক্রান্ত বিজ্ঞপ্তি",
        "display_name_en": "Admission Notice",
        "keywords": [
            r"admission", r"apply", r"merit\s*list", r"release\s*slip",
            r"ভর্তি", r"মেধা\s*তালিকা", r"রিলিজ\s*স্লিপ"
        ],
        "sql_patterns": ["%ভর্তি%", "%মেধা তালিকা%", "%Admission%"]
    },
    {
        "id": "RESCRUTINY",
        "display_name_bn": "উত্তরপত্র পুনঃমূল্যায়ন (খাতা চ্যালেঞ্জ)",
        "display_name_en": "Answer Script Re-scrutiny",
        "keywords": [
            r"rescrutiny", r"re-scrutiny", r"recheck", r"challenge",
            r"পুনর্নিরীক্ষণ", r"পুনঃমূল্যায়ন", r"পুনর্মূল্যায়ন", r"খাতা\s*চ্যালেঞ্জ", r"বোর্ড\s*চ্যালেঞ্জ"
        ],
        "sql_patterns": ["%পুনর্নিরীক্ষণ%", "%পুনঃমূল্যায়ন%", "%পুনর্মূল্যায়ন%", "%Rescutinee%", "%Rescrutiny%"]
    },
    {
        "id": "CENTER_LIST",
        "display_name_bn": "পরীক্ষার কেন্দ্র তালিকা",
        "display_name_en": "Exam Center List",
        "keywords": [
            r"center\s*list", r"centre\s*list", r"exam\s*center",
            r"কেন্দ্র\s*তালিকা", r"পরীক্ষা\s*কেন্দ্র", r"কেন্দ্র"
        ],
        "sql_patterns": ["%কেন্দ্র তালিকা%", "%কেন্দ্র%"]
    }
]

@dataclass
class NoticeQueryFilter:
    original_query: str
    subjects: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    years: List[str] = field(default_factory=list)
    semesters: List[str] = field(default_factory=list)
    academic_years: List[str] = field(default_factory=list)
    is_general_notice_query: bool = False

@dataclass
class NoticeQueryResult:
    query: str
    filters: NoticeQueryFilter
    matched_notices: List[Dict[str, Any]] = field(default_factory=list)
    has_subject_filter: bool = False
    is_empty_subject_result: bool = False
    formatted_reply: str = ""
    citations: List[SourceCitation] = field(default_factory=list)


class NoticeFilterService:
    """
    Intelligent Notice Extraction, Strict Filtering, Chrono-Sorting, and Formatting Service.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = str(db_path or DB_PATH)

    def extract_filters(self, query: str) -> NoticeQueryFilter:
        """Extracts subjects, actions, dates, and semester/year from query."""
        q_lower = query.lower()
        q_en_digits = to_en_digits(q_lower)

        extracted_subjects = []
        for subj in SUBJECT_DEFINITIONS:
            for kw in subj["keywords"]:
                if re.search(kw, q_lower, re.IGNORECASE):
                    extracted_subjects.append(subj)
                    break

        # Dynamic fallback for "{Subject} বিভাগ / বিষয় / কোর্স / ডিপার্টমেন্ট"
        if not extracted_subjects:
            dept_match = re.search(r"((?:[A-Za-z\u0980-\u09ff]+\s+){0,2}[A-Za-z\u0980-\u09ff]+)\s*(?:বিভাগ|কোর্স|বিষয়|বিষয়ের|ডিপার্টমেন্ট|department|dept)", q_lower)
            if dept_match:
                subj_name = dept_match.group(1).strip()
                # Strip leading stop words
                for prefix in ["আমার ", "আমাদের ", "এই ", "সকল ", "সব ", "কোন ", "যে কোন "]:
                    if subj_name.startswith(prefix):
                        subj_name = subj_name[len(prefix):].strip()

                excluded_words = {"সকল", "সব", "নতুন", "আজকের", "সাম্প্রতিক", "পরীক্ষা", "ভর্তি", "নোটিশ", "বিজ্ঞপ্তি", "general", "recent", "all", "latest"}
                if len(subj_name) >= 2 and subj_name not in excluded_words:
                    extracted_subjects.append({
                        "id": f"DYNAMIC_{subj_name.upper()}",
                        "display_name_bn": f"{subj_name} বিভাগ",
                        "display_name_en": f"{subj_name} Department",
                        "keywords": [subj_name],
                        "sql_patterns": [f"%{subj_name}%"]
                    })

        extracted_actions = []
        for act in ACTION_DEFINITIONS:
            for kw in act["keywords"]:
                if re.search(kw, q_lower, re.IGNORECASE):
                    extracted_actions.append(act)
                    break

        # Extract Years (e.g. 2020-2026, ২০২০-২০২৬)
        extracted_years = []
        year_matches = re.findall(r"\b(201[5-9]|202[0-9])\b", q_en_digits)
        for y in year_matches:
            extracted_years.append(y)
            extracted_years.append(to_bn_digits(y))

        # Extract Semesters (e.g. 1st - 8th semester, ১ম - ৮ম সেমিস্টার)
        extracted_semesters = []
        sem_patterns = [
            (r"(1st|১ম)\s*(semester|সেমিস্টার)", ["১ম সেমিস্টার", "1st Semester", "প্রথম সেমিস্টার"]),
            (r"(2nd|২য়|২য়)\s*(semester|সেমিস্টার)", ["২য় সেমিস্টার", "২য় সেমিস্টার", "2nd Semester", "দ্বিতীয় সেমিস্টার"]),
            (r"(3rd|৩য়|৩য়)\s*(semester|সেমিস্টার)", ["৩য় সেমিস্টার", "৩য় সেমিস্টার", "3rd Semester", "তৃতীয় সেমিস্টার"]),
            (r"(4th|৪র্থ)\s*(semester|সেমিস্টার)", ["৪র্থ সেমিস্টার", "4th Semester", "চতুর্থ সেমিস্টার"]),
            (r"(5th|৫ম)\s*(semester|সেমিস্টার)", ["৫ম সেমিস্টার", "5th Semester", "পঞ্চম সেমিস্টার"]),
            (r"(6th|৬ষ্ঠ)\s*(semester|সেমিস্টার)", ["৬ষ্ঠ সেমিস্টার", "6th Semester", "ষষ্ঠ সেমিস্টার"]),
            (r"(7th|৭ম)\s*(semester|সেমিস্টার)", ["৭ম সেমিস্টার", "7th Semester", "সপ্তম সেমিস্টার"]),
            (r"(8th|৮ম)\s*(semester|সেমিস্টার)", ["৮ম সেমিস্টার", "8th Semester", "অষ্টম সেমিস্টার"]),
        ]
        for pat, tags in sem_patterns:
            if re.search(pat, q_lower, re.IGNORECASE) or re.search(pat, q_en_digits, re.IGNORECASE):
                extracted_semesters.extend(tags)

        # Extract Year of study (e.g. 1st year / ১ম বর্ষ - 4th year / ৪র্থ বর্ষ / Final)
        extracted_academic_years = []
        acad_patterns = [
            (r"(1st|১ম)\s*(year|বর্ষ|part)", ["১ম বর্ষ", "1st Year", "Part-1", "প্রথম বর্ষ"]),
            (r"(2nd|২য়|২য়)\s*(year|বর্ষ|part)", ["২য় বর্ষ", "২য় বর্ষ", "2nd Year", "Part-2", "দ্বিতীয় বর্ষ"]),
            (r"(3rd|৩য়|৩য়)\s*(year|বর্ষ|part)", ["৩য় বর্ষ", "৩য় বর্ষ", "3rd Year", "Part-3", "তৃতীয় বর্ষ"]),
            (r"(4th|৪র্থ)\s*(year|বর্ষ|part)", ["৪র্থ বর্ষ", "4th Year", "Part-4", "চতুর্থ বর্ষ"]),
            (r"(final|শেষ|ফাইনাল)\s*(year|বর্ষ)?", ["ফাইনাল", "শেষ বর্ষ", "Final Year"]),
        ]
        for pat, tags in acad_patterns:
            if re.search(pat, q_lower, re.IGNORECASE) or re.search(pat, q_en_digits, re.IGNORECASE):
                extracted_academic_years.extend(tags)

        # Check if it is a general notice query (no subject specified)
        general_indicators = [
            "সাম্প্রতিক", "সকল নোটিশ", "সব নোটিশ", "আজকের নোটিশ", "নতুন নোটিশ",
            "recent notice", "latest notice", "all notice", "today notice", "recent news",
            "বিজ্ঞপ্তি", "notice board", "নোটিশ বোর্ড"
        ]
        is_general = len(extracted_subjects) == 0 and any(w in q_lower for w in general_indicators)

        return NoticeQueryFilter(
            original_query=query,
            subjects=extracted_subjects,
            actions=extracted_actions,
            years=extracted_years,
            semesters=extracted_semesters,
            academic_years=extracted_academic_years,
            is_general_notice_query=is_general
        )

    def format_single_notice_row(self, row: Tuple) -> Dict[str, Any]:
        """
        Intelligently parses SQLite row to determine true title, date, clickable URL, and parsed datetime.
        """
        r_id, r_title, r_url, r_pdf_url, r_cat, r_pub_date, r_hash, r_raw, r_scraped = row

        # Distinguish date vs title based on content and length
        pub_str = str(r_pub_date or "").strip()
        title_str = str(r_title or "").strip()
        raw_str = str(r_raw or "").strip()

        is_pub_date_title = len(pub_str) > 25 or any('\u0980' <= ch <= '\u09ff' for ch in pub_str)
        if is_pub_date_title:
            clean_title = pub_str
            clean_date = title_str if title_str else (r_scraped or "August 2026")
        else:
            clean_title = title_str if title_str else (raw_str if raw_str else "জাতীয় বিশ্ববিদ্যালয় বিজ্ঞপ্তি")
            clean_date = pub_str if pub_str else (r_scraped or "August 2026")

        # Clean title text
        clean_title = re.sub(r"\s+", " ", clean_title).strip()
        clean_date = re.sub(r"\s+", " ", clean_date).strip()

        # Construct clickable URL
        url = r_pdf_url or r_url or PORTAL_RECENT_NOTICES
        if url and not url.startswith("http"):
            url = f"https://www.nu.ac.bd/{url.lstrip('/')}"

        parsed_dt = parse_notice_date(clean_date, clean_title, url)

        return {
            "id": r_id,
            "title": clean_title,
            "date": clean_date,
            "url": url,
            "category": r_cat or "Notice",
            "raw_text": raw_str,
            "parsed_date": parsed_dt
        }

    def get_historical_notice_for_subject(self, subject: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Retrieves verified historical notices for a subject when recent queries are empty."""
        if not Path(self.db_path).exists():
            return []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            sql_pats = subject["sql_patterns"]
            subj_clause = " OR ".join(["title LIKE ? OR published_date LIKE ? OR raw_text LIKE ?" for _ in sql_pats])
            params = []
            for pat in sql_pats:
                params.extend([pat, pat, pat])
            cursor.execute(f"SELECT id, title, url, pdf_url, category, published_date, content_hash, raw_text, scraped_at FROM notices WHERE ({subj_clause}) ORDER BY id DESC LIMIT 50", params)
            rows = cursor.fetchall()
            results = []
            seen = set()
            for r in rows:
                item = self.format_single_notice_row(r)
                if item["title"] in seen:
                    continue
                # Mandatory keyword check on title
                if any(re.search(kw, item["title"].lower(), re.IGNORECASE) for kw in subject["keywords"]):
                    seen.add(item["title"])
                    results.append(item)
            results.sort(key=lambda x: x.get("parsed_date", datetime(2000, 1, 1)), reverse=True)
            return results
        except Exception as e:
            logger.error(f"Error finding historical notices: {e}")
            return []
        finally:
            conn.close()

    def search_filtered_notices(self, filters: NoticeQueryFilter, limit: int = 8) -> List[Dict[str, Any]]:
        """
        Executes a targeted, subject-isolated SQL query on the notices database with strict title matching and chrono-sorting.
        """
        if not Path(self.db_path).exists():
            logger.warning(f"Database {self.db_path} does not exist.")
            return []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 1. Subject-isolated query
            if filters.subjects:
                primary_subject = filters.subjects[0]
                sql_subj_patterns = primary_subject["sql_patterns"]

                # Build SQL conditions
                subj_clause = " OR ".join(["title LIKE ? OR published_date LIKE ? OR raw_text LIKE ?" for _ in sql_subj_patterns])
                params = []
                for pat in sql_subj_patterns:
                    params.extend([pat, pat, pat])

                # Optional Action Filter
                action_clause = ""
                if filters.actions:
                    act = filters.actions[0]
                    act_pats = act["sql_patterns"]
                    action_sub = " OR ".join(["title LIKE ? OR published_date LIKE ? OR raw_text LIKE ?" for _ in act_pats])
                    action_clause = f" AND ({action_sub})"
                    for pat in act_pats:
                        params.extend([pat, pat, pat])

                # Optional Year Filter
                year_clause = ""
                if filters.years:
                    year_sub = " OR ".join(["title LIKE ? OR published_date LIKE ? OR raw_text LIKE ?" for _ in filters.years])
                    year_clause = f" AND ({year_sub})"
                    for y in filters.years:
                        pat = f"%{y}%"
                        params.extend([pat, pat, pat])

                # Optional Semester / Academic Year Filter
                sem_clause = ""
                sem_tags = filters.semesters or filters.academic_years
                if sem_tags:
                    sem_sub = " OR ".join(["title LIKE ? OR published_date LIKE ? OR raw_text LIKE ?" for _ in sem_tags])
                    sem_clause = f" AND ({sem_sub})"
                    for s in sem_tags:
                        pat = f"%{s}%"
                        params.extend([pat, pat, pat])

                # Execute strict combined query
                query_sql = f"""
                    SELECT id, title, url, pdf_url, category, published_date, content_hash, raw_text, scraped_at 
                    FROM notices 
                    WHERE ({subj_clause}){action_clause}{year_clause}{sem_clause}
                    ORDER BY date_iso DESC, id DESC LIMIT ?
                """
                cursor.execute(query_sql, params + [limit * 10])
                rows = cursor.fetchall()

                # Strict title keyword verification: discard rows that do not explicitly contain subject keywords
                results = []
                seen_titles = set()
                for r in rows:
                    item = self.format_single_notice_row(r)
                    if item["title"] in seen_titles:
                        continue
                    title_lower = item["title"].lower()
                    has_subj_kw = any(re.search(kw, title_lower, re.IGNORECASE) for kw in primary_subject["keywords"])
                    if not has_subj_kw:
                        continue
                    seen_titles.add(item["title"])
                    results.append(item)

                # If strict query with actions/semesters returned 0 results, relax action/semester but STRICTLY KEEP SUBJECT!
                if not results and (action_clause or sem_clause or year_clause):
                    logger.info(f"Relaxing sub-filters for subject {primary_subject['id']} while keeping strict subject filter.")
                    relax_params = []
                    for pat in sql_subj_patterns:
                        relax_params.extend([pat, pat, pat])
                    
                    relax_sql = f"""
                        SELECT id, title, url, pdf_url, category, published_date, content_hash, raw_text, scraped_at 
                        FROM notices 
                        WHERE ({subj_clause})
                        ORDER BY date_iso DESC, id DESC LIMIT ?
                    """
                    cursor.execute(relax_sql, relax_params + [limit * 10])
                    relax_rows = cursor.fetchall()
                    for r in relax_rows:
                        item = self.format_single_notice_row(r)
                        if item["title"] in seen_titles:
                            continue
                        title_lower = item["title"].lower()
                        has_subj_kw = any(re.search(kw, title_lower, re.IGNORECASE) for kw in primary_subject["keywords"])
                        if not has_subj_kw:
                            continue
                        seen_titles.add(item["title"])
                        results.append(item)

                # Chronological sorting: Newest First!
                results.sort(key=lambda x: x.get("parsed_date", datetime(2000, 1, 1)), reverse=True)
                return results[:limit]

            # 2. General Notices Query (when no specific subject is requested)
            else:
                cursor.execute("""
                    SELECT id, title, url, pdf_url, category, published_date, content_hash, raw_text, scraped_at 
                    FROM notices 
                    ORDER BY date_iso DESC, id DESC LIMIT ?
                """, (limit * 5,))
                rows = cursor.fetchall()
                results = []
                seen_titles = set()
                for r in rows:
                    item = self.format_single_notice_row(r)
                    if item["title"] not in seen_titles:
                        seen_titles.add(item["title"])
                        results.append(item)
                # Chronological sorting: Newest First!
                results.sort(key=lambda x: x.get("parsed_date", datetime(2000, 1, 1)), reverse=True)
                return results[:limit]

        except Exception as e:
            logger.error(f"Error querying notices: {e}", exc_info=True)
            return []
        finally:
            conn.close()

    def process_notice_query(self, query: str, limit: int = 6) -> NoticeQueryResult:
        """
        Main entry point for processing notice requests with intelligent filtering and clean formatting.
        """
        filters = self.extract_filters(query)
        has_subject = len(filters.subjects) > 0
        notices = self.search_filtered_notices(filters, limit=limit)

        # 1. Subject requested and matching notices found
        if has_subject and notices:
            subj = filters.subjects[0]
            subj_title_bn = subj["display_name_bn"]
            act_title_bn = filters.actions[0]["display_name_bn"] if filters.actions else "বিজ্ঞপ্তিসমূহ"
            
            notice_bullets = []
            citations = []
            for n in notices:
                notice_bullets.append(f"• **{n['date']}:** [{n['title']}]({n['url']})")
                citations.append(SourceCitation(
                    title=n["title"][:80],
                    url=n["url"],
                    date=n["date"],
                    category=f"{subj['id']} Notice"
                ))

            bullets_text = "\n\n".join(notice_bullets)
            reply = f"""### 📄 জাতীয় বিশ্ববিদ্যালয় {subj_title_bn} - {act_title_bn}:

জাতীয় বিশ্ববিদ্যালয়ের অফিসিয়াল ডাটাবেজ থেকে **{subj_title_bn}** সম্পর্কিত প্রাসঙ্গিক নোটিশসমূহ নিচে তালিকাভুক্ত করা হলো:

{bullets_text}

---
🔗 **অফিসিয়াল নোটিশ বোর্ড:** [nu.ac.bd নোটিশ বোর্ড]({PORTAL_RECENT_NOTICES}) | [পরীক্ষা সংক্রান্ত রুটিন]({PORTAL_EXAM_NOTICES})
💡 *যেকোনো নোটিশের লিংকে ক্লিক করে সরাসরি অফিশিয়াল PDF বা বিজ্ঞপ্তি দেখতে পারবেন।*"""

            return NoticeQueryResult(
                query=query,
                filters=filters,
                matched_notices=notices,
                has_subject_filter=True,
                is_empty_subject_result=False,
                formatted_reply=reply,
                citations=citations
            )

        # 2. Subject requested, but ZERO matching notices found in database (POLITE FALLBACK - ZERO DUMPING)
        elif has_subject and not notices:
            subj = filters.subjects[0]
            subj_bn = subj["display_name_bn"]
            act_bn = filters.actions[0]["display_name_bn"] if filters.actions else "নোটিশ বা বিজ্ঞপ্তি"

            # Check if any historical notices exist in database
            hist_notices = self.get_historical_notice_for_subject(subj)
            if hist_notices:
                last_notice = hist_notices[0]
                reply = f"""### ℹ️ {subj_bn} সংক্রান্ত নোটিশ তথ্য:

জাতীয় বিশ্ববিদ্যালয়ের বর্তমান নোটিশ বোর্ডে **{subj_bn}** সংক্রান্ত কোনো নতুন {act_bn} পাওয়া যায়নি। সর্বশেষ সংরক্ষিত নোটিশটি **{last_notice['date']}** তারিখের: [{last_notice['title']}]({last_notice['url']})।

অনুগ্রহ করে সর্বশেষ হালনাগাদ তথ্যের জন্য সরাসরি অফিশিয়াল পোর্টাল চেক করুন:
- 📄 **সকল নোটিশ বোর্ড:** [{PORTAL_RECENT_NOTICES}]({PORTAL_RECENT_NOTICES})
- 📅 **পরীক্ষা সংক্রান্ত রুটিন ও নোটিশ:** [{PORTAL_EXAM_NOTICES}]({PORTAL_EXAM_NOTICES})
- 🌐 **অনলাইন ফরম পূরণ পোর্টাল (EMS):** [{PORTAL_EMS}]({PORTAL_EMS})

💡 *পরামর্শ: নতুন কোনো বিজ্ঞপ্তি প্রকাশিত হওয়া মাত্রই অফিশিয়াল ওয়েবসাইটে পাওয়া যাবে।*"""
                citations = [
                    SourceCitation(title=last_notice["title"][:80], url=last_notice["url"], date=last_notice["date"], category=f"{subj['id']} Historical Notice"),
                    SourceCitation(title=f"{subj_bn} Official Notice Board", url=PORTAL_RECENT_NOTICES, category="Notice Board")
                ]
            else:
                reply = f"""### ℹ️ {subj_bn} সংক্রান্ত নোটিশ তথ্য:

জাতীয় বিশ্ববিদ্যালয়ের বর্তমান নোটিশ বোর্ডে **{subj_bn}** সংক্রান্ত কোনো নোটিশ পাওয়া যায়নি।

অনুগ্রহ করে সর্বশেষ তথ্যের জন্য অফিশিয়াল নোটিশ বোর্ড ও পরীক্ষার পোর্টালগুলো সরাসরি ভিজিট করুন:
- 📄 **সকল নোটিশ বোর্ড:** [{PORTAL_RECENT_NOTICES}]({PORTAL_RECENT_NOTICES})
- 📅 **পরীক্ষা সংক্রান্ত রুটিন ও নোটিশ:** [{PORTAL_EXAM_NOTICES}]({PORTAL_EXAM_NOTICES})
- 🌐 **অনলাইন ফরম পূরণ পোর্টাল (EMS):** [{PORTAL_EMS}]({PORTAL_EMS})"""
                citations = [
                    SourceCitation(title=f"{subj_bn} Official Notice Board", url=PORTAL_RECENT_NOTICES, category="Notice Board"),
                    SourceCitation(title="Examination Notices & Guidelines", url=PORTAL_EXAM_NOTICES, category="Exam Notices")
                ]

            return NoticeQueryResult(
                query=query,
                filters=filters,
                matched_notices=[],
                has_subject_filter=True,
                is_empty_subject_result=True,
                formatted_reply=reply,
                citations=citations
            )

        # 3. General recent notices request (no subject specified)
        else:
            notice_bullets = []
            citations = []
            for n in notices[:limit]:
                notice_bullets.append(f"• **{n['date']}:** [{n['title']}]({n['url']})")
                citations.append(SourceCitation(
                    title=n["title"][:80],
                    url=n["url"],
                    date=n["date"],
                    category="General Notice"
                ))

            bullets_text = "\n\n".join(notice_bullets)
            reply = f"""### 📄 জাতীয় বিশ্ববিদ্যালয়ের সাম্প্রতিক নোটিশসমূহ:

জাতীয় বিশ্ববিদ্যালয়ের অফিশিয়াল ওয়েবসাইট ([nu.ac.bd]({PORTAL_RECENT_NOTICES})) অনুযায়ী প্রকাশিত সর্বশেষ নোটিশ নিচে তালিকাভুক্ত করা হলো:

{bullets_text}

---
🔗 **সকল নোটিশ দেখতে:** [সকল নোটিশ বোর্ড (nu.ac.bd)]({PORTAL_RECENT_NOTICES}) | [পরীক্ষা রুটিন]({PORTAL_EXAM_NOTICES})
💡 *যেকোনো নোটিশের শিরোনামে ক্লিক করে সরাসরি মূল বিজ্ঞপ্তি ও PDF দেখতে পারবেন।*"""

            return NoticeQueryResult(
                query=query,
                filters=filters,
                matched_notices=notices,
                has_subject_filter=False,
                is_empty_subject_result=False,
                formatted_reply=reply,
                citations=citations
            )


# Global singleton instance
_notice_service: Optional[NoticeFilterService] = None

def get_notice_filter_service() -> NoticeFilterService:
    global _notice_service
    if _notice_service is None:
        _notice_service = NoticeFilterService()
    return _notice_service
