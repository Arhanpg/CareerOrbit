import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from backend.config import settings
from backend.database import get_db_connection

logger = logging.getLogger("careerclaw.mem0_manager")

class CareerMemoryManager:
    def __init__(self):
        self.user_id = "default_user"
        self._mem0 = None
        self._init_memory_store()

    def _init_memory_store(self):
        if settings.is_nebius_configured:
            try:
                from mem0 import Memory
                qdrant_path = str(settings.STORAGE_DIR / "qdrant_db")
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
                            "collection_name": "student_career_vault",
                            "path": qdrant_path,
                        }
                    }
                }
                self._mem0 = Memory.from_config(nebius_mem0_config)
                logger.info("Initialized Mem0 with Nebius Token Factory and local Qdrant.")
            except Exception as e:
                logger.warning(f"Failed to initialize live Mem0 with Nebius: {e}. Falling back to local vault store.")
                self._mem0 = None
        else:
            logger.info("NEBIUS_API_KEY not set. Running hybrid SQLite/Semantic memory vault.")
            self._ensure_fallback_table()

    def _ensure_fallback_table(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS atomic_memories (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT NOT NULL, -- PROJECT, SKILL, INTERNSHIP, METRIC, EDUCATION
                source TEXT NOT NULL,
                metadata_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def add_memory(self, content: str, user_id: str = "default_user", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add an atomic memory or conversation fact."""
        meta = metadata or {}
        category = meta.get("category", self._classify_fact_category(content))
        source = meta.get("source", "user_update")

        if self._mem0:
            try:
                res = self._mem0.add(
                    content,
                    user_id=user_id,
                    metadata={"source": source, "category": category, **meta}
                )
                # Also mirror into local relational store for dashboard UI querying
                self._save_to_local_store(content, user_id, category, source, meta)
                return {"status": "success", "engine": "mem0_nebius", "result": res}
            except Exception as e:
                logger.error(f"Mem0 live add failed: {e}. Falling back to local storage.")

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
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO atomic_memories (id, user_id, content, category, source, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (mem_id, user_id, content, category, source, json.dumps(meta)))
        conn.commit()
        conn.close()
        return mem_id

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
        if self._mem0:
            try:
                results = self._mem0.search(query=query, filters={"user_id": user_id}, limit=limit)
                if results and len(results) > 0:
                    return results
            except Exception:
                try:
                    results = self._mem0.search(query=query, user_id=user_id, limit=limit)
                    if results and len(results) > 0:
                        return results
                except Exception as e:
                    logger.warning(f"Mem0 search failed: {e}. Falling back to semantic text ranking.")

        # Local semantic ranking search
        self._ensure_fallback_table()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, content, category, source, metadata_json FROM atomic_memories WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        conn.close()

        query_tokens = set(re.findall(r"\w+", query.lower()))
        scored_memories = []

        for r in rows:
            content = r["content"]
            content_tokens = set(re.findall(r"\w+", content.lower()))
            overlap = len(query_tokens.intersection(content_tokens))
            
            # Boost category-specific relevance
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
                    "category": r["category"],
                    "source": r["source"],
                    "score": score
                })

        scored_memories.sort(key=lambda x: x["score"], reverse=True)
        return scored_memories[:limit]

    def get_all_memories(self, user_id: str = "default_user") -> List[Dict[str, Any]]:
        """Retrieve all atomic memories for dashboard cards."""
        self._ensure_fallback_table()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, content, category, source, metadata_json, created_at 
            FROM atomic_memories 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": r["id"],
                "content": r["content"],
                "category": r["category"],
                "source": r["source"],
                "metadata": json.loads(r["metadata_json"] or "{}"),
                "created_at": r["created_at"]
            }
            for r in rows
        ]

    def extract_and_ingest_text(self, text: str, source_name: str, user_id: str = "default_user") -> List[Dict[str, Any]]:
        """
        Splits resume or document text into semantic bullet points/sections and stores them as atomic facts.
        """
        # Split on bullet points or double newlines
        lines = [line.strip() for line in re.split(r"\n+|\u2022|\*", text) if len(line.strip()) > 15]
        
        ingested = []
        for line in lines:
            # Skip header noise
            if re.match(r"^(page \d+|resume|curriculum vitae|phone|email)$", line.lower()):
                continue
            cat = self._classify_fact_category(line)
            record = self.add_memory(
                content=line,
                user_id=user_id,
                metadata={"source": source_name, "category": cat}
            )
            ingested.append(record)
            
        return ingested

memory_manager = CareerMemoryManager()
