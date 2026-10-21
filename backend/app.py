import os
import json
import logging
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .models import ChatRequest, ChatResponse, GapApprovalRequest, ManualCrawlRequest, DeepCrawlRequest
from .rate_limiter import rate_limiter
from .rag_engine import get_rag_engine
from db.sql_store import get_sql_store
from db.vector_store import get_vector_store
from crawler.scheduler import start_scheduler, stop_scheduler, run_full_crawl, get_crawler_status
from crawler.deep_crawler_bridge import run_deep_crawler, get_deep_crawler_status
from enrichment.worker import get_enrichment_worker
from token_service import init_token_database, token_router
from backend.api import auth_router, chat_v1_router, token_v1_router, admin_v1_router, mcp_router, credential_router, enrichment_router, ai_lab_router, academic_exam_router, faq_router, captcha_router
from backend.orchestrator.agent import get_ai_orchestrator
from backend.core.database import init_core_database
from backend.agents.autonomous_24x7_worker import get_24x7_worker

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("NU_API")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting National University AI Assistant API Server...")
    # Initialize DB instances
    sql_store = get_sql_store()
    vector_store = get_vector_store()
    init_token_database()
    init_core_database()
    
    # Start periodic background crawler (every 30 minutes)
    try:
        start_scheduler(crawl_interval_minutes=settings.CRAWL_INTERVAL_MINUTES)
    except Exception as e:
        logger.warning(f"Could not start background scheduler: {e}")

    # Initial crawl check in background (non-blocking)
    try:
        def _initial_crawl_worker():
            try:
                notices_count = len(sql_store.get_recent_notices(limit=5))
                if notices_count == 0:
                    logger.info("Database has 0 notices. Triggering non-blocking initial startup crawl...")
                    run_full_crawl()
                else:
                    logger.info(f"Database contains {notices_count}+ notices. Scheduler running incremental sync.")
            except Exception as e_init:
                logger.warning(f"Initial startup crawl background error: {e_init}")

        threading.Thread(target=_initial_crawl_worker, daemon=True, name="NU_Startup_Crawler").start()
    except Exception as e_th:
        logger.warning(f"Could not spawn startup crawler thread: {e_th}")

    # Ensure FAQ database seeded
    try:
        from backend.services.faq_service import get_faq_service
        get_faq_service().ensure_seeded()
    except Exception as e_faq:
        logger.warning(f"FAQ seed check: {e_faq}")

    # Start 24/7 Autonomous Knowledge Enrichment Agent
    try:
        enrichment_worker = get_24x7_worker()
        enrichment_worker.start_24x7_worker()
    except Exception as e:
        logger.warning(f"Could not start 24/7 enrichment worker: {e}")
        
    yield
    
    logger.info("Shutting down API Server...")
    stop_scheduler()
    try:
        get_24x7_worker().stop_24x7_worker()
    except Exception:
        pass

app = FastAPI(
    title="National University Bangladesh AI Academic Assistant",
    description="Production-grade AI Chatbot for nu.ac.bd powered by Gemini & Chroma RAG with Self-Enrichment Engine, Skills, MCP Servers, and Token Service",
    version=settings.VERSION,
    lifespan=lifespan
)

# Enable CORS for frontend and cross-origin access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Modular V1 Routers & Legacy Token Router
app.include_router(auth_router)
app.include_router(chat_v1_router)
app.include_router(token_v1_router)
app.include_router(credential_router)
app.include_router(admin_v1_router)
app.include_router(mcp_router)
app.include_router(enrichment_router)
app.include_router(ai_lab_router)
app.include_router(academic_exam_router)
app.include_router(faq_router)
app.include_router(captcha_router)
app.include_router(token_router)

STUDENT_CHAT_FILE = settings.STATIC_DIR / "chat.html"
HTML_FILE = settings.STATIC_DIR / "index.html"
# Legacy fallback HTML path
LEGACY_HTML_FILE = settings.BASE_DIR / "gemini-code-1786959765553.html"

# --- Frontend Serving Routes ---
@app.get("/")
def serve_root():
    if STUDENT_CHAT_FILE.exists():
        return FileResponse(STUDENT_CHAT_FILE)
    if HTML_FILE.exists():
        return FileResponse(HTML_FILE)
    return {"status": "online", "message": "National University AI Assistant API is running."}

@app.get("/chat")
@app.get("/widget")
def serve_chat_ui():
    if STUDENT_CHAT_FILE.exists():
        return FileResponse(STUDENT_CHAT_FILE)
    elif HTML_FILE.exists():
        return FileResponse(HTML_FILE)
    raise HTTPException(status_code=404, detail="Chat UI template not found.")

