from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, EmailStr

class CandidateHardConstraints(BaseModel):
    full_name: str = Field(..., min_length=2, description="Candidate's full legal name")
    email: EmailStr = Field(..., description="Primary contact email")
    phone: str = Field(..., min_length=8, description="Contact phone number with country code")
    current_location: str = Field(default="India")
    degree: str = Field(default="B.Tech", description="Academic degree, e.g. B.Tech / B.E.")
    graduation_batch: int = Field(default=2028, description="Graduation year (target 2028 batch)")
    current_academic_year: str = Field(default="3rd Year", description="Current academic year")
    cgpa: float = Field(..., ge=0.0, le=10.0, description="Current CGPA on 10.0 scale")
    target_roles: List[str] = Field(
        default=["SDE Intern", "AI/ML Intern", "Backend Developer", "Freelance", "Hackathon"]
    )
    allowed_locations: List[str] = Field(
        default=["India", "Remote", "Bangalore", "Hyderabad", "Pune", "Gurgaon", "Noida"]
    )
    github_url: str = Field(..., description="GitHub profile URL")
    linkedin_url: str = Field(..., description="LinkedIn profile URL")
    portfolio_url: Optional[str] = None
    address_line: str = Field(..., description="Residential street address")
    postal_code: str = Field(..., description="Postal PIN / Zip code")

    @field_validator("graduation_batch")
    @classmethod
    def validate_graduation_batch(cls, v: int) -> int:
        if v < 2026 or v > 2032:
            raise ValueError(f"Graduation batch {v} is outside the allowed range [2026-2032]. Target student cohort is B.Tech 2028.")
        return v

    @field_validator("cgpa")
    @classmethod
    def validate_cgpa(cls, v: float) -> float:
        if v < 0.0 or v > 10.0:
            raise ValueError(f"CGPA {v} must be between 0.0 and 10.0.")
        return v
