"""AI Task platform for Cloud Voice Assistants."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from homeassistant.components import ai_task, conversation
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from custom_components.cloud_voice_assistants.const import (
    CONF_MAX_TOKENS,
    CONF_MODEL,
    CONF_TEMPERATURE,
    DEFAULT_AI_TASK_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DOMAIN,
    LOGGER,
    SUBENTRY_TYPE_AI_TASK,
)
from custom_components.cloud_voice_assistants.conversation.helpers import async_run_llm_loop

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigSubentry
    from homeassistant.core import HomeAssistant

    from custom_components.cloud_voice_assistants.data import CloudVoiceAssistantsConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CloudVoiceAssistantsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up AI Task entities for all ai_task_data sub-entries."""
    for subentry in entry.subentries.values():
        if subentry.subentry_type == SUBENTRY_TYPE_AI_TASK:
            async_add_entities(
                [CloudVoiceAssistantsAiTaskEntity(hass, entry, subentry)],
                config_subentry_id=subentry.subentry_id,
            )


class CloudVoiceAssistantsAiTaskEntity(ai_task.AITaskEntity):
    """AI Task entity for Cloud Voice Assistants."""

    _attr_supported_features = ai_task.AITaskEntityFeature.GENERATE_DATA
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        hass: HomeAssistant,
        entry: CloudVoiceAssistantsConfigEntry,
        subentry: ConfigSubentry,
    ) -> None:
        """Initialize the AI Task entity."""
        self.hass = hass
        self._entry = entry
        self._subentry = subentry
        self._attr_unique_id = subentry.subentry_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this AI task entity."""
        provider = self._entry.runtime_data.provider
        return DeviceInfo(
            identifiers={(DOMAIN, self._subentry.subentry_id)},
            name=self._subentry.title,
            manufacturer=self._entry.title,
            model=self._subentry.data.get(CONF_MODEL, provider.default_chat_model),
            entry_type=DeviceEntryType.SERVICE,
        )

    async def _async_generate_data(
        self,
        task: ai_task.GenDataTask,
        chat_log: conversation.ChatLog,
    ) -> ai_task.GenDataTaskResult:
        """Generate structured or unstructured data using the provider's LLM."""
        opts = self._subentry.data
        data = self._entry.runtime_data
        provider = data.provider

        model = opts.get(CONF_MODEL, provider.default_chat_model)
        max_tokens = int(opts.get(CONF_MAX_TOKENS, DEFAULT_AI_TASK_MAX_TOKENS))
        temperature = max(0.0, min(1.0, float(opts.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE))))

        await async_run_llm_loop(
            chat_log=chat_log,
            provider=provider,
            session=data.session,
            agent_id=self.entity_id,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            max_iterations=1000,
        )

        # Extract the final assistant response
        result_text = ""
        for content in reversed(chat_log.content):
            if isinstance(content, conversation.AssistantContent) and content.content:
                result_text = str(content.content)
                break

        if not task.structure:
            return ai_task.GenDataTaskResult(
                conversation_id=chat_log.conversation_id,
                data=result_text,
            )

        try:
            data_out = json.loads(result_text)
        except json.JSONDecodeError as err:
            LOGGER.error(
                "AI task did not return valid JSON: %s. Response: %s",
                err,
                result_text,
            )
            raise HomeAssistantError("Provider did not return valid JSON") from err

        return ai_task.GenDataTaskResult(
            conversation_id=chat_log.conversation_id,
            data=data_out,
        )
