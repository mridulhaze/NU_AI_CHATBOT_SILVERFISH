"""
Public CAPTCHA & Bot Protection API Router
Provides math challenges and token validation to safeguard chat endpoints
and provide rate limit resilience for authentic users.
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from backend.services.captcha_service import captcha_service
from backend.rate_limiter import rate_limiter

router = APIRouter(prefix="/api/v1/captcha", tags=["Captcha & Bot Protection"])

class VerifyCaptchaRequest(BaseModel):
    captcha_id: str = Field(..., description="UUID of the challenge")
    answer: str = Field(..., description="User's numeric answer")

@router.get("/challenge")
def get_captcha_challenge():
    """
    Returns a simple math/logic challenge with a 5-minute expiry.
    """
    return captcha_service.generate_challenge()

@router.post("/verify")
def verify_captcha_solution(payload: VerifyCaptchaRequest, request: Request):
    """
    Verifies user answer. If correct, resets client IP rate limit velocity
    and returns a 20-minute verification token.
    """
    forwarded = request.headers.get("x-forwarded-for")
    client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "127.0.0.1")

    res = captcha_service.verify_answer(
        captcha_id=payload.captcha_id,
        user_answer=payload.answer,
        client_ip=client_ip
    )

    if res.get("verified"):
        # Reset IP rate limit history so user can continue chatting smoothly
        rate_limiter.reset_ip(client_ip)

    return res

@router.get("/status")
def check_token_status(token: Optional[str] = None):
    """
    Checks if a verification token is currently valid.
    """
    valid = captcha_service.is_token_valid(token)
    return {
        "valid": valid,
        "token": token
    }
