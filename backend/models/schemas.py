from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any

# --- Auth Schemas ---
class UserLoginRequest(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=4)

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = "USER"  # USER, SOLVER, ADMIN

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str
    department: Optional[str] = None
    active: bool

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# --- Chat & Orchestrator Schemas ---
class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: 'user' or 'bot' / 'assistant'")
    content: str = Field(..., description="Message text")

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User query or message")
    history: List[ChatMessage] = Field(default_factory=list, description="Multi-turn conversation history")
    session_id: Optional[str] = Field(default=None, description="Unique client session ID")
    service_code: Optional[str] = Field(default=None, description="Preselected service context")

class SourceCitation(BaseModel):
    title: str
    url: str
    date: Optional[str] = None
    category: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    sources: List[str] = Field(default_factory=list)
    citations: List[SourceCitation] = Field(default_factory=list)
    suggested_chips: List[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0)
    intent: str = Field(default="general")
    language: str = Field(default="bn")
    is_fallback: bool = Field(default=False)
    skill_used: Optional[str] = None
    token_card: Optional[Dict[str, Any]] = None
    interactive_buttons: Optional[List[Dict[str, str]]] = None

# --- MCP Standard Response Wrapper ---
class MCPResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

# --- Token Service Schemas ---
class ServiceTypeSchema(BaseModel):
    id: int
    service_code: str
    service_name: str
    service_name_bn: str
    description: Optional[str] = None
    active: bool = True
    sort_order: int = 0

class SolverSchema(BaseModel):
    id: int
    solver_name: str
    department: str
    email: Optional[str] = None
    phone: Optional[str] = None
    active: bool = True

class TokenCreateRequest(BaseModel):
    service_code: str = Field(..., description="Service code (e.g. FORM_FILLUP, EMS, CERTIFICATE, etc.)")
    problem: str = Field(..., min_length=5, max_length=2000, description="Problem description")
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None
    registration_no: Optional[str] = None
    college_code: Optional[str] = None
    priority: Optional[str] = "NORMAL"

class TokenCreateResponse(BaseModel):
    success: bool
    token_id: str
    service_code: str
    service_name: str
    problem: str
    status: str
    created_date: str
    message: str

class TokenHistorySchema(BaseModel):
    id: int
    token_id: str
    old_status: Optional[str] = None
    new_status: str
    changed_by: str
    message: Optional[str] = None
    created_date: str

class TokenPublicStatus(BaseModel):
    token_id: str
    service_code: str
    service_name: str
    problem: str
    status: str
    status_display: str
    status_badge: str
    solver_name: Optional[str] = None
    solve_message: Optional[str] = None
    created_date: str
    updated_date: str
    solved_date: Optional[str] = None
    history: List[TokenHistorySchema] = Field(default_factory=list)

class TokenAdminDetail(TokenPublicStatus):
    id: int
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None
    registration_no: Optional[str] = None
    college_code: Optional[str] = None
    priority: str
    admin_note: Optional[str] = None
    solver_id: Optional[int] = None

class SolvedSimilarProblem(BaseModel):
    token_id: str
    service_code: str
    service_name: str
    problem: str
    solution: str
    solved_date: Optional[str] = None
    similarity_score: float = 1.0

# --- Token Management Actions ---
class TokenAssignRequest(BaseModel):
    solver_id: int
    admin_note: Optional[str] = None

class TokenStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="PENDING, ASSIGNED, PROCESSING, SOLVED, CLOSED, REJECTED")
    message: Optional[str] = None
    admin_note: Optional[str] = None

class TokenReturnRequest(BaseModel):
    token_id: str
    return_reason: str = Field(..., min_length=3, description="Reason for sending back to admin")

# --- Many-to-Many Q&A Knowledge Schemas ---
class QAKnowledgeCreateRequest(BaseModel):
    primary_question: str = Field(..., min_length=3, description="Primary canonical question")
    category: str = Field(default="General", description="Category / Faculty / Department")
    tags: Optional[str] = Field(default="", description="Comma-separated tags")
    question_variants: List[str] = Field(default_factory=list, description="Alternative phrasing and synonyms")
    answer_variants: List[str] = Field(default_factory=list, description="Answer variants and explanations")

class QAKnowledgeResponse(BaseModel):
    id: int
    primary_question: str
    category: str
    tags: Optional[str] = ""
    question_variants: List[str] = Field(default_factory=list)
    answer_variants: List[Dict[str, Any]] = Field(default_factory=list)
    primary_answer: Optional[str] = ""
    created_at: Optional[str] = None

class TokenSolveRequest(BaseModel):
    solve_message: str = Field(..., min_length=5, description="Clear solution steps for the student")
    solver_name: Optional[str] = None
    admin_note: Optional[str] = None

