"""Groq cloud provider implementation."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import aiohttp

from custom_components.cloud_voice_assistants.const import LOGGER
from homeassistant.components.conversation import AssistantContentDeltaDict

from . import CannotConnectError, InvalidAPIKeyError
from .base import CloudProviderBase

BASE_URL = "https://api.groq.com/openai"
CHAT_ENDPOINT = "/v1/chat/completions"
STT_ENDPOINT = "/v1/audio/transcriptions"
VALIDATE_ENDPOINT = "/v1/models"

CHAT_MODELS: list[str] = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-8b-8192",
    "gemma2-9b-it",
]
STT_MODELS: list[str] = [
    "whisper-large-v3",
    "whisper-large-v3-turbo",
    "distil-whisper-large-v3-en",
]
DEFAULT_CHAT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_STT_MODEL = "whisper-large-v3-turbo"


class GroqProvider(CloudProviderBase):
    """Groq API provider.

    Chat: OpenAI-compatible /v1/chat/completions with SSE streaming.
    STT:  OpenAI Whisper-compatible /v1/audio/transcriptions.
    """

    provider_id = "groq"
    chat_models = CHAT_MODELS
    stt_models = STT_MODELS
    default_chat_model = DEFAULT_CHAT_MODEL
    default_stt_model = DEFAULT_STT_MODEL

    async def chat_stream(
        self,
        session: aiohttp.ClientSession,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[AssistantContentDeltaDict]:
        """Stream chat completion deltas from Groq."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        async with session.post(
            f"{BASE_URL}{CHAT_ENDPOINT}",
            headers=self._get_headers(),
            json=payload,
            timeout=aiohttp.ClientTimeout(total=90),
        ) as resp:
            if resp.status != 200:
                body = await resp.text()
                LOGGER.error("Groq chat HTTP %s — model=%s body=%s", resp.status, model, body)
                raise self._map_http_error(resp.status, body)
            async for delta in self._parse_sse_stream(resp):
                yield delta

    async def transcribe(
        self,
        session: aiohttp.ClientSession,
        wav_bytes: bytes,
        language: str | None,
        model: str,
    ) -> str:
        """Transcribe a WAV audio buffer via Groq Whisper-compatible API."""
        form = aiohttp.FormData()
        form.add_field(
            "file",
            wav_bytes,
            filename="audio.wav",
            content_type="application/octet-stream",
        )
        form.add_field("model", model)
        form.add_field("response_format", "json")
        if language:
            form.add_field("language", language)

        async with session.post(
            f"{BASE_URL}{STT_ENDPOINT}",
            headers=self._get_auth_header(),
            data=form,
            timeout=aiohttp.ClientTimeout(total=60),
        ) as resp:
            if resp.status != 200:
                body = await resp.text()
                LOGGER.error("Groq STT HTTP %s: %s", resp.status, body)
                raise self._map_http_error(resp.status, body)
            result = await resp.json()

        text = result.get("text", "").strip()
        LOGGER.debug("Groq STT transcription: %s", text)
        return text

    async def validate_api_key(self, session: aiohttp.ClientSession) -> None:
        """Validate the API key by calling the models list endpoint."""
        try:
            async with session.get(
                f"{BASE_URL}{VALIDATE_ENDPOINT}",
                headers=self._get_auth_header(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 401:
                    raise InvalidAPIKeyError("Invalid Groq API key")
                if resp.status != 200:
                    body = await resp.text()
                    raise CannotConnectError(f"Groq API returned HTTP {resp.status}: {body}")
        except (aiohttp.ClientError, TimeoutError) as err:
            raise CannotConnectError(f"Cannot connect to Groq: {err}") from err
