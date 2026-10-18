import io
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from pypdf import PdfReader
from backend.memory.mem0_manager import memory_manager

router = APIRouter(prefix="/api/v1/memory", tags=["Core Memory Vault"])

class ChatUpdateRequest(BaseModel):
    text: str
    user_id: Optional[str] = "default_user"

class SearchMemoryRequest(BaseModel):
    query: str
    limit: Optional[int] = 10
    user_id: Optional[str] = "default_user"

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
    FR-06: Accepts multiple resumes/documents (SDE resume, AI/ML resume, project notes)
    and extracts atomic facts into Mem0 and local Qdrant/SQLite memory.
    """
    results = []
    total_facts = 0

    for file in files:
        contents = await file.read()
        extracted_text = extract_text_from_file(file.filename, contents)
        ingested_facts = memory_manager.extract_and_ingest_text(
            text=extracted_text,
            source_name=file.filename,
            user_id=user_id
        )
        total_facts += len(ingested_facts)
        results.append({
            "filename": file.filename,
            "characters_extracted": len(extracted_text),
            "facts_stored": len(ingested_facts)
        })

    return {
        "status": "success",
        "files_processed": len(results),
        "total_facts_stored": total_facts,
        "details": results
    }

@router.post("/chat-update")
def chat_memory_update(payload: ChatUpdateRequest):
    """
    FR-07: Accepts natural language updates from the student
    (e.g., 'I built a distributed KV store in Rust with 15k RPS') and additively updates Mem0.
    """
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
