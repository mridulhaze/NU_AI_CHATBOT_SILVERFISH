from .auth_routes import router as auth_router
from .chat_routes import router as chat_v1_router
from .token_routes import router as token_v1_router
from .admin_routes import router as admin_v1_router
from .mcp_routes import router as mcp_router
from .credential_routes import router as credential_router
from .enrichment_routes import router as enrichment_router
from .ai_lab_routes import router as ai_lab_router
from .academic_exam_routes import router as academic_exam_router
from .faq_routes import faq_router

__all__ = [
    "auth_router",
    "chat_v1_router",
    "token_v1_router",
    "admin_v1_router",
    "mcp_router",
    "credential_router",
    "enrichment_router",
    "ai_lab_router",
    "academic_exam_router",
    "faq_router"
]
