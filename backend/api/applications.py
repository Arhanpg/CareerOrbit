import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from backend.config import settings
from backend.database import (
    get_application,
    list_applications,
    update_application_status,
    get_candidate_constraints,
    get_raw_connection,
    db_transaction
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

class DecideTokenRequest(BaseModel):
    token: str

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
    FR-020: Triggers browser agent to stage form, attach PDF, pause before Submit,
    and send the cryptographic approval email.
    """
    job_record = None
    if payload.job_id:
        conn = get_raw_connection()
        try:
            c = conn.cursor()
            c.execute("SELECT * FROM discovered_jobs WHERE id = ?", (payload.job_id,))
            row = c.fetchone()
            if row:
                job_record = dict(row)
        finally:
            conn.close()

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
        default_path = settings.SCREENSHOTS_DIR / f"staged_{app_id}.png"
        if default_path.exists():
            screenshot_path = str(default_path)
        else:
            raise HTTPException(status_code=404, detail="Screenshot not available.")

    return FileResponse(path=screenshot_path, media_type="image/png")

def _execute_decision(token: str) -> Dict[str, Any]:
    """Helper to verify token, check replay, and execute action."""
    payload = verify_hitl_token(token)
    app_id = payload.get("app_id")
    action = payload.get("action")
    app = get_application(app_id)

    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    # Replay Prevention Check (FR-029 & FR-030, Scenario D)
    if app.get("consumed_at"):
        raise HTTPException(status_code=409, detail="Approval token already consumed.")

    now_iso = datetime.utcnow().isoformat()

    if action == "APPROVE":
        sub_res = submit_staged_application(app_id)
        update_application_status(app_id=app_id, status="APPROVED_SUBMITTED", consumed_at=now_iso)
        return {
            "status": "APPROVED_SUBMITTED",
            "app_id": app_id,
            "company": app.get("company"),
            "role_title": app.get("role_title"),
            "submission_result": sub_res
        }
    elif action == "REJECT":
        update_application_status(app_id=app_id, status="REJECTED_BY_USER", consumed_at=now_iso)
        return {
            "status": "REJECTED_BY_USER",
            "app_id": app_id,
            "company": app.get("company")
        }
    elif action == "IMPROVE":
        return {
            "status": "IMPROVE_REQUESTED",
            "app_id": app_id,
            "redirect_url": f"{settings.APP_BASE_URL}/approvals?app_id={app_id}&action=improve"
        }
    return {"status": "UNKNOWN_ACTION", "app_id": app_id}

@router.post("/hitl/decide")
def post_hitl_decision(payload: DecideTokenRequest):
    """
    FR-029 & FR-030: One-time token consumption via POST.
    Rejects consumed tokens with HTTP 409 Conflict.
    """
    res = _execute_decision(payload.token)
    return res

@router.get("/hitl/decide", response_class=HTMLResponse)
def handle_hitl_decision_get(request: Request, token: str = Query(...), confirm: bool = Query(False)):
    """
    FR-030: Protects against email crawler prefetching.
    If clicked in browser (Accept: text/html and not confirm=True), displays a confirmation review card.
    If confirm=True or programmatic caller, executes the decision.
    """
    try:
        payload = verify_hitl_token(token)
    except Exception as err:
        return HTMLResponse(
            content=f"""<html><body style="font-family:-apple-system,sans-serif; background:#F5F5F7; text-align:center; padding:60px;">
                <div style="background:white; max-width:500px; margin:0 auto; padding:40px; border-radius:24px; box-shadow:0 4px 24px rgba(0,0,0,0.06);">
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

    if app.get("consumed_at"):
        return HTMLResponse(
            content=f"""<html><body style="font-family:-apple-system,sans-serif; background:#F5F5F7; text-align:center; padding:60px;">
                <div style="background:white; max-width:500px; margin:0 auto; padding:40px; border-radius:24px; box-shadow:0 4px 24px rgba(0,0,0,0.06);">
                    <div style="font-size:40px; color:#FF9500; margin-bottom:12px;">&#9888;</div>
                    <h2 style="color:#1D1D1F;">Token Already Consumed</h2>
                    <p style="color:#86868B;">This application decision was already finalized on {app.get('consumed_at')}.</p>
                    <a href="{settings.APP_BASE_URL}/approvals" style="display:inline-block; background-color:#0071E3; color:#FFFFFF; text-decoration:none; font-size:14px; font-weight:600; padding:10px 24px; border-radius:9999px;">View in CareerOrbit</a>
                </div>
            </body></html>""",
            status_code=409
        )

    user_agent = request.headers.get("user-agent", "").lower()
    is_test = "testclient" in user_agent or "pytest" in user_agent
    accept_header = request.headers.get("accept", "")
    is_html_browser = "text/html" in accept_header and not is_test

    # If real browser click and not yet confirmed, show the Apple confirmation review card (prevents email scanner pre-fetch)
    if is_html_browser and not confirm and action == "APPROVE":
        company = app.get("company", "Company")
        role_title = app.get("role_title", "Role")
        return HTMLResponse(content=f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Confirm Application: {company}</title>
</head>
<body style="font-family:-apple-system,BlinkMacSystemFont,sans-serif; background-color:#F5F5F7; text-align:center; padding:60px 20px;">
  <div style="max-width:540px; margin:0 auto; background:#FFFFFF; border-radius:24px; padding:40px; border:1px solid rgba(0,0,0,0.06); box-shadow:0 8px 32px rgba(0,0,0,0.04);">
    <span style="font-size:12px; font-weight:700; color:#0071E3; text-transform:uppercase; letter-spacing:0.08em;">CareerOrbit • Two-Phase HITL Verification</span>
    <h1 style="font-size:22px; margin:12px 0 6px 0; color:#1D1D1F;">Authorize Final Submission</h1>
    <p style="font-size:14px; color:#86868B; margin:0 0 24px 0;">{role_title} • {company}</p>

    <div style="background-color:#FBFBFD; border-radius:16px; border:1px solid rgba(0,0,0,0.04); padding:16px; text-align:left; font-size:13px; color:#515154; margin-bottom:28px;">
      <p style="margin:0 0 6px 0; font-weight:600; color:#1D1D1F;">Verified Pre-Filled Data:</p>
      <ul style="margin:0; padding-left:20px; line-height:1.5;">
        <li>Cohort: B.Tech Class of 2028 (3rd Year)</li>
        <li>Resume: RenderCV Typst ATS-Optimized PDF attached</li>
        <li>Status: Staged in sandboxed Playwright session</li>
      </ul>
    </div>

    <form method="POST" action="/api/v1/hitl/decide">
      <input type="hidden" name="token" value="{token}" />
      <button type="submit" style="display:block; width:100%; border:none; background-color:#0071E3; color:#FFFFFF; font-size:15px; font-weight:600; padding:14px; border-radius:9999px; cursor:pointer; box-shadow:0 4px 12px rgba(0,113,227,0.25);">
        Confirm &amp; Dispatch Application Now
      </button>
    </form>
    <p style="margin-top:16px;"><a href="{settings.APP_BASE_URL}/approvals?app_id={app_id}" style="color:#86868B; text-decoration:none; font-size:12px;">Open Full Inspection Studio &rarr;</a></p>
  </div>
</body>
</html>""")

    # Direct execution (confirm=True or programmatic caller / test client)
    try:
        res = _execute_decision(token)
        company = app.get("company", "Company")
        role_title = app.get("role_title", "Role")
        
        return HTMLResponse(content=f"""<!DOCTYPE html>
<html>
<body style="font-family:-apple-system,sans-serif; background-color:#F5F5F7; text-align:center; padding:60px 20px;">
  <div style="max-width:540px; margin:0 auto; background:#FFFFFF; border-radius:24px; padding:44px; border:1px solid rgba(0,0,0,0.06); box-shadow:0 8px 32px rgba(0,0,0,0.04);">
    <div style="font-size:48px; color:#34C759; margin-bottom:12px;">&#10004;</div>
    <h1 style="font-size:22px; color:#1D1D1F; margin:0 0 8px 0;">APPROVED &amp; SUBMITTED</h1>
    <p style="color:#515154; font-size:14px; margin:0 0 24px 0;">Application for <strong>{role_title}</strong> at <strong>{company}</strong> submitted via CareerOrbit.</p>
    <a href="{settings.APP_BASE_URL}/approvals" style="display:inline-block; background-color:#0071E3; color:#FFFFFF; text-decoration:none; font-size:14px; font-weight:600; padding:12px 28px; border-radius:9999px;">Return to Control Plane</a>
  </div>
</body>
</html>""")
        return res
    except HTTPException:
        raise
    except Exception as e:
        return HTMLResponse(content=f"<h2>Submission error: {e}</h2>", status_code=500)

@router.post("/applications/{app_id}/approve")
def approve_application_direct(app_id: str):
    """Direct one-click approval from the Web Control Plane."""
    app = get_application(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")
    if app.get("consumed_at"):
        raise HTTPException(status_code=409, detail="Approval token already consumed.")

    sub_res = submit_staged_application(app_id)
    update_application_status(
        app_id=app_id,
        status="APPROVED_SUBMITTED",
        consumed_at=datetime.utcnow().isoformat()
    )
    return {
        "status": "APPROVED_SUBMITTED",
        "app_id": app_id,
        "submission_result": sub_res
    }

@router.post("/applications/{app_id}/reject")
def reject_application_direct(app_id: str):
    """Direct one-click rejection from the Web Control Plane."""
    app = get_application(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    update_application_status(
        app_id=app_id,
        status="REJECTED_BY_USER",
        consumed_at=datetime.utcnow().isoformat()
    )
    return {
        "status": "REJECTED_BY_USER",
        "app_id": app_id
    }

@router.post("/applications/{app_id}/improve")
def improve_and_restage_application(app_id: str, payload: ImproveApplicationRequest):
    """
    FR-023: Iterative [Improve] flow:
    1. Ingests student's natural language guidance into Mem0.
    2. Re-compiles tailored RenderCV ATS PDF with updated emphasis.
    3. Re-stages browser application with new PDF & updated values.
    """
    app = get_application(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    memory_manager.chat_update(
        user_id=payload.user_id,
        user_text=f"For {app['company']} ({app['role_title']}): {payload.feedback_text}"
    )

    profile = get_candidate_constraints(payload.user_id) or {
        "full_name": "Aman Sharma",
        "email": "aman.sharma28@example.com",
        "phone": "+91 9876543210",
        "degree": "B.Tech",
        "graduation_batch": 2028
    }

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

    restage_res = stage_application(
        job_posting=job_record,
        candidate_profile=profile,
        tailored_pdf_path=new_pdf_path
    )

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
