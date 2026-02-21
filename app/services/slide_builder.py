import json
import re
from app.models.slide_model import Slide


def _extract_json(text: str) -> str:
    """
    Strip any markdown code fences or preamble the LLM might add
    so we get a clean JSON string even if the model isn't perfectly obedient.
    """
    # Try to find a JSON array in the response
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return match.group(0)
    return text  # fall through and let json.loads raise a clear error


def build_slides(llm_output: str) -> list:
    """Parse LLM JSON output into a list of Slide objects."""
    clean = _extract_json(llm_output)
    slides_json = json.loads(clean)
    return [Slide(title=s["title"], bullets=s["bullets"]) for s in slides_json]


def slides_to_dict(slides) -> list:
    """Convert Slide objects → plain dicts for storage / JSON responses."""
    return [{"title": s.title, "bullets": s.bullets} for s in slides]


def dict_to_slides(slides_json: list) -> list:
    """Convert plain dicts → Slide objects."""
    return [Slide(title=s["title"], bullets=s["bullets"]) for s in slides_json]
