"""API key validator for config flow."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.cloud_voice_assistants.providers.registry import build_provider
from homeassistant.helpers.aiohttp_client import async_get_clientsession

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def validate_api_key(hass: HomeAssistant, provider_id: str, api_key: str) -> None:
    """Validate an API key for the given provider.

    Args:
        hass: Home Assistant instance.
        provider_id: Provider identifier (e.g. "groq" or "mistral").
        api_key: The API key to validate.

    Raises:
        InvalidAPIKeyError: If the key is rejected by the provider.
        CannotConnectError: If the provider cannot be reached.

    """
    provider = build_provider(provider_id=provider_id, api_key=api_key)
    session = async_get_clientsession(hass)
    await provider.validate_api_key(session)


__all__ = ["validate_api_key"]
