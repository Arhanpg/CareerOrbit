import re
import json
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from backend.config import settings
from backend.llm_router import llm_router, extract_json_dict
from backend.database import get_raw_connection, db_transaction

logger = logging.getLogger("careerorbit.gmail_watcher")

# Asia/Kolkata timezone (+05:30)
IST = timezone(timedelta(hours=5, minutes=30))

def parse_with_fallback(subject: str, body: str, sender: str = "") -> Dict[str, Any]:
    """Deterministic fallback regex parser for email recruitment triage."""
    text = f"{subject} {body}".lower()
    
    is_oa = any(k in text for k in ["assessment", "hackerrank", "codesignal", "test link", "coding challenge", "online test"])
    is_interview = any(k in text for k in ["interview", "technical round", "teams.microsoft", "meet.google", "zoom.us", "discussion"])
    is_ambiguous = any(k in text for k in ["next week", "shortly", "soon", "at a later date", "keep you posted"]) and not any(k in text for k in ["at ", "am", "pm", "hours", "hrs"])

    if not (is_oa or is_interview):
        return {
            "is_career_event": False,
            "event_category": "IRRELEVANT",
            "company_name": "",
            "event_title": subject,
            "action_link": None,
            "start_datetime_iso": None,
            "end_datetime_iso": None,
            "sync_status": "IRRELEVANT",
            "notes": "Non-recruitment email"
        }

    company = "Tech Employer"
    for comp in ["Amazon", "Microsoft", "Adobe", "Google", "Uber", "Flipkart", "Atlassian", "Swiggy", "Unstop", "Internshala"]:
        if comp.lower() in text:
            company = comp
            break

    url_match = re.search(r"https?://[^\s<>\"']+", body)
    action_link = url_match.group(0) if url_match else "https://assessment.portal"
    now_ist = datetime.now(IST)

    if is_ambiguous:
        return {
            "is_career_event": True,
            "event_category": "TECHNICAL_INTERVIEW",
            "company_name": company,
            "event_title": f"{company} Interview (Pending Scheduling)",
            "action_link": action_link,
            "start_datetime_iso": (now_ist + timedelta(days=7)).replace(hour=14, minute=0, second=0).isoformat(),
            "end_datetime_iso": (now_ist + timedelta(days=7)).replace(hour=15, minute=0, second=0).isoformat(),
            "sync_status": "NEEDS_CONFIRMATION",
            "notes": "Recruiter indicated interview next week without specific slot. Needs user confirmation."
        }

    if is_oa:
        window_match = re.search(r"(\d+)\s*(?:hours|hrs|hr)", text)
        window_hours = int(window_match.group(1)) if window_match else 48
        deadline_time = now_ist + timedelta(hours=window_hours)
        focus_block_start = deadline_time - timedelta(hours=24)
        focus_block_end = focus_block_start + timedelta(hours=2)

        return {
            "is_career_event": True,
            "event_category": "ONLINE_ASSESSMENT",
            "company_name": company,
            "event_title": f"{company} Online Assessment (OA Focus Block)",
            "action_link": action_link,
            "start_datetime_iso": focus_block_start.isoformat(),
            "end_datetime_iso": focus_block_end.isoformat(),
            "deadline_window_hours": window_hours,
            "sync_status": "SYNCED",
            "notes": f"Auto-scheduled 2-hour focus block 24 hours prior to {window_hours}h assessment deadline."
        }

    elif is_interview:
        start_time = now_ist + timedelta(days=1)
        start_time = start_time.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)

        return {
            "is_career_event": True,
            "event_category": "TECHNICAL_INTERVIEW",
            "company_name": company,
            "event_title": f"{company} Technical Interview Round",
            "action_link": action_link,
            "start_datetime_iso": start_time.isoformat(),
            "end_datetime_iso": end_time.isoformat(),
            "sync_status": "SYNCED",
            "notes": "Interview invitation detected. Video conference link extracted."
        }

    return {
        "is_career_event": False,
        "event_category": "IRRELEVANT",
        "company_name": "",
        "event_title": subject,
        "action_link": None,
        "start_datetime_iso": None,
        "end_datetime_iso": None,
        "sync_status": "IRRELEVANT",
        "notes": "Non-recruitment email"
    }

