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

class CareerMemoryManager:
    def __init__(self):
        self.user_id = "default_user"
        self._mem0 = None
        self._qdrant_disabled = False
        self._init_memory_store()

    def _init_memory_store(self):
        if settings.is_nebius_configured and not self._qdrant_disabled:
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
                        }
                    },
                    "embedder": {
                        "provider": "openai",
                        "config": {
                            "model": settings.EMBEDDING_MODEL,
                            "api_key": settings.NEBIUS_API_KEY,
                            "openai_base_url": settings.NEBIUS_BASE_URL,
                            "embedding_dims": 4096,
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
        if any(w in t for w in ["intern", "experience", "work", "worked", "company", "role"]):
            return "INTERNSHIP"
        elif any(w in t for w in ["built", "developed", "project", "repo", "system", "engine", "agent", "created"]):
            return "PROJECT"
        elif any(w in t for w in ["reduced", "increased", "latency", "rps", "metrics", "%", "boosted", "optimized"]):
            return "METRIC"
        elif any(w in t for w in ["python", "pytorch", "fastapi", "react", "rust", "docker", "c++", "sql"]):
            return "SKILL"
        return "GENERAL"

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
        """Splits resume or document text into semantic bullet points and stores them."""
        # 1. Ingest full text into Mem0 in a single fast call (extracts all facts at once)
        if self._mem0 and not self._qdrant_disabled:
            try:
                self._mem0.add(text, user_id=user_id, metadata={"source": source_name})
            except Exception as e:
                logger.warning(f"Mem0 live store note: {e}. Using native semantic vault.")
                self._qdrant_disabled = True
                self._mem0 = None

        # 2. Extract lines for local atomic memory cards and semantic vault
        lines = [line.strip() for line in re.split(r"\n+|\u2022|\*", text) if len(line.strip()) > 15]
        ingested = []
        for line in lines:
            if re.match(r"^(page \d+|resume|curriculum vitae|phone|email)$", line.lower()):
                continue
            cat = self._classify_fact_category(line)
            mem_id = self._save_to_local_store(line, user_id, cat, source_name, {})
            ingested.append({"id": mem_id, "category": cat, "content": line, "memory": line})
            
        return ingested

memory_manager = CareerMemoryManager()
