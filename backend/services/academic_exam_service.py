"""
National University Bangladesh - Academic Examination Information Service
Handles structured administrative examination information lifecycle and 
student chatbot query grounding with small modern nice looking vertical cards.
"""

from typing import Optional, List, Dict, Any, Tuple
import re
from backend.models.schemas import ChatResponse, SourceCitation
from db.sql_store import get_sql_store

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


def format_exam_card_markdown(item: Dict[str, Any]) -> str:
    """
    Renders an official Academic Examination Card as Small Modern Nice Looking Vertical Cards.
    Empty fields display neutral notice 'তথ্য এখনো প্রকাশ করা হয়নি।'
    """
    prog = item.get("program_type", "Honours")
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
    <span class="font-bold text-slate-700 flex items-center gap-1.5">
      <span>🔗</span>
      <span>অফিসিয়াল পোর্টাল:</span>
    </span>
    <div class="flex flex-wrap gap-1.5">
      <a href="{reval_link}" target="_blank" class="bg-white hover:bg-blue-50 text-blue-700 border border-blue-200 px-2.5 py-1 rounded-lg font-semibold transition shadow-2xs inline-flex items-center gap-1">
        <span>ফলাফল পোর্টাল (Revaluation Link)</span>
        <span>↗</span>
      </a>
      <a href="{college_link}" target="_blank" class="bg-white hover:bg-indigo-50 text-indigo-700 border border-indigo-200 px-2.5 py-1 rounded-lg font-semibold transition shadow-2xs inline-flex items-center gap-1">
        <span>কলেজভিত্তিক রেজাল্ট অনুসন্ধান (College-wise Result)</span>
        <span>↗</span>
      </a>
      <a href="https://www.nu.ac.bd/recent-news-notice.php" target="_blank" class="bg-white hover:bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-1 rounded-lg font-semibold transition shadow-2xs inline-flex items-center gap-1">
        <span>জাতীয় বিশ্ববিদ্যালয় নোটিশ বোর্ড</span>
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