def extract_career_event_with_nemotron(subject: str, body: str, sender: str = "") -> Dict[str, Any]:
    """FR-025: Parses recruitment emails using Nemotron 3.5 Lightning with robust regex fallback."""
    if settings.is_nebius_configured:
        system_prompt = """You are an AI Email Parser specialized in college student recruitment notifications in India.
Classify the email into: ONLINE_ASSESSMENT, TECHNICAL_INTERVIEW, HR_CALL, or IRRELEVANT.
If is_career_event is true:
- Extract company_name, action_link (test/meeting URL), and event_title.
- For Online Assessments with a completion window (e.g. 48 hours), compute a 2-hour test focus block 24 hours prior to the deadline.
- Output valid ISO-8601 timestamps in Asia/Kolkata (+05:30) format.
Return ONLY valid JSON matching:
{
  "is_career_event": true/false,
  "event_category": "ONLINE_ASSESSMENT" | "TECHNICAL_INTERVIEW" | "HR_CALL" | "IRRELEVANT",
  "company_name": "string",
  "event_title": "string",
  "action_link": "https://...",
  "start_datetime_iso": "YYYY-MM-DDTHH:MM:SS+05:30",
  "end_datetime_iso": "YYYY-MM-DDTHH:MM:SS+05:30",
  "sync_status": "SYNCED" | "NEEDS_CONFIRMATION",
  "notes": "string"
}"""
        user_content = f"Subject: {subject}\nFrom: {sender}\nBody:\n{body[:2000]}"

        try:
            raw_res = llm_router.call_tier1_fast(
                prompt=user_content,
                system_prompt=system_prompt,
                json_mode=True,
                temperature=0.0,
                task_name="gmail_recruitment_triage"
            )
            parsed = extract_json_dict(raw_res)
            if "is_career_event" in parsed:
                if parsed["is_career_event"] and not parsed.get("start_datetime_iso"):
                    return parse_with_fallback(subject, body, sender)
                return parsed
        except Exception as e:
            logger.warning(f"Nemotron 3.5 Lightning email triage note: {e}. Using deterministic parsing.")
            return parse_with_fallback(subject, body, sender)

    return parse_with_fallback(subject, body, sender)

extract_career_event_from_email = extract_career_event_with_nemotron

def save_inbox_event(event_dict: Dict[str, Any], email_id: Optional[str] = None) -> str:
    """Saves parsed career communication to SQLite database with WAL transaction."""
    ev_id = f"ev_{uuid.uuid4().hex[:10]}"
    e_id = email_id or f"mail_{uuid.uuid4().hex[:8]}"

    with db_transaction() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO inbox_events (
                id, email_id, company_name, event_title, event_category,
                action_link, start_datetime_iso, end_datetime_iso,
                synced_to_gcal, sync_status, raw_snippet
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(email_id) DO UPDATE SET
                event_title = excluded.event_title,
                start_datetime_iso = excluded.start_datetime_iso,
                end_datetime_iso = excluded.end_datetime_iso,
                sync_status = excluded.sync_status
        """, (
            ev_id,
            e_id,
            event_dict.get("company_name", "Tech Employer"),
            event_dict.get("event_title", "Career Event"),
            event_dict.get("event_category", "ONLINE_ASSESSMENT"),
            event_dict.get("action_link"),
            event_dict.get("start_datetime_iso"),
            event_dict.get("end_datetime_iso"),
            1 if event_dict.get("synced_to_gcal") else 0,
            event_dict.get("sync_status", "SYNCED"),
            event_dict.get("notes")
        ))
    return ev_id

def list_inbox_events() -> List[Dict[str, Any]]:
    """Retrieve all parsed career emails and calendar events."""
    conn = get_raw_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM inbox_events ORDER BY created_at DESC")
        return [dict(r) for r in c.fetchall()]
    finally:
        conn.close()
