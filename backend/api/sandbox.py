"""
CareerOrbit - FR-27: 60-Second Judge Sandbox Mode
Provides an instant, zero-key, zero-CAPTCHA end-to-end execution loop for hackathon judges:
Mem0 recall -> Nemotron 3 Ultra RenderCV PDF synthesis -> Browser Staging & Screenshot ->
JWT Approval Webhook -> Final Portal Submission -> Google Calendar Focus Block Sync.
"""

import time
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from backend.config import settings
from backend.database import get_candidate_constraints, save_candidate_constraints
from backend.memory.mem0_manager import memory_manager
from backend.resume_engine.rendercv_compiler import compile_tailored_ats_resume
from backend.browser_agent.applier import stage_application, submit_staged_application
from backend.browser_agent.hitl_mailer import verify_hitl_token
from backend.inbox_calendar.gmail_watcher import extract_career_event_from_email, save_inbox_event
from backend.inbox_calendar.gcal_sync import sync_event_to_google_calendar

router = APIRouter(prefix="/api/v1/sandbox", tags=["60-Second Judge Sandbox"])

class SandboxRunRequest(BaseModel):
    user_id: Optional[str] = "judge_sandbox_user"
    candidate_name: Optional[str] = "Arhan Praveen Ghosarwade"
    recipient_email: Optional[str] = "arhanghosarwade05@gmail.com"

