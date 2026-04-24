"""Cloud Voice Assistants integration for Home Assistant.

Provides Conversation (LLM agent) and STT (speech-to-text) entities for
multiple AI cloud providers (Groq, Mistral AI). Each config entry creates
one ConversationEntity and one SpeechToTextEntity for the selected provider.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_PROVIDER, LOGGER
from .data import CloudVoiceAssistantsData
from .providers.registry import build_provider

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import CloudVoiceAssistantsConfigEntry

PLATFORMS: list[Platform] = [
    Platform.CONVERSATION,
    Platform.STT,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CloudVoiceAssistantsConfigEntry,
) -> bool:
    """Set up a Cloud Voice Assistants config entry."""
    provider = build_provider(
        provider_id=entry.data[CONF_PROVIDER],
        api_key=entry.data[CONF_API_KEY],
    )
    session = async_get_clientsession(hass)

    entry.runtime_data = CloudVoiceAssistantsData(provider=provider, session=session)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    LOGGER.debug("Set up Cloud Voice Assistants entry: %s", entry.entry_id)
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: CloudVoiceAssistantsConfigEntry,
) -> bool:
    """Unload a Cloud Voice Assistants config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
