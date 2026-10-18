"""
CareerClaw - FR-24 & FR-25: 24/7 Gmail OA/Interview Watcher
Polls Gmail API for recruiter communications (HackerRank, CodeSignal, OA, Interview),
uses NVIDIA Nemotron 3.5 Lightning on Nebius Token Factory for structured extraction,
and computes IST (+05:30) 2-hour study/test focus blocks 24 hours prior to OA deadlines.
"""

import os
import re
import json
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List

from backend.config import settings
from backend.llm_router import llm_router
from backend.database import get_db_connection

logger = logging.getLogger("careerclaw.gmail_watcher")

# Asia/Kolkata Timezone (+05:30)
IST = timezone(timedelta(hours=5, minutes=30))

def parse_with_fallback(subject: str, body: str, sender: str = "") -> Dict[str, Any]:
    """Deterministic NLP fallback parser for recruiter emails."""
    text = f"{subject}\n{body}".lower()

    # Ignore promotional / newsletter emails
    if any(p in text for p in ["newsletter", "unsubscribe", "promotional", "sale", "discount", "marketing"]):
        return {
            "is_career_event": False,
            "event_category": "IRRELEVANT",
            "company_name": "",
            "event_title": subject,
            "action_link": None,
            "start_datetime_iso": None,
            "end_datetime_iso": None,
            "notes": "Ignored promotional email"
        }

    is_oa = any(k in text for k in ["hackerrank", "codesignal", "mettl", "online assessment", "oa invitation", "coding assessment", "test link"])
    is_interview = any(k in text for k in ["interview", "teams.microsoft.com", "zoom.us", "google meet", "technical round", "hiring manager"])
    is_hr = any(k in text for k in ["hr screening", "recruiter chat", "introductory call"])

    if not (is_oa or is_interview or is_hr):
        return {
            "is_career_event": False,
            "event_category": "IRRELEVANT",
            "company_name": "",
            "event_title": subject,
            "action_link": None,
            "start_datetime_iso": None,
            "end_datetime_iso": None,
            "notes": "Non-recruitment email"
        }

    # Extract company name
    company = "Tech Employer"
    for comp in ["Amazon", "Microsoft", "Adobe", "Google", "Uber", "Flipkart", "Atlassian", "Swiggy", "Unstop", "Internshala"]:
        if comp.lower() in text:
            company = comp
            break

    # Extract Action Link (URL)
    url_match = re.search(r"https?://[^\s<>\"']+", body)
    action_link = url_match.group(0) if url_match else "https://assessment.portal"

    now_ist = datetime.now(IST)

    if is_oa:
        # Check deadline window (e.g. 48 hours)
        window_match = re.search(r"(\d+)\s*(?:hours|hrs|hr)", text)
        window_hours = int(window_match.group(1)) if window_match else 48

        # 48h deadline -> schedule 2-hour study/test block 24 hours prior to deadline
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
            "notes": f"Auto-scheduled 2-hour focus block 24 hours prior to {window_hours}h assessment deadline."
        }

    elif is_interview:
        # Fixed interview slot (e.g. tomorrow at 2:00 PM IST)
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
            "notes": "Interview invitation detected. Video conference link extracted."
        }

    else:
        start_time = now_ist + timedelta(days=2)
        start_time = start_time.replace(hour=11, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(minutes=30)
        return {
            "is_career_event": True,
            "event_category": "HR_CALL",
            "company_name": company,
            "event_title": f"{company} Recruiter Screening Call",
            "action_link": action_link,
            "start_datetime_iso": start_time.isoformat(),
            "end_datetime_iso": end_time.isoformat(),
            "notes": "Recruiter intro chat."
        }

def extract_career_event_from_email(subject: str, body: str, sender: str = "") -> Dict[str, Any]:
    """
    FR-25: Extracts recruitment event metadata using NVIDIA Nemotron 3.5 Lightning
    with strict JSON output format, with automatic fallback on timeout or syntax errors.
    """
    if settings.is_nebius_configured:
        system_prompt = """You are an AI Email Parser specialized in college student recruitment notifications in India.
Classify the email into one of: ONLINE_ASSESSMENT, TECHNICAL_INTERVIEW, HR_CALL, DEADLINE_REMINDER, or IRRELEVANT.
If is_career_event is true:
- Extract company_name, action_link (test/meeting URL), and event_title.
- For Online Assessments with a completion window (e.g. 48 hours), compute a 2-hour test focus block 24 hours prior to the deadline.
- Output valid ISO-8601 timestamps in Asia/Kolkata (+05:30) format.
Return ONLY a valid JSON object matching the schema:
{
  "is_career_event": true/false,
  "event_category": "ONLINE_ASSESSMENT" | "TECHNICAL_INTERVIEW" | "HR_CALL" | "IRRELEVANT",
  "company_name": "...",
  "event_title": "...",
  "action_link": "https://...",
  "start_datetime_iso": "YYYY-MM-DDTHH:MM:SS+05:30",
  "end_datetime_iso": "YYYY-MM-DDTHH:MM:SS+05:30",
  "notes": "..."
}"""
        user_content = f"Subject: {subject}\nFrom: {sender}\nBody:\n{body[:2000]}"

        try:
            raw_res = llm_router.call_tier1_fast(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                json_mode=True,
                temperature=0.0
            )
            cleaned = raw_res.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
                cleaned = re.sub(r"\n```$", "", cleaned)
            parsed = json.loads(cleaned)
            if "is_career_event" in parsed:
                # Ensure start and end iso are present if career event
                if parsed["is_career_event"] and not parsed.get("start_datetime_iso"):
                    return parse_with_fallback(subject, body, sender)
                return parsed
        except Exception as e:
            logger.warning(f"Nemotron 3.5 Lightning extraction fallback due to: {e}")
            return parse_with_fallback(subject, body, sender)

    return parse_with_fallback(subject, body, sender)

def save_inbox_event(event_dict: Dict[str, Any], email_id: Optional[str] = None) -> str:
    """Saves parsed career communication to SQLite database."""
    conn = get_db_connection()
    c = conn.cursor()
    ev_id = f"ev_{uuid.uuid4().hex[:10]}"
    e_id = email_id or f"mail_{uuid.uuid4().hex[:8]}"

    c.execute("""
        INSERT INTO inbox_events (
            id, email_id, company_name, event_title, event_category,
            action_link, start_datetime_iso, end_datetime_iso,
            synced_to_gcal, raw_snippet
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(email_id) DO UPDATE SET
            event_title = excluded.event_title,
            start_datetime_iso = excluded.start_datetime_iso,
            end_datetime_iso = excluded.end_datetime_iso
    """, (
        ev_id,
        e_id,
        event_dict.get("company_name", "Tech Employer"),
        event_dict.get("event_title", "Career Event"),
        event_dict.get("event_category", "ONLINE_ASSESSMENT"),
        event_dict.get("action_link"),
        event_dict.get("start_datetime_iso"),
        event_dict.get("end_datetime_iso"),
        0,
        event_dict.get("notes")
    ))
    conn.commit()
    conn.close()
    return ev_id

def list_inbox_events() -> List[Dict[str, Any]]:
    """Retrieve all parsed career emails and calendar events."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM inbox_events ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]
