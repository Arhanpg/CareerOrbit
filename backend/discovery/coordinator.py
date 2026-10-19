import os
import time
import json
import logging
import threading
from typing import List, Dict, Any, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.discovery.jobspy_worker import scrape_consumer_job_boards
from backend.discovery.tavily_hunter import hunt_opportunities_via_tavily
from backend.discovery.ats_readers import fetch_curated_ats_startup_internships
from backend.discovery.eligibility_gate import evaluate_batch_2028_eligibility
from backend.database import (
    get_raw_connection,
    db_transaction,
    get_candidate_constraints,
    record_search_run
)

logger = logging.getLogger("careerorbit.discovery_coordinator")

scheduler = AsyncIOScheduler()
_DISCOVERY_LOCK = threading.Lock()

def run_discovery_cycle(role_query: str = "AI ML Software Engineering") -> Dict[str, Any]:
    """
    Executes a complete 24/7 opportunity discovery and eligibility evaluation cycle:
    1. Acquires concurrency lock to prevent overlapping SQLite write transactions.
    2. Scrapes consumer boards via JobSpy, Tavily web search, and ATS endpoints.
    3. Evaluates listings in memory without holding a SQLite connection.
    4. Batch inserts results into SQLite in <10ms and records search telemetry.
    """
    if not _DISCOVERY_LOCK.acquire(blocking=False):
        logger.info("Discovery cycle already in progress. Skipping concurrent run.")
        return {
            "status": "skipped",
            "message": "A discovery sweep is currently executing."
        }

    start_time = time.time()
    try:
        logger.info("Starting CareerOrbit autonomous opportunity discovery cycle...")
        
        constraints = get_candidate_constraints() or {
            "degree": "B.Tech",
            "graduation_batch": 2028,
            "current_academic_year": "3rd Year",
            "current_location": "India",
            "target_roles": ["SDE Intern", "AI/ML Intern", "Backend Developer", "Hackathon"]
        }

        # 1. Harvest raw opportunities in memory across all 3 pipelines
        raw_listings: List[Dict[str, Any]] = []
        sources_queried = ["jobspy", "ats_readers"]
        try:
            raw_listings.extend(scrape_consumer_job_boards(role_query=role_query, results_wanted=8))
        except Exception as e:
            logger.warning(f"JobSpy harvest error: {e}")

        try:
            raw_listings.extend(hunt_opportunities_via_tavily(role_query=role_query))
            sources_queried.append("tavily")
        except Exception as e:
            logger.warning(f"Tavily harvest error: {e}")

        try:
            raw_listings.extend(fetch_curated_ats_startup_internships())
        except Exception as e:
            logger.warning(f"ATS readers harvest error: {e}")

        # 2. Evaluate each listing in memory
        evaluated_records = []
        eligible_count = 0

        # Check existing URLs to avoid redundant LLM evaluations
        existing_urls = set()
        conn_check = get_raw_connection()
        try:
            c = conn_check.cursor()
            c.execute("SELECT url FROM discovered_jobs")
            existing_urls = set(r["url"] for r in c.fetchall())
        finally:
            conn_check.close()

        for idx, job in enumerate(raw_listings):
            # Evaluate using Nemotron 3.5 Lightning for first 6 uncached, deterministic for remainder
            should_use_llm = (idx < 6) and (job.get("url") not in existing_urls)
            eval_result = evaluate_batch_2028_eligibility(job, constraints, use_llm=should_use_llm)
            
            is_eligible = eval_result.get("is_eligible", False)
            match_score = eval_result.get("match_score", 0)
            role_category = eval_result.get("role_category", "SDE")
            rejection_reason = eval_result.get("rejection_reason")
            
            if is_eligible:
                eligible_count += 1

            evaluated_records.append({
                **job,
                "is_eligible": is_eligible,
                "match_score": match_score,
                "role_category": role_category,
                "rejection_reason": rejection_reason,
                "eval_result": eval_result
            })

        # 3. Batch insert into SQLite in a single rapid transaction (<10ms)
        with db_transaction() as conn:
            cursor = conn.cursor()
            for item in evaluated_records:
                cursor.execute("""
                    INSERT INTO discovered_jobs (
                        id, source, title, company, location, url, description, 
                        is_eligible, match_score, role_category, rejection_reason, raw_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(url) DO UPDATE SET
                        is_eligible = excluded.is_eligible,
                        match_score = excluded.match_score,
                        role_category = excluded.role_category,
                        rejection_reason = excluded.rejection_reason
                """, (
                    item["id"],
                    item["source"],
                    item["title"],
                    item["company"],
                    item.get("location", "India / Remote"),
                    item["url"],
                    item.get("description", ""),
                    1 if item["is_eligible"] else 0,
                    item["match_score"],
                    item["role_category"],
                    item["rejection_reason"],
                    json.dumps(item)
                ))

        duration = time.time() - start_time
        record_search_run(
            query=role_query,
            sources_queried=sources_queried,
            jobs_discovered=len(raw_listings),
            jobs_eligible=eligible_count,
            duration_seconds=duration
        )

        logger.info(f"Discovery cycle complete in {duration:.2f}s: {len(raw_listings)} harvested, {eligible_count} verified for B.Tech 2028.")
        return {
            "status": "success",
            "total_harvested": len(raw_listings),
            "eligible_matches": eligible_count,
            "duration_seconds": round(duration, 2),
            "records": evaluated_records
        }
    finally:
        _DISCOVERY_LOCK.release()

