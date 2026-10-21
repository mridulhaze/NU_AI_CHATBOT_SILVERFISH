import asyncio
import logging
from fastapi import APIRouter, HTTPException, Request, Depends
from backend.models.schemas import ChatRequest, ChatResponse
from backend.orchestrator.agent import get_ai_orchestrator
from backend.rate_limiter import rate_limiter

from fastapi.responses import StreamingResponse
from backend.rag_engine import get_rag_engine

logger = logging.getLogger("NU_CHAT_API")
router = APIRouter(prefix="/api/v1/chat", tags=["AI Orchestrator & Skills Chat"])

@router.post("", response_model=ChatResponse)
async def process_orchestrated_chat(payload: ChatRequest, request: Request):
    forwarded = request.headers.get("x-forwarded-for")
    client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "127.0.0.1")
    captcha_token = request.headers.get("x-captcha-token")
    rate_limiter.check_rate_limit(client_ip, captcha_token=captcha_token)

    user_query = payload.message.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        orchestrator = get_ai_orchestrator()
        return await asyncio.to_thread(orchestrator.process_chat, payload)
    except Exception as e:
        logger.error(f"AI Orchestrator error: {e}", exc_info=True)
        return ChatResponse(
            reply="দুঃখিত, অভ্যন্তরীণ ত্রুটির কারণে অনুরোধটি সম্পন্ন করা সম্ভব হয়নি। অনুগ্রহ করে কিছুক্ষণ পর আবার চেষ্টা করুন।",
            confidence=0.0,
            is_fallback=True
        )

@router.post("/stream")
async def process_orchestrated_stream(payload: ChatRequest, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    captcha_token = request.headers.get("x-captcha-token")
    rate_limiter.check_rate_limit(client_ip, captcha_token=captcha_token)

    user_query = payload.message.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    rag_engine = get_rag_engine()
    return StreamingResponse(
        rag_engine.stream_answer_query(
            query=user_query,
            history=payload.history,
            session_id=payload.session_id
        ),
        media_type="text/event-stream"
    )
