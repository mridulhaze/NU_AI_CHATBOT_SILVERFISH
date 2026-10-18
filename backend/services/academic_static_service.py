"""
National University Bangladesh - Academic Exam Static Info Service
Provides structured responses for static examination schedules and result milestones
configured by Admin in SQLite (Honours, Degree Pass, Master's, Professional).
"""

from typing import Optional, List, Dict, Any
import re
from backend.models.schemas import ChatResponse, SourceCitation
from db.sql_store import get_sql_store

STATIC_CITATIONS = [
    SourceCitation(title="জাতীয় বিশ্ববিদ্যালয় ফলাফল ও পুনর্নিরীক্ষণ পোর্টাল", url="https://results.nu.ac.bd/", date="অফিসিয়াল পোর্টাল"),
    SourceCitation(title="কলেজভিত্তিক ফলাফল ও তথ্য অনুসন্ধান", url="http://103.113.200.68/nu-app/search.php", date="ERP রেজাল্ট সার্ভার"),
    SourceCitation(title="পরীক্ষা নিয়ন্ত্রণ দপ্তর ও নোটিশ বোর্ড", url="https://www.nu.ac.bd/recent-news-notice.php", date="অফিসিয়াল রুটিন")
]

def _format_single_record(item: Dict[str, Any], program_title: str) -> str:
    part_name = item.get("part_or_year") or "১ম বর্ষ / পার্ট ১"
    exam_year = item.get("exam_year") or "চলমান"
    incourse = item.get("incourse_date") or "বিজ্ঞপ্তি প্রকাশের অপেক্ষায়"
    last_incourse = item.get("last_date_incourse_marks") or "ঘোষণা হয়নি"
    form_fillup = item.get("form_fillup_date") or "ঘোষিত হয়নি"
    exam_date = item.get("exam_date") or "নির্ধারিত হয়নি"
    routine_url = item.get("routine_url") or ""
    admit_card = item.get("admit_card_date") or "পরীক্ষার পূর্বে কলেজ থেকে দেওয়া হবে"
    last_exam = item.get("last_date_exam") or "রুটিন অনুযায়ী সমাপ্য"
    practical_date = item.get("practical_marks_date") or "তত্ত্বীয় পরীক্ষার পর"
    last_practical = item.get("last_date_practical_marks") or "ঘোষণা হয়নি"
    prob_result = item.get("probable_result_date") or "পরীক্ষা সমাপ্তির ৩ মাসের মধ্যে"
    pub_result = item.get("result_publish_date") or "অপেক্ষমান"
    is_published = item.get("results_published") or "No"
    pub_badge = "✅ প্রকাশিত হয়েছে" if str(is_published).lower() in ["yes", "true", "1", "হ্যাঁ"] else "⏳ প্রকাশিত হয়নি"
    rescrutiny_apply = item.get("rescrutiny_apply_date") or "ফলাফল প্রকাশের পর ৩০ দিন"
    rescrutiny_pub = item.get("rescrutiny_result_date") or "আবেদনের পর প্রক্রিয়াধীন"
    cert_date = item.get("certificate_printing_date") or "ফলাফল প্রকাশের পর পর্যায়ক্রমে"
    is_printed = item.get("printed_status") or "No"
    print_badge = "✅ প্রিন্ট চলমান" if str(is_printed).lower() in ["yes", "true", "1", "হ্যাঁ"] else "⏳ প্রিন্ট অপেক্ষমান"
    reval_link = item.get("revaluation_result_link") or "https://results.nu.ac.bd/"
    college_link = item.get("collegewise_result_link") or "http://103.113.200.68/nu-app/search.php"
    notes = item.get("notes") or ""

    routine_display = f"[{routine_url}]({routine_url})" if routine_url and routine_url.startswith("http") else (routine_url or "অফিসিয়াল পোর্টালে প্রকাশ্য")

    card = f"""#### 📌 {program_title} — {part_name} (পরীক্ষার সাল: {exam_year})

| কার্যক্রম / মাইলফলক | তারিখ ও বিবরণ |
| :--- | :--- |
| 📝 **ইনকোর্স পরীক্ষার তারিখ** | {incourse} |
| ⏰ **ইনকোর্স নম্বর এন্ট্রির শেষ তারিখ** | {last_incourse} |
| 📋 **ফরম পূরণ (Form Fill-up)** | {form_fillup} |
| 📅 **পরীক্ষা শুরুর তারিখ** | {exam_date} |
| 📜 **পরীক্ষার রুটিন** | {routine_display} |
| 🪪 **প্রবেশপত্র (Admit Card) বিতরণ** | {admit_card} |
| 🏁 **তত্ত্বীয় পরীক্ষা সমাপ্তির তারিখ** | {last_exam} |
| 🧪 **ব্যবহারিক পরীক্ষা ও নম্বর এন্ট্রি** | {practical_date} |
| ⏳ **ব্যবহারিক নম্বর এন্ট্রির শেষ তারিখ** | {last_practical} |
| 📊 **সম্ভাব্য ফলাফল প্রকাশের তারিখ** | {prob_result} |
| 📢 **ফলাফল প্রকাশের তারিখ** | {pub_result} ({pub_badge}) |
| 🔍 **পুনর্নিরীক্ষণের (Re-scrutiny) আবেদন** | {rescrutiny_apply} |
| 📑 **পুনর্নিরীক্ষণের ফল প্রকাশ** | {rescrutiny_pub} |
| 🎓 **সনদ/মার্কশিট/ট্রান্সক্রিপ্ট প্রিন্টিং** | {cert_date} ({print_badge}) |
"""
    if notes:
        card += f"\n💡 **বিশেষ নির্দেশনা:** {notes}\n"

    card += f"\n🔗 **দ্রুত সেবা লিংক:**\n• [ফলাফল ও পুনর্নিরীক্ষণ পোর্টাল]({reval_link})\n• [কলেজভিত্তিক ফলাফল ও তথ্য অনুসন্ধান]({college_link})\n"
    return card