@app.get("/admin")
def serve_admin_portal():
    if HTML_FILE.exists():
        return FileResponse(HTML_FILE)
    elif LEGACY_HTML_FILE.exists():
        return FileResponse(LEGACY_HTML_FILE)
    raise HTTPException(status_code=404, detail="Admin UI template not found.")

@app.get("/docs/project-overview.pdf")
def serve_project_overview_pdf():
    pdf_path = settings.BASE_DIR / "docs" / "project-overview.pdf"
    if pdf_path.exists():
        return FileResponse(pdf_path, media_type="application/pdf", filename="National_University_AI_Project_Overview_BN.pdf")
    raise HTTPException(status_code=404, detail="Project overview PDF not found.")

@app.get("/docs/project-overview-en.pdf")
def serve_project_overview_en_pdf():
    pdf_path = settings.BASE_DIR / "docs" / "project-overview-en.pdf"
    if pdf_path.exists():
        return FileResponse(pdf_path, media_type="application/pdf", filename="National_University_AI_Project_Overview_EN.pdf")
    raise HTTPException(status_code=404, detail="English project overview PDF not found.")

@app.get("/docs/project-proposal.pdf")
def serve_project_proposal_pdf():
    pdf_path = settings.BASE_DIR / "project_proposal" / "project_proposal.pdf"
    if pdf_path.exists():
        return FileResponse(pdf_path, media_type="application/pdf", filename="National_University_AI_Project_Proposal.pdf")
    raise HTTPException(status_code=404, detail="Project proposal PDF not found.")

@app.get("/docs/project-proposal.docx")
def serve_project_proposal_docx():
    docx_path = settings.BASE_DIR / "project_proposal" / "project_proposal.docx"
    if docx_path.exists():
        return FileResponse(docx_path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename="National_University_AI_Project_Proposal.docx")
    raise HTTPException(status_code=404, detail="Project proposal DOCX not found.")

# --- Chat Endpoint ---
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest, request: Request):
    forwarded = request.headers.get("x-forwarded-for")
    client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "127.0.0.1")
    rate_limiter.check_rate_limit(client_ip)

    user_query = payload.message.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        rag_engine = get_rag_engine()
        response = rag_engine.answer_query(
            query=user_query,
            history=payload.history,
            session_id=payload.session_id
        )

        # Log service provided event
        try:
            from backend.services.activity_tracker import ActivityTracker
            ActivityTracker.record_event(
                event_type="SERVICE_PROVIDED",
                service_code="ACADEMIC_CHAT_AI",
                user_identifier=f"SESSION_{payload.session_id[:8]}" if payload.session_id else "STUDENT_WEB",
                solver_name="GEMINI_AI_AGENT",
                status="SUCCESS" if not response.is_fallback else "FALLBACK",
                details={"query": user_query[:80], "confidence": response.confidence},
                ip_address=client_ip
            )
        except Exception:
            pass

        return response
    except Exception as e:
        logger.error(f"Error in chat_endpoint: {e}", exc_info=True)
        return ChatResponse(
            reply=f"দুঃখিত, অভ্যন্তরীণ ত্রুটির কারণে অনুরোধটি সম্পন্ন করা যায়নি ({str(e)})। অনুগ্রহ করে কিছুক্ষণ পর আবার চেষ্টা করুন।",
            sources=["https://www.nu.ac.bd/"],
            suggested_chips=["📄 সাম্প্রতিক নোটিশ", "🎓 ভর্তি সংক্রান্ত তথ্য", "🌐 ফলাফল আর্কাইভ"],
            confidence=0.0,
            is_fallback=True
        )

