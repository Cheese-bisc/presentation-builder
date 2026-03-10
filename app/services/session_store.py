"""
session_store.py  —  app/services/session_store.py

In-memory session store. Each session is fully isolated —
its own slides, topic, theme, edit history, and ChromaDB collection.
"""

import uuid
from typing import Optional
from app.services.context_service import delete_session_context


_sessions: dict = {}


def create_session(slides_json: list, topic: str, theme: str = "corporate") -> str:
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "slides": slides_json,
        "topic": topic,
        "theme": theme,
        "history": [],
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
    """
    Full cleanup — removes in-memory state AND the ChromaDB collection
    so uploaded file context doesn't leak into future sessions.
    """
    if session_id in _sessions:
        del _sessions[session_id]
    delete_session_context(session_id)