def get_academic_static_response(query: str) -> Optional[ChatResponse]:
    """
    Evaluates query against academic static exam info triggers.
    Returns rich card if matching Honours, Degree Pass, Master's, or Professional exam info.
    """
    q = query.lower().strip()
    sql_store = get_sql_store()

    # Determine matched program
    program_type = None
    program_title = ""
    suggested_chips = []

    # 1. Honours Triggers
    if any(k in q for k in ["অনার্স পরীক্ষা বিষয়ক তথ্য", "অনার্স পরীক্ষা", "honours exam", "hons exam", "অনার্স পরীক্ষার"]):
        program_type = "Honours"
        program_title = "অনার্স (সম্মান) পরীক্ষা বিষয়ক তথ্য"
        suggested_chips = ["অনার্স ১ম বর্ষ", "অনার্স ২য় বর্ষ", "অনার্স ৩য় বর্ষ", "অনার্স ৪র্থ বর্ষ", "📅 পরীক্ষার রুটিন", "🏠 মূল মেনু"]

    # 2. Degree Pass Triggers
    elif any(k in q for k in ["ডিগ্রী পরীক্ষা বিষয়ক তথ্য", "ডিগ্রি পরীক্ষা বিষয়ক তথ্য", "ডিগ্রী পরীক্ষা", "ডিগ্রি পরীক্ষা", "degree exam", "degree pass"]):
        program_type = "Degree Pass"
        program_title = "ডিগ্রি (পাস) পরীক্ষা বিষয়ক তথ্য"
        suggested_chips = ["ডিগ্রী ১ম বর্ষ", "ডিগ্রী ২য় বর্ষ", "ডিগ্রী ৩য় বর্ষ", "📅 পরীক্ষার রুটিন", "🏠 মূল মেনু"]

    # 3. Master's Triggers
    elif any(k in q for k in ["মাস্টার্স পরীক্ষা বিষয়ক তথ্য", "মাস্টাস পরীক্ষা বিষয়ক তথ্য", "মাস্টার্স পরীক্ষা", "মাস্টাস পরীক্ষা", "masters exam"]):
        program_type = "Master's"
        program_title = "মাস্টার্স পরীক্ষা বিষয়ক তথ্য"
        suggested_chips = ["মাস্টার্স শেষ পর্ব", "মাস্টার্স প্রিলিমিনারি", "📅 পরীক্ষার রুটিন", "🏠 মূল মেনু"]

    # 4. Professional Triggers
    elif any(k in q for k in ["প্রফেশনাল পরীক্ষা বিষয়ক তথ্য", "প্রফেশনাল পরীক্ষা", "professional exam"]):
        program_type = "Professional"
        program_title = "প্রফেশনাল কোর্স পরীক্ষা বিষয়ক তথ্য"
        suggested_chips = ["প্রফেশনাল ১ম বর্ষ", "প্রফেশনাল ২য় বর্ষ", "প্রফেশনাল ৩য় বর্ষ", "প্রফেশনাল ৪র্থ বর্ষ", "🏠 মূল মেনু"]

    # Check for specific part sub-queries like "অনার্স ১ম বর্ষ", "ডিগ্রী ৩য় বর্ষ"
    specific_part = None
    if "১ম বর্ষ" in q or "1st year" in q or "part 1" in q or "পার্ট ১" in q:
        specific_part = "Part 1"
    elif "২য় বর্ষ" in q or "2nd year" in q or "part 2" in q or "পার্ট ২" in q:
        specific_part = "Part 2"
    elif "৩য় বর্ষ" in q or "3rd year" in q or "part 3" in q or "পার্ট ৩" in q:
        specific_part = "Part 3"
    elif "৪র্থ বর্ষ" in q or "4th year" in q or "part 4" in q or "পার্ট ৪" in q:
        specific_part = "Part 4"
    elif "প্রিলিমিনারি" in q or "preliminary" in q:
        specific_part = "Preliminary"
    elif "শেষ পর্ব" in q or "final" in q:
        specific_part = "Final"

    # If user just asked "অনার্স ১ম বর্ষ" without saying "পরীক্ষা", detect program type
    if not program_type:
        if "অনার্স" in q or "honours" in q:
            program_type = "Honours"
            program_title = "অনার্স (সম্মান) পরীক্ষা বিষয়ক তথ্য"
            suggested_chips = ["অনার্স ১ম বর্ষ", "অনার্স ২য় বর্ষ", "অনার্স ৩য় বর্ষ", "অনার্স ৪র্থ বর্ষ", "🏠 মূল মেনু"]
        elif "ডিগ্রী" in q or "ডিগ্রি" in q or "degree" in q:
            program_type = "Degree Pass"
            program_title = "ডিগ্রি (পাস) পরীক্ষা বিষয়ক তথ্য"
            suggested_chips = ["ডিগ্রী ১ম বর্ষ", "ডিগ্রী ২য় বর্ষ", "ডিগ্রী ৩য় বর্ষ", "🏠 মূল মেনু"]
        elif "মাস্টার্স" in q or "মাস্টাস" in q or "masters" in q:
            program_type = "Master's"
            program_title = "মাস্টার্স পরীক্ষা বিষয়ক তথ্য"
            suggested_chips = ["মাস্টার্স শেষ পর্ব", "মাস্টার্স প্রিলিমিনারি", "🏠 মূল মেনু"]
        elif "প্রফেশনাল" in q or "professional" in q:
            program_type = "Professional"
            program_title = "প্রফেশনাল কোর্স পরীক্ষা বিষয়ক তথ্য"
            suggested_chips = ["প্রফেশনাল ১ম বর্ষ", "প্রফেশনাল ২য় বর্ষ", "প্রফেশনাল ৩য় বর্ষ", "প্রফেশনাল ৪র্থ বর্ষ", "🏠 মূল মেনু"]

    if not program_type:
        return None

    # Fetch from SQLite
    all_records = sql_store.list_academic_static_info(program_type=program_type)

    # Filter by specific part if specified
    if specific_part:
        matched = [r for r in all_records if str(r.get("part_or_year")).lower() == specific_part.lower()]
        if matched:
            all_records = matched

    reply = f"### 🎓 {program_title}\n\n"
    reply += "জাতীয় বিশ্ববিদ্যালয়ের পরীক্ষা নিয়ন্ত্রণ দপ্তর ও এডমিন প্যানেল কর্তৃক সংরক্ষিত সাম্প্রতিক একাডেমিক ও পরীক্ষা বিষয়ক হালনাগাদ তথ্য নিচে উপস্থাপন করা হলো:\n\n"

    if all_records:
        for item in all_records:
            reply += _format_single_record(item, program_title) + "\n---\n\n"
    else:
        # Default placeholder if admin hasn't inserted rows yet
        default_item = {
            "part_or_year": specific_part or "সকল বর্ষ / পার্ট",
            "exam_year": "২০২৪/২০২৫",
            "incourse_date": "কলেজের নোটিশ অনুযায়ী নির্ধারিত",
            "last_date_incourse_marks": "পরীক্ষা শুরুর পূর্বে",
            "form_fillup_date": "অনলাইনে ইএমএস (EMS) পোর্টালে প্রকাশ্য",
            "exam_date": "জাতীয় বিশ্ববিদ্যালয়ের অফিসিয়াল রুটিন অনুযায়ী",
            "routine_url": "https://www.nu.ac.bd/recent-news-notice.php",
            "admit_card_date": "কলেজ কর্তৃপক্ষ কর্তৃক পরীক্ষার পূর্বে বিতরণ",
            "last_date_exam": "রুটিন অনুযায়ী সমাপ্য",
            "practical_marks_date": "তত্ত্বীয় পরীক্ষার সমাপ্তির পর স্ব স্ব কেন্দ্রে",
            "last_date_practical_marks": "বিজ্ঞপ্তিতে উল্লেখিত সময়সীমা অনুযায়ী",
            "probable_result_date": "পরীক্ষা শেষের ৩ মাসের মধ্যে",
            "result_publish_date": "অফিসিয়াল পোর্টালে ফলাফল প্রকাশ করা হয়",
            "results_published": "No",
            "rescrutiny_apply_date": "ফলাফল প্রকাশের পর ৩০ কার্যদিবসের মধ্যে",
            "rescrutiny_result_date": "আবেদনের পর প্রক্রিয়াকরণ শেষে প্রকাশ",
            "certificate_printing_date": "ফলাফল প্রকাশের পর অনলাইনে আবেদনসাপেক্ষে প্রস্তুত",
            "printed_status": "No",
            "revaluation_result_link": "https://results.nu.ac.bd/",
            "collegewise_result_link": "http://103.113.200.68/nu-app/search.php",
            "notes": "এডমিন প্যানেলে নতুন সময়সূচি এন্ট্রি করা মাত্রই তা এখানে সরাসরি আপডেট হবে।"
        }
        reply += _format_single_record(default_item, program_title)

    return ChatResponse(
        reply=reply.strip(),
        citations=STATIC_CITATIONS,
        intent="ACADEMIC_EXAM_STATIC_INFO",
        skill_used="academic_static_info",
        suggested_chips=suggested_chips
    )
