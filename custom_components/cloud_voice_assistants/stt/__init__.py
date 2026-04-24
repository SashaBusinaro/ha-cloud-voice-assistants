"""STT platform for Cloud Voice Assistants."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.cloud_voice_assistants.const import SUBENTRY_TYPE_STT
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .provider import CloudVoiceAssistantsSttEntity

if TYPE_CHECKING:
    from custom_components.cloud_voice_assistants.data import CloudVoiceAssistantsConfigEntry
    from homeassistant.core import HomeAssistant


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CloudVoiceAssistantsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up STT entities from sub-entries."""
    for subentry in entry.subentries.values():
        if subentry.subentry_type == SUBENTRY_TYPE_STT:
            async_add_entities(
                [CloudVoiceAssistantsSttEntity(hass, entry, subentry)],
                config_subentry_id=subentry.subentry_id,
            )
