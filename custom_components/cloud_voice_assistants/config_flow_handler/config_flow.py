"""Config flow for Cloud Voice Assistants.

Implements:
- step_user: provider selection
- step_credentials: API key entry + validation
- step_reauth / step_reauth_confirm: reauthentication
- step_reconfigure: update existing API key
- async_get_supported_subentry_types: conversation + STT sub-entry flows
"""

from __future__ import annotations

from typing import Any

from custom_components.cloud_voice_assistants.const import (
    CONF_PROVIDER,
    DOMAIN,
    LOGGER,
    SUBENTRY_TYPE_CONVERSATION,
    SUBENTRY_TYPE_STT,
)
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.core import callback

from .schemas.config import PROVIDER_LABELS, get_credentials_schema, get_provider_schema
from .subentry_flow import ConversationSubentryFlow, SttSubentryFlow
from .validators.credentials import validate_api_key

_ERROR_MAP: dict[str, str] = {
    "InvalidAPIKeyError": "invalid_auth",
    "CannotConnectError": "cannot_connect",
}


class CloudVoiceAssistantsConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cloud Voice Assistants."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow handler."""
        self._provider_id: str = ""

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls,
        config_entry: config_entries.ConfigEntry,
    ) -> dict[str, type[config_entries.ConfigSubentryFlow]]:
        """Return sub-entry types supported by this integration."""
        return {
            SUBENTRY_TYPE_CONVERSATION: ConversationSubentryFlow,
            SUBENTRY_TYPE_STT: SttSubentryFlow,
        }

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Step 1: Select the cloud provider."""
        if user_input is not None:
            self._provider_id = user_input[CONF_PROVIDER]
            return await self.async_step_credentials()

        return self.async_show_form(
            step_id="user",
            data_schema=get_provider_schema(),
        )

    async def async_step_credentials(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Step 2: Enter and validate API key."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY]
            try:
                await validate_api_key(self.hass, self._provider_id, api_key)
            except Exception as exc:  # noqa: BLE001
                LOGGER.warning("API key validation failed: %s", exc)
                errors["base"] = _ERROR_MAP.get(type(exc).__name__, "unknown")
            else:
                await self.async_set_unique_id(self._provider_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=PROVIDER_LABELS.get(self._provider_id, self._provider_id),
                    data={
                        CONF_PROVIDER: self._provider_id,
                        CONF_API_KEY: api_key,
                    },
                )

        provider_label = PROVIDER_LABELS.get(self._provider_id, self._provider_id)
        return self.async_show_form(
            step_id="credentials",
            data_schema=get_credentials_schema(),
            errors=errors,
            description_placeholders={"provider": provider_label},
        )

    async def async_step_reauth(
        self,
        entry_data: dict[str, Any],
    ) -> config_entries.ConfigFlowResult:
        """Trigger reauthentication flow."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle reauthentication with a new API key."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        provider_id: str = str(entry.data[CONF_PROVIDER])

        if user_input is not None:
            api_key = user_input[CONF_API_KEY]
            try:
                await validate_api_key(self.hass, provider_id, api_key)
            except Exception as exc:  # noqa: BLE001
                LOGGER.warning("Reauth API key validation failed: %s", exc)
                errors["base"] = _ERROR_MAP.get(type(exc).__name__, "unknown")
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data={**entry.data, CONF_API_KEY: api_key},
                )

        provider_label = PROVIDER_LABELS.get(provider_id, provider_id)
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=get_credentials_schema(),
            errors=errors,
            description_placeholders={"provider": provider_label},
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle reconfiguration (update API key)."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        provider_id: str = str(entry.data[CONF_PROVIDER])

        if user_input is not None:
            api_key = user_input[CONF_API_KEY]
            try:
                await validate_api_key(self.hass, provider_id, api_key)
            except Exception as exc:  # noqa: BLE001
                LOGGER.warning("Reconfigure API key validation failed: %s", exc)
                errors["base"] = _ERROR_MAP.get(type(exc).__name__, "unknown")
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data={**entry.data, CONF_API_KEY: api_key},
                )

        provider_label = PROVIDER_LABELS.get(provider_id, provider_id)
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=get_credentials_schema(),
            errors=errors,
            description_placeholders={"provider": provider_label},
        )


__all__ = ["CloudVoiceAssistantsConfigFlowHandler"]
