import io
import re
import uuid
import hashlib
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from pypdf import PdfReader
from backend.memory.mem0_manager import memory_manager
from backend.database import get_raw_connection, db_transaction, get_candidate_constraints

router = APIRouter(prefix="/api/v1/memory", tags=["Core Memory Vault"])

class ChatUpdateRequest(BaseModel):
    text: str
    user_id: Optional[str] = "default_user"

class SearchMemoryRequest(BaseModel):
    query: str
    limit: Optional[int] = 10
    user_id: Optional[str] = "default_user"

class ConflictResolveRequest(BaseModel):
    chosen_value: str

def extract_text_from_file(filename: str, content_bytes: bytes) -> str:
    """Extract plain text from PDF, DOCX, TXT, or MD files."""
    fn = filename.lower()
    
    # 1. PDF
    if fn.endswith(".pdf"):
        try:
            reader = PdfReader(io.BytesIO(content_bytes))
            text = ""
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
            return text
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse PDF {filename}: {e}")
            
    # 2. DOCX
    elif fn.endswith(".docx"):
        try:
            with zipfile.ZipFile(io.BytesIO(content_bytes)) as z:
                doc_xml = z.read("word/document.xml")
                root = ET.fromstring(doc_xml)
                return "\n".join(
                    "".join(node.itertext())
                    for node in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p")
                    if "".join(node.itertext()).strip()
                )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse DOCX {filename}: {e}")
            
    # 3. TXT / MD
    elif fn.endswith(".txt") or fn.endswith(".md"):
        try:
            return content_bytes.decode("utf-8", errors="ignore")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to decode text {filename}: {e}")
            
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file format for {filename}. Supported: PDF, DOCX, TXT, MD")

@router.post("/upload-files")
async def upload_resume_files(
    files: List[UploadFile] = File(...),
    user_id: str = Form("default_user")
):
    """
    FR-004 & FR-006: Accepts multiple resumes/documents (SDE resume, AI/ML resume, project notes)
    and extracts atomic facts into Mem0 and local Qdrant/SQLite memory, registering document provenance.
    """
    results = []
    total_facts = 0
    current_profile = get_candidate_constraints(user_id) or {}

    for file in files:
        contents = await file.read()
        content_hash = hashlib.sha256(contents).hexdigest()
        extracted_text = extract_text_from_file(file.filename, contents)
        ingested_facts = memory_manager.extract_and_ingest_text(
            text=extracted_text,
            source_name=file.filename,
            user_id=user_id
        )
        total_facts += len(ingested_facts)

        # Record document provenance (FR-004)
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO document_records (id, filename, content_hash, file_size, facts_extracted)
                VALUES (?, ?, ?, ?, ?)
            """, (doc_id, file.filename, content_hash, len(contents), len(ingested_facts)))

        # Contradiction Detection (FR-008, Scenario B)
        # Check for batch discrepancy
        batch_match = re.search(r"\b(202[4-9]|203[0-2])\b", extracted_text)
        if batch_match:
            found_year = int(batch_match.group(1))
            current_batch = current_profile.get("graduation_batch", 2028)
            if found_year != current_batch and abs(found_year - current_batch) <= 3:
                with db_transaction() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO memory_conflicts (id, field_name, existing_value, incoming_value, status, source_doc)
                        VALUES (?, ?, ?, ?, 'PENDING', ?)
                    """, (f"conf_{uuid.uuid4().hex[:8]}", "graduation_batch", str(current_batch), str(found_year), file.filename))

        results.append({
            "doc_id": doc_id,
            "filename": file.filename,
            "content_hash": content_hash[:12],
            "characters_extracted": len(extracted_text),
            "facts_stored": len(ingested_facts)
        })

    return {
        "status": "success",
        "files_processed": len(results),
        "total_facts_stored": total_facts,
        "details": results
    }

@router.get("/documents")
def list_uploaded_documents():
    """FR-004: Lists uploaded document registry with provenance and fact counts."""
    conn = get_raw_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM document_records ORDER BY created_at DESC")
        return {"documents": [dict(r) for r in cursor.fetchall()]}
    finally:
        conn.close()

@router.delete("/facts/{fact_id}")
def delete_fact(fact_id: str):
    """FR-009: Removes an individual memory fact from active candidate retrieval."""
    success = memory_manager.delete_memory_fact(fact_id)
    if not success:
        raise HTTPException(status_code=404, detail="Fact not found or already deleted.")
    return {"status": "success", "deleted_fact_id": fact_id}

@router.get("/conflicts")
def get_memory_conflicts():
    """FR-008: Retrieves pending memory contradictions for user resolution."""
    conn = get_raw_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM memory_conflicts WHERE status = 'PENDING' ORDER BY created_at DESC")
        return {"conflicts": [dict(r) for r in cursor.fetchall()]}
    finally:
        conn.close()

@router.post("/conflicts/{conflict_id}/resolve")
def resolve_memory_conflict(conflict_id: str, payload: ConflictResolveRequest):
    """FR-008: Resolves a detected memory conflict."""
    with db_transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE memory_conflicts 
            SET status = 'RESOLVED', resolved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (conflict_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Conflict record not found.")
    return {"status": "resolved", "conflict_id": conflict_id, "resolved_value": payload.chosen_value}

@router.post("/chat-update")
def chat_memory_update(payload: ChatUpdateRequest):
    """FR-007: Accepts natural language updates and additively updates memory."""
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Update text cannot be empty.")

    fact = memory_manager.add_memory(
        content=text,
        user_id=payload.user_id,
        metadata={"source": "chat_update", "category": memory_manager._classify_fact_category(text)}
    )
    return {
        "status": "success",
        "message": "Fact successfully integrated into candidate memory vault.",
        "fact": fact
    }

@router.get("/all")
def get_all_memories(user_id: str = "default_user"):
    """Retrieve all candidate memories grouped by category."""
    memories = memory_manager.get_all_memories(user_id=user_id)
    return {
        "total_count": len(memories),
        "memories": memories
    }

@router.post("/search")
def search_memory(payload: SearchMemoryRequest):
    """Semantic search against candidate memory vault."""
    results = memory_manager.search_memory(
        query=payload.query,
        user_id=payload.user_id,
        limit=payload.limit or 10
    )
    return {
        "query": payload.query,
        "results_count": len(results),
        "results": results
    }
