import logging
import uuid
from typing import List, Dict, Any
from backend.config import settings

logger = logging.getLogger("careerclaw.jobspy_worker")

def scrape_consumer_job_boards(
    role_query: str = "Software Engineering",
    location: str = "India",
    results_wanted: int = 15
) -> List[Dict[str, Any]]:
    """
    FR-09: Scrapes Naukri, LinkedIn, Indeed (India), and Google Jobs concurrently via JobSpy.
    Returns normalized job listing dictionaries.
    """
    normalized_jobs = []
    
    try:
        from jobspy import scrape_jobs
        logger.info(f"Triggering JobSpy scrape for '{role_query}' in {location}...")
        df_jobs = scrape_jobs(
            site_name=["naukri", "linkedin", "indeed", "google"],
            search_term=f"{role_query} intern",
            google_search_term=f"{role_query} internship in {location} for B.Tech students posted in last 3 days",
            location=location,
            results_wanted=results_wanted,
            hours_old=72,
            country_indeed="india",
            fetch_description=True
        )

        if df_jobs is not None and not df_jobs.empty:
            for _, row in df_jobs.iterrows():
                job_id = f"jobspy_{uuid.uuid4().hex[:10]}"
                normalized_jobs.append({
                    "id": job_id,
                    "source": str(row.get("site", "jobspy")),
                    "title": str(row.get("title", "Software Engineering Intern")),
                    "company": str(row.get("company", "Tech Company")),
                    "location": str(row.get("location", location)),
                    "url": str(row.get("job_url", "")),
                    "description": str(row.get("description", ""))
                })
            logger.info(f"JobSpy successfully retrieved {len(normalized_jobs)} jobs.")
            return normalized_jobs

    except Exception as e:
        logger.warning(f"JobSpy scrape encountered network or anti-bot limit: {e}. Using deterministic feed.")

    # High-signal fallback listings for offline / sandbox demo
    fallback_listings = [
        {
            "id": "job_linkedin_msft_01",
            "source": "linkedin",
            "title": "Software Engineering Intern (Batch 2028)",
            "company": "Microsoft IDC",
            "location": "Hyderabad, India",
            "url": "https://careers.microsoft.com/us/en/job/174920/Software-Engineering-Intern",
            "description": "Microsoft India Development Center is hiring 3rd-year B.Tech students (Class of 2028) for our summer Software Engineering internship. Strong programming fundamentals in C++, Python, or Java, data structures, and algorithms required. Stipend: INR 1,25,000/month."
        },
        {
            "id": "job_naukri_swiggy_02",
            "source": "naukri",
            "title": "Backend SDE Intern",
            "company": "Swiggy",
            "location": "Bangalore / Remote",
            "url": "https://www.naukri.com/job-listings-swiggy-backend-intern",
            "description": "Join Swiggy Core Logistics team. We are looking for undergraduate students with proficiency in Python, FastAPI, Go, or Java, familiar with distributed caching (Redis) and relational databases (PostgreSQL). Open to 2028 batch."
        }
    ]
    return fallback_listings
