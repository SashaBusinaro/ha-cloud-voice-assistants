"""Conversation entity for Cloud Voice Assistants.

Implements the HA ConversationEntity interface using a provider-agnostic
streaming approach. Supports tool calls for device control (when a HA LLM
API is selected in options).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Literal

import aiohttp

from custom_components.cloud_voice_assistants.const import (
    CONF_MAX_TOKENS,
    CONF_MODEL,
    CONF_PROMPT,
    CONF_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DOMAIN,
    LOGGER,
    MAX_TOOL_ITERATIONS,
)
from homeassistant.components import conversation
from homeassistant.components.conversation import (
    ConversationEntity,
    ConversationEntityFeature,
    ConversationInput,
    ConversationResult,
)
from homeassistant.config_entries import ConfigSubentry
from homeassistant.const import CONF_LLM_HASS_API, MATCH_ALL
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import llm
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

if TYPE_CHECKING:
    from custom_components.cloud_voice_assistants.data import CloudVoiceAssistantsConfigEntry
    from homeassistant.core import HomeAssistant


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


class CloudVoiceAssistantsConversationEntity(ConversationEntity):
    """Conversation entity that delegates to the configured cloud provider."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supports_streaming = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: CloudVoiceAssistantsConfigEntry,
        subentry: ConfigSubentry,
    ) -> None:
        """Initialize the conversation entity."""
        self.hass = hass
        self._entry = entry
        self._subentry = subentry
        self._attr_unique_id = subentry.subentry_id
        if subentry.data.get(CONF_LLM_HASS_API):  # non-empty list → device control enabled
            self._attr_supported_features = ConversationEntityFeature.CONTROL

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return supported languages (all)."""
        return MATCH_ALL

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this entity."""
        provider = self._entry.runtime_data.provider
        return DeviceInfo(
            identifiers={(DOMAIN, self._subentry.subentry_id)},
            name=self._subentry.title,
            manufacturer=self._entry.title,
            model=self._subentry.data.get(CONF_MODEL, provider.default_chat_model),
            entry_type=DeviceEntryType.SERVICE,
        )

    async def _async_handle_message(
        self,
        user_input: ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> ConversationResult:
        """Process a conversation turn using HA's ChatLog and the configured provider."""
        opts = self._subentry.data

        try:
            await chat_log.async_provide_llm_data(
                user_input.as_llm_context(DOMAIN),
                opts.get(CONF_LLM_HASS_API),
                opts.get(CONF_PROMPT),
                user_input.extra_system_prompt,
            )
        except conversation.ConverseError as err:
            return err.as_conversation_result()

        tools: list[dict[str, Any]] | None = None
        if chat_log.llm_api:
            tools = [_format_tool(tool, chat_log.llm_api.custom_serializer) for tool in chat_log.llm_api.tools]

        data = self._entry.runtime_data
        provider = data.provider
        session = data.session
        model = opts.get(CONF_MODEL, provider.default_chat_model)
        max_tokens = int(opts.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS))
        temperature = max(0.0, min(1.0, float(opts.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE))))

        for _iteration in range(MAX_TOOL_ITERATIONS):
            messages = _convert_chat_log_to_messages(chat_log)
            try:
                async for _content in chat_log.async_add_delta_content_stream(
                    user_input.agent_id,
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
                LOGGER.exception("Unexpected error in conversation")
                raise HomeAssistantError(f"Unexpected error: {err}") from err

            if not chat_log.unresponded_tool_results:
                break

        return conversation.async_get_result_from_chat_log(user_input, chat_log)
