"""Mistral cloud provider implementation, backed by the official mistralai SDK."""

from __future__ import annotations

import http
import json
from typing import TYPE_CHECKING, Any

import httpx
from homeassistant.components.conversation import AssistantContentDeltaDict
from homeassistant.helpers import llm
from mistralai.client import Mistral, errors

from custom_components.cloud_voice_assistants.const import LOGGER

from . import CannotConnectError, InvalidAPIKeyError, ProviderError
from .base import CloudProviderBase

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    import aiohttp

CHAT_MODELS: list[str] = [
    "ministral-8b-latest",
    "ministral-3b-latest",
    "mistral-small-latest",
    "mistral-large-latest",
]
STT_MODELS: list[str] = [
    "voxtral-mini-latest",
]
DEFAULT_CHAT_MODEL = "ministral-8b-latest"
DEFAULT_STT_MODEL = "voxtral-mini-latest"


class MistralProvider(CloudProviderBase):
    """
    Mistral provider implemented via the official mistralai Python SDK.

    Chat: `mistral.chat.stream_async` for plain function-calling tools, and
          `mistral.beta.conversations.start_stream_async` when a built-in
          connector tool (web_search / web_search_premium) is requested —
          /v1/chat/completions rejects connector tools.
    STT:  `mistral.audio.transcriptions.complete_async` (Voxtral).
    """

    provider_id = "mistral"
    chat_models = CHAT_MODELS
    stt_models = STT_MODELS
    default_chat_model = DEFAULT_CHAT_MODEL
    default_stt_model = DEFAULT_STT_MODEL

    def __init__(self, api_key: str) -> None:
        """Initialize the provider and its SDK client."""
        super().__init__(api_key)
        self._client = Mistral(api_key=api_key)

    async def async_close(self) -> None:
        """Close the SDK's internal httpx client."""
        await self._client.__aexit__(None, None, None)

    @staticmethod
    def _has_connectors(tools: list[dict[str, Any]] | None) -> bool:
        """Return True if any tool is a Mistral built-in connector (non-function)."""
        return bool(tools) and any(t.get("type") != "function" for t in tools)

    async def chat_stream(  # noqa: PLR0913
        self,
        session: aiohttp.ClientSession,  # noqa: ARG002 -- SDK manages its own httpx client
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[AssistantContentDeltaDict]:
        """
        Stream chat completion deltas via the mistralai SDK.

        Routes to the Conversations API when connector tools are present,
        because /v1/chat/completions rejects them with HTTP 400 (code 1800).
        """
        if self._has_connectors(tools):
            async for delta in self._chat_stream_conversations(
                messages, tools, model, temperature, max_tokens
            ):
                yield delta
            return

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        try:
            event_stream = await self._client.chat.stream_async(**kwargs)
        except errors.MistralError as err:
            LOGGER.error("Mistral chat error — model=%s: %s", model, err)
            raise self._map_sdk_error(err) from err
        except httpx.HTTPError as err:
            LOGGER.error("Mistral chat transport error — model=%s: %s", model, err)
            msg = f"Cannot connect to Mistral: {err}"
            raise CannotConnectError(msg) from err

        async with event_stream as stream:
            async for delta in self._iter_chat_events(stream):
                yield delta

    @staticmethod
    async def _iter_chat_events(  # noqa: PLR0912
        stream: Any,
    ) -> AsyncGenerator[AssistantContentDeltaDict]:
        """Translate the SDK's CompletionEvent stream into HA delta dicts."""
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

        try:
            async for event in stream:
                chunk = event.data
                if not chunk.choices:
                    continue
                choice = chunk.choices[0]
                delta = choice.delta

                if delta.content:
                    text = MistralProvider._coerce_text(delta.content)
                    if text:
                        yield AssistantContentDeltaDict(content=text)

                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index or 0
                        slot = current_tool_calls.setdefault(
                            idx,
                            {"id": "", "name": "", "arguments": ""},
                        )
                        # SDK ToolCall.id defaults to the string "null" when
                        # absent; first-write-wins prevents later chunks from
                        # clobbering a real id with the sentinel.
                        if not slot["id"] and tc_delta.id and tc_delta.id != "null":
                            slot["id"] = tc_delta.id
                        if (
                            not slot["name"]
                            and tc_delta.function
                            and tc_delta.function.name
                        ):
                            slot["name"] = tc_delta.function.name
                        args = (
                            tc_delta.function.arguments if tc_delta.function else None
                        )
                        if isinstance(args, str):
                            slot["arguments"] += args
                        elif isinstance(args, dict):
                            slot["arguments"] = json.dumps(args)

                if (
                    choice.finish_reason in ("tool_calls", "stop")
                    and current_tool_calls
                ):
                    async for item in _flush():
                        yield item
        except errors.MistralError as err:
            LOGGER.error("Mistral chat stream error: %s", err)
            raise MistralProvider._map_sdk_error(err) from err
        except httpx.HTTPError as err:
            LOGGER.error("Mistral chat stream transport error: %s", err)
            msg = f"Mistral stream interrupted: {err}"
            raise CannotConnectError(msg) from err

    async def _chat_stream_conversations(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[AssistantContentDeltaDict]:
        """Stream via the Conversations API (supports built-in connectors)."""
        instructions, inputs = self._messages_to_conversation_inputs(messages)
        kwargs: dict[str, Any] = {
            "model": model,
            "inputs": inputs,
            "completion_args": {
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        }
        if instructions:
            kwargs["instructions"] = instructions
        if tools:
            kwargs["tools"] = tools

        try:
            event_stream = await self._client.beta.conversations.start_stream_async(
                **kwargs
            )
        except errors.MistralError as err:
            LOGGER.error("Mistral conversations error — model=%s: %s", model, err)
            raise self._map_sdk_error(err) from err
        except httpx.HTTPError as err:
            LOGGER.error(
                "Mistral conversations transport error — model=%s: %s", model, err
            )
            msg = f"Cannot connect to Mistral: {err}"
            raise CannotConnectError(msg) from err

        async with event_stream as stream:
            async for delta in self._iter_conversation_events(stream):
                yield delta

    @staticmethod
    async def _iter_conversation_events(  # noqa: PLR0912
        stream: Any,
    ) -> AsyncGenerator[AssistantContentDeltaDict]:
        """Translate the SDK's ConversationEvents stream into HA delta dicts."""
        # Buffer is keyed by tool_call_id (always required on function.call.delta)
        # rather than output_index (optional) — deltas for the same call share the
        # same tool_call_id but can carry differing output_index values.
        current_tool_calls: dict[str, dict[str, str]] = {}

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

        try:
            async for event in stream:
                data = event.data
                event_type = getattr(data, "type", None)

                if event_type == "conversation.response.done":
                    async for item in _flush():
                        yield item
                    return

                if event_type == "conversation.response.error":
                    msg = f"Mistral: {getattr(data, 'message', 'unknown error')}"
                    raise CannotConnectError(msg)

                if event_type == "message.output.delta":
                    text = MistralProvider._coerce_text(getattr(data, "content", None))
                    if text:
                        yield AssistantContentDeltaDict(content=text)

                elif event_type == "function.call.delta":
                    tool_call_id = getattr(data, "tool_call_id", "") or getattr(
                        data, "id", ""
                    )
                    if not tool_call_id:
                        continue
                    slot = current_tool_calls.setdefault(
                        tool_call_id,
                        {"id": tool_call_id, "name": "", "arguments": ""},
                    )
                    name = getattr(data, "name", "")
                    if name and not slot["name"]:
                        slot["name"] = name
                    args = getattr(data, "arguments", None)
                    if isinstance(args, str):
                        slot["arguments"] += args
                    elif isinstance(args, dict):
                        slot["arguments"] = json.dumps(args)
        except errors.MistralError as err:
            LOGGER.error("Mistral conversations stream error: %s", err)
            raise MistralProvider._map_sdk_error(err) from err
        except httpx.HTTPError as err:
            LOGGER.error("Mistral conversations stream transport error: %s", err)
            msg = f"Mistral conversations stream interrupted: {err}"
            raise CannotConnectError(msg) from err

    @staticmethod
    def _messages_to_conversation_inputs(
        messages: list[dict[str, Any]],
    ) -> tuple[str | None, list[dict[str, Any]]]:
        """
        Convert OpenAI-format messages into (instructions, entries) tuple.

        System messages collapse into the `instructions` parameter.
        Other roles map to entries: user/assistant → message.{input,output},
        assistant tool_calls → function.call entries, role=tool → function.result.
        """
        instructions_parts: list[str] = []
        entries: list[dict[str, Any]] = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            if role == "system":
                if content:
                    instructions_parts.append(str(content))
            elif role == "user":
                entries.append(
                    {
                        "role": "user",
                        "content": str(content or ""),
                        "object": "entry",
                        "type": "message.input",
                    }
                )
            elif role == "assistant":
                tool_calls = msg.get("tool_calls") or []
                if content:
                    entries.append(
                        {
                            "role": "assistant",
                            "content": str(content),
                            "object": "entry",
                            "type": "message.output",
                        }
                    )
                for tc in tool_calls:
                    fn = tc.get("function", {}) or {}
                    entries.append(
                        {
                            "tool_call_id": str(tc.get("id", "")),
                            "name": str(fn.get("name", "")),
                            "arguments": fn.get("arguments", ""),
                            "object": "entry",
                            "type": "function.call",
                        }
                    )
            elif role == "tool":
                entries.append(
                    {
                        "tool_call_id": str(msg.get("tool_call_id", "")),
                        "result": str(content or ""),
                        "object": "entry",
                        "type": "function.result",
                    }
                )

        instructions = "\n\n".join(instructions_parts) if instructions_parts else None
        return instructions, entries

    @staticmethod
    def _coerce_text(content: Any) -> str:
        """Flatten a content field (str, single chunk, or list of chunks) to text."""
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(getattr(chunk, "text", "") or "" for chunk in content)
        return getattr(content, "text", "") or ""

    async def transcribe(
        self,
        session: aiohttp.ClientSession,  # noqa: ARG002 -- SDK manages its own httpx client
        wav_bytes: bytes,
        language: str | None,
        model: str,
    ) -> str:
        """Transcribe a WAV audio buffer via the Mistral Voxtral API."""
        try:
            result = await self._client.audio.transcriptions.complete_async(
                model=model,
                file={"file_name": "audio.wav", "content": wav_bytes},
                language=language,
            )
        except errors.MistralError as err:
            LOGGER.error("Mistral STT error: %s", err)
            raise self._map_sdk_error(err) from err
        except httpx.HTTPError as err:
            LOGGER.error("Mistral STT transport error: %s", err)
            msg = f"Cannot connect to Mistral: {err}"
            raise CannotConnectError(msg) from err

        text = (result.text or "").strip()
        LOGGER.debug("Mistral STT transcription: %s", text)
        return text

    async def validate_api_key(
        self,
        session: aiohttp.ClientSession,  # noqa: ARG002 -- SDK manages its own httpx client
    ) -> None:
        """Validate the API key by listing available models."""
        try:
            await self._client.models.list_async()
        except errors.MistralError as err:
            raise self._map_sdk_error(err) from err
        except httpx.HTTPError as err:
            msg = f"Cannot connect to Mistral: {err}"
            raise CannotConnectError(msg) from err

    @staticmethod
    def _map_sdk_error(err: errors.MistralError) -> ProviderError:
        """Translate a MistralError into the integration's typed exception."""
        if err.status_code == http.HTTPStatus.UNAUTHORIZED:
            return InvalidAPIKeyError(f"Invalid Mistral API key: {err.message}")
        return CannotConnectError(
            f"Mistral API error (HTTP {err.status_code}): {err.message}"
        )
