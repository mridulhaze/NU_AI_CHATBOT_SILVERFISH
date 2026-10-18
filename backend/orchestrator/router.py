from typing import Optional, Dict, Any

class SkillRouter:
    """
    Routes user messages to the appropriate AI Skill according to priority rules.
    """
    @staticmethod
    def route(intent: str, entities: Dict[str, Any], session_context: Optional[Any] = None) -> str:
        # Rule 1: Token ID provided -> Always Token Service Skill
        if intent == "TOKEN_STATUS" or "token_id" in entities:
            return "token_service"

        # Rule 2: Token Service workflow / confirmation / problem description -> Token Service Skill
        if intent in ["TOKEN_SERVICE_MENU", "TOKEN_CONFIRM_CREATE", "TOKEN_CANCEL", "TOKEN_PROBLEM_SUBMISSION"]:
            return "token_service"

        # Rule 3: Session already in an active token workflow
        if session_context and getattr(session_context, "active_skill", None) == "token_service":
            if getattr(session_context, "pending_token_confirmation", False):
                return "token_service"

        # Rule 4: Domain queries
        if intent == "NOTICE_QUERY":
            return "notice_service"
        if intent == "EXAM_QUERY":
            return "examination"
        if intent == "ADMISSION_QUERY":
            return "admission"
        if intent == "RESULT_QUERY":
            return "result"
        if intent == "DOCUMENT_QUERY":
            return "document_search"

        # Default fallback: General NU Skill
        return "nu_general"

_skill_router_instance: Optional[SkillRouter] = None

def get_skill_router() -> SkillRouter:
    global _skill_router_instance
    if _skill_router_instance is None:
        _skill_router_instance = SkillRouter()
    return _skill_router_instance
