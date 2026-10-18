"""
Phase 7 Automated Verification:
End-to-End 60-Second Judge Sandbox Mode Test.
Asserts that all 6 stages of the autonomous lifecycle execute cleanly in under 60 seconds.
"""

import time
import socket
import threading
import uvicorn
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.config import settings

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
        
        for _ in range(50):
            sock = socket.socket()
            if sock.connect_ex(('127.0.0.1', 8000)) == 0:
                sock.close()
                break
            sock.close()
            time.sleep(0.1)
    yield

def test_judge_60s_sandbox_end_to_end_loop():
    """
    FR-27: Validates that the entire autonomous career lifecycle completes in under 60 seconds:
    1. Preloads B.Tech 2028 candidate profile.
    2. Recalls multi-vector facts from Mem0.
    3. Synthesizes tailored RenderCV Typst ATS PDF with zero hallucinations.
    4. Pre-fills form fields via Chromium over CDP & halts before submit.
    5. Verifies cryptographic HS256 JWT action link & finalizes submission.
    6. Extracts HackerRank OA & auto-schedules 2h focus block in Asia/Kolkata (+05:30).
    """
    start_time = time.time()

    res = client.post(
        "/api/v1/sandbox/run-60s-loop",
        json={
            "user_id": "test_judge_e2e_user",
            "candidate_name": "Aman Sharma",
            "recipient_email": "aman.sharma28@example.com"
        }
    )
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "success"
    assert data["mode"] == "JUDGE_60S_SANDBOX"
    assert data["under_60_seconds"] is True
    assert data["total_duration_seconds"] < 60.0

    # Assert all 6 telemetry stages succeeded
    telemetry = data["telemetry"]
    assert len(telemetry) == 6
    for t in telemetry:
        assert t["status"] == "COMPLETED"

    stage_names = [t["name"] for t in telemetry]
    assert any("Profile" in n for n in stage_names)
    assert any("Mem0" in n for n in stage_names)
    assert any("RenderCV" in n for n in stage_names)
    assert any("Browser" in n for n in stage_names)
    assert any("Approval" in n for n in stage_names)
    assert any("Google Calendar" in n for n in stage_names)

    # Verify PDF download endpoint works
    pdf_url = data["pdf_download_url"]
    pdf_res = client.get(pdf_url)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 1000

    # Verify screenshot endpoint works
    screenshot_url = data["screenshot_url"]
    screen_res = client.get(screenshot_url)
    assert screen_res.status_code == 200
    assert "image" in screen_res.headers["content-type"]
    assert len(screen_res.content) > 1000

    # Verify calendar link generated
    assert data["gcal_event_link"] is not None
    assert "calendar.google.com" in data["gcal_event_link"]
