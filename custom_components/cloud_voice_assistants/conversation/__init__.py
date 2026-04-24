"""Conversation platform for Cloud Voice Assistants."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.cloud_voice_assistants.const import SUBENTRY_TYPE_CONVERSATION
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .agent import CloudVoiceAssistantsConversationEntity

if TYPE_CHECKING:
    from custom_components.cloud_voice_assistants.data import CloudVoiceAssistantsConfigEntry
    from homeassistant.core import HomeAssistant


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CloudVoiceAssistantsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up conversation entities from sub-entries."""
    for subentry in entry.subentries.values():
        if subentry.subentry_type == SUBENTRY_TYPE_CONVERSATION:
            async_add_entities(
                [CloudVoiceAssistantsConversationEntity(hass, entry, subentry)],
                config_subentry_id=subentry.subentry_id,
            )
