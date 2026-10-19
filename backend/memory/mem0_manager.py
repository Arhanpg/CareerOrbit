import os
# Disable Mem0 PostHog telemetry before any imports to prevent client collision warnings
os.environ["MEM0_TELEMETRY"] = "false"

import re
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from functools import lru_cache
from backend.config import settings
from backend.database import get_raw_connection, db_transaction

logger = logging.getLogger("careerorbit.mem0_manager")

def clean_extracted_pdf_text(text: str) -> str:
    """Strips LaTeX glyphs, control characters, fixes broken kerning, and normalizes line breaks."""
    if not text:
        return ""
    # Strip garbled/control characters & bullets
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\uf0b7\u2022\u25cf\u25cb\u25aa\u25ab]", " ", text)
    cleaned = cleaned.replace("&amp;", "&")

    # Fix LaTeX kerning splits
    kerning_replacements = [
        (r"GHOSAR\s*W\s*ADE", "GHOSARWADE"),
        (r"B\.?\s*T\s*ech", "B.Tech"),
        (r"F\s+ull-Stack", "Full-Stack"),
        (r"T\s+echnology", "Technology"),
        (r"UA\s+V", "UAV"),
        (r"CGP\s+A", "CGPA"),
        (r"F\s+AISS", "FAISS"),
        (r"W\s+ebSocket", "WebSocket"),
        (r"\bW\s+eb\b", "Web"),
        (r"\bT\s+ools\b", "Tools"),
        (r"\bT\s+rack\b", "Track"),
        (r"\bT\s+rue\b", "True"),
        (r"QLoR\s*A", "QLoRA"),
        (r"imple-\s*\n\s*mentation", "implementation"),
        (r"architec-\s*\n\s*ture", "architecture"),
    ]
    for pattern, rep in kerning_replacements:
        cleaned = re.sub(pattern, rep, cleaned, flags=re.IGNORECASE)

    return cleaned

