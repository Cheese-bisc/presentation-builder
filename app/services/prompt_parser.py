import re


def parse_prompt(prompt: str):
    slide_match = re.search(r"(\d+)\s+slide", prompt)
    slides = int(slide_match.group(1)) if slide_match else 5

    # naive topic extraction (LLM version later)
    topic = prompt

    return {"topic": topic, "slides": slides, "raw_prompt": prompt}
