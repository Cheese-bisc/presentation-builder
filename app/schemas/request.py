from pydantic import BaseModel
from typing import Optional


class PresentationRequest(BaseModel):
    prompt: str
    theme: Optional[str] = "corporate"


class EditRequest(BaseModel):
    session_id: str
    instruction: str  # e.g. "shorten by 2 slides", "make bullets simpler"