class GapApprovalRequest(BaseModel):
    custom_answer: Optional[str] = None

class ManualCrawlRequest(BaseModel):
    source: Optional[str] = Field(default="all", description="Source to crawl: all, notices, admission, results, ems, ict")

class DeepCrawlRequest(BaseModel):
    max_pages: int = Field(default=50, ge=5, le=5000, description="Max recursive pages to crawl")
    delay_seconds: float = Field(default=0.5, ge=0.2, le=5.0, description="Polite delay between requests")

# --- Academic Examination Information Management Schemas ---
class AcademicExamCreateUpdateRequest(BaseModel):
    program_type: str = Field(..., description="Honours, Degree Pass, Master's, Professional")
    program_type_name: Optional[str] = Field(default="", description="Bengali label: অনার্স, ডিগ্রি পাস, মাস্টার্স, প্রফেশনাল")
    course_name: Optional[str] = Field(default="", description="Course Name / Code: e.g. B.Sc. in Computer Science & Engineering (CSE), BBA, etc.")
    examination_year: str = Field(..., min_length=2, description="Examination Year: e.g. 2024, 2025")
    part: Optional[str] = Field(default="N/A", description="Part 1, Part 2, Part 3, Part 4, or N/A")
    semester: Optional[str] = Field(default="N/A", description="Semester 1 through Semester 8, or N/A")
    incourse_exam_date: Optional[str] = Field(default="", description="In-course Exam Date")
    incourse_marks_deadline: Optional[str] = Field(default="", description="Last Date for In-course Marks Entry")
    form_fillup_start_date: Optional[str] = Field(default="", description="Form Fill-up Start Date")
    form_fillup_deadline: Optional[str] = Field(default="", description="Form Fill-up Last Date")
    exam_date: Optional[str] = Field(default="", description="Examination Start Date")
    routine_publication_date: Optional[str] = Field(default="", description="Routine Publication Date or link")
    admit_card_date: Optional[str] = Field(default="", description="Admit Card Availability Date")
    last_exam_date: Optional[str] = Field(default="", description="Last Date of Examination")
    practical_marks_start_date: Optional[str] = Field(default="", description="Practical Marks Entry Start Date")
    practical_marks_deadline: Optional[str] = Field(default="", description="Last Date of Practical Marks Entry")
    probable_result_date: Optional[str] = Field(default="", description="Probable Result Publication Date (সম্ভাব্য ফল প্রকাশ)")
    actual_result_date: Optional[str] = Field(default="", description="Actual Result Publication Date (প্রকৃত ফল প্রকাশ)")
    results_published: Optional[str] = Field(default="No", description="Results Published: Yes / No")
    rescrutiny_start_date: Optional[str] = Field(default="", description="Re-scrutiny Application Start Date")
    rescrutiny_deadline: Optional[str] = Field(default="", description="Re-scrutiny Application Last Date")
    rescrutiny_result_date: Optional[str] = Field(default="", description="Re-scrutiny Result Publication Date")
    document_printing_date: Optional[str] = Field(default="", description="Certificate / Marksheet / Transcript Printing Date")
    documents_printed: Optional[str] = Field(default="No", description="Certificate / Marksheet Printed: Yes / No")
    revaluation_result_url: Optional[str] = Field(default="https://results.nu.ac.bd/", description="Revaluation Result Link")
    college_wise_result_url: Optional[str] = Field(default="http://103.113.200.68/nu-app/search.php", description="College-wise Result Link")
    remarks: Optional[str] = Field(default="", description="Additional Official Remarks / Guidelines")
    source_url: Optional[str] = Field(default="", description="Official Notice / Circular Source URL")

class AcademicExamResponse(AcademicExamCreateUpdateRequest):
    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = "Admin"
    updated_by: Optional[str] = "Admin"

# Backwards compatibility schemas
class AcademicStaticInfoRequest(AcademicExamCreateUpdateRequest):
    part_or_year: Optional[str] = Field(default="1")
    exam_year: Optional[str] = Field(default="")
    incourse_date: Optional[str] = Field(default="")
    last_date_incourse_marks: Optional[str] = Field(default="")
    form_fillup_date: Optional[str] = Field(default="")
    routine_url: Optional[str] = Field(default="")
    last_date_practical_marks: Optional[str] = Field(default="")
    rescrutiny_apply_date: Optional[str] = Field(default="")
    certificate_printing_date: Optional[str] = Field(default="")
    printed_status: Optional[str] = Field(default="No")
    revaluation_result_link: Optional[str] = Field(default="https://results.nu.ac.bd/")
    collegewise_result_link: Optional[str] = Field(default="http://103.113.200.68/nu-app/search.php")
    notes: Optional[str] = Field(default="")

class AcademicStaticInfoResponse(AcademicStaticInfoRequest):
    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
