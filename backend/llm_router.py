import json
import logging
from typing import Any, Dict, List, Optional, Union
from openai import OpenAI
from backend.config import settings

logger = logging.getLogger("careerclaw.llm_router")

class NebiusLLMRouter:
    def __init__(self):
        self.api_key = settings.NEBIUS_API_KEY
        self.base_url = settings.NEBIUS_BASE_URL
        self._client: Optional[OpenAI] = None
        
        if settings.is_nebius_configured:
            self._client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )

    @property
    def client(self) -> Optional[OpenAI]:
        if self._client is None and settings.is_nebius_configured:
            self._client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
        return self._client

    def test_connection(self) -> Dict[str, Any]:
        """Test connectivity to Nebius Token Factory or return mock status."""
        if not settings.is_nebius_configured:
            return {
                "status": "mock_mode",
                "message": "NEBIUS_API_KEY not configured. Running in deterministic mock mode for local testing.",
                "configured": False,
                "base_url": self.base_url,
                "tier1_model": settings.TIER1_MODEL,
                "tier2_model": settings.TIER2_MODEL,
                "tier3_model": settings.TIER3_MODEL
            }
        try:
            # Simple fast query to verify auth
            resp = self.call_tier1_fast(
                messages=[{"role": "user", "content": "Respond with 'OK'"}],
                max_tokens=10
            )
            return {
                "status": "connected",
                "message": "Successfully authenticated with Nebius Token Factory",
                "configured": True,
                "sample_response": resp.strip()
            }
        except Exception as e:
            logger.warning(f"Nebius Token Factory live connection test failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "configured": True
            }

    def call_tier1_fast(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        response_format: Optional[Dict[str, str]] = None,
        max_tokens: int = 1024
    ) -> str:
        """
        Tier 1 (High-Frequency Daemon): Mem0 additive fact extraction, B.Tech 2028 batch eligibility,
        and Gmail triage. Uses Nemotron-3_5-Lightning with fallback to Nemotron-3-Nano-30B-A3B.
        """
        if not settings.is_nebius_configured:
            # Deterministic mock response for local testing
            if response_format and response_format.get("type") == "json_object":
                # Check message content for mock behavior
                user_msg = " ".join(m.get("content", "") for m in messages).lower()
                if "reject" in user_msg and "2025" in user_msg:
                    return json.dumps({
                        "is_eligible": False,
                        "match_score": 20,
                        "role_category": "SDE",
                        "matched_skills": [],
                        "rejection_reason": "Restricted strictly to 2025 graduates; candidate is B.Tech 2028"
                    })
                elif "scam" in user_msg or "pay a fee" in user_msg or "unpaid" in user_msg:
                    return json.dumps({
                        "is_eligible": False,
                        "match_score": 0,
                        "role_category": "FREELANCE",
                        "matched_skills": [],
                        "rejection_reason": "Unpaid training scam requiring registration fees"
                    })
                elif "hackathon" in user_msg:
                    return json.dumps({
                        "is_eligible": True,
                        "match_score": 95,
                        "role_category": "HACKATHON",
                        "matched_skills": ["Python", "Machine Learning", "FastAPI"],
                        "rejection_reason": None
                    })
                else:
                    return json.dumps({
                        "is_eligible": True,
                        "match_score": 92,
                        "role_category": "AIML" if "ml" in user_msg or "ai" in user_msg else "SDE",
                        "matched_skills": ["Python", "FastAPI", "PyTorch"],
                        "rejection_reason": None
                    })
            return "Tier-1 Mock Response: Task processed successfully by Nemotron-3_5-Lightning (Sandbox)."

        try:
            kwargs = {
                "model": settings.TIER1_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if response_format:
                kwargs["response_format"] = response_format
            
            resp = self.client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content or ""
        except Exception as e:
            logger.warning(f"Tier 1 primary model ({settings.TIER1_MODEL}) failed: {e}. Retrying with fallback {settings.TIER1_FALLBACK_MODEL}")
            kwargs["model"] = settings.TIER1_FALLBACK_MODEL
            resp = self.client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content or ""

    def call_tier2_browser(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 2048
    ) -> str:
        """
        Tier 2 (Interactive & Browser Control): Driving browser-use DOM & Accessibility tree navigation,
        mapping form fields, and preparing approval briefs. Uses Nemotron-3-Super-120B.
        """
        if not settings.is_nebius_configured:
            return "Tier-2 Mock: Navigated to portal, pre-filled form fields accurately, and paused before submission."

        resp = self.client.chat.completions.create(
            model=settings.TIER2_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return resp.choices[0].message.content or ""

    def call_tier3_ultra(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> str:
        """
        Tier 3 (Deep Reasoning & Synthesis): Deep gap analysis, Action-Technology-Result bullet synthesis,
        and strict Pydantic-validated RenderCV YAML generation. Uses Nemotron-3-Ultra-550B.
        """
        if not settings.is_nebius_configured:
            return """
cv:
  name: Aman Sharma
  location: Bangalore, India
  email: student@example.com
  phone: +91 9876543210
  social_networks:
    - network: GitHub
      username: amansharma28
    - network: LinkedIn
      username: amansharma28
  sections:
    education:
      - institution: Indian Institute of Technology
        area: Computer Science & Engineering (B.Tech)
        degree: Bachelor of Technology
        start_date: 2024-08
        end_date: 2028-05
        highlights:
          - "CGPA: 8.9 / 10.0 (Current 3rd Year Standing)"
    projects:
      - name: Autonomous AI Career Agent
        date: 2026
        highlights:
          - "Engineered an autonomous multi-agent pipeline using FastAPI and Nemotron 3 Ultra, reducing application latency by 40%."
          - "Integrated Mem0 vector store with Qdrant for semantic resume recall across 15+ candidate projects."
design:
  theme: engineeringresumes
"""

        resp = self.client.chat.completions.create(
            model=settings.TIER3_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return resp.choices[0].message.content or ""

    def embed_text(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Dense Embeddings: Vectorizing resumes, projects, and queries using Qwen3-Embedding-8B.
        """
        is_single = isinstance(text, str)
        inputs = [text] if is_single else text
        
        if not settings.is_nebius_configured:
            # Deterministic mock embedding (4096-dim zeros with pseudo-hash)
            mock_emb = [[(hash(inp + str(i)) % 1000) / 1000.0 for i in range(128)] for inp in inputs]
            return mock_emb[0] if is_single else mock_emb

        resp = self.client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=inputs
        )
        embeddings = [data.embedding for data in resp.data]
        return embeddings[0] if is_single else embeddings

llm_router = NebiusLLMRouter()
