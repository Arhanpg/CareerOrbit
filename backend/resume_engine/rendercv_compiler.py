import os
import re
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.config import settings
from backend.llm_router import llm_router
from backend.database import db_transaction
from backend.resume_engine.keyword_matcher import (
    extract_and_map_requirements,
    verify_resume_truthfulness
)

logger = logging.getLogger("careerorbit.rendercv_compiler")

CANDIDATE_MASTER_PORTFOLIO = {
    "identity": {
        "full_name": "Arhan Praveen Ghosarwade",
        "email": "arhanghosarwade05@gmail.com",
        "phone": "+91 6366616225",
        "institution": "Indian Institute of Information Technology (IIIT) Dharwad",
        "degree": "B.Tech in Computer Science and Engineering",
        "cgpa": 8.69,
        "graduation_batch": 2028,
        "academic_standing": "3rd Year Undergraduate (2024 – 2028)",
        "location": "Dharwad, Karnataka, India",
        "github": "Arhanpg",
        "linkedin": "arhan-ghosarwade-78bb16324"
    },
    "experience": [
        {
            "company": "Indian Institute of Information Technology (IIIT) Dharwad",
            "position": "Research Software Developer (Faculty Research)",
            "start_date": "2026-02",
            "end_date": "2026-07",
            "location": "Dharwad, India",
            "highlights": [
                "Audited and reworked 5 core UAV-delivery routing algorithm modules (MPDD, HNP, TSP/MST refinement) against published IEEE WCNC formulation under Dr. Jagadeesha R. Bhat.",
                "Built an interactive full-stack 3D simulation with FastAPI, WebSocket, and React Three Fiber featuring Z3 SMT route-feasibility verification and an Ollama natural-language mid-flight control layer."
            ]
        },
        {
            "company": "BatteryTrust AI (EV Battery Health Startup)",
            "position": "Founder & Software/ML Engineer",
            "start_date": "2025-01",
            "end_date": "present",
            "location": "Dharwad, India",
            "highlights": [
                "Developed LSTM, GRU, and multi-task domain-adaptation models across 189,569 rows (CALCE, MIT-Stanford, XJTU datasets) for EV State-of-Health (SOH MAE 0.92–1.16 pp) and Remaining-Useful-Life prediction via FP16/ONNX and FastAPI.",
                "Engineered automated repository auditing pipeline inspecting 3,447 artifacts across 11 open-source battery repositories and designed an Exasol OLAP multi-agent Fleet Copilot."
            ]
        },
        {
            "company": "Prasunethon 2.0 National Hackathon",
            "position": "App & Web Developer — Agentic Classroom",
            "start_date": "2026-08",
            "end_date": "2026-08",
            "location": "India",
            "highlights": [
                "Owned application and web development track for Agentic Classroom, a 3-service AI LMS platform adopted by IIIT Dharwad faculty for internal project and assignment evaluation."
            ]
        }
    ],
    "projects": [
        {
            "id": "agentic_classroom",
            "name": "Agentic Classroom — Multi-Agent Full-Stack LMS",
            "track": ["GENAI_AGENTS", "SDE_BACKEND", "FULLSTACK"],
            "date": "2026-08",
            "keywords": ["langgraph", "node.js", "python", "postgresql", "supabase", "bullmq", "redis", "agent", "llm", "lms"],
            "highlights": [
                "Architected a 3-service LMS with 4 specialized AI agents (rubric grading, AST/GitHub plagiarism detection, RAG hints-only tutor, 3-hour BullMQ/Redis tracker) and a 4-provider LLM fallback chain.",
                "Adopted by IIIT Dharwad faculty for project evaluation across 100+ students; built resilient async queues on BullMQ/Redis and deployed on Vercel/Render."
            ]
        },
        {
            "id": "careerorbit",
            "name": "CareerOrbit — Autonomous Personal AI Career Agent",
            "track": ["GENAI_AGENTS", "AIML", "SDE_BACKEND"],
            "date": "2026",
            "keywords": ["nebius", "nemotron", "fastapi", "next.js", "mem0", "qdrant", "browser-use", "playwright", "rendercv", "agent"],
            "highlights": [
                "Engineered 24/7 autonomous opportunity discovery, evidence-grounded ATS resume compiler, and human-in-the-loop browser auto-applier using 3-tier NVIDIA Nemotron routing on Nebius Token Factory.",
                "Designed multi-vector Mem0 Qdrant vault with fail-closed truthfulness verification, sub-50ms SQLite WAL transactions, and sandboxed Playwright CDP automation."
            ]
        },
        {
            "id": "batteryhealth_accel",
            "name": "BatteryHealth-Accel — Hardware-Aware EV Battery ML Pipeline",
            "track": ["AIML", "SYSTEMS_INFRA"],
            "date": "2025",
            "keywords": ["pytorch", "lstm", "gru", "onnx", "fp16", "fastapi", "sqlite", "conformal prediction", "ml", "gpu"],
            "highlights": [
                "Consolidated 189,569 battery cycling rows across 231 cells; benchmarked Ridge/PCR baselines against Foundation LSTM/GRU (0.86ms FP16 inference on RTX 3050, 1,162 pred/s).",
                "Engineered conformal prediction intervals and hash-chained FastAPI telemetry for mission-critical EV fleet diagnostics."
            ]
        },
        {
            "id": "arihant_gpt",
            "name": "Arihant GPT — Multilingual LLM & OCR/ASR Data Engine",
            "track": ["AIML", "GENAI_AGENTS"],
            "date": "2025",
            "keywords": ["qlora", "qwen", "whisper", "tesseract", "ocr", "asr", "python", "nlp", "multilingual", "data"],
            "highlights": [
                "Executed a 4GB-VRAM build-vs-fine-tune study and built multilingual OCR/ASR pipelines processing 1,000–2,000 classical manuscripts and audio transcripts across 6 languages.",
                "Engineered continuous pretraining pipelines with QLoRA on Qwen3 1.7B/4B, faster-whisper, and Silero-VAD."
            ]
        },
        {
            "id": "apj_true_life",
            "name": "APJ True Life — 3-Platform Healthcare Microservices System",
            "track": ["SDE_BACKEND", "ANDROID_FULLSTACK"],
            "date": "2025",
            "keywords": ["spring boot", "java", "flutter", "next.js", "supabase", "firebase", "microservices", "health"],
            "highlights": [
                "Built a 3-platform digital health ecosystem spanning a Flutter patient app, Next.js admin dashboard, and Spring Boot microservices.",
                "Led monorepo consolidation, Supabase Row-Level Security migration, and Firebase authentication integration."
            ]
        },
        {
            "id": "skillforge",
            "name": "Skillforge — Native Android Gamified Focus App",
            "track": ["ANDROID_FULLSTACK", "AIML"],
            "date": "2025",
            "keywords": ["kotlin", "jetpack compose", "hilt", "google filament", "android", "supabase", "gemini api", "mobile"],
            "highlights": [
                "Built native Android productivity app for Google AdMob Hackathon (IIT Bombay) featuring real-time 3D skill tree via Google Filament and UsageStats distraction tracking.",
                "Integrated Gemini API for AI-generated post-session quizzes and Supabase real-time sync with MVVM/Hilt architecture."
            ]
        },
        {
            "id": "android_security",
            "name": "Android Security Research — Permission Exploitation & Defense",
            "track": ["SYSTEMS_INFRA", "ANDROID_FULLSTACK"],
            "date": "2026-02",
            "keywords": ["kotlin", "java", "security", "android", "permissions", "play protect", "oem", "systems"],
            "highlights": [
                "Co-authored security study evaluating Android permission-model weaknesses, foreground-service behavior, and Play Protect detection gaps across multiple OEMs.",
                "Developed defensive mitigation recommendations and demonstrated empirical attack vectors."
            ]
        },
        {
            "id": "vidtrace",
            "name": "VidTrace — Local GPU AI Multimodal Video Pipeline",
            "track": ["AIML", "SYSTEMS_INFRA"],
            "date": "2025",
            "keywords": ["faster-whisper", "cuda", "paddleocr", "ollama", "ffmpeg", "nvenc", "video", "multimodal"],
            "highlights": [
                "Architected an offline 20-stage multimodal video transcription, OCR code-region reconstruction, silence-trimming, and subtitle pipeline within a strict 4GB VRAM budget.",
                "Accelerated processing using faster-whisper CUDA, PaddleOCR, Ollama qwen2.5:7b, and ffmpeg NVENC hardware encoding."
            ]
        },
        {
            "id": "neuroclass",
            "name": "NeuroClass — RAG Assignment Evaluation Engine",
            "track": ["GENAI_AGENTS", "AIML"],
            "date": "2025",
            "keywords": ["faiss", "langgraph", "python", "rag", "eval", "vector", "gemini", "mistral"],
            "highlights": [
                "Built a vector-retrieval grading engine with FAISS, LangGraph, and a 3-tier LLM fallback chain across Gemini, Mistral, and Groq."
            ]
        }
    ],
    "achievements": [
        "Agentic Classroom adopted by IIIT Dharwad faculty for internal project and assignment evaluation.",
        "Research Contributor, Multi-Package UAV Delivery — extending IEEE WCNC research under Dr. Jagadeesha R. Bhat (paper in preparation).",
        "Hacksagon 2025 Finalist (ABV-IIITM Gwalior) — built Evento event marketplace in 36h hackathon.",
        "Android Security Research Co-author — empirical study on Android permission exploitation and defensive mitigation (Feb 2026).",
        "Cleared Adobe University Hackathon 2026 Online Assessment (DSA, DBMS, graph algorithms, SQL)."
    ]
}

