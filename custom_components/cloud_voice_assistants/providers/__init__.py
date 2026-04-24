"""Provider abstraction for Cloud Voice Assistants.

Defines the CloudProvider Protocol that all provider implementations must satisfy,
plus shared exception types. See ADR-002.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from homeassistant.components.conversation import AssistantContentDeltaDict
from homeassistant.exceptions import HomeAssistantError

if TYPE_CHECKING:
    import aiohttp


class ProviderError(HomeAssistantError):
    """Base exception for provider errors."""


class InvalidAPIKeyError(ProviderError):
    """Raised when the API key is rejected (HTTP 401)."""


class CannotConnectError(ProviderError):
    """Raised when the provider cannot be reached."""


@runtime_checkable
class CloudProvider(Protocol):
    """Contract all provider implementations must satisfy (ADR-002).

    Each provider is a self-contained class that handles authentication,
    streaming chat completions, and audio transcription. HA entities
    are provider-agnostic and call only Protocol methods.
    """

    provider_id: str
    chat_models: list[str]
    stt_models: list[str]
    default_chat_model: str
    default_stt_model: str

    def chat_stream(
        self,
        session: aiohttp.ClientSession,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[AssistantContentDeltaDict]:
        """Stream chat completion deltas.

        Yields AssistantContentDeltaDict with exactly one of:
          {"content": str}                — text content delta
          {"tool_calls": [llm.ToolInput]} — one completed tool call per yield

        Never yields both keys in the same dict.
        """
        ...

    async def transcribe(
        self,
        session: aiohttp.ClientSession,
        wav_bytes: bytes,
        language: str | None,
        model: str,
    ) -> str:
        """Transcribe a WAV audio buffer and return the transcript text."""
        ...

    async def validate_api_key(
        self,
        session: aiohttp.ClientSession,
    ) -> None:
        """Validate the stored API key against the provider's API.

        Raises:
            InvalidAPIKeyError: if the key is rejected (HTTP 401).
            CannotConnectError: if the provider cannot be reached.
        """
        ...


__all__ = [
    "CannotConnectError",
    "CloudProvider",
    "InvalidAPIKeyError",
    "ProviderError",
]
