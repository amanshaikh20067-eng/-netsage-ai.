"""Load application settings from the environment.

Secrets are never hardcoded. Callers must not log or display secret values.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def get_openai_api_key() -> str | None:
    """Return the OpenAI API key if it is set, otherwise None."""
    value = os.getenv("OPENAI_API_KEY")
    if value is None:
        return None
    stripped = value.strip()
    if stripped == "":
        return None
    return stripped


def is_openai_configured() -> bool:
    """Return True when an OpenAI API key is present. Does not expose the key."""
    return get_openai_api_key() is not None
