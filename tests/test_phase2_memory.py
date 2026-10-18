import io
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.memory.mem0_manager import memory_manager

client = TestClient(app)

def test_memory_upload_and_separation():
    """
    FR-06: Ingest two synthetic resumes (SDE and AI/ML) and verify semantic distinction.
    """
    # 1. Synthetic SDE Resume text
    sde_resume_content = b"""
    Aman Sharma - Software Engineering
    Projects:
    - Distributed Task Queue: Built a high-throughput distributed backend API with FastAPI, Redis, and Celery processing 12k jobs/sec.
    - PostgreSQL Replication Manager: Automated failover clustering using Raft consensus and Python asyncio.
    Skills: Python, FastAPI, Redis, Docker, PostgreSQL, Distributed Systems.
    """
    
    # 2. Synthetic AI/ML Resume text
    aiml_resume_content = b"""
    Aman Sharma - AI & Machine Learning Research
    Projects:
    - Multimodal RAG Engine: Developed an agentic retrieval-augmented pipeline using PyTorch, HuggingFace transformers, and Qdrant.
    - Computer Vision Defect Detection: Trained a YOLOv8 and ResNet model with PyTorch machine learning yielding 94% mAP.
    Skills: PyTorch, TensorFlow, LLMs, Computer Vision, Qdrant, CUDA, Python.
    """

    # Ingest SDE Resume via API
    res_sde = client.post(
        "/api/v1/memory/upload-files",
        files={"files": ("sde_resume.txt", io.BytesIO(sde_resume_content), "text/plain")},
        data={"user_id": "test_student"}
    )
    assert res_sde.status_code == 200
    assert res_sde.json()["files_processed"] == 1
    assert res_sde.json()["total_facts_stored"] > 0

    # Ingest AI/ML Resume via API
    res_aiml = client.post(
        "/api/v1/memory/upload-files",
        files={"files": ("aiml_resume.txt", io.BytesIO(aiml_resume_content), "text/plain")},
        data={"user_id": "test_student"}
    )
    assert res_aiml.status_code == 200
    assert res_aiml.json()["files_processed"] == 1

    # 3. Test FR-07: Conversational update
    res_chat = client.post(
        "/api/v1/memory/chat-update",
        json={
            "text": "Completed a new project: Built an autonomous browser agent using Nebius Token Factory and Nemotron 3 Ultra that reduced application latency by 40%.",
            "user_id": "test_student"
        }
    )
    assert res_chat.status_code == 200
    assert res_chat.json()["status"] == "success"

    # 4. Search for PyTorch machine learning -> should return AI/ML project
    aiml_query_res = client.post(
        "/api/v1/memory/search",
        json={"query": "PyTorch machine learning model", "user_id": "test_student", "limit": 5}
    )
    assert aiml_query_res.status_code == 200
    aiml_matches = aiml_query_res.json()["results"]
    assert len(aiml_matches) > 0
    top_aiml_text = " ".join([m["content"].lower() for m in aiml_matches])
    assert "pytorch" in top_aiml_text or "rag" in top_aiml_text or "vision" in top_aiml_text

    # 5. Search for distributed backend API -> should return SDE project
    sde_query_res = client.post(
        "/api/v1/memory/search",
        json={"query": "distributed backend API FastAPI", "user_id": "test_student", "limit": 5}
    )
    assert sde_query_res.status_code == 200
    sde_matches = sde_query_res.json()["results"]
    assert len(sde_matches) > 0
    top_sde_text = " ".join([m["content"].lower() for m in sde_matches])
    assert "fastapi" in top_sde_text or "distributed" in top_sde_text or "redis" in top_sde_text

    # 6. Retrieve all memories
    all_res = client.get("/api/v1/memory/all?user_id=test_student")
    assert all_res.status_code == 200
    assert all_res.json()["total_count"] >= 3
