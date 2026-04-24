"""Base class with shared helpers for all cloud providers.

Implements:
- SSE stream parser (OpenAI-compatible format) — ADR-004
- PCM→WAV conversion helper
- HTTP error mapping to typed exceptions
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
import io
import json
import wave

import aiohttp

from homeassistant.components.conversation import AssistantContentDeltaDict
from homeassistant.helpers import llm

from . import CannotConnectError, InvalidAPIKeyError, ProviderError


class CloudProviderBase:
    """Shared implementation helpers for cloud providers.

    Concrete providers inherit from this class and set BASE_URL,
    CHAT_ENDPOINT, STT_ENDPOINT, VALIDATE_ENDPOINT, plus the list
    and default constants. They must implement chat_stream, transcribe,
    and validate_api_key using the helpers here.
    """

    def __init__(self, api_key: str) -> None:
        """Initialize the provider with the given API key."""
        self._api_key = api_key

    def _get_headers(self) -> dict[str, str]:
        """Return JSON API request headers with Bearer auth."""
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _get_auth_header(self) -> dict[str, str]:
        """Return auth-only header (for multipart requests)."""
        return {"Authorization": f"Bearer {self._api_key}"}

    async def _parse_sse_stream(
        self,
        resp: aiohttp.ClientResponse,
    ) -> AsyncGenerator[AssistantContentDeltaDict]:
        r"""Parse an OpenAI-compatible SSE stream.

        Yields exactly one of per iteration:
          {"content": str}                — text content delta
          {"tool_calls": [llm.ToolInput]} — one completed tool call

        Never yields both keys in the same dict. HA's
        chat_log.async_add_delta_content_stream() requires this invariant.

        Implementation follows ADR-004: buffers resp.content.iter_any(),
        splits on \n\n SSE frame boundaries, accumulates streaming tool-call
        fragments, flushes on finish_reason or [DONE].
        """
        buffer = b""
        current_tool_calls: dict[int, dict[str, str]] = {}

        async def _flush() -> AsyncGenerator[AssistantContentDeltaDict]:
            for tc in current_tool_calls.values():
                try:
                    args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                except json.JSONDecodeError:
                    args = {}
                yield AssistantContentDeltaDict(
                    tool_calls=[
                        llm.ToolInput(
                            id=tc["id"],
                            tool_name=tc["name"],
                            tool_args=args,
                        )
                    ]
                )
            current_tool_calls.clear()

        async for raw_chunk in resp.content.iter_any():
            buffer += raw_chunk
            while b"\n\n" in buffer:
                frame, buffer = buffer.split(b"\n\n", 1)
                for line in frame.split(b"\n"):
                    line_str = line.decode("utf-8", errors="replace")
                    if not line_str.startswith("data: "):
                        continue
                    data_str = line_str[6:]
                    if data_str.strip() == "[DONE]":
                        async for item in _flush():
                            yield item
                        return
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    choice = data.get("choices", [{}])[0]
                    delta = choice.get("delta", {})

                    if delta.get("content"):
                        yield AssistantContentDeltaDict(content=str(delta["content"]))

                    if delta.get("tool_calls"):
                        for tc_delta in delta["tool_calls"]:
                            idx = tc_delta.get("index", 0)
                            if idx not in current_tool_calls:
                                current_tool_calls[idx] = {
                                    "id": tc_delta.get("id", ""),
                                    "name": tc_delta.get("function", {}).get("name", ""),
                                    "arguments": "",
                                }
                            else:
                                if tc_delta.get("id"):
                                    current_tool_calls[idx]["id"] = tc_delta["id"]
                                if tc_delta.get("function", {}).get("name"):
                                    current_tool_calls[idx]["name"] = tc_delta["function"]["name"]
                            if tc_delta.get("function", {}).get("arguments"):
                                current_tool_calls[idx]["arguments"] += tc_delta["function"]["arguments"]

                    if choice.get("finish_reason") in ("tool_calls", "stop") and current_tool_calls:
                        async for item in _flush():
                            yield item

    @staticmethod
    def pcm_to_wav(
        pcm_data: bytes,
        sample_rate: int,
        channels: int,
        sample_width: int,
    ) -> bytes:
        """Wrap raw PCM bytes in a RIFF/WAV container."""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_data)
        return buf.getvalue()

    @staticmethod
    def _map_http_error(status: int, body: str) -> ProviderError:
        """Map an HTTP error status to a typed ProviderError."""
        if status == 401:
            return InvalidAPIKeyError(f"Invalid API key (HTTP 401): {body}")
        return CannotConnectError(f"Provider API error (HTTP {status}): {body}")
