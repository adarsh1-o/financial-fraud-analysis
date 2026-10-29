from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)


def gemini_api_key() -> str | None:
    value = os.getenv("GEMINI_API_KEY", "").strip()
    return value or None


def gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash"
