"""Conversation entity for Cloud Voice Assistants.

Implements the HA ConversationEntity interface using a provider-agnostic
streaming approach. Supports tool calls for device control (when a HA LLM
API is selected in options).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from custom_components.cloud_voice_assistants.const import (
    CONF_MAX_TOKENS,
    CONF_MODEL,
    CONF_PROMPT,
    CONF_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DOMAIN,
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
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .helpers import async_run_llm_loop

if TYPE_CHECKING:
    from custom_components.cloud_voice_assistants.data import CloudVoiceAssistantsConfigEntry
    from homeassistant.core import HomeAssistant


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
        if subentry.data.get(CONF_LLM_HASS_API):
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

        data = self._entry.runtime_data
        provider = data.provider
        model = opts.get(CONF_MODEL, provider.default_chat_model)
        max_tokens = int(opts.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS))
        temperature = max(0.0, min(1.0, float(opts.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE))))

        await async_run_llm_loop(
            chat_log=chat_log,
            provider=provider,
            session=data.session,
            agent_id=user_input.agent_id,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            max_iterations=MAX_TOOL_ITERATIONS,
        )

        return conversation.async_get_result_from_chat_log(user_input, chat_log)
