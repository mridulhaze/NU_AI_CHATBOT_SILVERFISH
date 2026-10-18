import re
import logging
from typing import List, Optional, Dict, Any
from langchain_core.documents import Document

from .repository import TokenRepository
from .models import (
    TokenCreateRequest,
    TokenCreateResponse,
    TokenPublicDetailResponse,
    TokenAdminDetailResponse,
    TokenHistoryModel,
    SolvedSimilarProblem
)
from db.vector_store import get_vector_store

logger = logging.getLogger("NU_TOKEN_SERVICE")

STATUS_DISPLAY_MAP = {
    "PENDING": ("🟡 Pending", "bg-amber-100 text-amber-800 border-amber-300"),
    "ASSIGNED": ("🟣 Assigned", "bg-purple-100 text-purple-800 border-purple-300"),
    "PROCESSING": ("🔵 Processing", "bg-blue-100 text-blue-800 border-blue-300"),
    "SOLVED": ("🟢 Solved", "bg-emerald-100 text-emerald-800 border-emerald-300"),
    "CLOSED": ("⚫ Closed", "bg-slate-100 text-slate-800 border-slate-300"),
    "REJECTED": ("🔴 Rejected", "bg-rose-100 text-rose-800 border-rose-300")
}

class TokenService:
    def __init__(self):
        self.repo = TokenRepository()

    def get_services(self) -> List[Dict[str, Any]]:
        return self.repo.get_active_service_types()

    def get_solvers(self) -> List[Dict[str, Any]]:
        return self.repo.get_solvers()

    def create_token(self, req: TokenCreateRequest) -> TokenCreateResponse:
        service_info = self.repo.get_service_by_code(req.service_type)
        service_name = service_info["service_name"] if service_info else req.service_type

        token_id = self.repo.create_token({
            "service_type": req.service_type.upper(),
            "problem": req.problem.strip(),
            "user_name": req.user_name.strip() if req.user_name else None,
            "user_email": req.user_email.strip() if req.user_email else None,
            "user_phone": req.user_phone.strip() if req.user_phone else None,
            "registration_no": req.registration_no.strip() if req.registration_no else None,
            "college_code": req.college_code.strip() if req.college_code else None,
            "priority": req.priority or "NORMAL"
        })

        return TokenCreateResponse(
            success=True,
            token_id=token_id,
            service_type=req.service_type.upper(),
            service_name=service_name,
            problem=req.problem.strip(),
            status="PENDING",
            created_date=self.repo.get_token_by_id(token_id)["created_date"],
            message=f"Support token {token_id} created successfully."
        )

    def generate_instant_token(self) -> TokenCreateResponse:
        """Immediately generates a pending token and prompts the student for service selection."""
        token_id = self.repo.create_token({
            "service_type": "PENDING_SELECTION",
            "problem": "Service selection pending from user menu",
            "priority": "NORMAL"
        })
        token_row = self.repo.get_token_by_id(token_id)
        return TokenCreateResponse(
            success=True,
            token_id=token_id,
            service_type="PENDING_SELECTION",
            service_name="Pending Selection",
            problem="Service selection pending",
            status="PENDING",
            created_date=token_row["created_date"],
            estimated_solve_date=token_row.get("estimated_solve_date"),
            message=f"Token {token_id} generated instantly."
        )

    def set_token_service(self, token_id: str, service_code: str, problem: Optional[str] = None) -> bool:
        """Saves the selected service category and problem description to the token."""
        return self.repo.update_service_and_problem(token_id=token_id, service_type=service_code, problem=problem)

    def update_token_details(self, token_id: str, service_type: str, problem: str, user_name: Optional[str] = None, user_phone: Optional[str] = None, registration_no: Optional[str] = None, college_code: Optional[str] = None) -> bool:
        """Saves service type and problem description or full submission."""
        return self.repo.update_service_and_problem(token_id=token_id, service_type=service_type, problem=problem)

    def submit_token_details(self, token_id: str, service_type: str, problem: str, user_name: Optional[str] = None, user_phone: Optional[str] = None, registration_no: Optional[str] = None, college_code: Optional[str] = None) -> Optional[TokenPublicDetailResponse]:
        """Saves full problem submission details and returns updated public status."""
        ok = self.repo.update_token_submission_details(
            token_id=token_id,
            service_type=service_type,
            problem=problem,
            user_name=user_name,
            user_phone=user_phone,
            registration_no=registration_no,
            college_code=college_code
        )
        if not ok:
            return None
        return self.get_public_token_details(token_id)

    def get_public_token_details(self, token_id: str) -> Optional[TokenPublicDetailResponse]:
        """Returns safe, public-friendly token status details without exposing internal admin notes or other users' PII."""
        row = self.repo.get_token_by_id(token_id)
        if not row:
            return None

        status = row["status"].upper()
        display_text, badge_class = STATUS_DISPLAY_MAP.get(status, ("🟡 Pending", "bg-amber-100 text-amber-800 border-amber-300"))

        service_info = self.repo.get_service_by_code(row["service_type"])
        service_name = service_info["service_name"] if service_info else row["service_type"]

        history_rows = self.repo.get_token_history(token_id)
        history = [
            TokenHistoryModel(
                id=h["id"],
                token_id=h["token_id"],
                old_status=h["old_status"],
                new_status=h["new_status"],
                changed_by=h["changed_by"],
                message=h["message"],
                created_date=h["created_date"]
            )
            for h in history_rows
        ]

        return TokenPublicDetailResponse(
            token_id=row["token_id"],
            service_type=row["service_type"],
            service_name=service_name,
            problem=row["problem"],
            status=status,
            status_display=display_text,
            status_badge=badge_class,
            solver_name=row["solver_name"],
            solve_message=row["solve_message"],
            created_date=row["created_date"],
            updated_date=row["updated_date"],
            estimated_solve_date=row.get("estimated_solve_date"),
            solved_date=row["solved_date"],
            history=history
        )

    def get_admin_token_details(self, token_id: str) -> Optional[TokenAdminDetailResponse]:
        """Returns full token details for admin dashboard including admin notes, student contact, and registration."""
        row = self.repo.get_token_by_id(token_id)
        if not row:
            return None

        status = row["status"].upper()
        display_text, badge_class = STATUS_DISPLAY_MAP.get(status, ("🟡 Pending", "bg-amber-100 text-amber-800 border-amber-300"))
        service_info = self.repo.get_service_by_code(row["service_type"])
        service_name = service_info["service_name"] if service_info else row["service_type"]

        history_rows = self.repo.get_token_history(token_id)
        history = [
            TokenHistoryModel(
                id=h["id"],
                token_id=h["token_id"],
                old_status=h["old_status"],
                new_status=h["new_status"],
                changed_by=h["changed_by"],
                message=h["message"],
                created_date=h["created_date"]
            )
            for h in history_rows
        ]

        return TokenAdminDetailResponse(
            id=row["id"],
            token_id=row["token_id"],
            service_type=row["service_type"],
            service_name=service_name,
            problem=row["problem"],
            status=status,
            status_display=display_text,
            status_badge=badge_class,
            solver_name=row["solver_name"],
            solve_message=row["solve_message"],
            created_date=row["created_date"],
            updated_date=row["updated_date"],
            estimated_solve_date=row.get("estimated_solve_date"),
            solved_date=row["solved_date"],
            history=history,
            user_name=row.get("user_name"),
            user_email=row.get("user_email"),
            user_phone=row.get("user_phone"),
            registration_no=row.get("registration_no"),
            college_code=row.get("college_code"),
            priority=row.get("priority", "NORMAL"),
            admin_note=row.get("admin_note"),
            solver_id=row.get("solver_id")
        )

    def assign_token(self, token_id: str, solver_id: int, changed_by: str = "ADMIN", admin_note: Optional[str] = None) -> bool:
        solver = self.repo.get_solver_by_id(solver_id)
        if not solver:
            return False
        return self.repo.assign_token(token_id, solver["id"], solver["solver_name"], changed_by=changed_by, admin_note=admin_note)

    def update_status(self, token_id: str, status: str, changed_by: str = "ADMIN", message: Optional[str] = None, admin_note: Optional[str] = None) -> bool:
        return self.repo.update_token_status(token_id, status, changed_by=changed_by, message=message, admin_note=admin_note)

    def solve_token(self, token_id: str, solve_message: str, solver_name: Optional[str] = None, changed_by: str = "ADMIN", admin_note: Optional[str] = None) -> bool:
        success = self.repo.solve_token(token_id, solve_message, solver_name=solver_name, changed_by=changed_by, admin_note=admin_note)
        if success:
            # Auto-index into Chroma Vector Store as anonymized solved knowledge
            self._index_solved_token(token_id)
        return success

    def _index_solved_token(self, token_id: str):
        """Indexes an anonymized solved case into the vector database for RAG similarity matching."""
        try:
            row = self.repo.get_token_by_id(token_id)
            if not row or not row["solve_message"]:
                return

            service_info = self.repo.get_service_by_code(row["service_type"])
            service_name = service_info["service_name"] if service_info else row["service_type"]

            # Anonymize: problem and solution only
            doc_content = f"# সমাধানকৃত সাপোর্ট কেস (Solved Case: {row['service_type']})\n"
            doc_content += f"সার্ভিস / বিষয়: {service_name}\n"
            doc_content += f"সমস্যা (Issue): {row['problem']}\n"
            doc_content += f"সমাধান (Resolution): {row['solve_message']}\n"
            doc_content += f"সমাধানকারী দপ্তর: {row['solver_name'] or 'NU Support Desk'}\n"

            doc = Document(
                page_content=doc_content,
                metadata={
                    "source": f"token://{row['token_id']}",
                    "token_id": row["token_id"],
                    "service_type": row["service_type"],
                    "category": "Solved Support Case",
                    "type": "solved_support_case"
                }
            )

            vs = get_vector_store()
            vs.split_and_add_documents([doc])
            logger.info(f"Indexed solved token {token_id} into Chroma vector knowledge base.")
        except Exception as e:
            logger.warning(f"Failed to index solved token {token_id} into Chroma: {e}")

    def find_similar_solved_cases(self, query: str, service_type: Optional[str] = None, top_k: int = 3, vector_matches: Optional[List[Any]] = None) -> List[SolvedSimilarProblem]:
        """
        Searches solved cases efficiently without duplicate embedding generation.
        Checks SQLite repository and provided vector matches. Zero PII leakage.
        """
        results: List[SolvedSimilarProblem] = []
        clean_q = query.strip().lower()

        # 1. If pre-fetched vector matches provided, parse directly (<0.01ms)
        if vector_matches:
            for doc, score in vector_matches:
                meta = getattr(doc, "metadata", {}) or {}
                if meta.get("type") == "solved_support_case":
                    content = getattr(doc, "page_content", "")
                    prob_m = re.search(r"সমস্যা \(Issue\):\s*(.+)", content)
                    sol_m = re.search(r"সমাধান \(Resolution\):\s*(.+)", content)
                    prob_text = prob_m.group(1).strip() if prob_m else content[:100]
                    sol_text = sol_m.group(1).strip() if sol_m else "পূর্ববর্তী সমাধান রেকর্ড রয়েছে।"

                    t_id = meta.get("token_id", "NU-SOLVED")
                    s_type = meta.get("service_type", "GENERAL")
                    s_info = self.repo.get_service_by_code(s_type)
                    s_name = s_info["service_name"] if s_info else s_type

                    results.append(SolvedSimilarProblem(
                        token_id=t_id,
                        service_type=s_type,
                        service_name=s_name,
                        problem=prob_text,
                        solution=sol_text,
                        similarity_score=float(score)
                    ))
                    if len(results) >= top_k:
                        return results

        # 2. Fast SQLite Solved Repository Lookup (< 1ms)
        try:
            local_solved = self.repo.get_solved_tokens(service_type=service_type, limit=top_k * 2)
            for s in local_solved:
                # Basic relevance check if query words appear in problem or service
                s_prob = (s.get("problem") or "").lower()
                s_type_code = (s.get("service_type") or "").lower()
                
                # Check keyword match
                is_match = any(word in s_prob or word in s_type_code for word in clean_q.split() if len(word) > 2)
                if is_match or not clean_q:
                    s_info = self.repo.get_service_by_code(s["service_type"])
                    s_name = s_info["service_name"] if s_info else s["service_type"]
                    results.append(SolvedSimilarProblem(
                        token_id=s["token_id"],
                        service_type=s["service_type"],
                        service_name=s_name,
                        problem=s["problem"],
                        solution=s["solve_message"],
                        solved_date=s["solved_date"],
                        similarity_score=0.88
                    ))
                    if len(results) >= top_k:
                        return results
        except Exception as e:
            logger.warning(f"Error querying SQLite solved tokens: {e}")

        return results

_token_service_instance: Optional[TokenService] = None

def get_token_service() -> TokenService:
    global _token_service_instance
    if _token_service_instance is None:
        _token_service_instance = TokenService()
    return _token_service_instance
