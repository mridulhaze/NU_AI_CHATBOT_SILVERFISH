import re
from typing import Tuple, Optional, Dict, Any

TOKEN_ID_PATTERN = re.compile(r'\b(NU-\d{4}-\d{6})\b', re.IGNORECASE)

SERVICE_KEYWORDS = {
    "FORM_FILLUP": ["form fillup", "form fill up", "form fill-up", "ফরম পূরণ", "ফরম ফিলাপ", "ফি জমা"],
    "TC": ["tc", "transfer certificate", "ছাড়পত্র", "টিসি", "কলেজ পরিবর্তন"],
    "RESCRUTINY": ["rescrutiny", "re-check", "খাতা পুনঃনিরীক্ষণ", "পুনঃনিরীক্ষণ", "খাতা চ্যালেঞ্জ"],
    "EMS": ["ems", "ইএমএস", "ems portal", "ems লগইন", "ems পাসওয়ার্ড"],
    "CERTIFICATE": ["certificate", "সনদপত্র", "মূল সনদ", "সাময়িক সনদ", "সার্টিফিকেট", "provisional certificate"],
    "MARKSHEET": ["marksheet", "transcript", "নম্বরপত্র", "ট্রান্সক্রিপ্ট", "মার্কশিট", "একাডেমিক ট্রান্সক্রিপ্ট"],
    "REGISTRATION": ["registration", "রেজিস্ট্রেশন", "রেজিস্ট্রেশন কার্ড", "দ্বৈত ভর্তি"],
    "ADMISSION": ["admission", "ভর্তি", "app1", "মেধা তালিকা", "রিলিজ স্লিপ", "release slip", "কোটা"],
    "RESULT": ["result", "রেজাল্ট", "ফলাফল", "withheld", "স্থগিত", "cgpa", "gpa", "গ্রেড"]
}

class IntentClassifier:
    @staticmethod
    def classify(message: str, session_context: Optional[Any] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Extracts intent and relevant parameters (Token ID, Service Code, Confirmation intent).
        """
        text = message.strip()
        text_lower = text.lower()
        entities: Dict[str, Any] = {}

        # 1. Check for Token ID pattern (Priority 1)
        token_match = TOKEN_ID_PATTERN.search(text)
        if token_match:
            entities["token_id"] = token_match.group(1).upper()
            return "TOKEN_STATUS", entities

        # 2. Check for Token Creation Confirmation (e.g. user clicks "Create Token")
        if text_lower in ["create token", "create support token", "টোকেন তৈরি করুন", "হ্যাঁ টোকেন তৈরি করুন", "yes create token", "confirm"]:
            return "TOKEN_CONFIRM_CREATE", entities

        # 3. Check for Token Cancellation
        if text_lower in ["cancel", "সমস্যা সমাধান পেয়েছি", "no cancel", "বাতিল", "সমাধান হয়েছে"]:
            return "TOKEN_CANCEL", entities

        # 4. Check for Explicit Token Service Menu Request
        if any(w in text_lower for w in ["token service", "support token", "টোকেন সেবা", "সাপোর্ট টোকেন", "টিকিট", "সমস্যার সমাধান চাই"]):
            return "TOKEN_SERVICE_MENU", entities

        # 5. Check if user selected a specific service
        for code, keywords in SERVICE_KEYWORDS.items():
            if any(k in text_lower for k in keywords):
                entities["service_code"] = code
                break

        # 6. Intent classification based on keywords
        if any(w in text_lower for w in ["recent notice", "latest notice", "notices", "notice", "নোটিশ", "বিজ্ঞপ্তি", "অফিস আদেশ", "সার্কুলার"]):
            return "NOTICE_QUERY", entities

        if any(w in text_lower for w in ["routine", "রুটিন", "exam schedule", "পরীক্ষার সময়সূচী", "পরীক্ষা কেন্দ্র", "admit card"]):
            return "EXAM_QUERY", entities

        if any(w in text_lower for w in ["admission", "ভর্তি", "মেধা তালিকা", "release slip", "রিলিজ স্লিপ"]):
            return "ADMISSION_QUERY", entities

        if any(w in text_lower for w in ["cgpa", "gpa", "marksheet", "রেজাল্ট", "withheld", "স্থগিত"]):
            return "RESULT_QUERY", entities

        if any(w in text_lower for w in ["form", "download pdf", "ডাউনলোড", "সিলেবাস", "syllabus", "doc"]):
            return "DOCUMENT_QUERY", entities

        # 7. If user describes an issue/problem
        if any(w in text_lower for w in ["সমস্যা", "লগইন হচ্ছে না", "ভুল", "error", "problem", "cannot login", "failed", "pending", "আটকে আছে"]):
            return "TOKEN_PROBLEM_SUBMISSION", entities

        return "GENERAL_NU_QUERY", entities

_intent_classifier_instance: Optional[IntentClassifier] = None

def get_intent_classifier() -> IntentClassifier:
    global _intent_classifier_instance
    if _intent_classifier_instance is None:
        _intent_classifier_instance = IntentClassifier()
    return _intent_classifier_instance