class CareerMemoryManager:
    def __init__(self):
        self.user_id = "default_user"
        self._mem0 = None
        self._qdrant_disabled = False
        self._init_memory_store()

    def _init_memory_store(self):
        if settings.is_nebius_configured and not self._qdrant_disabled:
            # Fast probe to prevent blocking when Nebius embedding API is slow or unreachable
            try:
                import urllib.request
                req = urllib.request.Request(
                    settings.NEBIUS_BASE_URL,
                    headers={"User-Agent": "CareerOrbit/1.0"}
                )
                with urllib.request.urlopen(req, timeout=1.5):
                    pass
            except Exception as probe_err:
                # If cannot reach Nebius within 1.5s, fall back immediately to high-speed native vault
                logger.info(f"Nebius endpoint fast probe ({probe_err}); operating native semantic SQLite memory vault.")
                self._qdrant_disabled = True
                self._mem0 = None
                self._ensure_fallback_table()
                return

            try:
                from mem0 import Memory
                qdrant_path = str(settings.STORAGE_DIR / "qdrant_4096")
                Path(qdrant_path).mkdir(parents=True, exist_ok=True)
                
                nebius_mem0_config = {
                    "llm": {
                        "provider": "openai",
                        "config": {
                            "model": settings.TIER1_MODEL,
                            "temperature": 0.0,
                            "api_key": settings.NEBIUS_API_KEY,
                            "openai_base_url": settings.NEBIUS_BASE_URL,
                            "timeout": 4.0,
                            "max_retries": 0,
                        }
                    },
                    "embedder": {
                        "provider": "openai",
                        "config": {
                            "model": settings.EMBEDDING_MODEL,
                            "api_key": settings.NEBIUS_API_KEY,
                            "openai_base_url": settings.NEBIUS_BASE_URL,
                            "embedding_dims": 4096,
                            "timeout": 4.0,
                            "max_retries": 0,
                        }
                    },
                    "vector_store": {
                        "provider": "qdrant",
                        "config": {
                            "collection_name": "careerorbit_vault_v2_4096",
                            "path": qdrant_path,
                            "embedding_model_dims": 4096,
                        }
                    }
                }
                self._mem0 = Memory.from_config(nebius_mem0_config)
                logger.info("Initialized Mem0 with Nebius Token Factory and 4096-dim Qdrant store.")
            except Exception as e:
                logger.warning(f"Mem0 initialization: {e}. Running hybrid SQLite/Semantic memory vault.")
                self._mem0 = None
        else:
            self._ensure_fallback_table()

    def _ensure_fallback_table(self):
        with db_transaction() as conn:
            cursor = conn.cursor()
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

    def add_memory(self, content: str, user_id: str = "default_user", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add an atomic memory or conversation fact."""
        meta = metadata or {}
        category = meta.get("category", self._classify_fact_category(content))
        source = meta.get("source", "user_update")

        if self._mem0 and not self._qdrant_disabled:
            try:
                res = self._mem0.add(
                    content,
                    user_id=user_id,
                    metadata={"source": source, "category": category, **meta}
                )
                mem_id = self._save_to_local_store(content, user_id, category, source, meta)
                return {"status": "success", "engine": "mem0_nebius", "id": mem_id, "result": res}
            except Exception as e:
                # If Qdrant dimension conflict occurs, disable live Qdrant for this process without spamming logs
                logger.warning(f"Mem0 live store note: {e}. Using native semantic vault.")
                self._qdrant_disabled = True
                self._mem0 = None

        mem_id = self._save_to_local_store(content, user_id, category, source, meta)
        return {
            "status": "success",
            "engine": "local_semantic_vault",
            "id": mem_id,
            "category": category,
            "content": content
        }

    def chat_update(self, user_id: str, user_text: str) -> Dict[str, Any]:
        """Convenience method for conversational memory updates."""
        return self.add_memory(content=user_text, user_id=user_id, metadata={"source": "chat_update"})

    def _save_to_local_store(self, content: str, user_id: str, category: str, source: str, meta: dict) -> str:
        self._ensure_fallback_table()
        import uuid
        mem_id = f"mem_{uuid.uuid4().hex[:12]}"
        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO atomic_memories (id, user_id, content, category, source, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (mem_id, user_id, content, category, source, json.dumps(meta)))
        return mem_id

    def delete_memory_fact(self, fact_id: str) -> bool:
        """Removes a fact from active memory retrieval (FR-009)."""
        self._ensure_fallback_table()
        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM atomic_memories WHERE id = ?", (fact_id,))
            deleted = cursor.rowcount > 0
        return deleted

    def _classify_fact_category(self, text: str) -> str:
        t = text.lower()
        if any(w in t for w in ["research software developer", "batterytrust", "founder", "prasunethon", "intern", "experience", "worked", "faculty"]):
            return "INTERNSHIP"
        elif any(w in t for w in ["%", "mae", "189,569", "3,447", "8.69", "0.86", "1,162", "latency", "rps", "predictions/s"]):
            return "METRIC"
        elif any(w in t for w in ["b.tech", "cgpa", "degree", "education", "coursework", "iiit dharwad"]):
            return "EDUCATION"
        elif any(w in t for w in ["python", "pytorch", "fastapi", "react", "rust", "docker", "c++", "sql", "kotlin", "java", "langgraph", "bullmq"]):
            return "SKILL"
        return "PROJECT"

    def search_memory(self, query: str, user_id: str = "default_user", limit: int = 10) -> List[Dict[str, Any]]:
        """Search memory for relevant projects, skills, and metrics."""
        if self._mem0 and not self._qdrant_disabled:
            try:
                raw_results = self._mem0.search(query=query, filters={"user_id": user_id}, limit=limit)
                if isinstance(raw_results, dict) and "results" in raw_results:
                    raw_results = raw_results["results"]
                if raw_results and len(raw_results) > 0:
                    normalized = []
                    for item in raw_results:
                        if isinstance(item, dict):
                            c_val = item.get("content") or item.get("memory") or str(item)
                            normalized.append({
                                "id": str(item.get("id", "")),
                                "content": c_val,
                                "memory": c_val,
                                "score": item.get("score", 1.0)
                            })
                        elif isinstance(item, str):
                            normalized.append({
                                "id": "mem_0",
                                "content": item,
                                "memory": item,
                                "score": 1.0
                            })
                    if normalized:
                        return normalized
            except Exception as e:
                logger.warning(f"Mem0 search fallback: {e}")

        # Local semantic ranking search
        self._ensure_fallback_table()
        conn = get_raw_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, content, category, source, metadata_json FROM atomic_memories WHERE user_id = ?", (user_id,))
            rows = cursor.fetchall()
        finally:
            conn.close()

        query_tokens = set(re.findall(r"\w+", query.lower()))
        scored_memories = []

        for r in rows:
            content = r["content"]
            content_tokens = set(re.findall(r"\w+", content.lower()))
            overlap = len(query_tokens.intersection(content_tokens))
            
            score = overlap
            if "pytorch" in query.lower() or "machine learning" in query.lower() or "ai" in query.lower():
                if any(k in content.lower() for k in ["pytorch", "ml", "ai", "model", "rag", "vision", "cuda"]):
                    score += 5
            if "distributed" in query.lower() or "backend" in query.lower() or "api" in query.lower():
                if any(k in content.lower() for k in ["fastapi", "backend", "api", "distributed", "redis", "kv", "sql"]):
                    score += 5

            if score > 0 or len(query_tokens) == 0:
                scored_memories.append({
                    "id": r["id"],
                    "content": content,
                    "memory": content,
                    "category": r["category"],
                    "source": r["source"],
                    "score": score
                })

        scored_memories.sort(key=lambda x: x["score"], reverse=True)
        return scored_memories[:limit]

    def get_all_memories(self, user_id: str = "default_user") -> List[Dict[str, Any]]:
        """Retrieve all atomic memories for dashboard cards."""
        self._ensure_fallback_table()
        conn = get_raw_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, content, category, source, metadata_json, created_at 
                FROM atomic_memories 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            """, (user_id,))
            rows = cursor.fetchall()
            return [
                {
                    "id": r["id"],
                    "content": r["content"],
                    "memory": r["content"],
                    "category": r["category"],
                    "source": r["source"],
                    "metadata": json.loads(r["metadata_json"] or "{}"),
                    "created_at": r["created_at"]
                }
                for r in rows
            ]
        finally:
            conn.close()

    def extract_and_ingest_text(self, text: str, source_name: str, user_id: str = "default_user") -> List[Dict[str, Any]]:
        """Cleans, joins wrapped lines into complete sentences, and stores meaningful atomic facts."""
        cleaned_text = clean_extracted_pdf_text(text)

        # Ingest full cleaned text into Mem0 in a single fast call
        if self._mem0 and not self._qdrant_disabled:
            try:
                self._mem0.add(cleaned_text, user_id=user_id, metadata={"source": source_name})
            except Exception as e:
                logger.warning(f"Mem0 live store note: {e}. Using native semantic vault.")
                self._qdrant_disabled = True
                self._mem0 = None

        # Stitch wrapped PDF lines into full statements
        raw_lines = [l.strip() for l in cleaned_text.splitlines() if l.strip()]
        stitched_bullets: List[str] = []
        current_bullet = ""

        for line in raw_lines:
            # Skip noise lines: table of contents with 4+ dots, page numbers, generic headers
            if re.search(r"(\.\s*){4,}", line) or re.search(r"\.{4,}", line):
                continue
            if re.match(r"^(page \d+|resume|curriculum vitae|identity & education|technical skills|key projects|achievements & research|complete profile export|how you like to work|other work & plans)$", line.lower()):
                continue

            # If line starts with a dash or bullet, start a new bullet
            is_bullet_start = bool(re.match(r"^[-–—*•]\s+", line))
            clean_l = re.sub(r"^[-–—*•]\s+", "", line).strip()

            if is_bullet_start or not current_bullet:
                if current_bullet and len(current_bullet) >= 28:
                    stitched_bullets.append(current_bullet)
                current_bullet = clean_l
            else:
                # Check if previous line ended without sentence punctuation and this line continues it
                if not current_bullet.endswith((".", ";", ":", "!", "?", ")")) and (clean_l[0].islower() or clean_l.startswith(("and", "with", "using", "for", "in", "to", "across", "by"))):
                    current_bullet = f"{current_bullet} {clean_l}"
                else:
                    if len(current_bullet) >= 28:
                        stitched_bullets.append(current_bullet)
                    current_bullet = clean_l

        if current_bullet and len(current_bullet) >= 28:
            stitched_bullets.append(current_bullet)

        # Deduplicate facts by normalized content
        seen_hashes = set()
        ingested = []

        for bullet in stitched_bullets:
            norm_hash = re.sub(r"\W+", "", bullet.lower())
            if not norm_hash or norm_hash in seen_hashes:
                continue
            seen_hashes.add(norm_hash)

            cat = self._classify_fact_category(bullet)
            mem_id = self._save_to_local_store(bullet, user_id, cat, source_name, {})
            ingested.append({"id": mem_id, "category": cat, "content": bullet, "memory": bullet})

        return ingested

memory_manager = CareerMemoryManager()
