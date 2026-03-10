"""
content_generator.py  —  app/services/content_generator.py

Loads Qwen2.5-1.5B-Instruct once at startup and runs inference locally.
No Ollama, no external API calls.
"""

import json
import re
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"

# ---------------------------------------------------------------------------
# Singleton — model and tokenizer load ONCE when the module is first imported.
# Subsequent calls reuse the same loaded model in memory.
# ---------------------------------------------------------------------------

print(f"[DECKforge] Loading model {MODEL_ID} ...")

_tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

_model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16,  # float16 saves VRAM vs float32, no quality loss
    device_map="auto",  # automatically places on available GPU(s)
)

_model.eval()
print("[DECKforge] Model loaded and ready.")


# ---------------------------------------------------------------------------
# Core inference helper
# ---------------------------------------------------------------------------


def _call_model(
    system_prompt: str, user_prompt: str, max_new_tokens: int = 1024
) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    text = _tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = _tokenizer([text], return_tensors="pt").to(_model.device)

    with torch.no_grad():
        output_ids = _model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,  # greedy decoding — most deterministic, best for JSON
            temperature=None,  # must be None when do_sample=False
            top_p=None,  # must be None when do_sample=False
            repetition_penalty=1.1,
            pad_token_id=_tokenizer.eos_token_id,
        )

    # Strip input tokens from output — only decode what the model generated
    generated_ids = output_ids[0][inputs.input_ids.shape[1] :]
    return _tokenizer.decode(generated_ids, skip_special_tokens=True).strip()


# ---------------------------------------------------------------------------
# JSON extraction — handles markdown fences, preamble, minor formatting issues
# ---------------------------------------------------------------------------


def _extract_json(text: str) -> list:
    # 1. Markdown code fence: ```json [...] ```
    fenced = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    # 2. Raw JSON array anywhere in the response
    array_match = re.search(r"\[.*\]", text, re.DOTALL)
    if array_match:
        return json.loads(array_match.group(0))

    # 3. Last resort — try the whole response
    return json.loads(text)


# ---------------------------------------------------------------------------
# System prompts — tightly constrain output format
# ---------------------------------------------------------------------------

SYSTEM_GENERATE = (
    "You are a professional presentation creator. "
    "Your only output is a valid JSON array. No explanation, no markdown, no code fences. "
    'Each element has exactly two keys: "title" (string) and "bullets" (array of 3-5 strings). '
    "Never output anything outside the JSON array."
)

SYSTEM_EDIT = (
    "You are a professional presentation editor. "
    "Your only output is a valid JSON array. No explanation, no markdown, no code fences. "
    'Each element has exactly two keys: "title" (string) and "bullets" (array of 3-5 strings). '
    "Apply the requested changes precisely. Never output anything outside the JSON array."
)


# ---------------------------------------------------------------------------
# Public API — called by main.py endpoints
# NOTE -  now returns list directly, not a raw string.
#       slide_builder.build_slides() updated accordingly below.
# ---------------------------------------------------------------------------


def generate_slide_content(topic: str, slides: int, context: str = "") -> list:
    """Generate fresh slide content. Returns [{title, bullets}, ...]"""
    user_prompt = (
        f"Topic: {topic}\n"
        f"Number of slides: {slides}\n\n"
        f"Relevant context:\n{context if context else 'None'}\n\n"
        f"Return a JSON array with exactly {slides} slide objects."
    )
    raw = _call_model(SYSTEM_GENERATE, user_prompt)
    return _extract_json(raw)


def edit_slide_content(
    current_slides: list, instruction: str, context: str = ""
) -> list:
    """Apply an edit instruction to existing slides. Returns [{title, bullets}, ...]"""
    user_prompt = (
        f"Current slides:\n{json.dumps(current_slides, indent=2)}\n\n"
        f"Edit instruction: {instruction}\n\n"
        f"Additional context:\n{context if context else 'None'}\n\n"
        "Return the complete updated JSON array."
    )
    raw = _call_model(SYSTEM_EDIT, user_prompt, max_new_tokens=1500)
    return _extract_json(raw)