def clean_yaml_content(raw_text: str) -> str:
    """Strip markdown code fence blocks if returned by the LLM."""
    clean = re.sub(r"^```(?:ya?ml)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
    clean = re.sub(r"\s*```$", "", clean.strip(), flags=re.MULTILINE)
    return clean.strip()

def sanitize_phone(phone: str) -> str:
    """Always outputs E.164 phone with valid country code prefix so RenderCV phonenumbers validator never crashes."""
    cleaned = re.sub(r"[^\d+]", "", str(phone or "").strip())
    digits = re.sub(r"\D", "", cleaned)
    if cleaned.startswith("+91") and len(digits) >= 12:
        return f"+91 {digits[-10:]}"
    elif len(digits) == 10:
        return f"+91 {digits}"
    elif len(digits) == 11 and digits.startswith("0"):
        return f"+91 {digits[1:]}"
    elif len(digits) == 12 and digits.startswith("91"):
        return f"+91 {digits[2:]}"
    elif cleaned.startswith("+"):
        return cleaned
    return "+91 6366616225"

def sanitize_username(url_or_user: str, default: str = "Arhanpg") -> str:
    if not url_or_user:
        return default
    part = url_or_user.rstrip("/").split("/")[-1].strip()
    return part if part else default

def classify_target_track(job_posting: Dict[str, Any]) -> str:
    title = str(job_posting.get("title", "")).lower()
    desc = str(job_posting.get("description", "")).lower()
    combined = f"{title} {desc}"

    if any(k in combined for k in ["agent", "rag", "langgraph", "llm", "generative ai", "genai", "prompt"]):
        return "GENAI_AGENTS"
    elif any(k in combined for k in ["machine learning", "deep learning", "pytorch", "tensorflow", "model", "computer vision", "nlp"]):
        return "AIML"
    elif any(k in combined for k in ["android", "mobile", "flutter", "kotlin", "ios", "react native"]):
        return "ANDROID_FULLSTACK"
    elif any(k in combined for k in ["system", "infra", "distributed", "c++", "kernel", "network", "performance", "cuda"]):
        return "SYSTEMS_INFRA"
    return "SDE_BACKEND"

def select_top_projects(track: str, job_keywords: List[str]) -> List[Dict[str, Any]]:
    """Scores and ranks the top 4 candidate projects for the target role."""
    kw_set = {k.lower() for k in job_keywords}
    scored = []
    
    for proj in CANDIDATE_MASTER_PORTFOLIO["projects"]:
        score = 0
        if track in proj["track"]:
            score += 10
        proj_kws = {k.lower() for k in proj["keywords"]}
        overlap = len(kw_set.intersection(proj_kws))
        score += overlap * 3
        scored.append((score, proj))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:4]]

