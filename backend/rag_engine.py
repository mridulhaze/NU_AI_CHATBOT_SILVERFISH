import re
import time
import logging
import json
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Tuple, Optional, Iterator
from google import genai

from .config import settings
from .models import ChatMessage, ChatResponse, SourceCitation
from db.sql_store import get_sql_store
from db.vector_store import get_vector_store
from token_service.service import get_token_service
from backend.services.session_memory import get_session_memory
from backend.services.notice_service import get_notice_filter_service
from .orchestrator.preloaded_responses import get_preloaded_response, WELCOME_REPLY, CITATIONS_GENERAL

logger = logging.getLogger("NU_RAG_ENGINE")

TOKEN_ID_REGEX = re.compile(r'\b(NU-\d{4}-\d{6})\b', re.IGNORECASE)

# National University All Offices & Departments Directory (33+ Departments)
OFFICES_DIRECTORY = [
    # --- Under Vice-Chancellor ---
    {"name": "উপাচার্য দপ্তর (Vice-Chancellor Office)", "slug": "vc-office", "parent": "উপাচার্য দপ্তর (Vice-Chancellor)", "keywords": ["vice chancellor", "vc", "উপাচার্য", "ভিসি", "উপাচার্য দপ্তর"], "url": "https://www.nu.ac.bd/vice-chancellor-office.php"},
    {"name": "রেজিস্ট্রার দপ্তর (Registrar Office)", "slug": "registrar-office", "parent": "উপাচার্য দপ্তর (Vice-Chancellor)", "keywords": ["registrar", "রেজিস্ট্রার", "রেজিস্টার", "রেজিস্ট্রার দপ্তর"], "url": "https://www.nu.ac.bd/Registrar-office.php"},
    {"name": "পরিকল্পনা ও উন্নয়ন দপ্তর (Planning & Development)", "slug": "planning-development", "parent": "উপাচার্য দপ্তর (Vice-Chancellor)", "keywords": ["planning", "development", "পরিকল্পনা", "উন্নয়ন"], "url": "https://www.nu.ac.bd/planning-development.php"},
    {"name": "জনসংযোগ, তথ্য ও পরামর্শ দপ্তর (Public Relations)", "slug": "public-relations", "parent": "উপাচার্য দপ্তর (Vice-Chancellor)", "keywords": ["public relations", "pr", "জনসংযোগ", "পরামর্শ"], "url": "https://www.nu.ac.bd/public-relations.php"},
    {"name": "আন্তর্জাতিক ডেস্ক দপ্তর (International Desk)", "slug": "international-desk", "parent": "উপাচার্য দপ্তর (Vice-Chancellor)", "keywords": ["international", "আন্তর্জাতিক", "আন্তর্জাতিক ডেস্ক"], "url": "https://www.nu.ac.bd/international-desk-department.php"},
    {"name": "শৃঙ্খলা ও নিরাপত্তা দপ্তর (Discipline & Security)", "slug": "discipline-security", "parent": "উপাচার্য দপ্তর (Vice-Chancellor)", "keywords": ["security", "discipline", "নিরাপত্তা", "শৃঙ্খলা"], "url": "https://www.nu.ac.bd/office-of-the-discipline-and-security.php"},
    {"name": "প্রকৌশল দপ্তর (Engineering Department)", "slug": "engineering", "parent": "উপাচার্য দপ্তর (Vice-Chancellor)", "keywords": ["engineering", "প্রকৌশল", "ইঞ্জিনিয়ারিং"], "url": "https://www.nu.ac.bd/engineering-department-office.php"},
    {"name": "কলেজ মনিটরিং ও মূল্যায়ন দপ্তর (College Monitoring & Evaluation)", "slug": "college-monitoring", "parent": "উপাচার্য দপ্তর (Vice-Chancellor)", "keywords": ["monitoring", "evaluation", "মনিটরিং", "মূল্যায়ন"], "url": "https://www.nu.ac.bd/College-Monitoring-and-Evaluation-Department.php"},
    {"name": "আইন বিষয়ক দপ্তর (Law Affairs)", "slug": "law-affairs", "parent": "উপাচার্য দপ্তর (Vice-Chancellor)", "keywords": ["law", "আইন", "লিগ্যাল", "আইন বিষয়ক"], "url": "https://www.nu.ac.bd/Law_Department.php"},

    # --- Under Pro Vice-Chancellor 1 ---
    {"name": "উপ-উপাচার্য দপ্তর (Pro-Vice-Chancellor Office)", "slug": "pro-vc-office", "parent": "উপ-উপাচার্য দপ্তর ১ (Pro-Vice-Chancellor 1)", "keywords": ["pro-vc", "pro vc", "উপ-উপাচার্য", "প্রো-ভিসি"], "url": "https://www.nu.ac.bd/Pro-Vice-Chancellor-Office.php"},
    {"name": "পরীক্ষা নিয়ন্ত্রক দপ্তর (Controller of Examination Office)", "slug": "exam-controller", "parent": "উপ-উপাচার্য দপ্তর ১ (Pro-Vice-Chancellor 1)", "keywords": ["exam controller", "controller", "পরীক্ষা নিয়ন্ত্রক", "পরীক্ষা নিয়ন্ত্রক"], "url": "https://www.nu.ac.bd/exam-controller-office.php"},
    {"name": "কলেজ পরিদর্শন দপ্তর (College Inspection Department)", "slug": "inspector-of-college", "parent": "উপ-উপাচার্য দপ্তর ১ (Pro-Vice-Chancellor 1)", "keywords": ["college inspection", "inspector", "কলেজ পরিদর্শন", "পরিদর্শক"], "url": "https://www.nu.ac.bd/inspector-of-college.php"},
    {"name": "অভ্যন্তরীণ নিরীক্ষা দপ্তর (Internal Audit)", "slug": "internal-audit", "parent": "উপ-উপাচার্য দপ্তর ১ (Pro-Vice-Chancellor 1)", "keywords": ["audit", "নিরীক্ষা", "অডিট", "অভ্যন্তরীণ নিরীক্ষা"], "url": "https://www.nu.ac.bd/internal-audit-office.php"},
    {"name": "প্রকাশনা ও বিপণন দপ্তর (Publication & Marketing)", "slug": "publication-marketing", "parent": "উপ-উপাচার্য দপ্তর ১ (Pro-Vice-Chancellor 1)", "keywords": ["publication", "marketing", "প্রকাশনা", "বিপণন"], "url": "https://www.nu.ac.bd/publication-section.php"},
    {"name": "শারীরিক শিক্ষা ও সাংস্কৃতিক দপ্তর (Physical Education & Cultural Affairs)", "slug": "physical-education", "parent": "উপ-উপাচার্য দপ্তর ১ (Pro-Vice-Chancellor 1)", "keywords": ["physical education", "শারীরিক শিক্ষা", "খেলাধুলা", "সাংস্কৃতিক"], "url": "https://www.nu.ac.bd/physical-education.php"},
    {"name": "এস্টেট দপ্তর (Estate Department)", "slug": "estate", "parent": "উপ-উপাচার্য দপ্তর ১ (Pro-Vice-Chancellor 1)", "keywords": ["estate", "এস্টেট"], "url": "https://www.nu.ac.bd/Estate_Department.php"},
    {"name": "মানবসম্পদ উন্নয়ন ও শুদ্ধাচার দপ্তর (HR Development & Integrity)", "slug": "hr-development", "parent": "উপ-উপাচার্য দপ্তর ১ (Pro-Vice-Chancellor 1)", "keywords": ["hr", "human resource", "মানবসম্পদ", "শুদ্ধাচার", "সততা"], "url": "https://www.nu.ac.bd/Human-Resource-Development-and-Integrity.php"},

    # --- Under Pro Vice-Chancellor 2 ---
    {"name": "আইসিটি দপ্তর (ICT Department)", "slug": "ict-department", "parent": "উপ-উপাচার্য দপ্তর ২ (Pro-Vice-Chancellor 2)", "keywords": ["ict", "আইসিটি", "কম্পিউটার", "শাহনেওয়াজ", "shahnewaz", "programmer", "প্রোগ্রামার"], "url": "https://www.nu.ac.bd/ict-department.php"},
    {"name": "পরিবহন শাখা (Transport Section)", "slug": "transport-department", "parent": "উপ-উপাচার্য দপ্তর ২ (Pro-Vice-Chancellor 2)", "keywords": ["transport", "পরিবহন", "বাস", "গাড়ি", "যানবাহন"], "url": "https://www.nu.ac.bd/transport-department.php"},
    {"name": "চিকিৎসা কেন্দ্র (Medical Centre)", "slug": "medical-centre", "parent": "উপ-উপাচার্য দপ্তর ২ (Pro-Vice-Chancellor 2)", "keywords": ["medical", "চিকিৎসা", "ডাক্তার", "মেডিকেল"], "url": "https://www.nu.ac.bd/medical-services-department.php"},
    {"name": "আঞ্চলিক কেন্দ্র সমন্বয় দপ্তর (Regional Center Coordination)", "slug": "regional-center-coord", "parent": "উপ-উপাচার্য দপ্তর ২ (Pro-Vice-Chancellor 2)", "keywords": ["regional center", "আঞ্চলিক কেন্দ্র", "সমন্বয়"], "url": "https://www.nu.ac.bd/Regional-Center-Co-ordination.php"},
    {"name": "তথ্য ও সেবা দপ্তর (Information & Services)", "slug": "information-services", "parent": "উপ-উপাচার্য দপ্তর ২ (Pro-Vice-Chancellor 2)", "keywords": ["information services", "তথ্য ও সেবা", "হেল্পডেস্ক"], "url": "https://www.nu.ac.bd/Information-and-services-department.php"},
    {"name": "ক্রয় দপ্তর (Procurement Department)", "slug": "procurement", "parent": "উপ-উপাচার্য দপ্তর ২ (Pro-Vice-Chancellor 2)", "keywords": ["procurement", "store", "ক্রয়", "কেনাকাটা"], "url": "https://www.nu.ac.bd/Procurement_and_Store_Department.php"},
    {"name": "কেন্দ্রীয় ভাণ্ডার দপ্তর (Central Store)", "slug": "central-store", "parent": "উপ-উপাচার্য দপ্তর ২ (Pro-Vice-Chancellor 2)", "keywords": ["central store", "কেন্দ্রীয় ভাণ্ডার", "ভাণ্ডার"], "url": "https://www.nu.ac.bd/department-of-central-store.php"},

    # --- Under Treasurer ---
    {"name": "ট্রেজারার দপ্তর (Treasurer Office)", "slug": "treasurer-office", "parent": "কোষাধ্যক্ষ দপ্তর (Treasurer)", "keywords": ["treasurer", "ট্রেজারার", "কোষাধ্যক্ষ"], "url": "https://www.nu.ac.bd/Treasurer-office.php"},
    {"name": "অনলাইন শিক্ষা দপ্তর (Online Education)", "slug": "online-education", "parent": "কোষাধ্যক্ষ দপ্তর (Treasurer)", "keywords": ["online education", "অনলাইন শিক্ষা", "ই-লার্নিং"], "url": "https://www.nu.ac.bd/Online_Education_Department.php"},
    {"name": "গ্রন্থাগার দপ্তর (Library Department)", "slug": "library-department", "parent": "কোষাধ্যক্ষ দপ্তর (Treasurer)", "keywords": ["library", "গ্রন্থাগার", "লাইব্রেরি"], "url": "https://www.nu.ac.bd/library-department.php"},
    {"name": "অর্থ ও হিসাব দপ্তর (Finance & Accounts)", "slug": "finance-accounts", "parent": "কোষাধ্যক্ষ দপ্তর (Treasurer)", "keywords": ["finance", "accounts", "অর্থ", "হিসাব"], "url": "https://www.nu.ac.bd/finance-account.php"},
    {"name": "শিক্ষক প্রশিক্ষণ দপ্তর (Teachers Training Department)", "slug": "teachers-training", "parent": "কোষাধ্যক্ষ দপ্তর (Treasurer)", "keywords": ["teachers training", "শিক্ষক প্রশিক্ষণ"], "url": "https://www.nu.ac.bd/teachers-training-information.php"},
    {"name": "ভর্তি ও রেজিস্ট্রেশন সেল (Admission & Registration Cell)", "slug": "admission-registration", "parent": "কোষাধ্যক্ষ দপ্তর (Treasurer)", "keywords": ["admission cell", "registration cell", "ভর্তি ও রেজিস্ট্রেশন सेल", "ভর্তি সেল"], "url": "https://www.nu.ac.bd/admission-and-registration-cell.php"},
    {"name": "মুক্তিযুদ্ধ ও বাংলাদেশ গবেষণা ইনস্টিটিউট (ILBS)", "slug": "ilbs", "parent": "কোষাধ্যক্ষ দপ্তর (Treasurer)", "keywords": ["ilbs", "মুক্তিযুদ্ধ", "বাংলাদেশ গবেষণা"], "url": "https://www.nu.ac.bd/ILBS.php"},
    {"name": "আইকিউএসি (IQAC)", "slug": "iqac", "parent": "কোষাধ্যক্ষ দপ্তর (Treasurer)", "keywords": ["iqac", "আইকিউএসি", "quality assurance"], "url": "https://www.nu.ac.bd/IQAC.php"},
    {"name": "ফরেনসিক সায়েন্স ও সাইবার সিকিউরিটি ইনস্টিটিউট (IFSCS)", "slug": "ifscs", "parent": "কোষাধ্যক্ষ দপ্তর (Treasurer)", "keywords": ["ifscs", "ফরেনসিক", "সাইবার সিকিউরিটি", "সাইবার"], "url": "https://www.nu.ac.bd/IFSCS.php"}
]

