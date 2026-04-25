"""Shared helpers for LLM conversation and AI task entities."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import aiohttp

from custom_components.cloud_voice_assistants.const import LOGGER, MAX_TOOL_ITERATIONS
from homeassistant.components import conversation
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import llm

if TYPE_CHECKING:
    from custom_components.cloud_voice_assistants.providers import CloudProvider


def _sanitize(obj: Any) -> Any:
    """Recursively make an object fully JSON-serializable."""
    if isinstance(obj, dict):
        return {str(k): _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(i) for i in obj]
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    return repr(obj)


def _format_tool(tool: llm.Tool, custom_serializer: Any = None) -> dict[str, Any]:
    """Convert a HA LLM tool to OpenAI function-calling format."""
    try:
        from voluptuous_openapi import convert  # noqa: PLC0415

        parameters = convert(tool.parameters, custom_serializer=custom_serializer)
    except Exception:  # noqa: BLE001
        LOGGER.debug(
            "Could not serialize tool parameters for '%s', using empty schema",
            tool.name,
        )
        parameters = {"type": "object", "properties": {}}

    return {
        "type": "function",
        "function": {
            "name": str(tool.name),
            "description": str(tool.description or ""),
            "parameters": parameters,
        },
    }


def _convert_chat_log_to_messages(
    chat_log: conversation.ChatLog,
) -> list[dict[str, Any]]:
    """Convert HA ChatLog content into OpenAI-compatible messages list."""
    messages: list[dict[str, Any]] = []

    tool_results: dict[str, conversation.ToolResultContent] = {
        c.tool_call_id: c for c in chat_log.content if isinstance(c, conversation.ToolResultContent)
    }

    for content in chat_log.content:
        if isinstance(content, conversation.SystemContent):
            messages.append({"role": "system", "content": str(content.content)})

        elif isinstance(content, conversation.UserContent):
            messages.append({"role": "user", "content": str(content.content)})

        elif isinstance(content, conversation.AssistantContent):
            if content.tool_calls:
                all_have_results = all(tc.id in tool_results for tc in content.tool_calls)
                if not all_have_results:
                    if content.content:
                        messages.append({"role": "assistant", "content": str(content.content)})
                    continue

                msg: dict[str, Any] = {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": str(tc.id),
                            "type": "function",
                            "function": {
                                "name": str(tc.tool_name),
                                "arguments": json.dumps(
                                    _sanitize(tc.tool_args) if isinstance(tc.tool_args, dict) else tc.tool_args
                                ),
                            },
                        }
                        for tc in content.tool_calls
                    ],
                }
                messages.append(msg)

                messages.extend(
                    {
                        "role": "tool",
                        "tool_call_id": str(res.tool_call_id),
                        "name": str(res.tool_name),
                        "content": json.dumps(
                            _sanitize(res.tool_result) if isinstance(res.tool_result, (dict, list)) else res.tool_result
                        ),
                    }
                    for tc in content.tool_calls
                    if (res := tool_results.get(tc.id))
                )
            else:
                messages.append({"role": "assistant", "content": str(content.content or "")})

    return messages


async def async_run_llm_loop(
    chat_log: conversation.ChatLog,
    provider: CloudProvider,
    session: aiohttp.ClientSession,
    agent_id: str,
    model: str,
    temperature: float,
    max_tokens: int,
    max_iterations: int = MAX_TOOL_ITERATIONS,
) -> None:
    """Run the LLM tool-call loop, consuming deltas into chat_log.

    Shared by both the conversation and AI task entities.

    Raises:
        HomeAssistantError: on provider errors or unexpected exceptions.
    """
    tools: list[dict[str, Any]] | None = None
    if chat_log.llm_api:
        tools = [_format_tool(tool, chat_log.llm_api.custom_serializer) for tool in chat_log.llm_api.tools]

    for _iteration in range(max_iterations):
        messages = _convert_chat_log_to_messages(chat_log)
        try:
            async for _content in chat_log.async_add_delta_content_stream(
                agent_id,
                provider.chat_stream(
                    session=session,
                    messages=messages,
                    tools=tools,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ),
            ):
                pass
        except HomeAssistantError:
            raise
        except aiohttp.ClientError as err:
            LOGGER.error("Provider request failed: %s", err)
            raise HomeAssistantError(f"Cannot reach provider: {err}") from err
        except Exception as err:
            LOGGER.exception("Unexpected error in LLM loop")
            raise HomeAssistantError(f"Unexpected error: {err}") from err

        if not chat_log.unresponded_tool_results:
            break


__all__ = ["async_run_llm_loop"]
