import os
import json
import asyncio
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from backend.config import settings
from backend.database import get_candidate_constraints, get_raw_connection
from backend.memory.mem0_manager import memory_manager
from backend.resume_engine.rendercv_compiler import (
    compile_tailored_ats_resume,
    render_yaml_to_pdf,
    build_deterministic_yaml
)

router = APIRouter(prefix="/api/v1/resumes", tags=["Dynamic ATS Resume Engine"])

class CompileResumeRequest(BaseModel):
    job_id: str
    user_id: Optional[str] = "default_user"

@router.post("/compile")
async def compile_resume_for_job(payload: CompileResumeRequest):
    """
    FR-016: Synthesizes a tailored ATS PDF for the target job opportunity.
    """
    conn = get_raw_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM discovered_jobs WHERE id = ?", (payload.job_id,))
        row = cursor.fetchone()
    finally:
        conn.close()

    if not row:
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

    memories = memory_manager.search_memory(
        query=f"{job_record['title']} {job_record['description']}",
        user_id=payload.user_id,
        limit=10
    )

    pdf_path = await asyncio.to_thread(
        compile_tailored_ats_resume,
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
async def get_compiled_pdf(job_id: str):
    """
    FR-017 & Ephemeral Disk Recovery: Serves the compiled ATS Typst PDF.
    If Render restarted and cleared the local disk, recovers and re-renders the PDF from the database.
    """
    resumes_dir = settings.STORAGE_DIR / "resumes" / f"build_{job_id}"
    pdf_files = list(resumes_dir.glob("**/*.pdf"))
    
    if pdf_files and os.path.exists(pdf_files[0]):
        return FileResponse(
            path=str(pdf_files[0]),
            media_type="application/pdf",
            filename=pdf_files[0].name,
            headers={"Content-Disposition": f"inline; filename=CareerOrbit_Resume_{job_id}.pdf"}
        )

    # Ephemeral Recovery: Look up tailored_yaml in DB
    conn = get_raw_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM discovered_jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
    finally:
        conn.close()

    if row and row["tailored_yaml"]:
        yaml_path = resumes_dir / f"Resume_Recovered_{job_id}.yaml"
        recovered_pdf = await asyncio.to_thread(
            render_yaml_to_pdf,
            row["tailored_yaml"],
            resumes_dir,
            yaml_path
        )
        if recovered_pdf and os.path.exists(recovered_pdf):
            return FileResponse(
                path=recovered_pdf,
                media_type="application/pdf",
                filename=Path(recovered_pdf).name,
                headers={"Content-Disposition": f"inline; filename=CareerOrbit_Resume_{job_id}.pdf"}
            )

    # Compile dynamically on the fly
    job_record = {
        "id": job_id,
        "title": row["title"] if row else "Software Engineering Intern",
        "company": row["company"] if row else "Corporate Partner",
        "role_category": row["role_category"] if row else "SDE",
        "description": row["description"] if row else "Software Engineering and AI/ML internship opportunities for B.Tech 2028."
    }
    profile = get_candidate_constraints("default_user") or {
        "full_name": "Aman Sharma",
        "email": "aman.sharma28@example.com",
        "phone": "+91 9876543210",
        "current_location": "Bangalore, India",
        "degree": "B.Tech",
        "graduation_batch": 2028,
        "current_academic_year": "3rd Year",
        "cgpa": 8.95
    }
    memories = memory_manager.search_memory(
        query=f"{job_record['title']} {job_record['description']}",
        user_id="default_user",
        limit=10
    )
    new_pdf = await asyncio.to_thread(
        compile_tailored_ats_resume,
        candidate_profile=profile,
        retrieved_memories=memories,
        job_posting=job_record
    )
    if new_pdf and os.path.exists(new_pdf):
        return FileResponse(
            path=new_pdf,
            media_type="application/pdf",
            filename=Path(new_pdf).name,
            headers={"Content-Disposition": f"inline; filename=CareerOrbit_Resume_{job_id}.pdf"}
        )

    raise HTTPException(status_code=404, detail="Resume PDF could not be compiled for this opportunity.")

@router.get("/{job_id}/evidence")
def get_requirement_evidence(job_id: str):
    """FR-023: Returns the Requirement-to-Evidence map for an opportunity."""
    conn = get_raw_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT requirement_evidence_json, match_score, truthfulness_status FROM discovered_jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Opportunity not found.")
        evidence = json.loads(row["requirement_evidence_json"] or "{}")
        return {
            "job_id": job_id,
            "match_score": row["match_score"],
            "truthfulness_status": row["truthfulness_status"] or "VERIFIED",
            "evidence": evidence
        }
    finally:
        conn.close()
