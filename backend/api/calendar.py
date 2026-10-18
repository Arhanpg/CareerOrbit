"""
CareerOrbit - Inbox & Google Calendar API Router
Endpoints for viewing recruiter communications, triggering inbox polling,
and simulating incoming OA invitations and interview slots for judges.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from backend.inbox_calendar.gmail_watcher import (
    extract_career_event_from_email,
    save_inbox_event,
    list_inbox_events
)
from backend.inbox_calendar.gcal_sync import sync_event_to_google_calendar

router = APIRouter(prefix="/api/v1/calendar", tags=["Inbox & Google Calendar Sync"])

class SimulateEmailRequest(BaseModel):
    subject: str = "Amazon Student Programs: HackerRank Assessment Invitation"
    body: str = "Dear Candidate, Thank you for applying for the Software Development Engineer Intern (2028 Batch) position. Please complete your 90-minute online assessment on HackerRank within 48 hours of receiving this email: https://www.hackerrank.com/tests/amzn-sde-2028"
    sender: str = "university-recruiting@amazon.com"

@router.get("/events")
def get_all_calendar_events():
    """Retrieve all detected recruiter communications with Google Calendar sync status."""
    events = list_inbox_events()
    return {
        "count": len(events),
        "events": events
    }

@router.post("/simulate-email")
def simulate_incoming_recruiter_email(payload: SimulateEmailRequest):
    """
    Simulates receipt of an email (e.g. HackerRank OA or Teams Interview).
    Extracts structured data via Nemotron 3.5 Lightning and syncs to Google Calendar.
    """
    extracted = extract_career_event_from_email(
        subject=payload.subject,
        body=payload.body,
        sender=payload.sender
    )

    if not extracted.get("is_career_event"):
        return {
            "status": "ignored",
            "message": "Email classified as non-recruitment or promotional.",
            "data": extracted
        }

    # Save to SQLite DB
    ev_id = save_inbox_event(extracted)

    # Sync to Google Calendar
    sync_res = sync_event_to_google_calendar(extracted, event_id=ev_id)

    return {
        "status": "success",
        "event_id": ev_id,
        "extracted_event": extracted,
        "gcal_sync": sync_res
    }

@router.post("/sync-now")
def trigger_calendar_sweep():
    """Triggers an immediate sweep of all unsynced inbox events."""
    events = list_inbox_events()
    synced_count = 0
    for ev in events:
        if not ev.get("synced_to_gcal"):
            sync_event_to_google_calendar(ev, event_id=ev["id"])
            synced_count += 1

    return {
        "status": "success",
        "total_events": len(events),
        "newly_synced": synced_count
    }