NAME_TRANSLITERATIONS = {
    "mridul": ["মুদুল", "মৃদুল", "mri_roy"],
    "mri": ["মুদুল", "মৃদুল", "mri_roy"],
    "rakib": ["রাকিব"],
    "rakibul": ["রাকিবুল"],
    "shahnewaz": ["শাহনেওয়াজ", "শাহনেওয়াজ"],
    "monirul": ["মনিরুল"],
    "shahinul": ["শাহীনুল"],
    "rejaul": ["রেজাউল"],
    "billal": ["বিল্লাল"],
    "biplab": ["বিপ্লব"],
    "mobarak": ["মোবারক"],
    "hayder": ["হায়দার", "হায়দার"],
    "nazimul": ["নাজিমুল"],
    "faruk": ["ফারুক"],
    "azharul": ["আজহারুল"],
    "mahfuz": ["মাহফুজ"],
    "shofiqul": ["শফিকুল", "শফিক"],
    "hasan": ["হাসান"],
    "hossain": ["হোসেন"]
}

def convert_bn_to_en_digits(text: str) -> str:
    if not text:
        return ""
    trans = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
    return str(text).translate(trans)

def normalize_phones_in_text(text: str) -> str:
    if not text:
        return ""
    # 1. Convert phone numbers following labels like ফোন/মোবাইল, মোবাইল, ফোন, Tel, Mobile, Phone, Fax
    def _repl_phone_line(match):
        prefix = match.group(1)
        nums = match.group(2)
        return prefix + convert_bn_to_en_digits(nums)

    # Convert phone/mobile fields
    text = re.sub(r'((?:ফোন|মোবাইল|ফোন\/মোবাইল|টেলিফোন|Phone|Mobile|Tel|Fax)\s*[:ঃ\-]\s*)([০-৯\d\+\-\s\,\/]{4,})', _repl_phone_line, text, flags=re.IGNORECASE)
    # Also convert any remaining sequences of 6+ Bengali digits (phone numbers) into English digits
    text = re.sub(r'[০-৯]{5,}', lambda m: convert_bn_to_en_digits(m.group(0)), text)
    return text

