from pathlib import Path

app_path = Path("backend/app.py")
code = app_path.read_text(encoding="utf-8")

old_imp = "from backend.api import auth_router, chat_v1_router, token_v1_router, admin_v1_router, mcp_router, credential_router, enrichment_router, ai_lab_router, academic_exam_router"
new_imp = "from backend.api import auth_router, chat_v1_router, token_v1_router, admin_v1_router, mcp_router, credential_router, enrichment_router, ai_lab_router, academic_exam_router, faq_router"

if old_imp in code:
    code = code.replace(old_imp, new_imp, 1)

old_mount = "app.include_router(academic_exam_router)"
new_mount = "app.include_router(academic_exam_router)\napp.include_router(faq_router)"
if old_mount in code:
    code = code.replace(old_mount, new_mount, 1)

old_seed = "    # Start 24/7 Autonomous Knowledge Enrichment Agent"
new_seed = """    # Ensure FAQ database seeded
    try:
        from backend.services.faq_service import get_faq_service
        get_faq_service().ensure_seeded()
    except Exception as e_faq:
        logger.warning(f"FAQ seed check: {e_faq}")

    # Start 24/7 Autonomous Knowledge Enrichment Agent"""
if old_seed in code:
    code = code.replace(old_seed, new_seed, 1)

app_path.write_text(code, encoding="utf-8")
print("Updated backend/app.py successfully")
