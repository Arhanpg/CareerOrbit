from fastapi import APIRouter, HTTPException
from backend.models import CandidateHardConstraints
from backend.database import save_candidate_constraints, get_candidate_constraints

router = APIRouter(prefix="/api/v1/profile", tags=["Profile & Hard Constraints"])

@router.get("/constraints", response_model=CandidateHardConstraints)
def get_constraints(profile_id: str = "default_user"):
    """Retrieve canonical candidate constraints stored in the master vault."""
    saved = get_candidate_constraints(profile_id=profile_id)
    if not saved:
        # Return default recommended B.Tech 2028 profile
        default_profile = CandidateHardConstraints(
            full_name="Aman Sharma",
            email="aman.sharma28@example.com",
            phone="+91 9876543210",
            current_location="India",
            degree="B.Tech",
            graduation_batch=2028,
            current_academic_year="3rd Year",
            cgpa=8.95,
            target_roles=["SDE Intern", "AI/ML Intern", "Backend Developer", "Hackathon"],
            allowed_locations=["India", "Remote", "Bangalore", "Hyderabad", "Pune"],
            github_url="https://github.com/amansharma28",
            linkedin_url="https://linkedin.com/in/amansharma28",
            portfolio_url="https://amansharma.dev",
            address_line="Koramangala 4th Block, Bangalore",
            postal_code="560034"
        )
        save_candidate_constraints(profile_id, default_profile.model_dump())
        return default_profile
    return CandidateHardConstraints(**saved)

@router.post("/constraints", response_model=CandidateHardConstraints)
def save_constraints(constraints: CandidateHardConstraints, profile_id: str = "default_user"):
    """Save or update candidate canonical constraints."""
    save_candidate_constraints(profile_id, constraints.model_dump())
    return constraints
