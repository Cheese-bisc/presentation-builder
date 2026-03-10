"""
image_service.py  —  app/services/image_service.py

Fetches a relevant stock image URL from Unsplash for a given query.
Requires UNSPLASH_ACCESS_KEY in environment or config.
"""

import os
import requests
from typing import Optional

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")
UNSPLASH_URL = "https://api.unsplash.com/search/photos"


def fetch_image_url(query: str, fallback: bool = True) -> Optional[str]:
    """
    Search Unsplash for a photo matching the query.
    Returns the regular-size image URL, or None if unavailable.
    """
    if not UNSPLASH_ACCESS_KEY:
        return None

    try:
        response = requests.get(
            UNSPLASH_URL,
            params={
                "query": query,
                "per_page": 1,
                "orientation": "landscape",
            },
            headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
            timeout=5,
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        if results:
            return results[0]["urls"]["regular"]
    except Exception:
        pass

    return None


def fetch_images_for_slides(slide_titles: list[str]) -> list[Optional[str]]:
    """
    Fetch one image URL per slide title.
    Returns a list of URLs (or None for slides where fetch failed).
    """
    return [fetch_image_url(title) for title in slide_titles]
