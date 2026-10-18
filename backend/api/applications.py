"""
CareerClaw - Application Management & Two-Phase HITL Webhook Router
Endpoints for staging applications, viewing staged screenshots,
processing HMAC JWT approval webhooks, and the iterative [Improve] feedback loop.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from backend.config import settings
from backend.database import (
    get_application,
    list_applications,
    update_application_status,
    get_candidate_constraints,
    get_db_connection
)
from backend.browser_agent.hitl_mailer import verify_hitl_token, generate_hitl_tokens
from backend.browser_agent.applier import stage_application, submit_staged_application
from backend.memory.mem0_manager import memory_manager
from backend.resume_engine.rendercv_compiler import compile_tailored_ats_resume

router = APIRouter(prefix="/api/v1", tags=["Applications & HITL Approvals"])

class StageApplicationRequest(BaseModel):
    job_id: Optional[str] = None
    portal_url: Optional[str] = None
    company: Optional[str] = "Adobe"
    role_title: Optional[str] = "AI/ML Software Engineering Intern"
    user_id: Optional[str] = "default_user"

class ImproveApplicationRequest(BaseModel):
    feedback_text: str
    user_id: Optional[str] = "default_user"

@router.get("/applications")
def get_all_applications(status: Optional[str] = None):
    """List applications with optional filter (e.g. STAGED_FOR_APPROVAL)."""
    apps = list_applications(status=status)
    return {
        "count": len(apps),
        "applications": apps
    }

@router.get("/applications/{app_id}")
def get_application_by_id(app_id: str):
    """Retrieve details for a single application."""
    app = get_application(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")
    return app

@router.post("/applications/stage")
def trigger_stage_application(payload: StageApplicationRequest):
    """
    FR-20: Triggers browser agent to stage form, attach PDF, pause before Submit,
    and send the cryptographic approval email.
    """
    # 1. Fetch Job Info
    job_record = None
    if payload.job_id:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM discovered_jobs WHERE id = ?", (payload.job_id,))
        row = c.fetchone()
        conn.close()
        if row:
            job_record = dict(row)

    if not job_record:
        job_record = {
            "id": payload.job_id or "job_adobe_demo",
            "company": payload.company,
            "title": payload.role_title,
            "role_title": payload.role_title,
            "url": payload.portal_url or f"{settings.API_BASE_URL}/mock-portals/adobe-aiml-intern-2028",
            "role_category": "AIML",
            "description": "Looking for B.Tech interns with Python, PyTorch, and distributed systems skills."
        }

    # 2. Get Profile & Constraints
    profile = get_candidate_constraints(payload.user_id) or {
        "full_name": "Aman Sharma",
        "email": "aman.sharma28@example.com",
        "phone": "+91 9876543210",
        "degree": "B.Tech",
        "graduation_batch": 2028,
        "current_academic_year": "3rd Year",
        "github_url": "https://github.com/amansharma2028",
        "linkedin_url": "https://linkedin.com/in/amansharma2028"
    }

    # 3. Compile or retrieve Tailored PDF
    memories = memory_manager.search_memory(
        query=f"{job_record['title']} {job_record.get('description', '')}",
        user_id=payload.user_id,
        limit=8
    )
    pdf_path = compile_tailored_ats_resume(
        candidate_profile=profile,
        retrieved_memories=memories,
        job_posting=job_record
    )

    # 4. Stage via Browser Agent
    staging_res = stage_application(
        job_posting=job_record,
        candidate_profile=profile,
        tailored_pdf_path=pdf_path
    )

    return staging_res

@router.get("/applications/{app_id}/screenshot")
def get_staged_screenshot(app_id: str):
    """Serves the staged or submitted verification screenshot."""
    app = get_application(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    screenshot_path = app.get("staged_screenshot_path")
    if not screenshot_path or not os.path.exists(screenshot_path):
        # Fallback to default staged path
        default_path = settings.SCREENSHOTS_DIR / f"staged_{app_id}.png"
        if default_path.exists():
            screenshot_path = str(default_path)
        else:
            raise HTTPException(status_code=404, detail="Screenshot not available.")

    return FileResponse(path=screenshot_path, media_type="image/png")

@router.get("/hitl/decide", response_class=HTMLResponse)
def handle_hitl_decision(token: str = Query(...)):
    """
    FR-22: Webhook invoked when the student clicks [Approve], [Improve], or [Reject] in email.
    Verifies cryptographic JWT token and executes the decision.
    """
    try:
        payload = verify_hitl_token(token)
    except Exception as err:
        return HTMLResponse(
            content=f"""<html><body style="font-family:-apple-system,sans-serif; background:#F5F5F7; text-align:center; padding:60px;">
                <div style="background:white; max-width:500px; margin:0 auto; padding:40px; border-radius:20px; box-shadow:0 4px 24px rgba(0,0,0,0.06);">
                    <h2 style="color:#FF3B30;">Invalid or Expired Token</h2>
                    <p style="color:#86868B;">The cryptographic authorization link could not be verified ({err}).</p>
                </div>
            </body></html>""",
            status_code=400
        )

    app_id = payload.get("app_id")
    action = payload.get("action")
    app = get_application(app_id)

    if not app:
        return HTMLResponse(content="<h2>Application not found</h2>", status_code=404)

    company = app.get("company", "Company")
    role_title = app.get("role_title", "Role")

    if action == "APPROVE":
        # Execute Phase 2 Submission
        try:
            sub_res = submit_staged_application(app_id)
            return HTMLResponse(content=f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Application Approved &amp; Submitted</title>
</head>
<body style="font-family:-apple-system,BlinkMacSystemFont,sans-serif; background-color:#F5F5F7; text-align:center; padding:60px 20px;">
  <div style="max-width:560px; margin:0 auto; background:#FFFFFF; border-radius:24px; padding:48px; border:1px solid rgba(0,0,0,0.06); box-shadow:0 8px 32px rgba(0,0,0,0.04);">
    <div style="font-size:48px; color:#34C759; margin-bottom:12px;">&#10004;</div>
    <span style="background-color:#E8F8EE; color:#1D8348; font-size:12px; font-weight:700; padding:6px 14px; border-radius:9999px;">
      STATUS: APPROVED &amp; SUBMITTED
    </span>
    <h1 style="font-size:24px; margin:16px 0 8px 0; color:#1D1D1F;">Application Sent Successfully!</h1>
    <p style="font-size:15px; color:#515154; margin:0 0 20px 0;">
      Your application for <strong>{role_title}</strong> at <strong>{company}</strong> has been finalized and submitted by the CareerClaw Browser Agent.
    </p>
    <a href="{settings.APP_BASE_URL}/approvals" style="display:inline-block; background-color:#0071E3; color:#FFFFFF; text-decoration:none; font-size:14px; font-weight:600; padding:12px 28px; border-radius:9999px;">
      Return to Control Plane
    </a>
  </div>
</body>
</html>""")
        except Exception as e:
            return HTMLResponse(content=f"<h2>Submission error: {e}</h2>", status_code=500)

    elif action == "REJECT":
        update_application_status(app_id=app_id, status="REJECTED_BY_USER")
        return HTMLResponse(content=f"""<!DOCTYPE html>
<html>
<body style="font-family:-apple-system,sans-serif; background-color:#F5F5F7; text-align:center; padding:60px 20px;">
  <div style="max-width:520px; margin:0 auto; background:#FFFFFF; border-radius:24px; padding:48px; border:1px solid rgba(0,0,0,0.06); box-shadow:0 8px 32px rgba(0,0,0,0.04);">
    <div style="font-size:40px; color:#86868B; margin-bottom:12px;">&#10005;</div>
    <h2 style="color:#1D1D1F; margin:0 0 8px 0;">Opportunity Archived</h2>
    <p style="color:#86868B;">Application for {company} has been archived per your instruction.</p>
    <a href="{settings.APP_BASE_URL}/approvals" style="display:inline-block; background-color:#F5F5F7; color:#1D1D1F; text-decoration:none; font-size:14px; padding:10px 24px; border-radius:9999px; border:1px solid rgba(0,0,0,0.08);">
      Return to Dashboard
    </a>
  </div>
</body>
</html>""")

    elif action == "IMPROVE":
        # Redirect user to the Approvals view with the improve drawer open
        redirect_url = f"{settings.APP_BASE_URL}/approvals?app_id={app_id}&action=improve"
        return HTMLResponse(content=f"""<script>window.location.href = "{redirect_url}";</script>
        <p>Redirecting to <a href="{redirect_url}">CareerClaw Approvals Studio</a>...</p>""")

    return HTMLResponse(content="Action acknowledged.", status_code=200)

