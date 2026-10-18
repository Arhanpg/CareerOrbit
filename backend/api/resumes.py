from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from backend.database import get_candidate_constraints, get_db_connection
from backend.memory.mem0_manager import memory_manager
from backend.resume_engine.rendercv_compiler import compile_tailored_ats_resume

router = APIRouter(prefix="/api/v1/resumes", tags=["Dynamic ATS Resume Engine"])

class CompileResumeRequest(BaseModel):
    job_id: str
    user_id: Optional[str] = "default_user"

@router.post("/compile")
def compile_resume_for_job(payload: CompileResumeRequest):
    """
    FR-16: Synthesizes a tailored ATS PDF for the target job opportunity.
    """
    # 1. Fetch job record
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM discovered_jobs WHERE id = ?", (payload.job_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        # Default fallback job if not discovered yet
        job_record = {
            "id": payload.job_id,
            "title": "Software Engineering Intern",
            "company": "Tech Corp",
            "role_category": "SDE",
            "description": "Looking for B.Tech interns with Python, FastAPI, and distributed systems skills."
        }
    else:
        job_record = {
            "id": row["id"],
            "title": row["title"],
            "company": row["company"],
            "role_category": row["role_category"],
            "description": row["description"]
        }

    # 2. Get profile & memory facts
    profile = get_candidate_constraints(payload.user_id) or {
        "full_name": "Aman Sharma",
        "email": "aman.sharma28@example.com",
        "phone": "+91 9876543210",
        "current_location": "India",
        "degree": "B.Tech",
        "graduation_batch": 2028,
        "current_academic_year": "3rd Year",
        "cgpa": 8.95
    }

    # Search relevant memories
    memories = memory_manager.search_memory(
        query=f"{job_record['title']} {job_record['description']}",
        user_id=payload.user_id,
        limit=10
    )

    # 3. Compile resume
    pdf_path = compile_tailored_ats_resume(
        candidate_profile=profile,
        retrieved_memories=memories,
        job_posting=job_record
    )

    return {
        "status": "success",
        "job_id": payload.job_id,
        "pdf_path": str(pdf_path),
        "pdf_download_url": f"/api/v1/resumes/{payload.job_id}/pdf"
    }

@router.get("/{job_id}/pdf")
def get_compiled_pdf(job_id: str):
    """
    FR-17: Serves the compiled ATS Typst PDF.
    """
    from backend.config import settings
    resumes_dir = settings.STORAGE_DIR / "resumes" / f"build_{job_id}"
    pdf_files = list(resumes_dir.glob("**/*.pdf"))
    if not pdf_files:
        raise HTTPException(status_code=404, detail="Resume PDF not compiled yet for this job.")
    
    return FileResponse(
        path=str(pdf_files[0]),
        media_type="application/pdf",
        filename=pdf_files[0].name
    )
