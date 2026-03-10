# app/services/theme_service.py

from pptx.util import Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

THEMES = {
    "corporate": {
        "label": "Corporate",
        "bg": RGBColor(0xFF, 0xFF, 0xFF),
        "title_color": RGBColor(0x1A, 0x1A, 0x2E),
        "bullet_color": RGBColor(0x33, 0x33, 0x55),
        "accent": RGBColor(0x00, 0x5B, 0xFF),
        "title_font": "Calibri",
        "body_font": "Calibri",
        "title_size": Pt(32),
        "body_size": Pt(18),
    },
    "dark": {
        "label": "Dark",
        "bg": RGBColor(0x0C, 0x0C, 0x0E),
        "title_color": RGBColor(0xE8, 0xC5, 0x47),
        "bullet_color": RGBColor(0xA8, 0xA8, 0xB8),
        "accent": RGBColor(0x5B, 0x8A, 0xF0),
        "title_font": "Georgia",
        "body_font": "Arial",
        "title_size": Pt(34),
        "body_size": Pt(17),
    },
    "minimal": {
        "label": "Minimal",
        "bg": RGBColor(0xFA, 0xFA, 0xF8),
        "title_color": RGBColor(0x11, 0x11, 0x11),
        "bullet_color": RGBColor(0x44, 0x44, 0x44),
        "accent": RGBColor(0x11, 0x11, 0x11),
        "title_font": "Georgia",
        "body_font": "Helvetica Neue",
        "title_size": Pt(36),
        "body_size": Pt(16),
    },
    "vibrant": {
        "label": "Vibrant",
        "bg": RGBColor(0x6C, 0x63, 0xFF),
        "title_color": RGBColor(0xFF, 0xFF, 0xFF),
        "bullet_color": RGBColor(0xE0, 0xDD, 0xFF),
        "accent": RGBColor(0xFF, 0xD7, 0x00),
        "title_font": "Trebuchet MS",
        "body_font": "Trebuchet MS",
        "title_size": Pt(34),
        "body_size": Pt(17),
    },
    "nature": {
        "label": "Nature",
        "bg": RGBColor(0xF0, 0xF7, 0xEE),
        "title_color": RGBColor(0x2D, 0x6A, 0x4F),
        "bullet_color": RGBColor(0x1B, 0x40, 0x32),
        "accent": RGBColor(0x52, 0xB7, 0x88),
        "title_font": "Georgia",
        "body_font": "Arial",
        "title_size": Pt(33),
        "body_size": Pt(17),
    },
}


def get_theme(name: str) -> dict:
    return THEMES.get(name, THEMES["corporate"])


def list_themes() -> list:
    return [{"id": k, "label": v["label"]} for k, v in THEMES.items()]
