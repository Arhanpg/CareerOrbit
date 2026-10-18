from datetime import datetime, timezone
from fastapi import APIRouter
from backend.config import settings
from backend.llm_router import llm_router

router = APIRouter(tags=["Health & Diagnostics"])

@router.get("/health")
def health_check():
    """System health check and Nebius Token Factory router status."""
    nebius_status = llm_router.test_connection()
    return {
        "status": "healthy",
        "service": "CareerClaw Autonomous Career Agent",
        "version": "1.0.0",
        "nebius_token_factory": nebius_status,
        "models": {
            "tier1_fast": settings.TIER1_MODEL,
            "tier1_fallback": settings.TIER1_FALLBACK_MODEL,
            "tier2_browser": settings.TIER2_MODEL,
            "tier3_ultra": settings.TIER3_MODEL,
            "embedding": settings.EMBEDDING_MODEL
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
