import json
import logging
from typing import List, Dict, Any, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.discovery.jobspy_worker import scrape_consumer_job_boards
from backend.discovery.tavily_hunter import hunt_opportunities_via_tavily
from backend.discovery.ats_readers import fetch_curated_ats_startup_internships
from backend.discovery.eligibility_gate import evaluate_batch_2028_eligibility
from backend.database import get_db_connection, get_candidate_constraints

logger = logging.getLogger("careerclaw.discovery_coordinator")

scheduler = AsyncIOScheduler()

def run_discovery_cycle(role_query: str = "AI ML Software Engineering") -> Dict[str, Any]:
    """
    Executes a complete 24/7 opportunity discovery and eligibility evaluation cycle:
    1. Scrapes consumer boards via JobSpy
    2. Queries live web and portals via Tavily
    3. Reads direct ATS JSON endpoints (Greenhouse/Lever)
    4. Evaluates each listing through the Nemotron 3.5 Lightning 2028 Batch Eligibility Gate
    5. Persists verified opportunities to SQLite
    """
    logger.info("Starting CareerClaw autonomous opportunity discovery cycle...")
    
    constraints = get_candidate_constraints() or {
        "degree": "B.Tech",
        "graduation_batch": 2028,
        "current_academic_year": "3rd Year",
        "current_location": "India",
        "target_roles": ["SDE Intern", "AI/ML Intern", "Backend Developer", "Hackathon"]
    }

    # 1. Harvest raw opportunities from all 3 pipelines
    raw_listings: List[Dict[str, Any]] = []
    raw_listings.extend(scrape_consumer_job_boards(role_query=role_query, results_wanted=10))
    raw_listings.extend(hunt_opportunities_via_tavily(role_query=role_query))
    raw_listings.extend(fetch_curated_ats_startup_internships())

    evaluated_records = []
    eligible_count = 0

    conn = get_db_connection()
    cursor = conn.cursor()

    for job in raw_listings:
        # 2. Evaluate with Nemotron 3.5 Lightning Gate
        eval_result = evaluate_batch_2028_eligibility(job, constraints)
        
        is_eligible = eval_result.get("is_eligible", False)
        match_score = eval_result.get("match_score", 0)
        role_category = eval_result.get("role_category", "SDE")
        rejection_reason = eval_result.get("rejection_reason")
        
        if is_eligible:
            eligible_count += 1

        # 3. Upsert into database
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
            job["id"],
            job["source"],
            job["title"],
            job["company"],
            job.get("location", "India / Remote"),
            job["url"],
            job.get("description", ""),
            1 if is_eligible else 0,
            match_score,
            role_category,
            rejection_reason,
            json.dumps({**job, **eval_result})
        ))

        evaluated_records.append({
            **job,
            "is_eligible": is_eligible,
            "match_score": match_score,
            "role_category": role_category,
            "rejection_reason": rejection_reason
        })

    conn.commit()
    conn.close()

    logger.info(f"Discovery cycle complete: {len(raw_listings)} harvested, {eligible_count} verified for B.Tech 2028.")
    return {
        "status": "success",
        "total_harvested": len(raw_listings),
        "eligible_matches": eligible_count,
        "records": evaluated_records
    }

def get_discovered_jobs(only_eligible: bool = True) -> List[Dict[str, Any]]:
    """Retrieve discovered opportunities from database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM discovered_jobs"
    if only_eligible:
        query += " WHERE is_eligible = 1"
    query += " ORDER BY match_score DESC, created_at DESC"
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    
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
            "created_at": r["created_at"]
        }
        for r in rows
    ]

def start_discovery_scheduler():
    """Initializes APScheduler 60-minute loop for 24/7 background hunting."""
    if not scheduler.running:
        scheduler.add_job(
            run_discovery_cycle,
            "interval",
            minutes=60,
            id="autonomous_opportunity_hunter",
            replace_existing=True
        )
        scheduler.start()
        logger.info("24/7 Autonomous Opportunity Hunter APScheduler started (runs every 60 mins).")