def get_discovered_jobs(only_eligible: bool = True) -> List[Dict[str, Any]]:
    """Retrieve discovered opportunities from database without locking SQLite."""
    conn = get_raw_connection()
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM discovered_jobs"
        if only_eligible:
            query += " WHERE is_eligible = 1"
        query += " ORDER BY match_score DESC, created_at DESC"
        cursor.execute(query)
        rows = cursor.fetchall()
        return [
            {
                "id": r["id"],
                "source": r["source"],
                "title": r["title"],
                "company": r["company"],
                "location": r["location"],
                "url": r["url"],
                "description": r["description"],
                "is_eligible": bool(r["is_eligible"]),
                "match_score": r["match_score"],
                "role_category": r["role_category"],
                "rejection_reason": r["rejection_reason"],
                "tailored_yaml": r["tailored_yaml"] if "tailored_yaml" in r.keys() else None,
                "truthfulness_status": r["truthfulness_status"] if "truthfulness_status" in r.keys() else "VERIFIED",
                "created_at": r["created_at"]
            }
            for r in rows
        ]
    finally:
        conn.close()

def keep_render_awake():
    """
    Pings the public Render backend URL every 10 minutes over HTTPS.
    Resets Render Free Tier's 15-minute inactivity shutdown timer so the container
    stays warm and active 24/7 without requiring the student's laptop to be powered on.
    """
    public_url = os.getenv("BACKEND_PUBLIC_URL") or os.getenv("RENDER_EXTERNAL_URL") or "https://careerorbit-s1ar.onrender.com"
    health_endpoint = f"{public_url.rstrip('/')}/health"
    try:
        import httpx
        with httpx.Client(timeout=8.0) as client:
            resp = client.get(health_endpoint)
            logger.info(f"Keep-alive self-ping to {health_endpoint} returned {resp.status_code}")
    except Exception as e:
        logger.debug(f"Keep-alive self-ping notice ({health_endpoint}): {e}")

def start_discovery_scheduler():
    """Initializes APScheduler loops for 24/7 background hunting and 10-minute keep-alive."""
    if not scheduler.running:
        scheduler.add_job(
            run_discovery_cycle,
            "interval",
            minutes=60,
            id="autonomous_opportunity_hunter",
            replace_existing=True
        )
        scheduler.add_job(
            keep_render_awake,
            "interval",
            minutes=10,
            id="render_24_7_keep_awake",
            replace_existing=True
        )
        scheduler.start()
        logger.info("24/7 Autonomous Opportunity Hunter & Keep-Alive APScheduler started.")