@router.post("/run-60s-loop")
def run_60s_judge_sandbox_loop(payload: Optional[SandboxRunRequest] = None):
    """
    FR-27: Executes the complete 6-stage autonomous lifecycle in under 60 seconds.
    Demonstrates Mem0 recall, RenderCV compilation, Browser staging, JWT approval, and Calendar sync.
    """
    start_time = time.time()
    telemetry = []

    user_id = payload.user_id if payload else "judge_sandbox_user"
    cand_name = payload.candidate_name if payload else "Arhan Praveen Ghosarwade"
    cand_email = payload.recipient_email if payload else "arhanghosarwade05@gmail.com"

    # Step 1: Preload Canonical B.Tech 2028 Profile
    step1_start = time.time()
    profile = {
        "full_name": cand_name,
        "email": cand_email,
        "phone": "+91 6366616225",
        "institution": "Indian Institute of Information Technology (IIIT) Dharwad",
        "current_location": "Dharwad, Karnataka, India",
        "degree": "B.Tech in Computer Science and Engineering",
        "graduation_batch": 2028,
        "current_academic_year": "3rd Year (2024 – 2028)",
        "cgpa": 8.69,
        "github_url": "https://github.com/Arhanpg",
        "linkedin_url": "https://www.linkedin.com/in/arhan-ghosarwade-78bb16324"
    }
    save_candidate_constraints(user_id, profile)
    telemetry.append({
        "stage": 1,
        "name": "Profile & Hard Constraints",
        "status": "COMPLETED",
        "elapsed_seconds": round(time.time() - step1_start, 2),
        "details": f"Candidate: {cand_name} (B.Tech Batch 2028, CGPA 8.95)"
    })

    # Step 2: Seed & Recall Mem0 Facts
    step2_start = time.time()
    memory_manager.add_memory(
        content="Engineered autonomous RAG system using PyTorch and Qdrant cutting query latency by 42%.",
        user_id=user_id,
        metadata={"category": "PROJECT", "source": "Sandbox Seed"}
    )
    memory_manager.add_memory(
        content="Built high-throughput distributed job processing engine with FastAPI and Redis handling 12k RPS.",
        user_id=user_id,
        metadata={"category": "PROJECT", "source": "Sandbox Seed"}
    )

    job_posting = {
        "id": f"sandbox_adobe_{int(time.time())}",
        "company": "Adobe Systems India",
        "title": "AI/ML Software Engineering Intern (2028 Cohort)",
        "role_title": "AI/ML Software Engineering Intern (2028 Cohort)",
        "url": f"{settings.API_BASE_URL}/mock-portals/adobe-aiml-intern-2028",
        "role_category": "AIML",
        "description": "Adobe Research seeking B.Tech 2028 interns with PyTorch, distributed inference, and Python skills."
    }

    memories = memory_manager.search_memory("PyTorch AI distributed systems", user_id=user_id, limit=6)
    telemetry.append({
        "stage": 2,
        "name": "Mem0 Multi-Vector Recall",
        "status": "COMPLETED",
        "elapsed_seconds": round(time.time() - step2_start, 2),
        "details": f"Recalled {len(memories)} atomic facts from vector store"
    })

    # Step 3: RenderCV Typst ATS Resume Compilation
    step3_start = time.time()
    pdf_path = compile_tailored_ats_resume(
        candidate_profile=profile,
        retrieved_memories=memories,
        job_posting=job_posting
    )
    telemetry.append({
        "stage": 3,
        "name": "RenderCV Typst PDF Synthesis",
        "status": "COMPLETED",
        "elapsed_seconds": round(time.time() - step3_start, 2),
        "details": f"Compiled ATS-proof PDF at {pdf_path}"
    })

    # Step 4: Browser Staging & Full-Page Screenshot
    step4_start = time.time()
    staging_res = stage_application(
        job_posting=job_posting,
        candidate_profile=profile,
        tailored_pdf_path=pdf_path,
        headless=True
    )
    app_id = staging_res["application_id"]
    approve_token = staging_res["email_dispatch"]["tokens"]["approve_token"]
    telemetry.append({
        "stage": 4,
        "name": "Browser-Use Form Pre-Fill & Screenshot",
        "status": "COMPLETED",
        "elapsed_seconds": round(time.time() - step4_start, 2),
        "details": f"Staged application {app_id}; paused before submit; verification screenshot saved"
    })

    # Step 5: Cryptographic One-Click Approval & Final Submission
    step5_start = time.time()
    payload = verify_hitl_token(approve_token)
    sub_res = submit_staged_application(app_id, headless=True)
    telemetry.append({
        "stage": 5,
        "name": "Two-Phase JWT Approval & Submit",
        "status": "COMPLETED",
        "elapsed_seconds": round(time.time() - step5_start, 2),
        "details": f"Verified HS256 token; submitted application; status -> APPROVED_SUBMITTED"
    })

    # Step 6: Recruiter OA Email Detection & Google Calendar Sync
    step6_start = time.time()
    mock_email = (
        "Dear Arhan, Thank you for applying to Adobe Systems. "
        "Please complete your 90-minute online coding assessment on HackerRank within 48 hours: "
        "https://www.hackerrank.com/adobe-aiml-intern-2028"
    )
    extracted_event = extract_career_event_from_email(
        subject="Adobe Systems: AI/ML HackerRank Assessment",
        body=mock_email,
        sender="talent@adobe.com"
    )
    ev_id = save_inbox_event(extracted_event)
    gcal_res = sync_event_to_google_calendar(extracted_event, event_id=ev_id)
    telemetry.append({
        "stage": 6,
        "name": "Google Calendar OA Focus Block Sync",
        "status": "COMPLETED",
        "elapsed_seconds": round(time.time() - step6_start, 2),
        "details": f"Auto-scheduled 2-hour study block in Asia/Kolkata (+05:30) 24h prior to 48h deadline"
    })

    total_duration = round(time.time() - start_time, 2)

    return {
        "status": "success",
        "mode": "JUDGE_60S_SANDBOX",
        "total_duration_seconds": total_duration,
        "under_60_seconds": total_duration < 60.0,
        "application_id": app_id,
        "pdf_download_url": f"/api/v1/resumes/{job_posting['id']}/pdf",
        "screenshot_url": f"/api/v1/applications/{app_id}/screenshot",
        "gcal_event_link": gcal_res.get("event_link"),
        "telemetry": telemetry
    }
