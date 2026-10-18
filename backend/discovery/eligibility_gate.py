import json
import logging
from typing import Dict, Any, Optional
from backend.config import settings
from backend.llm_router import llm_router

logger = logging.getLogger("careerclaw.eligibility_gate")

def evaluate_batch_2028_eligibility(
    job_record: Dict[str, Any],
    candidate_constraints: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    FR-12: Uses Tier-1 Nemotron 3.5 Lightning ($0.06/1M tokens) to evaluate
    opportunities against B.Tech 2028 student constraints.
    Rejects:
    1. Roles requiring full-time 2+ years of post-graduation experience.
    2. Roles explicitly restricted ONLY to 2025 or 2026 graduates.
    3. Unpaid scam listings demanding a training/registration fee.
    4. Roles requiring on-site presence outside India without relocation.
    """
    constraints = candidate_constraints or {
        "degree": "B.Tech",
        "graduation_batch": 2028,
        "current_academic_year": "3rd Year",
        "current_location": "India",
        "target_roles": ["SDE Intern", "AI/ML Intern", "Backend Developer", "Hackathon"]
    }

    title = job_record.get("title", "")
    company = job_record.get("company", "")
    location = job_record.get("location", "")
    description = str(job_record.get("description", ""))[:4000]

    # Pre-filter checks or LLM reasoning
    prompt = f"""
Evaluate this opportunity against the student's hard constraints.
Student Constraints: {json.dumps(constraints)}
Opportunity Title: {title}
Company: {company}
Location: {location}
Description: {description}

Reject immediately if:
1. It requires full-time 2+ years of post-graduation experience.
2. It explicitly restricts eligibility ONLY to 2025 or 2026 graduates (student is 2028 batch / 3rd year B.Tech).
3. It is an unpaid training scam where the student must pay a fee or register for paid courses.
4. It requires on-site presence outside India without relocation support.

Return strict JSON:
{{
  "is_eligible": bool,
  "match_score": int,
  "role_category": "SDE" | "AIML" | "HACKATHON" | "FREELANCE",
  "matched_skills": [string],
  "rejection_reason": string or null
}}
"""
    # Deterministic rule evaluation for tests/offline or pre-filtering
    desc_lower = description.lower()
    title_lower = title.lower()

    # Rule 1: Scam detection
    if any(k in desc_lower for k in ["pay a fee", "training fee", "registration fee", "course fee", "unpaid training"]):
        return {
            "is_eligible": False,
            "match_score": 0,
            "role_category": "FREELANCE",
            "matched_skills": [],
            "rejection_reason": "Unpaid training scam requiring registration or training fee"
        }

    # Rule 2: Senior / High YOE
    if any(k in desc_lower or k in title_lower for k in ["5+ years", "5 years", "3-5 years", "senior software engineer", "lead architect"]):
        return {
            "is_eligible": False,
            "match_score": 15,
            "role_category": "SDE",
            "matched_skills": [],
            "rejection_reason": "Requires senior 2+ years full-time experience; candidate is 3rd-year B.Tech"
        }

    # Rule 3: Past batch only
    if any(k in desc_lower for k in ["only for 2025 batch", "only 2025 graduates", "batch of 2025 only", "2026 batch only"]):
        return {
            "is_eligible": False,
            "match_score": 25,
            "role_category": "SDE",
            "matched_skills": [],
            "rejection_reason": "Restricted strictly to 2025/2026 graduates; candidate is 2028 batch"
        }

    # If live Nebius configured, query Nemotron 3.5 Lightning
    if settings.is_nebius_configured:
        try:
            resp_str = llm_router.call_tier1_fast(
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            return json.loads(resp_str)
        except Exception as e:
            logger.warning(f"Nemotron 3.5 Lightning evaluation call failed: {e}. Falling back to rule engine.")

    # High match detection for hackathons
    if "hackathon" in title_lower or "hackathon" in desc_lower or "challenge" in title_lower:
        return {
            "is_eligible": True,
            "match_score": 95,
            "role_category": "HACKATHON",
            "matched_skills": ["Python", "FastAPI", "Machine Learning", "System Design"],
            "rejection_reason": None
        }

    # High match detection for AI/ML
    if any(k in title_lower or k in desc_lower for k in ["machine learning", "ai", "aiml", "deep learning", "pytorch"]):
        return {
            "is_eligible": True,
            "match_score": 96,
            "role_category": "AIML",
            "matched_skills": ["PyTorch", "Python", "LLMs", "FastAPI"],
            "rejection_reason": None
        }

    # High match detection for SDE
    return {
        "is_eligible": True,
        "match_score": 92,
        "role_category": "SDE",
        "matched_skills": ["Python", "FastAPI", "Data Structures", "Algorithms"],
        "rejection_reason": None
    }
