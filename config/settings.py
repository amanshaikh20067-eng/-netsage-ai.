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


DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OPENAI_TIMEOUT_SECONDS = 30.0


def get_openai_model() -> str:
    """Return the configured OpenAI model name. This is not a secret."""
    value = os.getenv("OPENAI_MODEL")
    if value is None:
        return DEFAULT_OPENAI_MODEL
    stripped = value.strip()
    if stripped == "":
        return DEFAULT_OPENAI_MODEL
    return stripped


def get_openai_timeout_seconds() -> float:
    """Return the OpenAI request timeout in seconds."""
    value = os.getenv("OPENAI_TIMEOUT_SECONDS")
    if value is None or value.strip() == "":
        return DEFAULT_OPENAI_TIMEOUT_SECONDS
    try:
        timeout = float(value)
    except ValueError:
        return DEFAULT_OPENAI_TIMEOUT_SECONDS
    if timeout <= 0:
        return DEFAULT_OPENAI_TIMEOUT_SECONDS
    return timeout
