"""
Phase 6 Automated Verification:
Tests 24/7 Gmail OA/Interview Parser, Nemotron 3.5 Lightning Extraction,
Asia/Kolkata (+05:30) 2-Hour OA Focus Block Calculation, and Google Calendar Sync.
"""

from datetime import datetime
from fastapi.testclient import TestClient

from backend.main import app
from backend.inbox_calendar.gmail_watcher import extract_career_event_from_email
from backend.inbox_calendar.gcal_sync import build_gcal_event_body, sync_event_to_google_calendar

client = TestClient(app)

def test_gmail_oa_extraction_and_focus_block_scheduling():
    """
    FR-24 & FR-25: Validates that an Amazon HackerRank OA email with a 48-hour completion window
    triggers an automated 2-hour study/test block 24 hours prior to deadline in Asia/Kolkata (+05:30).
    """
    subject = "Amazon Student Programs: HackerRank Assessment Invitation"
    body = (
        "Dear Candidate,\n"
        "Thank you for applying for the Software Development Engineer Intern (2028 Batch) position.\n"
        "Please complete your 90-minute online assessment on HackerRank within 48 hours of receiving this email: "
        "https://www.hackerrank.com/tests/amzn-sde-2028"
    )
    sender = "university-recruiting@amazon.com"

    extracted = extract_career_event_from_email(subject, body, sender)

    assert extracted["is_career_event"] is True
    assert extracted["event_category"] == "ONLINE_ASSESSMENT"
    assert "Amazon" in extracted["company_name"]
    assert "hackerrank.com" in extracted["action_link"]

    # Verify Asia/Kolkata (+05:30) ISO-8601 formatting
    start_iso = extracted["start_datetime_iso"]
    end_iso = extracted["end_datetime_iso"]
    assert "+05:30" in start_iso
    assert "+05:30" in end_iso

    # Verify 2-hour focus block duration (120 minutes)
    start_dt = datetime.fromisoformat(start_iso)
    end_dt = datetime.fromisoformat(end_iso)
    duration_minutes = (end_dt - start_dt).total_seconds() / 60
    assert duration_minutes == 120

    # Verify standard Google Calendar payload
    gcal_body = build_gcal_event_body(extracted)
    assert gcal_body["start"]["timeZone"] == "Asia/Kolkata"
    assert gcal_body["end"]["timeZone"] == "Asia/Kolkata"
    assert len(gcal_body["reminders"]["overrides"]) == 3

def test_gmail_technical_interview_extraction():
    """
    FR-25: Validates that a Microsoft technical interview email extracts
    TECHNICAL_INTERVIEW category, Teams meeting URL, and valid Asia/Kolkata slot.
    """
    subject = "Microsoft: Technical Interview Invitation (Batch 2028)"
    body = (
        "Hello Aman,\n"
        "We are pleased to invite you for your round 1 technical interview on distributed algorithms.\n"
        "Meeting Link: https://teams.microsoft.com/l/meetup-join/msft-intern-2028"
    )
    sender = "interviews@microsoft.com"

    extracted = extract_career_event_from_email(subject, body, sender)

    assert extracted["is_career_event"] is True
    assert extracted["event_category"] == "TECHNICAL_INTERVIEW"
    assert "Microsoft" in extracted["company_name"]
    assert "teams.microsoft.com" in extracted["action_link"]
    assert "+05:30" in extracted["start_datetime_iso"]

def test_promotional_newsletter_ignored():
    """
    FR-25: Validates that marketing newsletters and non-recruitment emails
    are filtered out with is_career_event == False.
    """
    subject = "Special 50% discount on tech courses! Unsubscribe anytime"
    body = "Promotional offer for students. Check out our seasonal sale on certification bundles."
    sender = "promotions@techcourses.example"

    extracted = extract_career_event_from_email(subject, body, sender)

    assert extracted["is_career_event"] is False
    assert extracted["event_category"] == "IRRELEVANT"

def test_gcal_sync_and_api_simulation():
    """
    FR-26: Test API simulation endpoint and Google Calendar sync flow.
    """
    # 1. Simulate Amazon OA
    res = client.post(
        "/api/v1/calendar/simulate-email",
        json={
            "subject": "Adobe Careers: Coding Challenge for AI/ML Internships",
            "body": "Hi Aman, Please complete the Adobe AI/ML challenge on CodeSignal within 48 hours: https://app.codesignal.com/invite/adobe-aiml-2028",
            "sender": "talent@adobe.com"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "event_id" in data
    assert "gcal_sync" in data
    assert "event_link" in data["gcal_sync"]

    # 2. Query Calendar events endpoint
    events_res = client.get("/api/v1/calendar/events")
    assert events_res.status_code == 200
    events_data = events_res.json()
    assert events_data["count"] >= 1
    found_adobe = any("Adobe" in e["company_name"] for e in events_data["events"])
    assert found_adobe is True