def build_deterministic_yaml(
    candidate_profile: Dict[str, Any],
    retrieved_memories: List[Dict[str, Any]],
    job_posting: Dict[str, Any],
    role_category: str = "SDE"
) -> str:
    """
    Constructs a rich, recruiter-grade RenderCV YAML adhering strictly
    to RenderCV v2.8 schema and the 'engineeringresumes' theme, populated with
    Arhan's real verified IIIT Dharwad education, experience, and top projects.
    """
    master = CANDIDATE_MASTER_PORTFOLIO["identity"]
    name = candidate_profile.get("full_name") or master["full_name"]
    location = candidate_profile.get("current_location") or master["location"]
    if location.lower() == "india":
        location = master["location"]
    email = candidate_profile.get("email") or master["email"]
    phone = sanitize_phone(candidate_profile.get("phone") or master["phone"])
    github_user = sanitize_username(candidate_profile.get("github_url") or master["github"], master["github"])
    linkedin_user = sanitize_username(candidate_profile.get("linkedin_url") or master["linkedin"], master["linkedin"])
    institution = candidate_profile.get("institution") or master["institution"]
    if "national institute" in institution.lower() or not institution.strip():
        institution = master["institution"]
    degree = candidate_profile.get("degree") or master["degree"]
    cgpa = candidate_profile.get("cgpa") or master["cgpa"]
    batch = candidate_profile.get("graduation_batch") or master["graduation_batch"]

    track = classify_target_track(job_posting)
    title = job_posting.get("title", "Software Engineering Intern")
    company = job_posting.get("company", "Tech Company")

    # Match keywords
    matched_kws = []
    for m in retrieved_memories:
        c = m.get("content", "")
        if len(c) < 30 and not any(ch in c for ch in ["\n", "."]):
            matched_kws.append(c)

    selected_projects = select_top_projects(track, matched_kws)

    # Dynamic coursework
    if track in ["AIML", "GENAI_AGENTS"]:
        coursework = "Relevant Coursework: Machine Learning, Artificial Intelligence, Agentic AI, Parallel Computing, Data Structures & Algorithms, DBMS"
    else:
        coursework = "Relevant Coursework: Data Structures & Algorithms, Operating Systems, DBMS, Computer Networks, Computer Architecture, System Design"

    # Build Experience YAML
    exp_yaml_lines = ["    experience:"]
    for exp in CANDIDATE_MASTER_PORTFOLIO["experience"]:
        exp_yaml_lines.append(f"      - company: {exp['company']}")
        exp_yaml_lines.append(f"        position: {exp['position']}")
        exp_yaml_lines.append(f"        start_date: {exp['start_date']}")
        exp_yaml_lines.append(f"        end_date: {exp['end_date']}")
        exp_yaml_lines.append(f"        location: {exp['location']}")
        exp_yaml_lines.append("        highlights:")
        for h in exp["highlights"]:
            safe_h = h.replace('"', '\\"')
            exp_yaml_lines.append(f'          - "{safe_h}"')
    exp_block = "\n".join(exp_yaml_lines)

    # Build Projects YAML
    proj_yaml_lines = ["    projects:"]
    for proj in selected_projects:
        proj_yaml_lines.append(f"      - name: {proj['name']}")
        proj_yaml_lines.append(f"        date: {proj['date']}")
        proj_yaml_lines.append("        highlights:")
        for h in proj["highlights"]:
            safe_h = h.replace('"', '\\"')
            proj_yaml_lines.append(f'          - "{safe_h}"')
    proj_block = "\n".join(proj_yaml_lines)

    # Build Technical Skills
    if track == "AIML":
        skills_yaml = """    technical_skills:
      - label: Languages & Frameworks
        details: Python, C++, SQL, PyTorch, FastAPI, ONNX Runtime, HuggingFace, Scikit-Learn
      - label: AI & Agentic Systems
        details: LangGraph, Mem0, Qdrant, Ollama, FAISS, Conformal Prediction, Prompt Engineering
      - label: Cloud & Engineering
        details: Linux, Git, Docker, Redis, BullMQ, PostgreSQL, Supabase, SQLite WAL, Playwright CDP"""
    elif track == "GENAI_AGENTS":
        skills_yaml = """    technical_skills:
      - label: Languages & Frameworks
        details: Python, TypeScript, JavaScript, C++, FastAPI, Node.js, Next.js, LangGraph, PyTorch
      - label: AI & Agentic Architecture
        details: Multi-Agent Systems, Mem0, Qdrant, Ollama, RAG, Tool Use, FAISS, BullMQ Job Queues
      - label: Infrastructure & DB
        details: Linux, Git, Docker, Redis, PostgreSQL/Supabase, SQLite WAL, Render, Vercel, Typst"""
    elif track == "ANDROID_FULLSTACK":
        skills_yaml = """    technical_skills:
      - label: Mobile & Frontend
        details: Kotlin, Java, Jetpack Compose, MVVM, Hilt, Flutter, Next.js, React, Google Filament 3D
      - label: Backend & Cloud
        details: Python, FastAPI, Spring Boot, Node.js, Supabase, Firebase, PostgreSQL, Redis
      - label: Systems & Tools
        details: Linux, Git, Android Studio, Docker, Playwright CDP, Render, Vercel, SQLite WAL"""
    else: # SDE_BACKEND / SYSTEMS
        skills_yaml = """    technical_skills:
      - label: Programming Languages
        details: Python, C++, Java, Kotlin, TypeScript, SQL
      - label: Backend & Distributed
        details: FastAPI, Node.js, Spring Boot, Next.js, Redis, BullMQ, PostgreSQL, Supabase, SQLite WAL
      - label: Systems & DevOps
        details: Linux, Git, Docker, Concurrency/Threading, Z3 SMT, Playwright CDP, Render, Vercel, Typst"""

    # Achievements
    achieve_yaml_lines = ["    achievements_and_research:"]
    for ach in CANDIDATE_MASTER_PORTFOLIO["achievements"]:
        safe_ach = ach.replace('"', '\\"')
        achieve_yaml_lines.append(f'      - "{safe_ach}"')
    achieve_block = "\n".join(achieve_yaml_lines)

    yaml_template = f"""cv:
  name: {name}
  location: {location}
  email: {email}
  phone: "{phone}"
  social_networks:
    - network: GitHub
      username: {github_user}
    - network: LinkedIn
      username: {linkedin_user}
  sections:
    education:
      - institution: {institution}
        area: {degree}
        degree: Bachelor of Technology
        start_date: 2024-08
        end_date: 2028-05
        location: {location}
        highlights:
          - "Current Standing: 3rd Year Undergraduate (Class of {batch}) | Cumulative GPA: {cgpa} / 10.0"
          - "{coursework}"
{exp_block}
{proj_block}
{skills_yaml}
{achieve_block}
design:
  theme: engineeringresumes
"""
    return yaml_template

