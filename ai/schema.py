"""JSON extraction helpers for AI diagnosis output.

Only extracts and parses JSON. Does not perform field-level validation —
that is validator.py's job. Never invents or fills in missing data.
"""
from __future__ import annotations

import json
import re

_CODE_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class JSONExtractionError(Exception):
    """Raised when raw AI text cannot be parsed as JSON."""


def extract_json_object(raw_text: str) -> dict:
    """Parse raw AI text into a dict.

    Strips common Markdown code fences (```json ... ```) since models
    sometimes wrap JSON in them despite instructions not to. Does not
    attempt any other repair — malformed JSON is rejected, not guessed at.
    """
    if raw_text is None:
        raise JSONExtractionError("AI response was None; expected JSON text.")

    text = raw_text.strip()
    if text == "":
        raise JSONExtractionError("AI response was empty; expected JSON text.")

    cleaned = _CODE_FENCE.sub("", text).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise JSONExtractionError(f"AI response is not valid JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise JSONExtractionError(
            f"AI response must be a JSON object, got {type(parsed).__name__}."
        )

    return parsed