"""
Public Academic Examination Information Router
Provides read-only access for students and frontend pickers to official
examination schedules, dates, and results published by administrators.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from db.sql_store import get_sql_store
from backend.services.academic_exam_service import PROGRAM_CONFIG, format_exam_card_markdown

router = APIRouter(prefix="/api/v1/academic-exams", tags=["Academic Examination Information (Public)"])

@router.get("/programs")
def get_available_programs():
    """
    Returns available programs, parts, semesters, and existing examination years in the database.
    Used by frontend pickers and quick chips.
    """
    sql_store = get_sql_store()
    records, _ = sql_store.list_academic_exam_info(limit=500)
    
    # Collect unique years per program
    program_years: Dict[str, set] = {
        "Honours": set(),
        "Degree Pass": set(),
        "Master's": set(),
        "Professional": set()
    }
    
    for r in records:
        ptype = r.get("program_type")
        yr = r.get("examination_year")
        if ptype in program_years and yr:
            program_years[ptype].add(yr)
            
    # Format response
    categories = []
    for ptype, cfg in PROGRAM_CONFIG.items():
        categories.append({
            "program_type": ptype,
            "title_bn": cfg.get("bn_name", ptype),
            "parts": cfg.get("parts", []),
            "part_labels": cfg.get("part_labels", {}),
            "part_semesters": cfg.get("part_semesters", {}),
            "available_years": sorted(list(program_years.get(ptype, set())), reverse=True)
        })
        
    return {
        "status": "success",
        "programs": categories
    }

@router.get("")
def list_academic_exams(
    program_type: Optional[str] = Query(None, description="Honours, Degree Pass, Master's, Professional"),
    examination_year: Optional[str] = Query(None, description="e.g. 2024, 2025"),
    part: Optional[str] = Query(None, description="e.g. Part 1, Part 2, Final"),
    semester: Optional[str] = Query(None, description="e.g. Semester 1"),
    course_name: Optional[str] = Query(None, description="e.g. CSE, BBA"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """
    Public query list of examination schedules.
    """
    sql_store = get_sql_store()
    items, total = sql_store.list_academic_exam_info(
        program_type=program_type,
        examination_year=examination_year,
        part=part,
        semester=semester,
        course_name=course_name,
        limit=limit,
        offset=offset
    )
    return {
        "status": "success",
        "total": total,
        "items": items
    }

@router.get("/lookup")

def lookup_academic_exam(
    program_type: str = Query(..., description="Honours, Degree Pass, Master's, or Professional"),
    examination_year: Optional[str] = Query(None, description="Examination Year e.g. 2024"),
    part: Optional[str] = Query(None, description="Part e.g. Part 1"),
    semester: Optional[str] = Query(None, description="Semester e.g. Semester 1"),
    course_name: Optional[str] = Query(None, description="Course name e.g. CSE, BBA")
):
    """
    Finds a specific exam schedule record and returns both structured data and formatted Markdown.
    """
    sql_store = get_sql_store()
    records = sql_store.lookup_academic_exam_info(
        program_type=str(program_type),
        examination_year=examination_year if isinstance(examination_year, str) else None,
        part=part if isinstance(part, str) else None,
        semester=semester if isinstance(semester, str) else None,
        course_name=course_name if isinstance(course_name, str) else None
    )
    if not records:
        raise HTTPException(status_code=404, detail="উক্ত শিক্ষাবর্ষ ও কোর্সের পরীক্ষার তথ্য পাওয়া যায়নি।")
        
    record = records[0]
    markdown_card = format_exam_card_markdown(record)
    return {
        "status": "success",
        "record": record,
        "markdown_card": markdown_card
    }


@router.get("/{record_id}")
def get_academic_exam_by_id(record_id: int):
    """
    Fetch a single record by primary key ID.
    """
    sql_store = get_sql_store()
    record = sql_store.get_academic_exam_info_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="তথ্য পাওয়া যায়নি।")
    return {
        "status": "success",
        "record": record,
        "markdown_card": format_exam_card_markdown(record)
    }
