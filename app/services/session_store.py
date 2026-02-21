"""
In-memory session store for slide editing workflow.
Each session holds the current slide JSON and metadata.
"""

import uuid
from typing import Optional


_sessions: dict = {}


def create_session(slides_json: list, topic: str) -> str:
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "slides": slides_json,  # list of dicts: [{title, bullets}, ...]
        "topic": topic,
        "history": [],  # list of edit prompts applied so far
    }
    return session_id


def get_session(session_id: str) -> Optional[dict]:
    return _sessions.get(session_id)


def update_session(session_id: str, slides_json: list, edit_prompt: str):
    session = _sessions.get(session_id)
    if not session:
        raise KeyError(f"Session {session_id} not found")
    session["history"].append(edit_prompt)
    session["slides"] = slides_json


def delete_session(session_id: str):
    _sessions.pop(session_id, None)