class RAGEngine:
    def __init__(self):
        self.sql_store = get_sql_store()
        self.vector_store = get_vector_store()
        self.token_service = get_token_service()
        self.api_key = settings.GEMINI_API_KEY
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        self.models = [settings.PRIMARY_MODEL] + settings.FALLBACK_MODELS
        self.greeted_sessions: set[str] = set()

    @staticmethod
    def detect_language(text: str) -> str:
        """
        Default language is Bangla ('bn').
        Only return 'en' if text is exclusively English and explicitly requests English.
        """
        text_lower = text.lower()
        if "in english" in text_lower or "english please" in text_lower or "reply in english" in text_lower:
            return "en"
        
        bengali_chars = len(re.findall(r'[\u0980-\u09FF]', text))
        if bengali_chars > 0:
            return "bn"

        # By default, National University assistant defaults to Bangla
        return "bn"

    @staticmethod
    def classify_intent(query: str) -> str:
        q = query.lower()
        # 1. Token ID lookup or token check
        if TOKEN_ID_REGEX.search(query) or any(w in q for w in ["check token", "token status", "টোকেন চেক", "টোকেন স্ট্যাটাস", "আমার টোকেন", "check my token", "টোকেন নম্বর"]):
            return "token_lookup"
        # 2. Token service menu / creation request
        elif any(w in q for w in ["token service", "টোকেন সার্ভিস", "create token", "support token", "টোকেন খুলব", "টোকেন বানাব", "অভিযোগ", "সমস্যা জানাতে চাই", "support desk", "হেল্পডেস্ক"]):
            return "token_service_menu"
        # 3. High-Priority Student Services & Admissions
        elif any(w in q for w in ["tc", "transfer certificate", "college transfer", "ছাড়পত্র", "ছাড়পত্র", "কলেজ পরিবর্তন", "কলেজ ট্রান্সফার", "টিসি"]):
            return "tc_services"
        elif any(w in q for w in ["admission", "apply", "eligibility", "merit", "release slip", "ভর্তি", "আবেদন", "যোগ্যতা", "মেধা তালিকা", "রিলিজ", "app11"]):
            return "admissions"
        elif any(w in q for w in ["correction", "সংশোধন", "নাম সংশোধন", "ভুল সংশোধন", "মার্কশিট সংশোধন", "সনদপত্র সংশোধন"]):
            return "document_correction"
        elif any(w in q for w in ["certificate", "transcript", "marksheet", "সনদপত্র", "ট্রান্সক্রিপ্ট", "নম্বরপত্র", "মূল সনদ", "সাময়িক সনদ"]):
            return "certificate_transcript"
        elif any(w in q for w in ["erp", "student login", "103.113.200.68/nu-app", "nu-app", "103.113.200.68", "স্টুডেন্ট লগইন", "ইআরপি"]):
            return "erp_services"
        elif any(w in q for w in ["services", "service menu", "all services", "সার্ভিস মেনু", "সকল সেবা", "সেবাসমূহ"]):
            return "services_menu"
        elif any(w in q for w in ["cmes", "tmis", "ttis", "wes", "viva bill", "ডরমিটরি", "ভিডিও লেকচার", "সত্যায়ন"]):
            return "specialized_services"
        elif any(w in q for w in ["notice", "routine", "circular", "exam date", "schedule", "নোটিশ", "রুটিন", "পরীক্ষা", "বিজ্ঞপ্তি", "সময়সূচি"]):
            return "notices"
        elif any(w in q for w in ["result", "cgpa", "gpa", "grading", "marks", "sms", "scrutiny", "রেজাল্ট", "ফলাফল", "গ্রেডিং", "পুনর্নিরীক্ষণ", "নম্বর"]):
            return "results"
        elif any(w in q for w in ["form", "fillup", "fill-up", "ems", "sonali", "fee", "ফরম", "ফিলাপ", "ফি", "সোনালী সেবা"]):
            return "form_fillup"
        # 4. Office & Department Directory query (Only when specific office / officer name is requested)
        elif (
            any(any(k in q for k in d["keywords"]) for d in OFFICES_DIRECTORY)
            or any(k in q for k in NAME_TRANSLITERATIONS)
            or any(w in q for w in ["who is", "কে আছেন", "দপ্তর কর্মকর্তা", "কর্মকর্তা তালিকা", "কর্মচারী তালিকা", "অফিসার", "ফোন নম্বর", "ইমেইল অ্যাড্রেস", "officer list", "employee list", "director", "programmer", "analyst", "engineer", "registrar", "controller", "vc", "উপ-উপাচার্য"])
        ):
            return "department_offices"
        elif any(w in q for w in ["hi", "hello", "hey", "salam", "assalamu", "সালাম", "কেমন", "নমস্কার"]):
            return "greeting"
        return "general"

    def _safe_vector_search(self, query: str, k: int = 5):
        try:
            return self.vector_store.similarity_search(query, k=k)
        except Exception as e:
            logger.warning(f"Vector search error: {e}")
            return []

    def retrieve_context(self, query: str, intent: str) -> Tuple[str, List[SourceCitation], float]:
        context_parts = []
        citations: List[SourceCitation] = []
        confidence = 0.85

        # 1. Structured SQL & Domain Lookups
        if intent == "token_lookup":
            token_match = TOKEN_ID_REGEX.search(query)
            if token_match:
                token_id = token_match.group(1).upper()
                token_data = self.token_service.get_public_token_details(token_id)
                if token_data:
                    t_text = f"### Verified Student Support Token Record:\n"
                    t_text += f"- Token ID: {token_data.token_id}\n"
                    t_text += f"- Service: {token_data.service_name} ({token_data.service_type})\n"
                    t_text += f"- Problem: {token_data.problem}\n"
                    t_text += f"- Current Status: {token_data.status} ({token_data.status_display})\n"
                    t_text += f"- Assigned Solver: {token_data.solver_name or 'Under Review'}\n"
                    t_text += f"- Solution Message: {token_data.solve_message or 'No solution entered yet.'}\n"
                    t_text += f"- Created Date: {token_data.created_date}\n"
                    t_text += f"- Solved Date: {token_data.solved_date or 'N/A'}\n"
                    context_parts.append(t_text)
                    citations.append(SourceCitation(
                        title=f"Support Token #{token_data.token_id}",
                        url=f"token://{token_data.token_id}",
                        category="Support Token"
                    ))
                    return t_text, citations, 1.0

        elif intent == "department_offices":
            q_lower = query.lower()

            # Check if user asks for full list of all departments
            if any(w in q_lower for w in ["list all departments", "all departments", "all department", "সকল দপ্তর", "সকল বিভাগ", "দপ্তরের তালিকা", "list of departments", "list of all departments", "list of all departmets", "সকল দপ্তরের তালিকা"]):
                dept_list_text = "### জাতীয় বিশ্ববিদ্যালয় অফিশিয়াল দপ্তর ও বিভাগ সমূহের পূর্ণাঙ্গ তালিকা (All 33 Official Departments Hierarchy):\n\n"
                
                # Group by Parent Office
                hierarchy_groups = {}
                for d in OFFICES_DIRECTORY:
                    parent = d.get("parent", "সাধারণ দপ্তর")
                    if parent not in hierarchy_groups:
                        hierarchy_groups[parent] = []
                    hierarchy_groups[parent].append(d)

                for parent, depts in hierarchy_groups.items():
                    dept_list_text += f"#### 🏛️ {parent}:\n"
                    for d in depts:
                        dept_list_text += f"- **[{d['name']}]({d['url']})**\n"
                    dept_list_text += "\n"

                context_parts.append(dept_list_text)
                for d in OFFICES_DIRECTORY[:5]:
                    citations.append(SourceCitation(
                        title=d['name'],
                        url=d['url'],
                        category="Offices & Departments"
                    ))
                return dept_list_text, citations, 1.0

            matched_depts = [d for d in OFFICES_DIRECTORY if any(k in q_lower for k in d["keywords"])]
            
            # Prioritize VC Office if VC keywords present
            if any(k in q_lower for k in ["vc", "vice chancellor", "vice-chancellor", "উপাচার্য", "ভিসি"]):
                matched_depts = [d for d in OFFICES_DIRECTORY if d["slug"] == "vc-office"]
            elif not matched_depts:
                # Default to ICT & Registrar if general officer query
                matched_depts = [OFFICES_DIRECTORY[0], OFFICES_DIRECTORY[1]]

            for dept in matched_depts:
                citations.append(SourceCitation(
                    title=f"{dept['name']} Directory & Officers",
                    url=dept['url'],
                    category="Offices & Departments"
                ))

            # 1. Direct Search in SQL Officers Directory
            officers = []
            
            # First, fetch all verified officers & staff belonging to matched department(s)
            for dept in matched_depts:
                dept_officers = self.sql_store.get_officers_by_department(dept["slug"])
                for o in dept_officers:
                    if o not in officers:
                        officers.append(o)

            # Clean search terms for specific person/title search
            search_terms = [w.strip().lower() for w in re.split(r'[\s\?\,\.\!]+', query) if len(w.strip()) > 2 and w.strip().lower() not in ["who", "is", "the", "of", "and", "in", "to", "for", "ke", "ki", "কারা", "কে", "কী", "দপ্তর", "তালিকা", "তথ্য", "দিন", "all", "list", "employee", "officer", "department"]]
            for term in search_terms:
                found = self.sql_store.search_officers(term, limit=10)
                for o in found:
                    if o not in officers:
                        officers.append(o)
                # Check transliteration variants
                if term in NAME_TRANSLITERATIONS:
                    for variant in NAME_TRANSLITERATIONS[term]:
                        v_found = self.sql_store.search_officers(variant, limit=10)
                        for vo in v_found:
                            if vo not in officers:
                                officers.append(vo)

            # If specific designation queried
            if any(p in q_lower for p in ["assistant programmer", "সহকারী প্রোগ্রামার", "সহকারি প্রোগ্রামার"]):
                for o in self.sql_store.search_officers("assistant programmer", limit=20) + self.sql_store.search_officers("সহকারী প্রোগ্রামার", limit=20):
                    if o not in officers:
                        officers.append(o)
            elif any(p in q_lower for p in ["senior programmer", "সিনিয়র প্রোগ্রামার", "সিনিয়র প্রোগ্রামার"]):
                for o in self.sql_store.search_officers("senior programmer", limit=15) + self.sql_store.search_officers("সিনিয়র প্রোগ্রামার", limit=15):
                    if o not in officers:
                        officers.append(o)
            elif any(p in q_lower for p in ["system analyst", "সিস্টেম এনালিস্ট"]):
                for o in self.sql_store.search_officers("system analyst", limit=10) + self.sql_store.search_officers("সিস্টেম এনালিস্ট", limit=10):
                    if o not in officers:
                        officers.append(o)
            elif any(p in q_lower for p in ["network administrator", "নেটওয়ার্ক এডমিনিস্ট্রেটর"]):
                for o in self.sql_store.search_officers("network administrator", limit=10) + self.sql_store.search_officers("নেটওয়ার্ক এডমিনিস্ট্রেটর", limit=10):
                    if o not in officers:
                        officers.append(o)
            elif any(p in q_lower for p in ["maintenance engineer", "মেইনটেন্যান্স ইঞ্জিনিয়ার"]):
                for o in self.sql_store.search_officers("maintenance engineer", limit=10) + self.sql_store.search_officers("মেইনটেন্যান্স", limit=10):
                    if o not in officers:
                        officers.append(o)
            elif any(p in q_lower for p in ["programmer", "প্রোগ্রামার"]):
                for o in self.sql_store.search_officers("programmer", limit=15) + self.sql_store.search_officers("প্রোগ্রামার", limit=15):
                    if o not in officers:
                        officers.append(o)
            elif any(p in q_lower for p in ["director", "পরিচালক"]):
                for o in self.sql_store.search_officers("director", limit=10) + self.sql_store.search_officers("পরিচালক", limit=10):
                    if o not in officers:
                        officers.append(o)
            elif any(p in q_lower for p in ["registrar", "রেজিস্ট্রার", "রেজিস্টার"]):
                for o in self.sql_store.search_officers("registrar", limit=10) + self.sql_store.search_officers("রেজিস্ট্রার", limit=10):
                    if o not in officers:
                        officers.append(o)

            if officers:
                off_text = "### Official National University Officers & Employee Directory (Direct Database Match):\n"
                for o in officers:
                    name = o.get('name') or o.get('officer_name', '')
                    desig = o.get('designation_bn') or o.get('designation_en') or o.get('designation', '')
                    dept = o.get('department_name') or o.get('department', '')
                    off_text += f"- **নাম (Name):** {name}\n"
                    if desig:
                        off_text += f"  **পদবি (Designation):** {desig}\n"
                    if dept:
                        off_text += f"  **দপ্তর (Department):** {dept}\n"
                    if o.get('phone') and str(o['phone']).strip() not in ['-', 'None', '']:
                        phone_en = convert_bn_to_en_digits(str(o['phone']).strip())
                        off_text += f"  **ফোন/মোবাইল (Phone):** {phone_en}\n"
                    if o.get('email') and str(o['email']).strip() not in ['-', 'None', '']:
                        off_text += f"  **ইমেইল (Email):** {o['email']}\n"
                    off_text += "\n"
                context_parts.append(off_text)
                confidence = 0.98

        elif intent == "tc_services":
            citations.append(SourceCitation(
                title="জাতীয় বিশ্ববিদ্যালয় স্টুডেন্ট ERP সার্ভিসেস পোর্টাল",
                url="http://103.113.200.68/nu-app/",
                category="Student ERP Portal"
            ))
            tc_text = """### Official National University Student ERP Transfer (TC) Rules:
- **Online Application Portal:** http://103.113.200.68/nu-app/
- **Eligible Courses:** Honours (Regular), Degree (Pass), Professional.
- **Requirements:** Student Registration Card, HSC Registration, Both College Principal Approvals.
- **Fee Payment:** Online Sonali Seba Pay Slip generated after online application.
- **Instructions:** Never visit offline brokers. All TC operations are 100% digital via http://103.113.200.68/nu-app/."""
            context_parts.append(tc_text)
            confidence = 0.95

        elif intent in ["certificate_transcript", "document_correction", "erp_services"]:
            citations.append(SourceCitation(
                title="জাতীয় বিশ্ববিদ্যালয় স্টুডেন্ট ERP সার্ভিসেস পোর্টাল",
                url="http://103.113.200.68/nu-app/",
                category="Student ERP Portal"
            ))
            svc_text = """### Official National University Student ERP Portal Guidelines:
- **Official URL:** http://103.113.200.68/nu-app/
- **Available Digital Services:**
  1. Original Certificate & Provisional Certificate (মূল ও সাময়িক সনদপত্র উত্তোলন)
  2. Academic Transcript & Marksheet (একাডেমিক ট্রান্সক্রিপ্ট ও নম্বরপত্র উত্তোলন)
  3. Student College Transfer / TC (ছাড়পত্র / কলেজ পরিবর্তন)
  4. Registration & Admit Card Name/Subject Correction (রেজিস্ট্রেশন কার্ড ও প্রবেশপত্র তথ্য সংশোধন)
- **Fee Payment Process:** All fees must be deposited exclusively via online generated **Sonali Seba** pay slips."""
            context_parts.append(svc_text)
            confidence = 0.95

        elif intent == "admissions":
            citations.append(SourceCitation(
                title="জাতীয় বিশ্ববিদ্যালয় অনলাইন ভর্তি পোর্টাল",
                url="http://app11.nu.edu.bd/",
                category="Admission Portal"
            ))
            adm_text = """### National University Online Admission System (app11.nu.edu.bd):
- **Official Admission Portal:** http://app11.nu.edu.bd/
- **Application Process:** Online submission with SSC & HSC Roll/Reg details.
- **Merit Lists:** 1st Merit List, 2nd Merit List, Quota Merit List, and 1st & 2nd Release Slips (রিলিজ স্লিপ)."""
            context_parts.append(adm_text)
            confidence = 0.95

        if intent != "department_offices" or not officers:
            with ThreadPoolExecutor(max_workers=3) as executor:
                fut_faqs = executor.submit(self.sql_store.search_faqs, query, 3)
                fut_vector = executor.submit(self._safe_vector_search, query, 5)

                faqs = fut_faqs.result()
                vector_results = fut_vector.result()
        else:
            faqs = self.sql_store.search_faqs(query, 2)
            vector_results = []

        try:
            solved_cases = self.token_service.find_similar_solved_cases(query, top_k=2, vector_matches=vector_results)
            if solved_cases:
                solved_text = "### Previously Solved Student Support Cases (Anonymized):\n"
                for s in solved_cases:
                    solved_text += f"- **Service:** {s.service_name}\n"
                    solved_text += f"  **Problem:** {s.problem}\n"
                    solved_text += f"  **Common Solution:** {s.solution}\n\n"
                context_parts.append(solved_text)
                confidence = max(confidence, 0.92)
        except Exception as e:
            logger.warning(f"Error retrieving solved cases: {e}")

        if faqs:
            faq_text = "### Verified Academic Knowledge & FAQs:\n"
            for f in faqs:
                faq_text += f"Q: {f['question']}\nA: {f['answer']}\nSource: {f['source_url']}\n\n"
                citations.append(SourceCitation(
                    title=f['question'][:60],
                    url=f.get('source_url', 'https://www.nu.ac.bd/'),
                    category=f.get('category', 'FAQ')
                ))
            context_parts.append(faq_text)
            confidence = max(confidence, 0.90)

        if vector_results:
            vector_text = "### Related Official Portal Documentation:\n"
            for doc, score in vector_results:
                vector_text += doc.page_content + "\n\n"
                src = doc.metadata.get("source", "https://www.nu.ac.bd/recent-news-notice.php")
                citations.append(SourceCitation(
                    title=doc.metadata.get("category", "General Knowledge"),
                    url=src,
                    category=doc.metadata.get("type", "documentation")
                ))
            context_parts.append(vector_text)
            confidence = max(confidence, 0.88)

        seen_urls = set()
        unique_citations = []
        for c in citations:
            if c.url not in seen_urls:
                seen_urls.add(c.url)
                unique_citations.append(c)

        combined_context = "\n\n---\n\n".join(context_parts)
        if not combined_context.strip():
            confidence = 0.3

        return combined_context, unique_citations, confidence

    def get_suggested_chips(self, intent: str, lang: str) -> List[str]:
        chips_map = {
            "token_lookup": ["🎫 নতুন টোকেন তৈরি করুন", "🎫 টোকেন সার্ভিস মেনু", "📄 সকল নোটিশ বোর্ড"],
            "token_service_menu": ["📝 ফরম পূরণ সমস্যা", "💻 ইএমএস লগইন সমস্যা", "📜 সনদপত্র সংক্রান্ত", "🔍 খাতা পুনঃনিরীক্ষণ"],
            "tc_services": ["📜 স্টুডেন্ট nu-app পোর্টাল", "💳 সোনালী সেবা ফি প্রদান", "🎫 টিসি সহায়তা টোকেন", "🏠 মূল মেনু"],
            "admissions": ["🎓 অনলাইন ভর্তি পোর্টাল (app11)", "🎯 রিলিজ স্লিপের নিয়ম", "📋 মেধা তালিকার নিয়ম", "🎫 ভর্তি সহায়তা টোকেন"],
            "certificate_transcript": ["📜 nu-app সার্টিফিকেট আবেদন", "📊 ট্রান্সক্রিপ্ট উত্তোলন", "💳 সোনালী সেবা", "🏠 মূল মেনু"],
            "document_correction": ["✏️ nu-app সংশোধন পোর্টাল", "💳 সোনালী সেবা পে-স্লিপ", "🎫 সংশোধন সাপোর্ট টোকেন"],
            "erp_services": ["🌐 স্টুডেন্ট nu-app পোর্টাল", "📜 টিসি আবেদন", "🎓 সার্টিফিকেট আবেদন", "🏠 মূল মেনু"],
            "services_menu": ["🌐 স্টুডেন্ট nu-app পোর্টাল", "🎓 ভর্তি পোর্টাল (app11)", "🔍 WES ভেরিফিকেশন", "📊 CMES পোর্টাল"],
            "department_offices": ["💻 আইসিটি কর্মকর্তা তালিকা", "🏛️ রেজিস্ট্রার দপ্তর কর্মকর্তা তালিকা", "🏢 পরীক্ষা নিয়ন্ত্রক দপ্তর", "📞 সকল দপ্তরের যোগাযোগ তালিকা"],
            "notices": ["📄 সাম্প্রতিক সকল নোটিশ", "📅 অনার্স পরীক্ষার রুটিন", "🌐 ফলাফল দেখার নিয়ম"],
            "results": ["📱 SMS-এ রেজাল্ট দেখার পদ্ধতি", "📊 CGPA গ্রেডিং স্কেল", "📝 খাতা পুনর্নিরীক্ষণ নিয়ম"],
            "form_fillup": ["🎫 ফরম পূরণ সাপোর্ট টোকেন", "💳 সোনালী সেবা ফি প্রদান", "📋 ফরম ফিলাপের নিয়ম"],
            "greeting": ["🎫 টোকেন সার্ভিস (Token Service)", "🎓 ভর্তি পোর্টাল (app11)", "📜 স্টুডেন্ট nu-app সেবা", "📄 সাম্প্রতিক নোটিশ"]
        }
        return chips_map.get(intent, ["🎫 টোকেন সার্ভিস", "📄 সাম্প্রতিক নোটিশ", "🎓 অনার্স ভর্তি তথ্য"])

    def _build_system_prompt(self, query: str, context: str, history: List[ChatMessage], session_id: Optional[str], intent: str, lang: str) -> str:
        session_mem = get_session_memory()
        history_text = session_mem.get_formatted_history_text(session_id, history)
        is_subsequent_turn = bool(history_text) or bool(history) or (session_id and session_id in self.greeted_sessions)

        return f"""You are the official, highly knowledgeable AI Academic Counselor for the National University of Bangladesh (জাতীয় বিশ্ববিদ্যালয়, nu.ac.bd).
Your purpose is to answer student, teacher, and administrative queries accurately, politely, and clearly with verified official information.

### STRICT CONVERSATIONAL RULES:
1. **NO REPETITIVE GREETINGS (একই স্বাগত বক্তব্য বারবার দেওয়া সম্পূর্ণ নিষেধ)**:
   - {"DO NOT include any greeting or welcome message. Jump directly into the factual answer." if is_subsequent_turn else "Only if the user explicitly greets (Hi/Salam), give a concise 1-sentence welcome. Never output long boilerplate welcome texts."}
   - NEVER start your response with 'সম্মানিত শিক্ষার্থী, শিক্ষক এবং জাতীয় বিশ্ববিদ্যালয়ের শুভানুধ্যায়ী...' or repetitive boilerplate.
2. **MANDATORY CLICKABLE NOTICE HYPERLINKS (নোটিশের প্রতিটি লিংক ক্লিকেবল করা বাধ্যতামূলক)**:
   - When listing notices or referring to circulars, you MUST format EVERY notice title as a clickable Markdown link `[তারিখ: নোটিশের শিরোনাম](URL)` using the direct URL from the context.
   - Never output notice titles as plain unclickable text bullets.
3. **DEFAULT LANGUAGE IS BANGLA (বাংলা)**:
   - Always respond in clear, courteous, and grammatically accurate Bengali (বাংলা) by default.
   - Only respond in English if the user explicitly requests English.
4. **Strict Grounding & Truthfulness**:
   - Answer directly using the verified context below.
   - For official dates, circulars, and notices, always provide the published date and official URL.
   - If the exact answer is not present, do NOT hallucinate dates. State what is available and link to the portal.
5. **Accurate Official Portal & Office Links**:
   - All Notice Board (সকল নোটিশ): https://www.nu.ac.bd/recent-news-notice.php
   - Registrar Office (রেজিস্ট্রার দপ্তর): https://www.nu.ac.bd/Registrar-office.php
   - Controller of Examination (পরীক্ষা নিয়ন্ত্রক দপ্তর): https://www.nu.ac.bd/exam-controller-office.php
   - ICT Department (আইসিটি দপ্তর): https://www.nu.ac.bd/ict-department.php
   - Vice-Chancellor Office (উপাচার্য দপ্তর): https://www.nu.ac.bd/vice-chancellor-office.php
   - Pro-Vice-Chancellor Office (উপ-উপাচার্য দপ্তর): https://www.nu.ac.bd/Pro-Vice-Chancellor-Office.php
   - Treasurer Office (ট্রেজারার দপ্তর): https://www.nu.ac.bd/Treasurer-office.php
   - Admission Portal (ভর্তি পোর্টাল): http://app11.nu.edu.bd/
   - Results Portal (ফলাফল পোর্টাল): https://results.nu.ac.bd/
   - Form Fill-up & EMS (ফরম পূরণ): http://ems.nu.ac.bd/
6. **Privacy Protection**:
   - NEVER fabricate or expose personal individual student roll results. Instruct students to check securely at https://results.nu.ac.bd/ or via SMS to 16222.
8. **Student TC, Certificate, Transcript & Correction Portal Rules**:
   - For any inquiries regarding College Transfer / TC (ছাড়পত্র), Original/Provisional Certificates, Academic Transcripts, Marksheets, and Document/Name Corrections, ALWAYS instruct the student to log in to the official **National University Student ERP Services Portal (http://103.113.200.68/nu-app/ or http://103.113.200.68/nu-app/)** with complete step-by-step guidance.
7. **University Offices & Employee Directory Queries**:
   - When asked about any National University office (e.g. Registrar, Examination Controller, ICT, VC office, Finance, Library, Planning, Security), provide the officer names, designations, phone numbers, emails, location, and the direct official department URL formatted in Markdown (e.g. `[রেজিস্ট্রার দপ্তর](https://www.nu.ac.bd/Registrar-office.php)`).
9. **Strict University Leadership Reference (বিশ্ববিদ্যালয়ের শীর্ষ নেতৃত্ব)**:
   - **Vice-Chancellor (উপাচার্য): Professor Dr. ASM Amanullah (প্রফেসর ড. এ এস এম আমানুল্লাহ)**. Email: `vc@nu.ac.bd`, `dramanullah@hotmail.com`. Official URL: https://www.nu.ac.bd/vice-chancellor-office.php
   - **Pro-Vice-Chancellors (উপ-উপাচার্য): Prof. Md. Lutfor Rahaman and Professor Dr. Mohammad Ali Zinnah**.
   - **Treasurer (কোষাধ্যক্ষ / ট্রেজারার): Professor Dr. Md. Nazmul Hossain / Prof. Dr. A. T. M. Zafrul Azam**.
   - **Registrar (রেজিস্ট্রার): Molla Mahfuz Al-Hossain (মোল্লা মাহফুজ আল-হোসেন)**.
   - NEVER name any other person as the Vice-Chancellor or top leadership. When asked about VC or VC office employees, always present Professor Dr. ASM Amanullah as the Vice-Chancellor, followed by the officers and employees of the Vice-Chancellor Office.
10. **PHONE & MOBILE NUMBERS MUST ALWAYS BE IN ENGLISH DIGITS (0-9)**:
    - Always format all phone numbers, mobile numbers, telephone numbers, IP numbers, and helpline numbers exclusively in English digits (e.g. `01711-677577`, `01973-062388`, `+8802996691511`).
    - NEVER output contact phone or mobile numbers using Bengali digits (০-৯).

---
### Verified University Context:
{context if context.strip() else "No specific records found in local database for this query."}

---
### Recent Conversation History:
{history_text if history_text else "No prior turns in this session."}

---
### Current User Question:
{query}

Compose a structured, formatted markdown response in Bengali (বাংলা):
"""

    def stream_answer_query(self, query: str, history: List[ChatMessage], session_id: Optional[str] = None) -> Iterator[str]:
        start_time = time.perf_counter()
        lang = self.detect_language(query)
        intent = self.classify_intent(query)

        preloaded = get_preloaded_response(query)
        if preloaded:
            elapsed = time.perf_counter() - start_time
            yield f"data: {json.dumps({'type': 'token', 'content': preloaded.reply}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'citations', 'citations': [c.model_dump() for c in preloaded.citations]}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'chips', 'chips': preloaded.suggested_chips}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'response_time_sec': round(elapsed, 2), 'intent': preloaded.intent, 'confidence': preloaded.confidence})}\n\n"
            return

        if intent == "greeting":
            elapsed = time.perf_counter() - start_time
            chips = self.get_suggested_chips("greeting", lang)
            yield f"data: {json.dumps({'type': 'token', 'content': WELCOME_REPLY}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'citations', 'citations': [c.model_dump() for c in CITATIONS_GENERAL]}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'chips', 'chips': chips}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'response_time_sec': round(elapsed, 2), 'intent': 'greeting', 'confidence': 1.0})}\n\n"
            return

        if intent in ["token_service_menu", "token_lookup"] or (intent == "notices" and any(w in query.lower() for w in ["সাম্প্রতিক", "সকল নোটিশ", "সব নোটিশ", "recent", "latest notice", "all notice", "বিজ্ঞপ্তি"])):
            fast_resp = self.answer_query(query, history, session_id)
            elapsed = time.perf_counter() - start_time
            yield f"data: {json.dumps({'type': 'token', 'content': fast_resp.reply}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'citations', 'citations': [c.model_dump() for c in fast_resp.citations]}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'chips', 'chips': fast_resp.suggested_chips}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'response_time_sec': round(elapsed, 2), 'intent': fast_resp.intent, 'confidence': fast_resp.confidence})}\n\n"
            return

        yield f"data: {json.dumps({'type': 'status', 'content': 'তথ্য অনুসন্ধান করছি...'}, ensure_ascii=False)}\n\n"

        try:
            context, citations, confidence = self.retrieve_context(query, intent)
        except Exception as e:
            logger.error(f"Error in retrieve_context during stream: {e}", exc_info=True)
            context, citations, confidence = "", [], 0.5

        yield f"data: {json.dumps({'type': 'status', 'content': 'উত্তর তৈরি করছি...'}, ensure_ascii=False)}\n\n"

        try:
            system_prompt = self._build_system_prompt(query, context, history, session_id, intent, lang)
        except Exception as e:
            logger.error(f"Error in _build_system_prompt: {e}", exc_info=True)
            system_prompt = f"User query: {query}\nContext: {context}"

        stream_success = False
        if self.client:
            for model_name in self.models:
                try:
                    stream = self.client.models.generate_content_stream(
                        model=model_name,
                        contents=system_prompt
                    )
                    for chunk in stream:
                        if chunk and chunk.text:
                            yield f"data: {json.dumps({'type': 'token', 'content': chunk.text}, ensure_ascii=False)}\n\n"
                    stream_success = True
                    break
                except Exception as err:
                    logger.warning(f"Streaming on {model_name} failed: {err}")

        if not stream_success:
            if context.strip():
                fallback_text = (
                    "জাতীয় বিশ্ববিদ্যালয়ের ডাটাবেজ থেকে পাওয়া প্রাসঙ্গিক তথ্য নিচে দেওয়া হলো:\n\n"
                    + context[:900]
                    + "\n\nবিস্তারিত তথ্যের জন্য অফিশিয়াল ওয়েবসাইট ভিজিট করুন: [সকল নোটিশ বোর্ড](https://www.nu.ac.bd/recent-news-notice.php)"
                )
            else:
                fallback_text = (
                    "দুঃখিত, এই বিষয়টি সম্পর্কে নির্দিষ্ট কোনো নোটিশ বা তথ্য এই মুহূর্তে পাওয়া যায়নি।\n\n"
                    "অনুগ্রহ করে সর্বশেষ তথ্য জানতে জাতীয় বিশ্ববিদ্যালয়ের অফিশিয়াল পোর্টালগুলো দেখুন:\n"
                    "- 📄 [সকল নোটিশ বোর্ড](https://www.nu.ac.bd/recent-news-notice.php)\n"
                    "- 🎓 [ভর্তি পোর্টাল](http://app11.nu.edu.bd/)\n"
                    "- 🌐 [ফলাফল পোর্টাল](https://results.nu.ac.bd/)\n"
                    "- 📝 [ফরম ফিলাপ পোর্টাল (EMS)](http://ems.nu.ac.bd/)"
                )
            yield f"data: {json.dumps({'type': 'token', 'content': fallback_text}, ensure_ascii=False)}\n\n"

        elapsed = time.perf_counter() - start_time
        try:
            chips = self.get_suggested_chips(intent, lang)
        except Exception:
            chips = ["🎫 টোকেন সার্ভিস", "📋 টোকেন স্ট্যাটাস", "📄 সাম্প্রতিক নোটিশ"]

        yield f"data: {json.dumps({'type': 'citations', 'citations': [c.model_dump() for c in citations]}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'chips', 'chips': chips}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'response_time_sec': round(elapsed, 2), 'intent': intent, 'confidence': confidence})}\n\n"

    def answer_query(self, query: str, history: List[ChatMessage], session_id: Optional[str] = None) -> ChatResponse:
        lang = self.detect_language(query)
        intent = self.classify_intent(query)

        preloaded = get_preloaded_response(query)
        if preloaded:
            return preloaded

        if intent == "greeting":
            chips = self.get_suggested_chips("greeting", lang)
            return ChatResponse(
                reply=WELCOME_REPLY,
                sources=[c.url for c in CITATIONS_GENERAL],
                citations=CITATIONS_GENERAL,
                suggested_chips=chips,
                confidence=1.0,
                intent="greeting",
                language=lang,
                is_fallback=False
            )

        if intent == "token_service_menu":
            instant_token = self.token_service.generate_instant_token()
            t_id = instant_token.token_id
            created_date = instant_token.created_date
            est_date = instant_token.estimated_solve_date or "২-৩ কার্যদিবস"

            services = self.token_service.get_services()
            service_links = []
            for idx, s in enumerate(services):
                name_en = s['service_name']
                name_bn = s['service_name_bn']
                desc = s.get('description', '')
                code = s['service_code']
                link_html = f"{idx+1}. <a href=\"javascript:void(0)\" onclick=\"openServiceFormPopup('{code}', '{name_en} ({name_bn})', '{t_id}')\" style=\"font-weight:700;color:#047857;text-decoration:underline;cursor:pointer;\">📝 {name_en} ({name_bn})</a> — <span style=\"color:#475569;\">{desc}</span>"
                service_links.append(link_html)

            service_list_html = "<br>".join(service_links)
            menu_reply = f"""### 🎫 আপনার সাপোর্ট টোকেন সফলভাবে তৈরি হয়েছে!

--------------------------------
* 🎫 **টোকেন নম্বর:** `{t_id}`
* 🟡 **বর্তমান স্ট্যাটাস:** **PENDING (অপেক্ষমান)**
* 📅 **তারিখ:** {created_date}
* ⏳ **সম্ভাব্য সমাধান তারিখ:** **{est_date}**

> ⚠️ **ভবিষ্যতের জন্য অত্যন্ত জরুরি নোটিশ:**
> অনুগ্রহ করে আপনার **টোকেন নম্বরটি (`{t_id}`) এখনই লিখে বা কপি করে সংরক্ষণ করে রাখুন**। পরবর্তীতে এই টোকেন নম্বর দিয়ে চ্যাটবটে সরাসরি আপনার সমস্যার সর্বশেষ অবস্থা ও সমাধান জানতে পারবেন।
--------------------------------

### 📋 অনুগ্রহ করে নিচে আপনার সেবার নামের উপর ক্লিক করে বিস্তারিত ফরম পূরণ করুন:

{service_list_html}

👉 **উপরে আপনার সেবায় ক্লিক করুন অথবা নিচের বাটনে চাপ দিন:**"""

            chips = [f"📝 {s['service_name_bn']} ({t_id})" for s in services[:6]] + [f"📋 Check {t_id}"]
            return ChatResponse(
                reply=menu_reply,
                sources=[],
                citations=[],
                suggested_chips=chips,
                confidence=1.0,
                intent="token_service_menu",
                language=lang,
                is_fallback=False
            )

        token_attach_match = TOKEN_ID_REGEX.search(query)
        if token_attach_match and not any(w in query.lower() for w in ["check", "status", "স্ট্যাটাস", "চেক", "কোথায়"]):
            t_id = token_attach_match.group(1).upper()
            q_clean = query.replace(t_id, "").strip()
            services = self.token_service.get_services()
            selected_svc = None
            for s in services:
                if s["service_code"].lower() in q_clean.lower() or s["service_name"].lower() in q_clean.lower() or s["service_name_bn"] in q_clean:
                    selected_svc = s
                    break

            if not selected_svc and len(q_clean) > 3:
                selected_svc = {"service_code": "OTHER", "service_name": "General Support", "service_name_bn": "সাধারণ সহায়তা"}

            if selected_svc:
                ok = self.token_service.update_token_details(
                    token_id=t_id,
                    service_type=selected_svc["service_code"],
                    problem=q_clean if len(q_clean) > 3 else f"{selected_svc['service_name']} বিষয়ক সেবা প্রয়োজন।"
                )
                if ok:
                    est_date = self.token_service.get_public_token_details(t_id).estimated_solve_date if hasattr(self.token_service, 'get_public_token_details') else "২-৩ কার্যদিবস"
                    confirm_reply = f"""### ✅ টোকেন বিস্তারিত সফলভাবে সংরক্ষিত হয়েছে!

--------------------------------
* 🎫 **টোকেন নম্বর:** `{t_id}`
* 🎯 **সেবা/বিষয়:** {selected_svc['service_name_bn']} ({selected_svc['service_name']})
* 📝 **সমস্যার বিবরণ:** {q_clean}
* 🟡 **স্ট্যাটাস:** **PENDING (অপেক্ষমান)**
* ⏳ **সম্ভাব্য সমাধানের তারিখ:** **{est_date or '২-৩ কার্যদিবস'}**
--------------------------------

আপনার সমস্যাটি জাতীয় বিশ্ববিদ্যালয়ের সংশ্লিষ্ট কর্মকর্তা/ডেস্কে সফলভাবে পাঠানো হয়েছে। আপনি যেকোনো সময় এই টোকেন নম্বর দিয়ে চ্যাটবটে স্ট্যাটাস দেখতে পারবেন।"""
                    return ChatResponse(
                        reply=confirm_reply,
                        sources=[],
                        citations=[],
                        suggested_chips=[f"📋 Check {t_id}", "🎫 নতুন টোকেন", "📄 সাম্প্রতিক নোটিশ"],
                        confidence=1.0,
                        intent="token_service_update",
                        language=lang,
                        is_fallback=False
                    )

        token_match = TOKEN_ID_REGEX.search(query)
        if token_match:
            t_id = token_match.group(1).upper()
            detail = self.token_service.get_public_token_details(t_id)
            if detail:
                solve_msg_part = f"\n* 💡 **গৃহীত সমাধান:** {detail.solve_message}" if detail.solve_message else ""
                solver_part = f"\n* 👨‍💼 **দায়িত্বপ্রাপ্ত দপ্তর:** {detail.solver_name}" if detail.solver_name else ""
                est_part = f"\n* ⏳ **সম্ভাব্য সমাধানের তারিখ:** {detail.estimated_solve_date}" if getattr(detail, 'estimated_solve_date', None) else ""
                
                status_reply = f"""### 🎫 সাপোর্ট টোকেন অনুসন্ধান ফলাফল

--------------------------------
* 🎫 **টোকেন নম্বর:** `{detail.token_id}`
* 🎯 **সেবা ক্যাটাগরি:** {detail.service_name}
* 📝 **সমস্যার বিবরণ:** {detail.problem}
* 📌 **বর্তমান অবস্থা:** **{detail.status_display}** ({detail.status}){solver_part}{est_part}
* 📅 **তৈরির তারিখ:** {detail.created_date}{solve_msg_part}
--------------------------------

💡 *জাতীয় বিশ্ববিদ্যালয়ের এআই বা মানব হেল্পডেস্ক আপনার সমস্যাটি দ্রুত সমাধানের জন্য কাজ করছে।*"""
                return ChatResponse(
                    reply=status_reply,
                    sources=[],
                    citations=[SourceCitation(title=f"Token {detail.token_id}", url=f"token://{detail.token_id}", category="Support Token")],
                    suggested_chips=["🎫 নতুন টোকেন তৈরি করুন", "📄 সাম্প্রতিক নোটিশ", "🏠 মূল মেনু"],
                    confidence=1.0,
                    intent="token_lookup",
                    language=lang,
                    is_fallback=False
                )

        # Fast path for Subject/Course-Specific or General Notices via NoticeFilterService
        if intent == "notices":
            notice_service = get_notice_filter_service()
            notice_result = notice_service.process_notice_query(query, limit=8)
            if notice_result and (notice_result.has_subject_filter or notice_result.matched_notices or notice_result.filters.is_general_notice_query):
                session_mem = get_session_memory()
                session_mem.add_turn(session_id, "user", query)
                session_mem.add_turn(session_id, "assistant", notice_result.formatted_reply)
                return ChatResponse(
                    reply=notice_result.formatted_reply,
                    sources=[c.url for c in notice_result.citations],
                    citations=notice_result.citations,
                    suggested_chips=["📄 সকল নোটিশ বোর্ড", "📅 পরীক্ষার রুটিন", "🌐 ফলাফল ও SMS নিয়ম"],
                    confidence=1.0,
                    intent="notices",
                    language=lang,
                    is_fallback=False
                )

        # Fast-path: Check Admin Many-to-Many Q&A Knowledge Base
        qa_match = self.sql_store.match_qa_knowledge(query)
        if qa_match:
            session_mem = get_session_memory()
            session_mem.add_turn(session_id, "user", query)
            session_mem.add_turn(session_id, "assistant", qa_match["answer"])
            return ChatResponse(
                reply=qa_match["answer"],
                sources=["https://www.nu.ac.bd/"],
                citations=[SourceCitation(title="Verified Q&A Knowledge Base", url="https://www.nu.ac.bd/", category="Admin Knowledge Base")],
                suggested_chips=["📄 সাম্প্রতিক নোটিশ", "🎓 ভর্তি তথ্য", "🎫 টোকেন সার্ভিস"],
                confidence=1.0,
                intent="qa_knowledge_match",
                language=lang,
                is_fallback=False
            )

        context, citations, confidence = self.retrieve_context(query, intent)

        # Log query to gap queue if confidence is low or query is unanswered
        if confidence < 0.60 or not context.strip():
            self.sql_store.log_gap(
                user_query=query,
                language=lang,
                session_id=session_id or "default_session",
                reason=f"low_confidence ({confidence:.2f})"
            )

        # Format multi-turn conversation history
        history_text = ""
        if history:
            recent_turns = history[-6:]
            history_lines = []
            for h in recent_turns:
                role = getattr(h, 'role', None) or (h.get('role') if isinstance(h, dict) else 'user')
                content = getattr(h, 'content', None) or (h.get('content') if isinstance(h, dict) else str(h))
                speaker = 'User' if role == 'user' else 'Assistant'
                history_lines.append(f"{speaker}: {content}")
            history_text = "\n".join(history_lines)

        # Determine if this turn is a subsequent turn in this session
        is_subsequent_turn = bool(history) or (session_id and session_id in self.greeted_sessions)

        # Build Grounded System Prompt
        system_prompt = f"""You are the official, highly knowledgeable AI Academic Counselor for the National University of Bangladesh (জাতীয় বিশ্ববিদ্যালয়, nu.ac.bd).
Your purpose is to answer student, teacher, and administrative queries accurately, politely, and clearly with verified official information.

### STRICT CONVERSATIONAL RULES:
1. **NO REPETITIVE GREETINGS (একই স্বাগত বক্তব্য বারবার দেওয়া সম্পূর্ণ নিষেধ)**:
   - {"DO NOT include any greeting or welcome message. Jump directly into the factual answer." if is_subsequent_turn else "Only if the user explicitly greets (Hi/Salam), give a concise 1-sentence welcome. Never output long boilerplate welcome texts."}
   - NEVER start your response with 'সম্মানিত শিক্ষার্থী, শিক্ষক এবং জাতীয় বিশ্ববিদ্যালয়ের শুভানুধ্যায়ী...' or repetitive boilerplate.
2. **MANDATORY CLICKABLE NOTICE HYPERLINKS (নোটিশের প্রতিটি লিংক ক্লিকেবল করা বাধ্যতামূলক)**:
   - When listing notices or referring to circulars, you MUST format EVERY notice title as a clickable Markdown link `[তারিখ: নোটিশের শিরোনাম](URL)` using the direct URL from the context.
   - Never output notice titles as plain unclickable text bullets.
3. **DEFAULT LANGUAGE IS BANGLA (বাংলা)**:
   - Always respond in clear, courteous, and grammatically accurate Bengali (বাংলা) by default.
   - Only respond in English if the user explicitly requests English.
4. **Strict Grounding & Truthfulness**:
   - Answer directly using the verified context below.
   - For official dates, circulars, and notices, always provide the published date and official URL.
   - If the exact answer is not present, do NOT hallucinate dates. State what is available and link to the portal.
5. **Accurate Official Portal & Office Links**:
   - All Notice Board (সকল নোটিশ): https://www.nu.ac.bd/recent-news-notice.php
   - Registrar Office (রেজিস্ট্রার দপ্তর): https://www.nu.ac.bd/Registrar-office.php
   - Controller of Examination (পরীক্ষা নিয়ন্ত্রক দপ্তর): https://www.nu.ac.bd/exam-controller-office.php
   - ICT Department (আইসিটি দপ্তর): https://www.nu.ac.bd/ict-department.php
   - Vice-Chancellor Office (উপাচার্য দপ্তর): https://www.nu.ac.bd/vice-chancellor-office.php
   - Pro-Vice-Chancellor Office (উপ-উপাচার্য দপ্তর): https://www.nu.ac.bd/Pro-Vice-Chancellor-Office.php
   - Treasurer Office (ট্রেজারার দপ্তর): https://www.nu.ac.bd/Treasurer-office.php
   - Admission Portal (ভর্তি পোর্টাল): http://app11.nu.edu.bd/
   - Results Portal (ফলাফল পোর্টাল): https://results.nu.ac.bd/
   - Form Fill-up & EMS (ফরম পূরণ): http://ems.nu.ac.bd/
6. **Privacy Protection**:
   - NEVER fabricate or expose personal individual student roll results. Instruct students to check securely at https://results.nu.ac.bd/ or via SMS to 16222.
8. **Student TC, Certificate, Transcript & Correction Portal Rules**:
   - For any inquiries regarding College Transfer / TC (ছাড়পত্র), Original/Provisional Certificates, Academic Transcripts, Marksheets, and Document/Name Corrections, ALWAYS instruct the student to log in to the official **National University Student ERP Services Portal (http://103.113.200.68/nu-app/ or http://103.113.200.68/nu-app/)** with complete step-by-step guidance.
7. **University Offices & Employee Directory Queries**:
   - When asked about any National University office (e.g. Registrar, Examination Controller, ICT, VC office, Finance, Library, Planning, Security), provide the officer names, designations, phone numbers, emails, location, and the direct official department URL formatted in Markdown (e.g. `[রেজিস্ট্রার দপ্তর](https://www.nu.ac.bd/Registrar-office.php)`).

---
### Verified University Context:
{context if context.strip() else "No specific records found in local database for this query."}

---
### Recent Conversation History:
{history_text if history_text else "No prior turns in this session."}

---
### Current User Question:
{query}

Compose a structured, formatted markdown response in Bengali (বাংলা):
"""

        bot_reply = None
        is_fallback = False

        if self.client:
            for model_name in self.models:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=system_prompt
                    )
                    if response and response.text:
                        bot_reply = response.text.strip()
                        break
                except Exception as err:
                    logger.warning(f"Generation on {model_name} failed: {err}")
                    time.sleep(1.0)

        # Resilient Graceful Degradation if Gemini API is unreachable or exhausted
        if not bot_reply:
            is_fallback = True
            if context.strip():
                bot_reply = (
                    "জাতীয় বিশ্ববিদ্যালয়ের ডাটাবেজ থেকে পাওয়া প্রাসঙ্গিক তথ্য নিচে দেওয়া হলো:\n\n"
                    + context[:900]
                    + "\n\nবিস্তারিত তথ্যের জন্য অফিশিয়াল ওয়েবসাইট ভিজিট করুন: [সকল নোটিশ বোর্ড](https://www.nu.ac.bd/recent-news-notice.php)"
                )
            else:
                bot_reply = (
                    "দুঃখিত, এই বিষয়টি সম্পর্কে নির্দিষ্ট কোনো নোটিশ বা তথ্য এই মুহূর্তে পাওয়া যায়নি।\n\n"
                    "অনুগ্রহ করে সর্বশেষ তথ্য জানতে জাতীয় বিশ্ববিদ্যালয়ের অফিশিয়াল পোর্টালগুলো দেখুন:\n"
                    "- 📄 [সকল নোটিশ বোর্ড](https://www.nu.ac.bd/recent-news-notice.php)\n"
                    "- 🎓 [ভর্তি পোর্টাল](http://app11.nu.edu.bd/)\n"
                    "- 🌐 [ফলাফল পোর্টাল](https://results.nu.ac.bd/)\n"
                    "- 📝 [ফরম ফিলাপ পোর্টাল (EMS)](http://ems.nu.ac.bd/)\n"
                    "- 💻 [আইসিটি দপ্তর ও কর্মকর্তা তালিকা](https://www.nu.ac.bd/ict-department.php)"
                )

        # Strip boilerplate repetitive greetings if present
        repetitive_patterns = [
            r"^(সম্মানিত শিক্ষার্থী,\s*শিক্ষক এবং জাতীয় বিশ্ববিদ্যালয়ের শুভানুধ্যায়ী,\s*জাতীয় বিশ্ববিদ্যালয়ের অফিশিয়াল এআই একাডেমিক কাউন্সেলর হেল্পডেস্কে আপনাকে স্বাগত জানাচ্ছি।?\s*)",
            r"^(জাতীয় বিশ্ববিদ্যালয়ের অফিশিয়াল এআই একাডেমিক কাউন্সেলর হেল্পডেস্কে আপনাকে স্বাগত জানাচ্ছি।?\s*)",
            r"^(স্বাগতম!\s*জাতীয় বিশ্ববিদ্যালয়ের অফিশিয়াল এআই একাডেমিক কাউন্সেলর হেল্পডেস্কে আপনাকে স্বাগতম।?\s*)"
        ]
        for pat in repetitive_patterns:
            bot_reply = re.sub(pat, "", bot_reply, flags=re.IGNORECASE).strip()

        # Ensure all phone numbers in bot reply use English digits
        bot_reply = normalize_phones_in_text(bot_reply)

        # Record to multi-turn session memory
        session_mem = get_session_memory()
        session_mem.add_turn(session_id, "user", query)
        session_mem.add_turn(session_id, "assistant", bot_reply)

        if session_id:
            self.greeted_sessions.add(session_id)

        source_urls = [c.url for c in citations]
        chips = self.get_suggested_chips(intent, lang)

        return ChatResponse(
            reply=bot_reply,
            sources=source_urls,
            citations=citations,
            suggested_chips=chips,
            confidence=confidence,
            intent=intent,
            language=lang,
            is_fallback=is_fallback
        )

_rag_engine_instance = None

def get_rag_engine() -> RAGEngine:
    global _rag_engine_instance
    if _rag_engine_instance is None:
        _rag_engine_instance = RAGEngine()
    return _rag_engine_instance
