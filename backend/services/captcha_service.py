"""
Lightweight Bot Protection & Math CAPTCHA Service
Provides simple, accessible math & logic challenges (Bengali & English digits)
to distinguish human students from automated scrapers/bots and enable rate-limit bypass.
"""

import time
import uuid
import hmac
import hashlib
import random
from typing import Dict, Any, Optional

SECRET_SALT = "nu-bangladesh-academic-bot-shield-2026"

# Bengali to English digit translation
BN_TO_EN = {
    '০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4',
    '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9'
}

EN_TO_BN = {v: k for k, v in BN_TO_EN.items()}

def to_bn_digits(num: int) -> str:
    return "".join(EN_TO_BN.get(c, c) for c in str(num))

def normalize_digits(s: str) -> str:
    cleaned = "".join(BN_TO_EN.get(c, c) for c in str(s).strip())
    return "".join(c for c in cleaned if c.isdigit() or c == '-')

class CaptchaService:
    def __init__(self):
        # Store active challenges: {captcha_id: {"answer": str, "expires_at": float}}
        self._challenges: Dict[str, Dict[str, Any]] = {}
        # Store verified tokens: {token: {"client_ip": str, "expires_at": float}}
        self._verified_tokens: Dict[str, Dict[str, Any]] = {}

    def _cleanup_expired(self):
        now = time.time()
        expired_ch = [cid for cid, item in self._challenges.items() if item["expires_at"] < now]
        for cid in expired_ch:
            self._challenges.pop(cid, None)

        expired_tok = [tok for tok, item in self._verified_tokens.items() if item["expires_at"] < now]
        for tok in expired_tok:
            self._verified_tokens.pop(tok, None)

    def generate_challenge(self) -> Dict[str, Any]:
        """
        Generates a simple, human-friendly arithmetic challenge.
        Example: ৭ + ৫ = ? (7 + 5 = ?)
        """
        self._cleanup_expired()
        
        # Pick 2 friendly numbers
        a = random.randint(3, 19)
        b = random.randint(2, 15)
        operation = random.choice(["+", "+", "-"]) # mostly additions
        
        if operation == "+":
            ans = a + b
            op_sym = "+"
        else:
            if a < b:
                a, b = b, a
            ans = a - b
            op_sym = "-"

        a_bn = to_bn_digits(a)
        b_bn = to_bn_digits(b)
        
        question_bn = f"{a_bn} {op_sym} {b_bn} = ?"
        question_en = f"({a} {op_sym} {b} = ?)"
        full_question = f"{question_bn} {question_en}"

        captcha_id = str(uuid.uuid4())
        expires_at = time.time() + 300.0  # 5 minutes validity

        self._challenges[captcha_id] = {
            "answer": str(ans),
            "expires_at": expires_at
        }

        return {
            "captcha_id": captcha_id,
            "question": full_question,
            "prompt_bn": question_bn,
            "prompt_en": f"{a} {op_sym} {b} = ?",
            "expires_in": 300
        }

    def verify_answer(self, captcha_id: str, user_answer: str, client_ip: Optional[str] = None) -> Dict[str, Any]:
        """
        Validates user answer and returns verification token if correct.
        """
        self._cleanup_expired()

        challenge = self._challenges.get(captcha_id)
        if not challenge:
            return {
                "verified": False,
                "status": "expired",
                "message": "ক্যাপচাটির মেয়াদ উত্তীর্ণ হয়েছে বা এটি বিদ্যমান নেই। অনুগ্রহ করে নতুন ক্যাপচা চেষ্টা করুন।"
            }

        expected = challenge["answer"]
        normalized_user = normalize_digits(user_answer)

        # One-time use: consume challenge
        del self._challenges[captcha_id]

        if normalized_user == expected:
            # Issue verification token (valid for 20 minutes)
            token = f"nu_tok_{uuid.uuid4().hex}"
            self._verified_tokens[token] = {
                "client_ip": client_ip,
                "created_at": time.time(),
                "expires_at": time.time() + 1200.0  # 20 mins
            }
            return {
                "verified": True,
                "status": "success",
                "verification_token": token,
                "message": "সফলভাবে নিরাপত্তা যাচাই সম্পন্ন হয়েছে!"
            }
        else:
            return {
                "verified": False,
                "status": "incorrect",
                "message": "ভুল উত্তর প্রদান করা হয়েছে। অনুগ্রহ করে পুনরায় চেষ্টা করুন।"
            }

    def is_token_valid(self, token: Optional[str], client_ip: Optional[str] = None) -> bool:
        """
        Checks whether a verification token is valid and active.
        """
        if not token:
            return False
        self._cleanup_expired()
        entry = self._verified_tokens.get(token)
        if not entry:
            return False
        if entry["expires_at"] < time.time():
            self._verified_tokens.pop(token, None)
            return False
        return True

captcha_service = CaptchaService()
