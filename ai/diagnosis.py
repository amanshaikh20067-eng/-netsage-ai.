"""Gemini diagnosis service.

Returns raw model text for later validation. Never fabricates a diagnosis.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai.prompts import build_messages
from config.settings import get_gemini_api_key, get_gemini_model, get_gemini_timeout_seconds


class DiagnosisServiceError(Exception):
    """Base error for the diagnosis service."""


class MissingAPIKeyError(DiagnosisServiceError):
    """Raised when GEMINI_API_KEY is not configured."""


class AIRequestError(DiagnosisServiceError):
    """Raised when the Gemini API fails. No fallback diagnosis is produced."""


class AITimeoutError(AIRequestError):
    """Raised when the Gemini request times out."""


@dataclass(frozen=True)
class RawDiagnosisResponse:
    """Unvalidated model output. Must not be treated as a final diagnosis."""

    content: str
    model: str | None = None


def _split_messages(messages: list[dict[str, str]]) -> tuple[str, str]:
    system = next((m["content"] for m in messages if m["role"] == "system"), "")
    user = next((m["content"] for m in messages if m["role"] == "user"), "")
    return system, user


def _is_timeout_error(exc: Exception) -> bool:
    name = type(exc).__name__
    return "Timeout" in name or "DeadlineExceeded" in name


def _extract_content(response: Any) -> str | None:
    text = getattr(response, "text", None)
    if text is not None:
        return str(text)
    candidates = getattr(response, "candidates", None)
    if not candidates:
        return None
    content = getattr(candidates[0], "content", None)
    parts = getattr(content, "parts", None) if content is not None else None
    if not parts:
        return None
    part_text = getattr(parts[0], "text", None)
    return str(part_text) if part_text is not None else None


class DiagnosisService:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
        client: Any = None,
    ) -> None:
        self._api_key = get_gemini_api_key() if api_key is None else api_key
        if self._api_key is not None:
            stripped = self._api_key.strip()
            self._api_key = stripped if stripped else None
        self._model_name = model if model is not None else get_gemini_model()
        self._timeout_seconds = (
            timeout_seconds if timeout_seconds is not None else get_gemini_timeout_seconds()
        )
        self._client = client

    def _require_api_key(self) -> str:
        if not self._api_key:
            raise MissingAPIKeyError(
                "GEMINI_API_KEY is not configured. Set it in the environment or .env."
            )
        return self._api_key

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        import google.generativeai as genai

        genai.configure(api_key=self._require_api_key())
        return genai

    def build_request(
        self,
        symptom: str,
        topology_notes: str,
        show_output: str,
        python_findings: Any = None,
    ) -> dict[str, Any]:
        """Return the message payload without sending it."""
        return {
            "model": self._model_name,
            "messages": build_messages(symptom, topology_notes, show_output, python_findings),
            "timeout": self._timeout_seconds,
        }

    def request_diagnosis(
        self,
        symptom: str,
        topology_notes: str,
        show_output: str,
        python_findings: Any = None,
    ) -> RawDiagnosisResponse:
        self._require_api_key()
        request = self.build_request(symptom, topology_notes, show_output, python_findings)
        system_instruction, user_content = _split_messages(request["messages"])
        client = self._get_client()

        try:
            model = client.GenerativeModel(request["model"], system_instruction=system_instruction)
            response = model.generate_content(
                user_content,
                generation_config={"temperature": 0},
                request_options={"timeout": self._timeout_seconds},
            )
        except Exception as exc:  # Gemini SDK raises several distinct exception types
            if _is_timeout_error(exc):
                raise AITimeoutError("Gemini request timed out.") from exc
            raise AIRequestError(f"Gemini request failed: {exc}") from exc

        content = _extract_content(response)
        if content is None or content.strip() == "":
            raise AIRequestError("Gemini returned an empty response.")
        return RawDiagnosisResponse(content=content, model=request["model"])