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
from app.services.session_store import create_session, get_session, update_session
from app.services.file_service import ingest_file, SUPPORTED_EXTENSIONS

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
# 0. UPLOAD FILE  — extract text, chunk it, store in ChromaDB
#    Call this BEFORE /generate if the user attaches a file.
#    /generate will automatically pull the stored context via retrieve_context()
# ---------------------------------------------------------------------------
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {SUPPORTED_EXTENSIONS}",
        )

    save_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    result = ingest_file(save_path, source_name=file.filename)

    return JSONResponse(
        {
            "message": "File uploaded and indexed successfully.",
            "file": file.filename,
            "chunks_stored": result["chunks_stored"],
            "preview": result["preview"],
        }
    )


# ---------------------------------------------------------------------------
# 1. GENERATE  — creates a new session and returns slide JSON for preview
# ---------------------------------------------------------------------------
@app.post("/generate")
def generate_presentation(req: PresentationRequest):
    parsed = parse_prompt(req.prompt)

    # Pulls context — includes any uploaded file content automatically
    context_chunks = retrieve_context(parsed["topic"])
    context = "\n\n".join(context_chunks)

    llm_output = generate_slide_content(parsed["topic"], parsed["slides"], context)
    slides = build_slides(llm_output)
    slides_dict = slides_to_dict(slides)
    session_id = create_session(slides_dict, parsed["topic"])

    return JSONResponse(
        {
            "session_id": session_id,
            "topic": parsed["topic"],
            "slides": slides_dict,
        }
    )


# ---------------------------------------------------------------------------
# 2. PREVIEW  — return the current slide JSON for an existing session
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
            "edit_history": session["history"],
        }
    )


# ---------------------------------------------------------------------------
# 3. EDIT  — apply a natural-language instruction and update the session
# ---------------------------------------------------------------------------
@app.post("/edit")
def edit_presentation(req: EditRequest):
    session = get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    context_chunks = retrieve_context(req.instruction)
    context = "\n\n".join(context_chunks)

    llm_output = edit_slide_content(session["slides"], req.instruction, context)
    updated_slides = build_slides(llm_output)
    updated_dict = slides_to_dict(updated_slides)
    update_session(req.session_id, updated_dict, req.instruction)

    return JSONResponse(
        {
            "session_id": req.session_id,
            "topic": session["topic"],
            "slides": updated_dict,
            "edit_history": session["history"] + [req.instruction],
        }
    )


# ---------------------------------------------------------------------------
# 4. DOWNLOAD  — export the current session state as a .pptx file
# ---------------------------------------------------------------------------
@app.get("/download/{session_id}")
def download_presentation(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    slides = dict_to_slides(session["slides"])
    safe_topic = session["topic"].strip().replace(" ", "_")
    filename = f"{safe_topic}.pptx"
    output_path = export_ppt(slides, filename)

    return FileResponse(
        path=output_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=filename,
    )
