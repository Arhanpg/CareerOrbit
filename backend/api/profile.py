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
            full_name="Arhan Praveen Ghosarwade",
            email="arhanghosarwade05@gmail.com",
            phone="+91 6366616225",
            institution="Indian Institute of Information Technology (IIIT) Dharwad",
            current_location="Dharwad, Karnataka, India",
            degree="B.Tech in Computer Science and Engineering",
            graduation_batch=2028,
            current_academic_year="3rd Year (2024 – 2028)",
            cgpa=8.69,
            target_roles=["SDE Intern", "AI/ML Intern", "Backend Developer", "GenAI / Agentic AI", "Hackathon"],
            allowed_locations=["India", "Remote", "Bangalore", "Hyderabad", "Pune", "Dharwad"],
            github_url="https://github.com/Arhanpg",
            linkedin_url="https://www.linkedin.com/in/arhan-ghosarwade-78bb16324",
            portfolio_url="https://github.com/Arhanpg",
            address_line="IIIT Dharwad Campus, Ittigatti Road",
            postal_code="580009"
        )
        save_candidate_constraints(profile_id, default_profile.model_dump())
        return default_profile
    return CandidateHardConstraints(**saved)

@router.post("/constraints", response_model=CandidateHardConstraints)
def save_constraints(constraints: CandidateHardConstraints, profile_id: str = "default_user"):
    """Save or update candidate canonical constraints."""
    save_candidate_constraints(profile_id, constraints.model_dump())
    return constraints
