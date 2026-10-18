from datetime import datetime, timezone
from fastapi import APIRouter
from backend.config import settings
from backend.llm_router import llm_router
from backend.database import list_model_telemetry, list_search_runs, get_raw_connection

router = APIRouter(tags=["Health & Diagnostics"])

@router.api_route("/health", methods=["GET", "HEAD"])
@router.api_route("/api/v1/health", methods=["GET", "HEAD"])
def health_check():
    """System health check and Nebius Token Factory router status (supports GET and HEAD probes)."""
    nebius_status = llm_router.test_connection()
    return {
        "status": "healthy",
        "service": "CareerOrbit Personal AI Career Agent",
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

@router.get("/api/v1/operations/metrics")
def get_operations_metrics():
    """
    FR-042: Live Nebius Token Factory & Autonomous Agent Telemetry.
    Returns quantitative benchmark data, model invocation counts, and latency metrics for hackathon evaluation.
    """
    telemetry_logs = list_model_telemetry(limit=30)
    search_runs = list_search_runs(limit=10)

    # Compute model-level aggregate metrics
    model_stats = {
        settings.TIER1_MODEL: {"invocations": 0, "total_latency_ms": 0.0, "total_tokens": 0, "passed": 0},
        settings.TIER2_MODEL: {"invocations": 0, "total_latency_ms": 0.0, "total_tokens": 0, "passed": 0},
        settings.TIER3_MODEL: {"invocations": 0, "total_latency_ms": 0.0, "total_tokens": 0, "passed": 0},
        settings.EMBEDDING_MODEL: {"invocations": 0, "total_latency_ms": 0.0, "total_tokens": 0, "passed": 0},
    }

    for log in telemetry_logs:
        m_id = log["model_id"]
        if m_id not in model_stats:
            model_stats[m_id] = {"invocations": 0, "total_latency_ms": 0.0, "total_tokens": 0, "passed": 0}
        model_stats[m_id]["invocations"] += 1
        model_stats[m_id]["total_latency_ms"] += log["latency_ms"]
        model_stats[m_id]["total_tokens"] += log.get("tokens_used", 0)
        if log.get("validation_passed"):
            model_stats[m_id]["passed"] += 1

    summary = []
    for model_name, s in model_stats.items():
        inv = s["invocations"]
        avg_lat = round(s["total_latency_ms"] / max(inv, 1), 1)
        pass_rate = round((s["passed"] / max(inv, 1)) * 100, 1) if inv > 0 else 100.0
        summary.append({
            "model_id": model_name,
            "invocations": inv,
            "avg_latency_ms": avg_lat,
            "total_tokens": s["total_tokens"],
            "validation_pass_rate": f"{pass_rate}%"
        })

    # Count database entities
    conn = get_raw_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM discovered_jobs")
        jobs_count = c.fetchone()["cnt"]
        c.execute("SELECT COUNT(*) as cnt FROM applications")
        apps_count = c.fetchone()["cnt"]
        c.execute("SELECT COUNT(*) as cnt FROM inbox_events")
        inbox_count = c.fetchone()["cnt"]
    finally:
        conn.close()

    return {
        "status": "success",
        "service": "CareerOrbit Agent Operations Hub",
        "live_token_factory_connected": settings.is_nebius_configured,
        "summary": summary,
        "recent_telemetry": telemetry_logs[:10],
        "recent_search_runs": search_runs[:5],
        "db_stats": {
            "total_discovered_jobs": jobs_count,
            "total_applications": apps_count,
            "total_inbox_events": inbox_count
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