@router.post("/applications/{app_id}/improve")
def improve_and_restage_application(app_id: str, payload: ImproveApplicationRequest):
    """
    FR-23: Iterative [Improve] flow:
    1. Ingests student's natural language guidance into Mem0.
    2. Re-compiles tailored RenderCV ATS PDF with updated emphasis.
    3. Re-stages browser application with new PDF & updated values.
    """
    app = get_application(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    # 1. Update Mem0 with the student's improvement instruction
    memory_manager.chat_update(
        user_id=payload.user_id,
        user_text=f"For {app['company']} ({app['role_title']}): {payload.feedback_text}"
    )

    # 2. Re-fetch candidate profile
    profile = get_candidate_constraints(payload.user_id) or {
        "full_name": "Aman Sharma",
        "email": "aman.sharma28@example.com",
        "phone": "+91 9876543210",
        "degree": "B.Tech",
        "graduation_batch": 2028
    }

    # 3. Re-compile tailored PDF
    job_record = {
        "id": app.get("job_id", app_id),
        "company": app["company"],
        "title": app["role_title"],
        "url": app["portal_url"],
        "description": f"Role at {app['company']}. Candidate notes: {payload.feedback_text}"
    }

    memories = memory_manager.search_memory(
        query=f"{app['role_title']} {payload.feedback_text}",
        user_id=payload.user_id,
        limit=8
    )

    new_pdf_path = compile_tailored_ats_resume(
        candidate_profile=profile,
        retrieved_memories=memories,
        job_posting=job_record
    )

    # 4. Re-stage application
    restage_res = stage_application(
        job_posting=job_record,
        candidate_profile=profile,
        tailored_pdf_path=new_pdf_path
    )

    # Record improve notes
    update_application_status(
        app_id=app_id,
        status="STAGED_FOR_APPROVAL",
        notes=payload.feedback_text
    )

    return {
        "status": "success",
        "message": "Application re-staged with revised RenderCV PDF and candidate feedback.",
        "application_id": app_id,
        "revised_pdf": new_pdf_path,
        "restage_result": restage_res
    }