@app.post("/api/chat/stream")
async def chat_stream_endpoint(payload: ChatRequest, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    rate_limiter.check_rate_limit(client_ip)

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

# --- Quick Links Directory ---
@app.get("/api/quick-links")
def get_quick_links():
    links_file = settings.DATA_DIR / "quick_links.json"
    if links_file.exists():
        with open(links_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# --- Health Check ---
@app.get("/api/health")
def health_check():
    sql_store = get_sql_store()
    crawler_status = get_crawler_status()
    return {
        "status": "healthy",
        "service": "National University AI Academic Assistant",
        "version": settings.VERSION,
        "primary_model": settings.PRIMARY_MODEL,
        "database": "connected",
        "crawler": crawler_status
    }

# --- Admin API Routes ---
@app.get("/api/admin/crawl-status")
def admin_crawl_status():
    sql_store = get_sql_store()
    logs = sql_store.get_recent_crawl_logs(limit=15)
    live_status = get_crawler_status()
    return {
        "live_status": live_status,
        "recent_logs": logs
    }

@app.post("/api/admin/trigger-crawl")
async def admin_trigger_crawl(background_tasks: BackgroundTasks, payload: Optional[ManualCrawlRequest] = None):
    crawler_status = get_crawler_status()
    if crawler_status["is_running"]:
        return JSONResponse(status_code=409, content={"status": "error", "message": "Crawler is already executing."})
    
    background_tasks.add_task(run_full_crawl)
    return {"status": "started", "message": "Full polite crawl initiated in background."}

# --- Deep Crawler (nu_site_crawler_project) Routes ---
@app.get("/api/admin/deep-crawl-status")
def admin_deep_crawl_status():
    return get_deep_crawler_status()

@app.post("/api/admin/trigger-deep-crawl")
async def admin_trigger_deep_crawl(background_tasks: BackgroundTasks, payload: Optional[DeepCrawlRequest] = None):
    deep_status = get_deep_crawler_status()
    if deep_status["is_running"]:
        return JSONResponse(status_code=409, content={"status": "error", "message": "Deep crawler is currently running."})
    
    max_pages = payload.max_pages if payload else 50
    delay_sec = payload.delay_seconds if payload else 0.5

    def bg_deep_task():
        run_deep_crawler(max_pages=max_pages, delay_seconds=delay_sec)

    background_tasks.add_task(bg_deep_task)
    return {
        "status": "started",
        "message": f"Deep crawler (nu_site_crawler) started in background for up to {max_pages} pages."
    }

@app.get("/api/admin/gap-queue")
def admin_get_gap_queue(status: Optional[str] = None):
    sql_store = get_sql_store()
    gaps = sql_store.get_gap_queue(status=status, limit=100)
    return {"total": len(gaps), "items": gaps}

@app.post("/api/admin/gap-queue/{gap_id}/approve")
def admin_approve_gap(gap_id: int, payload: Optional[GapApprovalRequest] = None):
    worker = get_enrichment_worker()
    custom_ans = payload.custom_answer if payload else None
    success = worker.approve_gap(gap_id=gap_id, custom_answer=custom_ans)
    if not success:
        raise HTTPException(status_code=404, detail="Gap item not found or failed to approve.")
    return {"status": "success", "message": f"Gap item #{gap_id} approved and added to active knowledge base."}

@app.post("/api/admin/gap-queue/{gap_id}/reject")
def admin_reject_gap(gap_id: int):
    worker = get_enrichment_worker()
    success = worker.reject_gap(gap_id=gap_id)
    if not success:
        raise HTTPException(status_code=404, detail="Gap item not found.")
    return {"status": "success", "message": f"Gap item #{gap_id} marked as rejected."}

@app.post("/api/admin/trigger-enrichment")
async def admin_trigger_enrichment(background_tasks: BackgroundTasks):
    worker = get_enrichment_worker()
    def run_enrichment():
        worker.process_pending_gaps()
    background_tasks.add_task(run_enrichment)
    return {"status": "started", "message": "Self-enrichment worker triggered in background."}

# Alias for legacy updater endpoint
@app.post("/api/update-knowledge")
async def trigger_legacy_update(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_full_crawl)
    return {"status": "started", "message": "Knowledge base crawl triggered in background."}

# --- Static Files & Demo Hosting ---
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

@app.get("/", response_class=FileResponse, include_in_schema=False)
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="index.html not found")

@app.get("/index.html", response_class=FileResponse, include_in_schema=False)
def serve_index_alias():
    return serve_index()

@app.get("/chat", response_class=FileResponse, include_in_schema=False)
@app.get("/student", response_class=FileResponse, include_in_schema=False)
def serve_chat_ui():
    chat_file = STATIC_DIR / "chat.html"
    if chat_file.exists():
        return FileResponse(chat_file)
    raise HTTPException(status_code=404, detail="chat.html not found")

@app.get("/embed-demo.html", response_class=FileResponse, include_in_schema=False)
@app.get("/demo", response_class=FileResponse, include_in_schema=False)
def serve_embed_demo():
    demo_file = STATIC_DIR / "embed-demo.html"
    if demo_file.exists():
        return FileResponse(demo_file)
    raise HTTPException(status_code=404, detail="embed-demo.html not found")

@app.get("/widget.js", response_class=FileResponse, include_in_schema=False)
def serve_widget_js():
    js_file = STATIC_DIR / "widget.js"
    if js_file.exists():
        return FileResponse(js_file, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="widget.js not found")

# Mount /static for all files inside static directory
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

