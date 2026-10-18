import sqlite3
import json
import logging
import threading
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextlib import contextmanager
from backend.config import settings

logger = logging.getLogger("careerorbit.database")

# Global re-entrant lock to prevent concurrent SQLite write conflicts
DB_WRITE_LOCK = threading.RLock()

def get_raw_connection() -> sqlite3.Connection:
    """Creates a hardened SQLite connection with WAL mode and 30-second busy timeout."""
    settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(settings.SQLITE_DB_PATH), timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    return conn

def get_db_connection() -> sqlite3.Connection:
    return get_raw_connection()

@contextmanager
def db_transaction():
    """Thread-safe context manager for writing to SQLite without concurrency lock errors."""
    with DB_WRITE_LOCK:
        conn = get_raw_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

_db_initialized = False

def ensure_db():
    global _db_initialized
    if not _db_initialized:
        init_db()
        _db_initialized = True

def _safe_add_column(cursor: sqlite3.Cursor, table: str, col_def: str):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
    except sqlite3.OperationalError:
        pass # Column already exists

def init_db():
    with DB_WRITE_LOCK:
        conn = get_raw_connection()
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
                tailored_yaml TEXT,
                requirement_evidence_json TEXT,
                truthfulness_status TEXT DEFAULT 'VERIFIED',
                keyword_coverage_json TEXT,
                source_confidence TEXT DEFAULT 'HIGH',
                eligibility_state TEXT DEFAULT 'ELIGIBLE',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        _safe_add_column(cursor, "discovered_jobs", "tailored_yaml TEXT")
        _safe_add_column(cursor, "discovered_jobs", "requirement_evidence_json TEXT")
        _safe_add_column(cursor, "discovered_jobs", "truthfulness_status TEXT DEFAULT 'VERIFIED'")
        _safe_add_column(cursor, "discovered_jobs", "keyword_coverage_json TEXT")
        _safe_add_column(cursor, "discovered_jobs", "source_confidence TEXT DEFAULT 'HIGH'")
        _safe_add_column(cursor, "discovered_jobs", "eligibility_state TEXT DEFAULT 'ELIGIBLE'")

        # 3. Applications & HITL Staging
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id TEXT PRIMARY KEY,
                job_id TEXT,
                company TEXT NOT NULL,
                role_title TEXT NOT NULL,
                portal_url TEXT NOT NULL,
                status TEXT NOT NULL,
                tailored_pdf_path TEXT,
                staged_screenshot_path TEXT,
                cached_dom_actions TEXT,
                improve_notes TEXT,
                token_hash TEXT,
                approved_payload_hash TEXT,
                expires_at TIMESTAMP,
                consumed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        _safe_add_column(cursor, "applications", "token_hash TEXT")
        _safe_add_column(cursor, "applications", "approved_payload_hash TEXT")
        _safe_add_column(cursor, "applications", "expires_at TIMESTAMP")
        _safe_add_column(cursor, "applications", "consumed_at TIMESTAMP")

        # 4. Inbox Recruiter Communications & Calendar Events
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inbox_events (
                id TEXT PRIMARY KEY,
                email_id TEXT UNIQUE,
                company_name TEXT NOT NULL,
                event_title TEXT NOT NULL,
                event_category TEXT NOT NULL,
                action_link TEXT,
                start_datetime_iso TEXT,
                end_datetime_iso TEXT,
                gcal_event_link TEXT,
                synced_to_gcal BOOLEAN DEFAULT 0,
                sync_status TEXT DEFAULT 'SYNCED',
                raw_snippet TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        _safe_add_column(cursor, "inbox_events", "sync_status TEXT DEFAULT 'SYNCED'")

        # 5. Memory Document Registry (FR-004)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_records (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                file_size INTEGER DEFAULT 0,
                facts_extracted INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 6. Memory Conflicts (FR-008)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_conflicts (
                id TEXT PRIMARY KEY,
                field_name TEXT NOT NULL,
                existing_value TEXT NOT NULL,
                incoming_value TEXT NOT NULL,
                status TEXT DEFAULT 'PENDING',
                source_doc TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP
            )
        """)

        # 7. Nebius Model Telemetry (FR-042)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_telemetry (
                id TEXT PRIMARY KEY,
                model_id TEXT NOT NULL,
                task_type TEXT NOT NULL,
                latency_ms REAL NOT NULL,
                tokens_used INTEGER DEFAULT 0,
                validation_passed BOOLEAN DEFAULT 1,
                error_details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 8. Search Runs (FR-013)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_runs (
                id TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                sources_queried TEXT NOT NULL,
                jobs_discovered INTEGER DEFAULT 0,
                jobs_eligible INTEGER DEFAULT 0,
                duration_seconds REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
        logger.info(f"CareerOrbit Database initialized at {settings.SQLITE_DB_PATH}")

def save_candidate_constraints(profile_id: str, constraints_dict: Dict[str, Any]):
    ensure_db()
    with db_transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO candidate_profile (id, data_json, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                data_json = excluded.data_json,
                updated_at = CURRENT_TIMESTAMP
        """, (profile_id, json.dumps(constraints_dict)))

