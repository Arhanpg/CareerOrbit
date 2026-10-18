import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.discovery.eligibility_gate import evaluate_batch_2028_eligibility

client = TestClient(app)

def test_eligibility_gate_four_fixtures():
    """
    FR-12 & Automated Verification Test:
    Pass 4 distinct fixtures through eligibility_gate.py:
    1. Valid 2028 Adobe AI/ML internship -> Pass
    2. Unstop National AI Hackathon 2028 -> Pass
    3. Senior 5-YOE role -> Reject
    4. Unpaid training fee scam -> Reject
    """
    candidate_constraints = {
        "degree": "B.Tech",
        "graduation_batch": 2028,
        "current_academic_year": "3rd Year",
        "current_location": "India",
        "target_roles": ["SDE Intern", "AI/ML Intern", "Backend Developer", "Hackathon"]
    }

    # Fixture 1: Valid 2028 Adobe AI/ML Internship
    fixture_valid_adobe = {
        "title": "AI/ML Research Intern (Class of 2028)",
        "company": "Adobe Systems India",
        "location": "Bangalore, India",
        "description": "Adobe Media and Data Science Lab is hiring 3rd-year B.Tech students graduating in 2028. Work with PyTorch, LLMs, and computer vision. Stipend: INR 1,00,000/month."
    }

    # Fixture 2: Valid Unstop Hackathon
    fixture_valid_unstop = {
        "title": "National AI Hackathon & Hiring Challenge 2026",
        "company": "Unstop",
        "location": "Online / India",
        "description": "Collegiate hackathon open to undergraduate B.Tech students (Class of 2027 and 2028). Top teams qualify for fast-track interview rounds at sponsor tech companies."
    }

    # Fixture 3: Senior Role (5+ YOE)
    fixture_senior_role = {
        "title": "Senior Staff Software Engineer",
        "company": "Enterprise Cloud Corp",
        "location": "Bangalore",
        "description": "Requires minimum 5+ years of post-graduation software engineering experience. Lead architectural decisions for distributed databases."
    }

    # Fixture 4: Unpaid Training Scam
    fixture_scam_training = {
        "title": "Software Intern & Training Program",
        "company": "CertifyFast Institute",
        "location": "Remote",
        "description": "Selected candidates must pay a registration fee of INR 9,999 for mandatory certification materials before project allocation. Unpaid training."
    }

    res_adobe = evaluate_batch_2028_eligibility(fixture_valid_adobe, candidate_constraints)
    res_unstop = evaluate_batch_2028_eligibility(fixture_valid_unstop, candidate_constraints)
    res_senior = evaluate_batch_2028_eligibility(fixture_senior_role, candidate_constraints)
    res_scam = evaluate_batch_2028_eligibility(fixture_scam_training, candidate_constraints)

    # Assertions
    assert res_adobe["is_eligible"] is True
    assert res_adobe["match_score"] >= 80
    assert res_adobe["role_category"] in ["AIML", "SDE"]

    assert res_unstop["is_eligible"] is True
    assert res_unstop["match_score"] >= 80
    assert res_unstop["role_category"] == "HACKATHON"

    assert res_senior["is_eligible"] is False
    assert "experience" in res_senior["rejection_reason"].lower()

    assert res_scam["is_eligible"] is False
    assert "fee" in res_scam["rejection_reason"].lower() or "scam" in res_scam["rejection_reason"].lower()

def test_hunter_api_endpoints():
    """Verify GET and POST /api/v1/hunter endpoints."""
    # Test on-demand discovery run
    post_res = client.post("/api/v1/hunter/run-now")
    assert post_res.status_code == 200
    data = post_res.json()
    assert data["status"] == "success"
    assert data["total_harvested"] > 0

    # Test list jobs
    get_res = client.get("/api/v1/hunter/jobs?only_eligible=true")
    assert get_res.status_code == 200
    job_list = get_res.json()
    assert job_list["count"] > 0
    first_job = job_list["jobs"][0]
    assert first_job["is_eligible"] is True
    assert "title" in first_job
    assert "company" in first_job
