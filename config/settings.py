"""Load application settings from the environment.
Secrets are never hardcoded. Callers must not log or display secret values.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def get_gemini_api_key() -> str | None:
    """Return the Gemini API key if it is set, otherwise None."""
    value = os.getenv("GEMINI_API_KEY")
    if value is None:
        return None
    stripped = value.strip()
    if stripped == "":
        return None
    return stripped


def is_gemini_configured() -> bool:
    """Return True when a Gemini API key is present. Does not expose the key."""
    return get_gemini_api_key() is not None


def get_gemini_model() -> str:
    """Return the configured Gemini model name, defaulting to gemini-3.6-flash."""
    value = os.getenv("GEMINI_MODEL")
    return value.strip() if value and value.strip() else "gemini-3.6-flash"


def get_gemini_timeout_seconds() -> float:
    """Return the configured request timeout in seconds, defaulting to 30."""
    value = os.getenv("GEMINI_TIMEOUT_SECONDS")
    if value is None or value.strip() == "":
        return 30.0
    try:
        return float(value)
    except ValueError:
        return 30.0