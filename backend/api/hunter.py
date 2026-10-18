from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
from backend.discovery.coordinator import run_discovery_cycle, get_discovered_jobs

router = APIRouter(prefix="/api/v1/hunter", tags=["24/7 Opportunity Hunter"])

class RunHunterRequest(BaseModel):
    role_query: Optional[str] = "AI ML Software Engineering Intern"

@router.get("/jobs")
def list_jobs(only_eligible: bool = True):
    """Retrieve discovered opportunities with B.Tech 2028 batch verification."""
    jobs = get_discovered_jobs(only_eligible=only_eligible)
    # If no jobs in DB yet, run a fast initial harvest
    if not jobs:
        run_discovery_cycle()
        jobs = get_discovered_jobs(only_eligible=only_eligible)
        
    return {
        "count": len(jobs),
        "jobs": jobs
    }

@router.post("/run-now")
def trigger_hunt_cycle(payload: Optional[RunHunterRequest] = None):
    """Trigger an immediate 24/7 discovery sweep across JobSpy, Tavily, and ATS portals."""
    query = payload.role_query if payload else "AI ML Software Engineering Intern"
    result = run_discovery_cycle(role_query=query)
    return result
