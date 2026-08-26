"""OpenAI diagnosis service.

Returns raw model text for later validation. Never fabricates a diagnosis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from openai import APIError, APITimeoutError, OpenAI, OpenAIError

from ai.prompts import build_messages
from config.settings import (
    get_openai_api_key,
    get_openai_model,
    get_openai_timeout_seconds,
)


class DiagnosisServiceError(Exception):
    """Base error for the diagnosis service."""


class MissingAPIKeyError(DiagnosisServiceError):
    """Raised when OPENAI_API_KEY is not configured."""


class AIRequestError(DiagnosisServiceError):
    """Raised when the OpenAI API fails. No fallback diagnosis is produced."""


class AITimeoutError(AIRequestError):
    """Raised when the OpenAI request times out."""


@dataclass(frozen=True)
class RawDiagnosisResponse:
    """Unvalidated model output. Must not be treated as a final diagnosis."""

    content: str
    model: str | None = None


class DiagnosisService:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
        client: Any = None,
    ) -> None:
        self._api_key = get_openai_api_key() if api_key is None else api_key
        if self._api_key is not None:
            stripped = self._api_key.strip()
            self._api_key = stripped if stripped else None
        self._model = model if model is not None else get_openai_model()
        self._timeout_seconds = (
            timeout_seconds if timeout_seconds is not None else get_openai_timeout_seconds()
        )
        self._client = client

    def _require_api_key(self) -> str:
        if not self._api_key:
            raise MissingAPIKeyError(
                "OPENAI_API_KEY is not configured. Set it in the environment or .env."
            )
        return self._api_key

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        return OpenAI(api_key=self._require_api_key(), timeout=self._timeout_seconds)

    def build_request(
        self,
        symptom: str,
        topology_notes: str,
        show_output: str,
        python_findings: Any = None,
    ) -> dict[str, Any]:
        """Return the OpenAI chat payload without sending it."""
        return {
            "model": self._model,
            "messages": build_messages(
                symptom,
                topology_notes,
                show_output,
                python_findings,
            ),
            "temperature": 0,
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
        request = self.build_request(
            symptom,
            topology_notes,
            show_output,
            python_findings,
        )
        client = self._get_client()
        try:
            response = client.chat.completions.create(
                model=request["model"],
                messages=request["messages"],
                temperature=request["temperature"],
            )
        except APITimeoutError as exc:
            raise AITimeoutError("OpenAI request timed out.") from exc
        except APIError as exc:
            raise AIRequestError(f"OpenAI API error: {exc}") from exc
        except OpenAIError as exc:
            raise AIRequestError(f"OpenAI request failed: {exc}") from exc

        content = _extract_content(response)
        if content is None or content.strip() == "":
            raise AIRequestError("OpenAI returned an empty response.")
        model_name = getattr(response, "model", None)
        return RawDiagnosisResponse(content=content, model=model_name)


def _extract_content(response: Any) -> str | None:
    choices = getattr(response, "choices", None)
    if not choices:
        return None
    message = getattr(choices[0], "message", None)
    if message is None:
        return None
    content = getattr(message, "content", None)
    if content is None:
        return None
    return str(content)
