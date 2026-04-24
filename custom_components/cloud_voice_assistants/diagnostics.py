"""Diagnostics support for Cloud Voice Assistants.

Redacts the API key so it never appears in downloaded diagnostics.
https://developers.home-assistant.io/docs/core/integration_diagnostics
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.const import CONF_API_KEY
from homeassistant.helpers.redact import async_redact_data

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import CloudVoiceAssistantsConfigEntry

TO_REDACT: set[str] = {CONF_API_KEY}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: CloudVoiceAssistantsConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    provider = entry.runtime_data.provider

    subentries = [
        {
            "subentry_id": subentry.subentry_id,
            "subentry_type": subentry.subentry_type,
            "title": subentry.title,
            "data": dict(subentry.data),
        }
        for subentry in entry.subentries.values()
    ]

    return {
        "entry": {
            "entry_id": entry.entry_id,
            "title": entry.title,
            "unique_id": entry.unique_id,
            "state": str(entry.state),
            "data": async_redact_data(dict(entry.data), TO_REDACT),
        },
        "provider": {
            "provider_id": provider.provider_id,
            "chat_models": provider.chat_models,
            "stt_models": provider.stt_models,
        },
        "subentries": subentries,
    }
