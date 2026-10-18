import sqlite3
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from backend.config import settings

logger = logging.getLogger("careerclaw.database")

def get_db_connection() -> sqlite3.Connection:
    settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(settings.SQLITE_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

# Auto-ensure database schema on module load
_db_initialized = False

def ensure_db():
    global _db_initialized
    if not _db_initialized:
        init_db()
        _db_initialized = True

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Candidate Constraints & Profile
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_profile (
            id TEXT PRIMARY KEY,
            data_json TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. Discovered Opportunities
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS discovered_jobs (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            url TEXT UNIQUE,
            description TEXT,
            is_eligible BOOLEAN DEFAULT 0,
            match_score INTEGER DEFAULT 0,
            role_category TEXT,
            rejection_reason TEXT,
            raw_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 3. Applications & HITL Staging
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id TEXT PRIMARY KEY,
            job_id TEXT,
            company TEXT NOT NULL,
            role_title TEXT NOT NULL,
            portal_url TEXT NOT NULL,
            status TEXT NOT NULL, -- STAGED_FOR_APPROVAL, APPROVED_SUBMITTED, IMPROVEMENT_REQUESTED, REJECTED_BY_USER
            tailored_pdf_path TEXT,
            staged_screenshot_path TEXT,
            cached_dom_actions TEXT,
            improve_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 4. Inbox Recruiter Communications & Calendar Events
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inbox_events (
            id TEXT PRIMARY KEY,
            email_id TEXT UNIQUE,
            company_name TEXT NOT NULL,
            event_title TEXT NOT NULL,
            event_category TEXT NOT NULL, -- ONLINE_ASSESSMENT, TECHNICAL_INTERVIEW, HR_CALL
            action_link TEXT,
            start_datetime_iso TEXT,
            end_datetime_iso TEXT,
            gcal_event_link TEXT,
            synced_to_gcal BOOLEAN DEFAULT 0,
            raw_snippet TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {settings.SQLITE_DB_PATH}")

def save_candidate_constraints(profile_id: str, constraints_dict: Dict[str, Any]):
    ensure_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO candidate_profile (id, data_json, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            data_json = excluded.data_json,
            updated_at = CURRENT_TIMESTAMP
    """, (profile_id, json.dumps(constraints_dict)))
    conn.commit()
    conn.close()

def get_candidate_constraints(profile_id: str = "default_user") -> Optional[Dict[str, Any]]:
    ensure_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT data_json FROM candidate_profile WHERE id = ?", (profile_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row["data_json"])
    return None

def save_application(app_data: Dict[str, Any]):
    ensure_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO applications (
            id, job_id, company, role_title, portal_url, status,
            tailored_pdf_path, staged_screenshot_path, cached_dom_actions, improve_notes, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            status = excluded.status,
            tailored_pdf_path = COALESCE(excluded.tailored_pdf_path, applications.tailored_pdf_path),
            staged_screenshot_path = COALESCE(excluded.staged_screenshot_path, applications.staged_screenshot_path),
            cached_dom_actions = COALESCE(excluded.cached_dom_actions, applications.cached_dom_actions),
            improve_notes = COALESCE(excluded.improve_notes, applications.improve_notes),
            updated_at = CURRENT_TIMESTAMP
    """, (
        app_data["id"],
        app_data.get("job_id"),
        app_data.get("company", "Company"),
        app_data.get("role_title", "Role"),
        app_data.get("portal_url", ""),
        app_data.get("status", "STAGED_FOR_APPROVAL"),
        app_data.get("tailored_pdf_path"),
        app_data.get("staged_screenshot_path"),
        json.dumps(app_data.get("cached_dom_actions", {})) if isinstance(app_data.get("cached_dom_actions"), (dict, list)) else app_data.get("cached_dom_actions"),
        app_data.get("improve_notes"),
    ))
    conn.commit()
    conn.close()

def get_application(app_id: str) -> Optional[Dict[str, Any]]:
    ensure_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        d = dict(row)
        if d.get("cached_dom_actions"):
            try:
                d["cached_dom_actions"] = json.loads(d["cached_dom_actions"])
            except Exception:
                pass
        return d
    return None

def update_application_status(app_id: str, status: str, screenshot_path: Optional[str] = None, notes: Optional[str] = None):
    ensure_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    if screenshot_path and notes:
        cursor.execute("UPDATE applications SET status = ?, staged_screenshot_path = ?, improve_notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, screenshot_path, notes, app_id))
    elif screenshot_path:
        cursor.execute("UPDATE applications SET status = ?, staged_screenshot_path = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, screenshot_path, app_id))
    elif notes:
        cursor.execute("UPDATE applications SET status = ?, improve_notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, notes, app_id))
    else:
        cursor.execute("UPDATE applications SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, app_id))
    conn.commit()
    conn.close()

def list_applications(status: Optional[str] = None) -> List[Dict[str, Any]]:
    ensure_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute("SELECT * FROM applications WHERE status = ? ORDER BY updated_at DESC", (status,))
    else:
        cursor.execute("SELECT * FROM applications ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        if d.get("cached_dom_actions"):
            try:
                d["cached_dom_actions"] = json.loads(d["cached_dom_actions"])
            except Exception:
                pass
        result.append(d)
    return result

# Ensure DB on import
ensure_db()
