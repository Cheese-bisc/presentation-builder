import json
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3-coder:30b"


def _call_llm(prompt: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "prompt": prompt, "stream": False},
    )
    response.raise_for_status()
    return response.json()["response"]


def generate_slide_content(topic: str, slides: int, context: str = "") -> str:
    """Generate fresh slide content from a topic."""
    prompt = f"""
You are a professional presentation creator.

Topic: {topic}
Number of slides: {slides}

Relevant Context:
{context}

Create structured content for a presentation.

Return STRICT JSON only — no explanation, no markdown, no code fences:
[
  {{
    "title": "Slide title here",
    "bullets": ["Point one", "Point two", "Point three"]
  }}
]
"""
    return _call_llm(prompt)


def edit_slide_content(
    current_slides: list, edit_instruction: str, context: str = ""
) -> str:
    """
    Apply a natural-language edit instruction to the existing slides.
    Returns updated slides as a JSON string.
    """
    current_json = json.dumps(current_slides, indent=2)

    prompt = f"""
You are a professional presentation editor.

The user wants to modify an existing presentation.

Current slides (JSON):
{current_json}

Edit instruction:
"{edit_instruction}"

Additional context:
{context if context else "None"}

Apply the requested changes to the slides. Common edits include:
- Removing slides (e.g. "shorten by 2 slides", "remove the last slide")
- Adding slides (e.g. "add a slide about X")
- Rewriting bullets (e.g. "make bullets shorter", "use simpler language")
- Reordering slides
- Changing titles

Return STRICT JSON only — no explanation, no markdown, no code fences.
The output must be a valid JSON array in the same format as the input:
[
  {{
    "title": "Slide title here",
    "bullets": ["Point one", "Point two", "Point three"]
  }}
]
"""
    return _call_llm(prompt)
