import os
import shutil
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.schemas.request import PresentationRequest, EditRequest
from app.services.prompt_parser import parse_prompt
from app.services.context_service import retrieve_context
from app.services.content_generator import generate_slide_content, edit_slide_content
from app.services.slide_builder import build_slides, slides_to_dict, dict_to_slides
from app.services.ppt_exporter import export_ppt
from app.services.session_store import (
    create_session,
    get_session,
    update_session,
    delete_session,
)
from app.services.file_service import ingest_file, SUPPORTED_EXTENSIONS
from app.services.theme_service import list_themes

app = FastAPI(title="PPT Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# 0. THEMES
# ---------------------------------------------------------------------------
@app.get("/themes")
def get_themes():
    return list_themes()


# ---------------------------------------------------------------------------
# 1. UPLOAD FILE
# session_id is required — file is scoped to this session only.
# Frontend should create a pending session_id before upload, or pass the
# session_id it already has. We use a simple query param for this.
# ---------------------------------------------------------------------------
@app.post("/upload")
async def upload_file(session_id: str, file: UploadFile = File(...)):
    filename: str = file.filename or "uploaded_file"
    ext = Path(filename).suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {SUPPORTED_EXTENSIONS}",
        )

    save_path = os.path.join(UPLOAD_DIR, filename)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Ingest scoped to this session — no global contamination
    result = ingest_file(save_path, source_name=filename, session_id=session_id)

    return JSONResponse(
        {
            "message": "File uploaded and indexed successfully.",
            "file": filename,
            "chunks_stored": result["chunks_stored"],
            "preview": result["preview"],
        }
    )


# ---------------------------------------------------------------------------
# 2. GENERATE
# ---------------------------------------------------------------------------
@app.post("/generate")
def generate_presentation(req: PresentationRequest):
    parsed = parse_prompt(req.prompt)
    theme = req.theme or "corporate"

    # Create session first so we have a session_id to scope context retrieval
    # Initialise with empty slides — updated below
    session_id = create_session([], parsed["topic"], theme)

    # Retrieve only from this session's uploaded docs
    context_chunks = retrieve_context(session_id, parsed["topic"])
    context = "\n\n".join(context_chunks)

    slides_data = generate_slide_content(parsed["topic"], parsed["slides"], context)
    slides = build_slides(slides_data)
    slides_dict = slides_to_dict(slides)

    # Update session with real slides
    update_session(session_id, slides_dict, "__init__")
    # Clear the fake __init__ history entry
    get_session(session_id)["history"] = []

    return JSONResponse(
        {
            "session_id": session_id,
            "topic": parsed["topic"],
            "slides": slides_dict,
            "theme": theme,
        }
    )


# ---------------------------------------------------------------------------
# 3. PREVIEW
# ---------------------------------------------------------------------------
@app.get("/preview/{session_id}")
def preview_presentation(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return JSONResponse(
        {
            "session_id": session_id,
            "topic": session["topic"],
            "slides": session["slides"],
            "theme": session.get("theme", "corporate"),
            "edit_history": session["history"],
        }
    )


# ---------------------------------------------------------------------------
# 4. EDIT
# ---------------------------------------------------------------------------
@app.post("/edit")
def edit_presentation(req: EditRequest):
    session = get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Context from this session's uploads only
    context_chunks = retrieve_context(req.session_id, req.instruction)
    context = "\n\n".join(context_chunks)

    updated_data = edit_slide_content(session["slides"], req.instruction, context)
    updated_slides = build_slides(updated_data)
    updated_dict = slides_to_dict(updated_slides)
    update_session(req.session_id, updated_dict, req.instruction)

    return JSONResponse(
        {
            "session_id": req.session_id,
            "topic": session["topic"],
            "slides": updated_dict,
            "theme": session.get("theme", "corporate"),
            "edit_history": session["history"],
        }
    )


# ---------------------------------------------------------------------------
# 5. DOWNLOAD
# ---------------------------------------------------------------------------
@app.get("/download/{session_id}")
def download_presentation(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    slides = dict_to_slides(session["slides"])
    theme_name: str = session.get("theme", "corporate")
    safe_topic = session["topic"].strip().replace(" ", "_")
    filename = f"{safe_topic}.pptx"
    output_path = export_ppt(slides, filename, theme_name=theme_name)

    return FileResponse(
        path=output_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=filename,
    )


# ---------------------------------------------------------------------------
# 6. DELETE SESSION — called when user hits "Start over"
# Cleans up in-memory state AND the ChromaDB collection for this session
# ---------------------------------------------------------------------------
@app.delete("/session/{session_id}")
def end_session(session_id: str):
    delete_session(session_id)
    return JSONResponse({"message": "Session cleared."})
