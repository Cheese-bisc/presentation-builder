"""
file_service.py  —  app/services/file_service.py

Extracts text from uploaded files and stores chunks scoped to a session.
"""

import uuid
import pdfplumber
import docx
from pathlib import Path
from app.services.context_service import add_documents

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------


def extract_text_from_pdf(file_path: str) -> str:
    text = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return "\n\n".join(text)


def extract_text_from_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())


def extract_text_from_txt(file_path: str) -> str:
    return Path(file_path).read_text(encoding="utf-8")


def extract_text(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext == ".txt":
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        chunk = " ".join(words[start : start + chunk_size])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


# ---------------------------------------------------------------------------
# Ingest — scoped to a session_id
# ---------------------------------------------------------------------------


def ingest_file(file_path: str, source_name: str, session_id: str) -> dict:
    """
    Extract, chunk, embed and store file content scoped to session_id.
    Only this session can retrieve these chunks.
    """
    text = extract_text(file_path)
    chunks = chunk_text(text)

    if not chunks:
        raise ValueError("No text could be extracted from the file.")

    ids = [f"{session_id}_{i}_{uuid.uuid4().hex[:6]}" for i in range(len(chunks))]
    metadatas = [{"source": source_name, "chunk_index": i} for i in range(len(chunks))]

    add_documents(
        session_id=session_id,
        documents=chunks,
        metadata=metadatas,
        ids=ids,
    )

    return {
        "source": source_name,
        "chunks_stored": len(chunks),
        "preview": chunks[0][:200] + "..." if len(chunks[0]) > 200 else chunks[0],
    }
