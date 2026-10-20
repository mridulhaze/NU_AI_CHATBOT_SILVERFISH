"""
FAQ Forum API Endpoints for National University AI Assistant
High-performance SQLite querying and atomic like management.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Header, Body
from pydantic import BaseModel

from backend.services.faq_service import get_faq_service

faq_router = APIRouter(prefix="/api/v1/faqs", tags=["FAQ Forum"])


class LikeToggleRequest(BaseModel):
    session_id: Optional[str] = None


class LikeResponse(BaseModel):
    faq_id: int
    likes_count: int
    has_liked: bool


@faq_router.get("", summary="List FAQs with filtering, search, and sorting")
def list_faqs(
    category: Optional[str] = Query(None, description="Category filter"),
    search: Optional[str] = Query(None, description="Search keyword in Bengali or English"),
    sort: str = Query("most_liked", description="Sort order: most_liked, latest, all"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    session_id: Optional[str] = Query(None, description="Client session ID for like status"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    eff_session_id = session_id or x_session_id
    faq_service = get_faq_service()
    offset = (page - 1) * limit
    result = faq_service.list_faqs(
        category=category,
        search=search,
        sort=sort,
        limit=limit,
        offset=offset,
        session_id=eff_session_id
    )
    return {
        "status": "success",
        "page": page,
        "limit": limit,
        "total": result["total"],
        "items": result["items"]
    }


@faq_router.get("/top-liked", summary="Fetch top 10 most liked FAQs")
def get_top_liked_faqs(
    limit: int = Query(10, ge=1, le=50, description="Number of top items"),
    session_id: Optional[str] = Query(None, description="Client session ID"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    eff_session_id = session_id or x_session_id
    faq_service = get_faq_service()
    items = faq_service.get_top_liked(limit=limit, session_id=eff_session_id)
    return {
        "status": "success",
        "count": len(items),
        "items": items
    }


@faq_router.get("/categories", summary="List FAQ categories with counts")
def get_faq_categories():
    faq_service = get_faq_service()
    categories = faq_service.get_categories()
    return {
        "status": "success",
        "categories": categories
    }


@faq_router.get("/{faq_id}", summary="Get FAQ detail by ID")
def get_faq_detail(
    faq_id: int,
    session_id: Optional[str] = Query(None, description="Client session ID"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    eff_session_id = session_id or x_session_id
    faq_service = get_faq_service()
    faq = faq_service.get_by_id(faq_id=faq_id, session_id=eff_session_id)
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found.")
    return {
        "status": "success",
        "faq": faq
    }


@faq_router.post("/{faq_id}/like", response_model=LikeResponse, summary="Toggle like/unlike on an FAQ")
def toggle_faq_like(
    faq_id: int,
    payload: Optional[LikeToggleRequest] = Body(None),
    session_id: Optional[str] = Query(None),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    body_session = payload.session_id if payload else None
    eff_session_id = body_session or session_id or x_session_id or "anonymous_device"
    faq_service = get_faq_service()
    result = faq_service.toggle_like(faq_id=faq_id, session_id=eff_session_id)
    if "error" in result:
        raise HTTPException(status_code=result.get("status", 400), detail=result["error"])
    return result


@faq_router.post("/sync", summary="Trigger synchronization from FAQ/faq.txt")
def sync_faqs():
    faq_service = get_faq_service()
    res = faq_service.sync_from_file()
    return res