def get_candidate_constraints(profile_id: str = "default_user") -> Optional[Dict[str, Any]]:
    ensure_db()
    conn = get_raw_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT data_json FROM candidate_profile WHERE id = ?", (profile_id,))
        row = cursor.fetchone()
        if row:
            return json.loads(row["data_json"])
        return None
    finally:
        conn.close()

def save_application(app_data: Dict[str, Any]):
    ensure_db()
    with db_transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO applications (
                id, job_id, company, role_title, portal_url, status,
                tailored_pdf_path, staged_screenshot_path, cached_dom_actions, improve_notes,
                token_hash, approved_payload_hash, expires_at, consumed_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                status = excluded.status,
                tailored_pdf_path = COALESCE(excluded.tailored_pdf_path, applications.tailored_pdf_path),
                staged_screenshot_path = COALESCE(excluded.staged_screenshot_path, applications.staged_screenshot_path),
                cached_dom_actions = COALESCE(excluded.cached_dom_actions, applications.cached_dom_actions),
                improve_notes = COALESCE(excluded.improve_notes, applications.improve_notes),
                token_hash = COALESCE(excluded.token_hash, applications.token_hash),
                approved_payload_hash = COALESCE(excluded.approved_payload_hash, applications.approved_payload_hash),
                expires_at = COALESCE(excluded.expires_at, applications.expires_at),
                consumed_at = COALESCE(excluded.consumed_at, applications.consumed_at),
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
            app_data.get("token_hash"),
            app_data.get("approved_payload_hash"),
            app_data.get("expires_at"),
            app_data.get("consumed_at"),
        ))

def get_application(app_id: str) -> Optional[Dict[str, Any]]:
    ensure_db()
    conn = get_raw_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
        row = cursor.fetchone()
        if row:
            d = dict(row)
            if d.get("cached_dom_actions"):
                try:
                    d["cached_dom_actions"] = json.loads(d["cached_dom_actions"])
                except Exception:
                    pass
            return d
        return None
    finally:
        conn.close()

def update_application_status(
    app_id: str, 
    status: str, 
    screenshot_path: Optional[str] = None, 
    notes: Optional[str] = None,
    consumed_at: Optional[str] = None
):
    ensure_db()
    with db_transaction() as conn:
        cursor = conn.cursor()
        fields = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
        params = [status]
        if screenshot_path:
            fields.append("staged_screenshot_path = ?")
            params.append(screenshot_path)
        if notes:
            fields.append("improve_notes = ?")
            params.append(notes)
        if consumed_at:
            fields.append("consumed_at = ?")
            params.append(consumed_at)
        params.append(app_id)
        cursor.execute(f"UPDATE applications SET {', '.join(fields)} WHERE id = ?", tuple(params))

def list_applications(status: Optional[str] = None) -> List[Dict[str, Any]]:
    ensure_db()
    conn = get_raw_connection()
    try:
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM applications WHERE status = ? ORDER BY updated_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM applications ORDER BY updated_at DESC")
        rows = cursor.fetchall()
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
    finally:
        conn.close()

# Telemetry and Search Run helpers
def record_model_telemetry(
    model_id: str,
    task_type: str,
    latency_ms: float,
    tokens_used: int = 0,
    validation_passed: bool = True,
    error_details: Optional[str] = None
):
    ensure_db()
    import uuid
    with db_transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO model_telemetry (id, model_id, task_type, latency_ms, tokens_used, validation_passed, error_details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4())[:8], model_id, task_type, latency_ms, tokens_used, validation_passed, error_details))

def list_model_telemetry(limit: int = 20) -> List[Dict[str, Any]]:
    ensure_db()
    conn = get_raw_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM model_telemetry ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

def record_search_run(
    query: str,
    sources_queried: List[str],
    jobs_discovered: int,
    jobs_eligible: int,
    duration_seconds: float
):
    ensure_db()
    import uuid
    with db_transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO search_runs (id, query, sources_queried, jobs_discovered, jobs_eligible, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4())[:8], query, json.dumps(sources_queried), jobs_discovered, jobs_eligible, duration_seconds))

def list_search_runs(limit: int = 10) -> List[Dict[str, Any]]:
    ensure_db()
    conn = get_raw_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM search_runs ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        out = []
        for r in rows:
            d = dict(r)
            try:
                d["sources_queried"] = json.loads(d.get("sources_queried", "[]"))
            except Exception:
                pass
            out.append(d)
        return out
    finally:
        conn.close()

ensure_db()
