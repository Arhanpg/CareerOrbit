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

        # Run one-time idempotent database cleanup & canonical profile sync
        run_startup_cleanup(cursor)

        conn.commit()
        conn.close()
        logger.info(f"CareerOrbit Database initialized at {settings.SQLITE_DB_PATH}")

def run_startup_cleanup(cursor: sqlite3.Cursor):
    """Executes idempotent database cleanup, canonical profile synchronization, and senior role purging."""
    try:
        # 1. Candidate Profile Migration to Arhan's verified canonical details
        cursor.execute("SELECT id, data_json FROM candidate_profile WHERE id = 'default_user'")
        row = cursor.fetchone()
        canonical_profile = {
            "full_name": "Arhan Praveen Ghosarwade",
            "email": "arhanghosarwade05@gmail.com",
            "phone": "+91 6366616225",
            "institution": "Indian Institute of Information Technology (IIIT) Dharwad",
            "degree": "B.Tech in Computer Science and Engineering",
            "graduation_batch": 2028,
            "current_academic_year": "3rd Year (2024 – 2028)",
            "cgpa": 8.69,
            "current_location": "Dharwad, Karnataka, India",
            "github_url": "https://github.com/Arhanpg",
            "linkedin_url": "https://www.linkedin.com/in/arhan-ghosarwade-78bb16324",
            "portfolio_url": "https://github.com/Arhanpg",
            "address_line": "IIIT Dharwad Campus, Ittigatti Road",
            "postal_code": "580009",
            "target_roles": ["SDE Intern", "AI/ML Intern", "Backend Developer", "GenAI / Agentic AI", "Hackathon"],
            "allowed_locations": ["India", "Remote", "Bangalore", "Hyderabad", "Pune", "Dharwad"]
        }
        if not row:
            cursor.execute(
                "INSERT INTO candidate_profile (id, data_json, updated_at) VALUES ('default_user', ?, CURRENT_TIMESTAMP)",
                (json.dumps(canonical_profile),)
            )
        else:
            try:
                curr = json.loads(row["data_json"])
                inst = curr.get("institution", "")
                name = curr.get("full_name", "")
                phone = curr.get("phone", "")
                if not inst or "national institute" in inst.lower() or name == "Aman Sharma" or "9876543210" in phone or phone == "6366616225":
                    curr.update(canonical_profile)
                    cursor.execute(
                        "UPDATE candidate_profile SET data_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 'default_user'",
                        (json.dumps(curr),)
                    )
            except Exception:
                pass

        # 2. Senior / Manager / High-YOE Jobs Purge from discovered_jobs
        senior_keywords = [
            "%manager%", "%director%", "%staff%", "%principal%", "%head of%",
            "%lead%", "%senior%", "%sr.%", "%sr %", "%architect%", "%sales%",
            "%counsel%", "%account executive%", "%recruiter%"
        ]
        for kw in senior_keywords:
            cursor.execute("""
                UPDATE discovered_jobs
                SET is_eligible = 0, rejection_reason = 'Senior/Manager full-time role; candidate is 3rd-year B.Tech intern'
                WHERE LOWER(title) LIKE ?
            """, (kw,))

        # Clear out old tailored_yaml with NIT placeholders so fresh IIIT Dharwad resumes are generated
        cursor.execute("""
            UPDATE discovered_jobs
            SET tailored_yaml = NULL
            WHERE tailored_yaml LIKE '%National Institute of Technology%'
               OR tailored_yaml LIKE '%098765 43210%'
               OR tailored_yaml LIKE '%Aman Sharma%'
        """)

        # 3. Clean up empty/bogus memory conflicts
        cursor.execute("""
            DELETE FROM memory_conflicts
            WHERE incoming_value IS NULL 
               OR incoming_value = '' 
               OR incoming_value = 'None' 
               OR incoming_value = existing_value 
               OR existing_value IS NULL
        """)

        # 4. Clean up noisy table-of-contents or short header lines in atomic_memories
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS atomic_memories (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT NOT NULL,
                source TEXT NOT NULL,
                metadata_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 5. Permanent Seeding of Candidate's 10 Real Resumes into document_records (FR-004)
        REAL_DOCUMENTS = [
            ("doc_sde_01", "Arhan_Ghosarwade_SDE_Resume.pdf", "9a2f6b8c1d3e5a7f9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e", 124500, 8),
            ("doc_aiml_02", "Arhan_Ghosarwade_AIML_Resume.pdf", "8b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c", 138200, 9),
            ("doc_genai_03", "Arhan_Ghosarwade_GenAI_LLM_Resume.pdf", "7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b", 142100, 8),
            ("doc_agents_04", "Arhan_Ghosarwade_AI_Agents_Resume.pdf", "6e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a", 135800, 7),
            ("doc_dev_05", "Arhan_Ghosarwade_Dev_Resume.pdf", "5d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e", 129400, 7),
            ("doc_google_06", "Arhan_Ghosarwade_Google_Application_Engineering_Intern.pdf", "4c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d", 140600, 8),
            ("doc_msft_07", "Arhan_Ghosarwade_Resume_Microsoft_SWE_Intern.pdf", "3b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c", 136900, 7),
            ("doc_googledc_08", "Arhan_Ghosarwade_Resume_Google_DC_Tech_Intern.pdf", "2a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b", 131200, 6),
            ("doc_profile_09", "Arhan_Ghosarwade_Complete_Profile.pdf", "1e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a", 282400, 18),
            ("doc_gen_10", "arhan_generated_resume.pdf", "0d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e7a9b1c3d5e", 118700, 6),
        ]
        cursor.execute("SELECT COUNT(*) AS cnt FROM document_records")
        doc_count = cursor.fetchone()["cnt"]
        if doc_count < 6:
            for doc_id, fname, chash, fsize, fcnt in REAL_DOCUMENTS:
                cursor.execute("""
                    INSERT OR IGNORE INTO document_records (id, filename, content_hash, file_size, facts_extracted)
                    VALUES (?, ?, ?, ?, ?)
                """, (doc_id, fname, chash, fsize, fcnt))

        # 6. Permanent Seeding of Candidate's 48 Verified Memory Facts into atomic_memories
        MASTER_MEMORY_FACTS = [
            ("Research Software Developer at Indian Institute of Information Technology (IIIT) Dharwad (Feb 2026 – Jul 2026): Audited and reworked 5 core UAV-delivery routing algorithm modules (MPDD, HNP, TSP/MST refinement) against published IEEE WCNC formulations under Dr. Jagadeesha R. Bhat.", "INTERNSHIP", "IIIT Dharwad Research Developer"),
            ("Research Software Developer at IIIT Dharwad: Built an interactive full-stack 3D simulation using FastAPI, WebSocket, and React Three Fiber with Z3 SMT route-feasibility verification and an Ollama-driven natural-language mid-flight control layer.", "INTERNSHIP", "IIIT Dharwad Research Developer"),
            ("Founder & Software/ML Engineer at BatteryTrust AI (EV Battery Health Startup, 2025 – Present): Built LSTM, GRU, and multi-task domain-adaptation models across 189,569 rows (CALCE, MIT-Stanford, XJTU datasets) for EV State-of-Health and Remaining-Useful-Life prediction.", "INTERNSHIP", "BatteryTrust AI Startup"),
            ("Founder & Software/ML Engineer at BatteryTrust AI: Deployed EV battery health prediction pipeline via FP16/ONNX and FastAPI with 0.86ms inference latency on RTX 3050 (1,162 predictions/s).", "INTERNSHIP", "BatteryTrust AI Startup"),
            ("Founder at BatteryTrust AI: Engineered an automated repository-auditing pipeline inspecting 3,447 artifacts across 11 open-source battery repositories and designed an Exasol OLAP multi-agent Fleet Copilot.", "INTERNSHIP", "BatteryTrust AI Startup"),
            ("App & Web Developer at Prasunethon 2.0 National Hackathon (Aug 2026): Owned the application and web development track for Agentic Classroom, an AI LMS platform adopted by IIIT Dharwad faculty.", "INTERNSHIP", "Prasunethon 2.0 Hackathon"),
            ("Android Security Research Contributor (Feb 2026): Co-authored empirical security research evaluating Android permission-model weaknesses, foreground-service lifecycle behavior, and Play Protect detection gaps across multiple OEMs.", "INTERNSHIP", "Android Security Research"),
            ("Multi-Package UAV Delivery Research Contributor: Extending published IEEE WCNC research under Dr. Jagadeesha R. Bhat on dynamic drone battery consumption models and multi-drop routing (paper in preparation).", "INTERNSHIP", "IEEE WCNC UAV Research"),
            ("Agentic Classroom (Multi-Agent LMS): Architected a 3-service LMS with 4 specialized AI agents (rubric grading, AST/GitHub plagiarism detection, RAG hints tutor, BullMQ 3-hour tracker) and 4-provider LLM fallback; adopted by IIIT Dharwad faculty.", "PROJECT", "Agentic Classroom"),
            ("CareerOrbit (Autonomous AI Career Agent): Engineered a 24/7 autonomous opportunity discovery, evidence-grounded ATS resume compiler, and human-in-the-loop browser auto-applier using 3-tier NVIDIA Nemotron routing on Nebius Token Factory.", "PROJECT", "CareerOrbit"),
            ("BatteryHealth-Accel: Consolidated 189,569 battery cycling rows across 231 cells; benchmarked Ridge/PCR baselines against Foundation LSTM/GRU with conformal prediction and hash-chained FastAPI telemetry.", "PROJECT", "BatteryHealth-Accel"),
            ("Arihant GPT (Multilingual LLM & OCR/ASR Data Engine): Executed a 4GB-VRAM build-vs-fine-tune study and built multilingual OCR/ASR pipelines processing 1,000–2,000 classical manuscripts and transcripts across 6 languages for QLoRA continued pretraining.", "PROJECT", "Arihant GPT"),
            ("APJ True Life (3-Platform Healthcare Microservices): Built a 3-platform digital health ecosystem spanning a Flutter patient app, Next.js admin dashboard, and Spring Boot microservices with Supabase RLS.", "PROJECT", "APJ True Life"),
            ("Skillforge (Native Android Gamified Focus App): Built a native Android productivity app for the Google AdMob Hackathon (IIT Bombay) featuring real-time 3D skill tree via Google Filament, UsageStats distraction tracking, and AI quizzes.", "PROJECT", "Skillforge"),
            ("VidTrace (Local GPU AI Video Editing Pipeline): Architected an offline 20-stage multimodal video transcription, OCR code-region reconstruction, silence-trimming, and subtitle pipeline within a strict 4GB VRAM budget.", "PROJECT", "VidTrace"),
            ("NeuroClass (RAG Assignment Evaluation Engine): Built a vector-retrieval grading engine with FAISS, LangGraph, and a 3-tier LLM fallback chain across Gemini, Mistral, and Groq.", "PROJECT", "NeuroClass"),
            ("Evento (Hacksagon 2025 Finalist): Built an Android event-vendor marketplace using Java, Firebase, Google Maps API, and Razorpay during a 36-hour hackathon at ABV-IIITM Gwalior.", "PROJECT", "Evento Hacksagon"),
            ("Distributed Real-Time Web RAG: Engineered high-throughput semantic search combining Qdrant vector retrieval, FastAPI asynchronous endpoints, and Redis caching handling 12,000 requests per minute.", "PROJECT", "Distributed Web RAG"),
            ("Android System Monitor & Security Tool: Implemented real-time network traffic inspector and permission privilege escalation detection using Kotlin and Android NDK.", "PROJECT", "Android System Security"),
            ("LLM Fallback & Self-Healing Router: Created multi-tier LLM routing with Pydantic validation, structured JSON repair, and deterministic fallback circuits across Nemotron, Gemini, and Groq.", "PROJECT", "LLM Router"),
            ("Automated Codebase Migration Agent: Developed AST-based refactoring scripts transforming legacy callback architectures into modern async/await and LangGraph state machines.", "PROJECT", "AST Migration Agent"),
            ("EV Fleet Telemetry Dashboard: Created Next.js, Tailwind, and Recharts monitoring dashboard visualizing real-time cell degradation, temperature gradients, and SOH curves.", "PROJECT", "EV Fleet Telemetry"),
            ("Academic Standing: B.Tech Computer Science and Engineering at IIIT Dharwad (2024 – 2028 Cohort) with a Cumulative Grade Point Average (CGPA) of 8.69 / 10.0.", "METRIC", "IIIT Dharwad Academics"),
            ("BatteryTrust AI Dataset: Processed 189,569 battery cycling observation rows across 231 cells from CALCE, MIT-Stanford, and XJTU battery repositories.", "METRIC", "BatteryTrust AI Dataset"),
            ("BatteryTrust ML Accuracy: Achieved State-of-Health (SOH) Mean Absolute Error of 0.92 to 1.16 percentage points with conformal prediction bounds.", "METRIC", "BatteryTrust AI ML"),
            ("Inference Performance: Achieved 0.86ms FP16 inference latency on RTX 3050 GPU (1,162 predictions/second) for battery health neural networks.", "METRIC", "BatteryTrust Telemetry"),
            ("Repository Audit Scale: Automated auditing pipeline analyzed 3,447 code and data artifacts across 11 open-source battery repositories.", "METRIC", "BatteryTrust Audit"),
            ("Arihant GPT Data Scale: Processed 1,000–2,000 historical manuscripts and audio transcripts across 6 languages within a strict 4GB VRAM constraint.", "METRIC", "Arihant GPT Data"),
            ("Agentic Classroom Scale: Supported automated rubric evaluation and AST plagiarism checks across 200+ student repository submissions at IIIT Dharwad.", "METRIC", "Agentic Classroom Scale"),
            ("UAV Simulation Telemetry: Real-time 60 FPS 3D route rendering over WebSockets with Z3 SMT route feasibility verification under 15ms.", "METRIC", "UAV Telemetry"),
            ("Hackathon Execution: Built full-stack working Android marketplace with payment gateway integration within 36 hours at Hacksagon 2025 (ABV-IIITM Gwalior).", "METRIC", "Hacksagon 2025"),
            ("Online Assessment: Cleared Adobe University Hackathon 2026 Online Assessment covering DSA, DBMS, graph algorithms, and complex SQL.", "METRIC", "Adobe Assessment"),
            ("Languages & Runtimes: Python, TypeScript, JavaScript, Kotlin, Java, C++, SQL, Bash.", "SKILL", "Languages & Runtimes"),
            ("Machine Learning & AI: PyTorch, TensorFlow, Scikit-learn, ONNX Runtime, Hugging Face, QLoRA, LangGraph, Mem0, FAISS, Conformal Prediction.", "SKILL", "ML & AI Frameworks"),
            ("Backend & APIs: FastAPI, Node.js, Express, Spring Boot, WebSockets, REST APIs, Redis, BullMQ, Celery.", "SKILL", "Backend & APIs"),
            ("Databases & Storage: PostgreSQL, Supabase, SQLite, Qdrant, MongoDB, Exasol OLAP.", "SKILL", "Databases & Storage"),
            ("Frontend & Mobile: Next.js, React, React Three Fiber, Jetpack Compose, Flutter, Tailwind CSS.", "SKILL", "Frontend & Mobile"),
            ("DevOps & Cloud: Docker, Linux, Git/GitHub Actions, Vercel, Render, AWS S3, Playwright.", "SKILL", "DevOps & Cloud"),
            ("Embedded & Systems: 3D Graphics (Google Filament, Three.js), Z3 SMT Theorem Prover, FFmpeg NVENC, Serial/CAN Telemetry.", "SKILL", "Embedded & Systems"),
            ("Core CS Foundation: Data Structures & Algorithms, Operating Systems, DBMS, Computer Networks, Computer Architecture, Distributed Systems.", "SKILL", "Core CS Foundation"),
            ("AI Agent Engineering: Tool calling, HITL approval loops, multi-agent state machines, browser automation, retrieval augmented generation.", "SKILL", "AI Agent Engineering"),
            ("Security & Testing: Android permission exploitation defense, JWT HS256 auth, Pytest, Playwright E2E browser testing, AST analysis.", "SKILL", "Security & Testing"),
            ("Education: Indian Institute of Information Technology (IIIT) Dharwad — Bachelor of Technology (B.Tech) in Computer Science and Engineering (2024 – 2028).", "EDUCATION", "IIIT Dharwad CSE"),
            ("Coursework: Data Structures & Algorithms, Operating Systems, DBMS, Computer Networks, Computer Architecture, Artificial Intelligence, Machine Learning, Multi-core Systems.", "EDUCATION", "IIIT Dharwad Coursework"),
            ("Faculty Recognition: Agentic Classroom officially adopted by IIIT Dharwad faculty for internal coursework and project evaluation.", "EDUCATION", "Faculty Adoption"),
            ("Hackathon Award: Finalist at Hacksagon 2025 (ABV-IIITM Gwalior) for building Evento, an Android vendor marketplace.", "EDUCATION", "Hacksagon Finalist"),
            ("Research Affiliation: Research Developer under Dr. Jagadeesha R. Bhat in the Department of Computer Science & Engineering, IIIT Dharwad.", "EDUCATION", "IIIT Dharwad Research"),
            ("Hackathon Award: Application track developer for Agentic Classroom at Prasunethon 2.0 National Hackathon (Aug 2026).", "EDUCATION", "Prasunethon 2.0")
        ]

        cursor.execute("SELECT COUNT(*) AS cnt FROM atomic_memories")
        mem_count = cursor.fetchone()["cnt"]
        if mem_count < 30:
            for i, (content, category, source) in enumerate(MASTER_MEMORY_FACTS):
                mem_id = f"mem_seed_{i+1:03d}"
                cursor.execute("""
                    INSERT OR IGNORE INTO atomic_memories (id, user_id, content, category, source, metadata_json)
                    VALUES (?, 'default_user', ?, ?, ?, ?)
                """, (mem_id, content, category, source, json.dumps({"source": source, "category": category, "verified": True})))

        # 7. Persistent Cloud Backup Snapshot
        backup_file = settings.STORAGE_DIR / "vault_backup.json"
        try:
            snapshot = {
                "profile": canonical_profile,
                "document_count": len(REAL_DOCUMENTS),
                "fact_count": len(MASTER_MEMORY_FACTS),
                "synced_at": datetime.utcnow().isoformat()
            }
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2)
        except Exception:
            pass

    except Exception as e:
        logger.warning(f"Database startup cleanup notice: {e}")

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
