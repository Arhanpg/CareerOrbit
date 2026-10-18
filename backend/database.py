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

# Ensure DB on import
ensure_db()
