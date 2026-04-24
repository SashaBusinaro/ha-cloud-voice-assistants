"""Config flow schemas for Cloud Voice Assistants.

Schemas for:
- Provider selection (step_user)
- API key entry (step_credentials)
- Reauthentication (step_reauth_confirm)
- Reconfiguration (step_reconfigure)
"""

from __future__ import annotations

import voluptuous as vol

from custom_components.cloud_voice_assistants.const import CONF_PROVIDER, PROVIDER_GROQ, PROVIDER_MISTRAL
from homeassistant.const import CONF_API_KEY
from homeassistant.helpers import selector

PROVIDER_OPTIONS = [
    selector.SelectOptionDict(value=PROVIDER_GROQ, label="Groq"),
    selector.SelectOptionDict(value=PROVIDER_MISTRAL, label="Mistral"),
]

PROVIDER_LABELS: dict[str, str] = {
    PROVIDER_GROQ: "Groq",
    PROVIDER_MISTRAL: "Mistral",
}


def get_provider_schema() -> vol.Schema:
    """Schema for the provider selection step."""
    return vol.Schema(
        {
            vol.Required(CONF_PROVIDER): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=PROVIDER_OPTIONS,
                    mode=selector.SelectSelectorMode.LIST,
                )
            ),
        }
    )


def get_credentials_schema() -> vol.Schema:
    """Schema for the API key entry step."""
    return vol.Schema(
        {
            vol.Required(CONF_API_KEY): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.PASSWORD,
                )
            ),
        }
    )


__all__ = [
    "PROVIDER_LABELS",
    "get_credentials_schema",
    "get_provider_schema",
]
