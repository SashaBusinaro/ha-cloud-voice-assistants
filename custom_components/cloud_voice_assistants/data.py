"""Custom types for cloud_voice_assistants."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import aiohttp

    from homeassistant.config_entries import ConfigEntry

    from .providers import CloudProvider


type CloudVoiceAssistantsConfigEntry = ConfigEntry[CloudVoiceAssistantsData]


@dataclass
class CloudVoiceAssistantsData:
    """Runtime data for a cloud_voice_assistants config entry.

    Stored as entry.runtime_data after successful async_setup_entry.
    """

    provider: CloudProvider
    session: aiohttp.ClientSession
