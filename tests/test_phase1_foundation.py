import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from backend.main import app
from backend.models import CandidateHardConstraints
from backend.llm_router import llm_router

client = TestClient(app)

def test_health_check_returns_200():
    """Verify GET /health returns HTTP 200 and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "nebius_token_factory" in data
    assert "models" in data
    assert data["models"]["tier1_fast"] == "nebius/nvidia/Nemotron-3_5-Lightning"
    assert data["models"]["tier2_browser"] == "nebius/nvidia/nemotron-3-super-120b-a12b"
    assert data["models"]["tier3_ultra"] == "nebius/nvidia/Nemotron-3-Ultra-550b-a55b"

def test_candidate_constraints_schema_valid():
    """Validate CandidateHardConstraints accepts valid B.Tech 2028 batch candidate."""
    valid_data = {
        "full_name": "Aman Sharma",
        "email": "aman@example.com",
        "phone": "+91 9876543210",
        "current_location": "India",
        "degree": "B.Tech",
        "graduation_batch": 2028,
        "current_academic_year": "3rd Year",
        "cgpa": 8.9,
        "target_roles": ["SDE Intern", "AI/ML Intern"],
        "allowed_locations": ["India", "Remote"],
        "github_url": "https://github.com/amansharma28",
        "linkedin_url": "https://linkedin.com/in/amansharma28",
        "address_line": "Bangalore",
        "postal_code": "560001"
    }
    candidate = CandidateHardConstraints(**valid_data)
    assert candidate.graduation_batch == 2028
    assert candidate.cgpa == 8.9

def test_candidate_constraints_schema_rejects_invalid_batch():
    """Validate schema rejects invalid graduation batch (e.g. past or out-of-range year)."""
    invalid_data = {
        "full_name": "Invalid Candidate",
        "email": "invalid@example.com",
        "phone": "+91 9876543210",
        "degree": "B.Tech",
        "graduation_batch": 2024, # Too old for 3rd year / 2028 target
        "cgpa": 8.5,
        "github_url": "https://github.com/test",
        "linkedin_url": "https://linkedin.com/test",
        "address_line": "Delhi",
        "postal_code": "110001"
    }
    with pytest.raises(ValidationError):
        CandidateHardConstraints(**invalid_data)

def test_candidate_constraints_schema_rejects_invalid_cgpa():
    """Validate schema rejects CGPA out of bounds."""
    invalid_data = {
        "full_name": "Invalid CGPA",
        "email": "invalid@example.com",
        "phone": "+91 9876543210",
        "degree": "B.Tech",
        "graduation_batch": 2028,
        "cgpa": 11.5, # Out of 0-10 bounds
        "github_url": "https://github.com/test",
        "linkedin_url": "https://linkedin.com/test",
        "address_line": "Delhi",
        "postal_code": "110001"
    }
    with pytest.raises(ValidationError):
        CandidateHardConstraints(**invalid_data)

def test_profile_constraints_api_endpoints():
    """Test GET and POST /api/v1/profile/constraints endpoints."""
    # Test GET returns profile
    get_res = client.get("/api/v1/profile/constraints")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["graduation_batch"] == 2028
    assert "email" in data

    # Test POST updates profile
    update_payload = data.copy()
    update_payload["full_name"] = "Aman Vikram Sharma"
    update_payload["cgpa"] = 9.15
    post_res = client.post("/api/v1/profile/constraints", json=update_payload)
    assert post_res.status_code == 200
    updated_data = post_res.json()
    assert updated_data["full_name"] == "Aman Vikram Sharma"
    assert updated_data["cgpa"] == 9.15

    # Verify persistence
    verify_res = client.get("/api/v1/profile/constraints")
    assert verify_res.json()["full_name"] == "Aman Vikram Sharma"

def test_llm_router_connectivity_and_routing():
    """Test live connectivity or deterministic fallback behavior of Nebius router."""
    status = llm_router.test_connection()
    assert "status" in status
    assert status["status"] in ["connected", "mock_mode"]

    # Test Tier 1 Fast
    t1_res = llm_router.call_tier1_fast(
        messages=[{"role": "user", "content": "Check eligibility for 2028 batch internship"}],
        response_format={"type": "json_object"}
    )
    assert t1_res is not None
    assert "is_eligible" in t1_res

    # Test Tier 2 Browser
    t2_res = llm_router.call_tier2_browser(
        messages=[{"role": "user", "content": "Navigate and fill form fields"}]
    )
    assert t2_res is not None
    assert len(t2_res) > 0

    # Test Tier 3 Ultra
    t3_res = llm_router.call_tier3_ultra(
        messages=[{"role": "user", "content": "Generate RenderCV YAML"}]
    )
    assert t3_res is not None
    assert "cv:" in t3_res or "name:" in t3_res

    # Test Embeddings
    emb = llm_router.embed_text("Autonomous AI Career Agent")
    assert isinstance(emb, list)
    assert len(emb) > 0