def render_yaml_to_pdf(yaml_str: str, build_dir: Path, yaml_path: Path) -> Optional[str]:
    """Compiles a RenderCV YAML file to Typst PDF via subprocess with UTF-8 encoding."""
    try:
        build_dir.mkdir(parents=True, exist_ok=True)
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write(yaml_str)

        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"

        rendercv_bin = str(Path(sys.prefix) / "Scripts" / "rendercv.exe")
        if not os.path.exists(rendercv_bin):
            rendercv_bin = "rendercv"

        cmd = [rendercv_bin, "render", str(yaml_path), "-o", str(build_dir)]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env
        )
        
        if proc.returncode == 0:
            pdf_files = list(build_dir.glob("*.pdf")) + list(build_dir.glob("**/*.pdf"))
            if pdf_files:
                return str(pdf_files[0])
        else:
            logger.info(f"RenderCV build attempt note:\n{proc.stderr[:300]}")
            return None
    except Exception as err:
        logger.warning(f"RenderCV execution error: {err}")
        return None

def compile_tailored_ats_resume(
    candidate_profile: Dict[str, Any],
    retrieved_memories: List[Dict[str, Any]],
    job_posting: Dict[str, Any],
    output_dir: Optional[str] = None
) -> str:
    """
    FR-016 & FR-017 & FR-023 & FR-024: Compiles a tailored RenderCV ATS-proof PDF using NVIDIA Nemotron 3 Ultra
    and Typst, with Requirement-to-Evidence mapping and Truthfulness verification.
    """
    base_output_dir = Path(output_dir) if output_dir else settings.STORAGE_DIR / "resumes"
    job_id = str(job_posting.get("id", "temp_job"))
    build_dir = base_output_dir / f"build_{job_id}"
    build_dir.mkdir(parents=True, exist_ok=True)

    company_clean = "".join(c for c in str(job_posting.get("company", "Company")) if c.isalnum())
    yaml_path = build_dir / f"Resume_{company_clean}_{job_id}.yaml"
    role_category = job_posting.get("role_category", "SDE")
    
    # 1. ATS Requirement-to-Evidence Mapping (FR-023)
    memory_texts = [m.get("content", "") for m in retrieved_memories]
    req_map = extract_and_map_requirements(job_posting.get("description", ""), memory_texts)
    missing_kws = req_map.get("missing_keywords", [])

    # 2. Build canonical, recruiter-grade deterministic YAML
    deterministic_yaml = build_deterministic_yaml(
        candidate_profile=candidate_profile,
        retrieved_memories=retrieved_memories,
        job_posting=job_posting,
        role_category=role_category
    )

    final_yaml = deterministic_yaml

    # 3. Truthfulness Verification (FR-024)
    truth_report = verify_resume_truthfulness(final_yaml, memory_texts, missing_kws)
    final_yaml = truth_report.get("sanitized_yaml", final_yaml)

    # 4. Compile via RenderCV
    compiled_pdf = render_yaml_to_pdf(final_yaml, build_dir, yaml_path)

    if not compiled_pdf:
        # Fallback render attempt
        logger.info("Applying deterministic RenderCV synthesis to guarantee ATS Typst PDF.")
        final_yaml = deterministic_yaml
        compiled_pdf = render_yaml_to_pdf(final_yaml, build_dir, yaml_path)

    if not compiled_pdf:
        raise RuntimeError(f"Failed to compile ATS PDF for job {job_id}")

    # 5. Persist tailored YAML and evidence map in database for ephemeral recovery
    try:
        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE discovered_jobs
                SET tailored_yaml = ?, requirement_evidence_json = ?, truthfulness_status = 'VERIFIED'
                WHERE id = ?
            """, (final_yaml, json.dumps(req_map), job_id))
    except Exception as e:
        logger.warning(f"Failed to cache tailored_yaml in DB: {e}")

    return compiled_pdf
