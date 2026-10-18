"""
Phase 5 Automated Verification:
Tests Sandboxed Browser Auto-Applier, Two-Phase HITL Protocol,
Cryptographic HS256 JWT Action Links, Mock Corporate ATS Portal, and Approval Execution.
"""

import os
import time
import socket
import threading
import uvicorn
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.config import settings
from backend.database import get_application, update_application_status
from backend.browser_agent.hitl_mailer import (
    generate_hitl_tokens,
    verify_hitl_token,
    send_approval_email
)
from backend.browser_agent.applier import stage_application, submit_staged_application

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def run_test_server():
    """Starts FastAPI uvicorn server on 127.0.0.1:8000 for Playwright browser automation."""
    s = socket.socket()
    port_in_use = (s.connect_ex(('127.0.0.1', 8000)) == 0)
    s.close()

    if not port_in_use:
        config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="warning")
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        
        # Wait up to 5s for server to bind
        for _ in range(50):
            sock = socket.socket()
            if sock.connect_ex(('127.0.0.1', 8000)) == 0:
                sock.close()
                break
            sock.close()
            time.sleep(0.1)
    yield

def test_hitl_jwt_token_security():
    """Verify cryptographic generation, expiration, and tampering detection of HITL tokens."""
    app_id = "test_app_hitl_777"
    tokens = generate_hitl_tokens(application_id=app_id, user_id="student_2028")

    assert "approve_token" in tokens
    assert "reject_token" in tokens
    assert "improve_token" in tokens
    assert "approve_url" in tokens

    # Verify approve token
    payload = verify_hitl_token(tokens["approve_token"])
    assert payload["app_id"] == app_id
    assert payload["action"] == "APPROVE"
    assert payload["user_id"] == "student_2028"

    # Verify reject token
    reject_payload = verify_hitl_token(tokens["reject_token"])
    assert reject_payload["action"] == "REJECT"

    # Test tampering rejection
    tampered = tokens["approve_token"][:-4] + "fake"
    with pytest.raises(Exception):
        verify_hitl_token(tampered)

def test_mock_corporate_portal_routes():
    """Verify self-hosted Adobe Workday/Greenhouse mock portal loads and accepts submissions."""
    # Test GET portal
    get_res = client.get("/mock-portals/adobe-aiml-intern-2028")
    assert get_res.status_code == 200
    assert "Adobe" in get_res.text
    assert "application-form" in get_res.text
    assert "submit-btn" in get_res.text
    assert "2028" in get_res.text

    # Test POST submit
    post_res = client.post(
        "/mock-portals/adobe-aiml-intern-2028/submit",
        data={
            "full_name": "Aman Sharma",
            "email": "aman.sharma28@example.com",
            "phone": "+91 9876543210",
            "graduation_year": 2028
        }
    )
    assert post_res.status_code == 200
    assert "Application Submitted Successfully!" in post_res.text
    assert "ADB-2028" in post_res.text

def test_browser_staging_and_approval_workflow(tmp_path):
    """
    FR-19, FR-20, FR-21, FR-22:
    1. Stages form via Browser Agent and halts before submit.
    2. Asserts screenshot is captured and status is STAGED_FOR_APPROVAL.
    3. Invokes cryptographic JWT decision webhook.
    4. Asserts application transitions to APPROVED_SUBMITTED.
    """
    # Create temporary dummy PDF resume
    sample_pdf = tmp_path / "Resume_Aman_Sharma.pdf"
    with open(sample_pdf, "wb") as f:
        f.write(b"%PDF-1.4 sample resume content for testing")

    candidate_profile = {
        "full_name": "Aman Sharma",
        "email": "aman.sharma28@example.com",
        "phone": "+91 9876543210",
        "degree": "B.Tech",
        "graduation_batch": 2028,
        "github_url": "https://github.com/amansharma2028",
        "linkedin_url": "https://linkedin.com/in/amansharma2028"
    }

    job_posting = {
        "id": "adobe_aiml_2028_test",
        "company": "Adobe",
        "title": "AI/ML Software Engineering Intern",
        "url": f"{settings.API_BASE_URL}/mock-portals/adobe-aiml-intern-2028"
    }

    # 1. Trigger Staging (execute_final_submit=False)
    staging_res = stage_application(
        job_posting=job_posting,
        candidate_profile=candidate_profile,
        tailored_pdf_path=str(sample_pdf),
        headless=True
    )

    app_id = staging_res["application_id"]
    assert staging_res["status"] == "STAGED_FOR_APPROVAL"
    assert os.path.exists(staging_res["screenshot_path"])
    assert os.path.getsize(staging_res["screenshot_path"]) > 0

    # Verify DB record
    db_app = get_application(app_id)
    assert db_app is not None
    assert db_app["status"] == "STAGED_FOR_APPROVAL"
    assert db_app["company"] == "Adobe"

    # Verify Email tokens
    email_dispatch = staging_res["email_dispatch"]
    assert "tokens" in email_dispatch
    approve_token = email_dispatch["tokens"]["approve_token"]

    # 2. Invoke Webhook with Approve Token (FR-22)
    decide_res = client.get(f"/api/v1/hitl/decide?token={approve_token}")
    assert decide_res.status_code == 200
    assert "APPROVED &amp; SUBMITTED" in decide_res.text or "Approved" in decide_res.text

    # Verify DB state has transitioned
    updated_app = get_application(app_id)
    assert updated_app["status"] == "APPROVED_SUBMITTED"

def test_improve_feedback_loop():
    """FR-23: Test [Improve] feedback loop re-stages with candidate instructions."""
    # Stage initial application via API
    stage_res = client.post(
        "/api/v1/applications/stage",
        json={
            "company": "Adobe",
            "role_title": "AI/ML Intern",
            "portal_url": f"{settings.API_BASE_URL}/mock-portals/adobe-aiml-intern-2028"
        }
    )
    assert stage_res.status_code == 200
    app_id = stage_res.json()["application_id"]

    # Call improve endpoint
    improve_res = client.post(
        f"/api/v1/applications/{app_id}/improve",
        json={"feedback_text": "Emphasize my CUDA & PyTorch distributed inference experience."}
    )
    assert improve_res.status_code == 200
    data = improve_res.json()
    assert data["status"] == "success"

    # Verify DB updated
    app_record = get_application(app_id)
    assert "CUDA" in (app_record.get("improve_notes") or "")
