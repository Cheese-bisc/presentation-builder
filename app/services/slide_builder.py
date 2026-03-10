"""
slide_builder.py  —  app/services/slide_builder.py

content_generator now returns a list of dicts directly.
build_slides() accepts either a list (new) or a JSON string (fallback).
"""

import json
import re
from app.models.slide_model import Slide


def _extract_json(text: str) -> list:
    fenced = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))
    array_match = re.search(r"\[.*\]", text, re.DOTALL)
    if array_match:
        return json.loads(array_match.group(0))
    return json.loads(text)


def build_slides(llm_output) -> list:
    """
    Accept either a list of dicts (from updated content_generator)
    or a raw JSON string (legacy / fallback).
    Returns a list of Slide objects.
    """
    if isinstance(llm_output, list):
        slides_json = llm_output
    else:
        slides_json = _extract_json(llm_output)

    return [Slide(title=s["title"], bullets=s["bullets"]) for s in slides_json]


def slides_to_dict(slides) -> list:
    """Slide objects → plain dicts for session storage and JSON responses."""
    return [{"title": s.title, "bullets": s.bullets} for s in slides]


def dict_to_slides(slides_json: list) -> list:
    """Plain dicts → Slide objects for export."""
    return [Slide(title=s["title"], bullets=s["bullets"]) for s in slides_json]
