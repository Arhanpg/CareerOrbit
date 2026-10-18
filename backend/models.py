from typing import List, Optional, Dict, Any
from datetime import datetime
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
    address_line: str = Field(default="Koramangala, 5th Block, Bangalore", description="Residential street address")
    postal_code: str = Field(default="560095", description="Postal PIN / Zip code")

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

class RequirementEvidenceMap(BaseModel):
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    evidence_map: Dict[str, str] = Field(default_factory=dict, description="Keyword -> Candidate Evidence snippet")
    coverage_score: int = Field(default=0, ge=0, le=100)
    truthfulness_verified: bool = Field(default=True)

class ModelTelemetryItem(BaseModel):
    id: str
    model_id: str
    task_type: str
    latency_ms: float
    tokens_used: int = 0
    validation_passed: bool = True
    error_details: Optional[str] = None
    timestamp: Optional[str] = None

class SearchRunRecord(BaseModel):
    id: str
    query: str
    sources_queried: List[str] = Field(default_factory=list)
    jobs_discovered: int = 0
    jobs_eligible: int = 0
    duration_seconds: float = 0.0
    timestamp: Optional[str] = None

class DocumentRecord(BaseModel):
    id: str
    filename: str
    content_hash: str
    file_size: int = 0
    facts_extracted: int = 0
    created_at: Optional[str] = None

class MemoryConflictItem(BaseModel):
    id: str
    field_name: str
    existing_value: str
    incoming_value: str
    status: str = "PENDING" # PENDING, RESOLVED
    source_doc: Optional[str] = None
    created_at: Optional[str] = None
    resolved_at: Optional[str] = None

class DiscoveredJobRecord(BaseModel):
    id: str
    source: str
    title: str
    company: str
    location: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    is_eligible: bool = False
    match_score: int = 0
    role_category: Optional[str] = "SDE"
    rejection_reason: Optional[str] = None
    tailored_yaml: Optional[str] = None
    requirement_evidence_json: Optional[str] = None
    truthfulness_status: str = "VERIFIED"
    keyword_coverage_json: Optional[str] = None
    source_confidence: str = "HIGH"
    eligibility_state: str = "ELIGIBLE"
    created_at: Optional[str] = None
