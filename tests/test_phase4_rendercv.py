import os
import pytest
from pathlib import Path
from pypdf import PdfReader
from fastapi.testclient import TestClient
from backend.main import app
from backend.resume_engine.rendercv_compiler import compile_tailored_ats_resume

client = TestClient(app)

def test_rendercv_compilation_sde_and_aiml(tmp_path):
    """
    FR-16 & FR-17: Test dynamic compilation of tailored ATS-proof PDFs via RenderCV & Typst.
    Asserts:
    1. Both SDE and AI/ML compilations produce valid, non-empty .pdf files on disk.
    2. pypdf text extraction confirms SDE PDF contains backend keywords ('FastAPI', 'Redis', 'distributed').
    3. pypdf text extraction confirms AI/ML PDF contains ML keywords ('Nemotron', 'PyTorch', 'Vision' or 'RAG').
    """
    candidate_profile = {
        "full_name": "Aman Sharma",
        "email": "aman.sharma28@example.com",
        "phone": "+919876543210",
        "current_location": "Bangalore, India",
        "degree": "B.Tech",
        "graduation_batch": 2028,
        "current_academic_year": "3rd Year",
        "cgpa": 8.95,
        "github_url": "https://github.com/amansharma28",
        "linkedin_url": "https://linkedin.com/in/amansharma28"
    }

    retrieved_memories = [
        {"content": "Engineered distributed queue with FastAPI and Redis processing 12k jobs/sec.", "category": "PROJECT"},
        {"content": "Trained multimodal vision transformer with PyTorch achieving 94% precision.", "category": "PROJECT"},
        {"content": "Implemented Mem0 vector memory with local Qdrant reducing latency by 40%.", "category": "PROJECT"}
    ]

    # 1. Compile SDE Resume
    sde_job = {
        "id": "test_sde_role_01",
        "title": "Backend SDE Intern (Class of 2028)",
        "company": "Swiggy",
        "role_category": "SDE",
        "description": "Looking for B.Tech interns to work on distributed microservices, FastAPI, Redis caching, and PostgreSQL database replication."
    }
    sde_pdf_path = compile_tailored_ats_resume(
        candidate_profile=candidate_profile,
        retrieved_memories=retrieved_memories,
        job_posting=sde_job,
        output_dir=str(tmp_path / "resumes")
    )

    assert os.path.exists(sde_pdf_path)
    assert os.path.getsize(sde_pdf_path) > 1000

    # Read SDE PDF content via pypdf
    sde_reader = PdfReader(sde_pdf_path)
    sde_text = "".join(page.extract_text() or "" for page in sde_reader.pages)
    assert "Aman Sharma" in sde_text
    assert "2028" in sde_text
    assert "FastAPI" in sde_text or "Distributed" in sde_text

    # 2. Compile AI/ML Resume
    aiml_job = {
        "id": "test_aiml_role_02",
        "title": "AI/ML Research Intern (B.Tech 2028)",
        "company": "Adobe",
        "role_category": "AIML",
        "description": "Adobe Research is hiring for generative AI, PyTorch deep learning, multimodal vision, and vector embeddings."
    }
    aiml_pdf_path = compile_tailored_ats_resume(
        candidate_profile=candidate_profile,
        retrieved_memories=retrieved_memories,
        job_posting=aiml_job,
        output_dir=str(tmp_path / "resumes")
    )

    assert os.path.exists(aiml_pdf_path)
    assert os.path.getsize(aiml_pdf_path) > 1000

    # Read AI/ML PDF content via pypdf
    aiml_reader = PdfReader(aiml_pdf_path)
    aiml_text = "".join(page.extract_text() or "" for page in aiml_reader.pages)
    assert "Aman Sharma" in aiml_text
    assert "PyTorch" in aiml_text or "Vision" in aiml_text or "Nemotron" in aiml_text

def test_resume_api_compile_and_serve():
    """Test POST /api/v1/resumes/compile and GET /api/v1/resumes/{job_id}/pdf."""
    compile_res = client.post(
        "/api/v1/resumes/compile",
        json={"job_id": "api_test_job_123"}
    )
    assert compile_res.status_code == 200
    data = compile_res.json()
    assert data["status"] == "success"
    assert "pdf_download_url" in data

    # Test PDF download endpoint
    pdf_res = client.get("/api/v1/resumes/api_test_job_123/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 1000
