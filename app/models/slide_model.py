from typing import List, Optional


class Slide:
    def __init__(
        self, title: str, bullets: List[str], image_path: Optional[str] = None
    ):
        self.title = title
        self.bullets = bullets
        self.image_path = image_path
