"""Sub-entry flows for Cloud Voice Assistants.

Each sub-entry represents one assistant endpoint:
- ConversationSubentryFlow: a chat/LLM model (creates a ConversationEntity)
- SttSubentryFlow: a speech-to-text model (creates a SpeechToTextEntity)
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from custom_components.cloud_voice_assistants.const import (
    CONF_MAX_TOKENS,
    CONF_MODEL,
    CONF_PROMPT,
    CONF_PROVIDER,
    CONF_STT_MODEL,
    CONF_TEMPERATURE,
    DEFAULT_AI_TASK_MAX_TOKENS,
    DEFAULT_MAX_TOKENS,
    DEFAULT_PROMPT,
    DEFAULT_TEMPERATURE,
    LOGGER,
    PROVIDER_GROQ,
    PROVIDER_MISTRAL,
)
from custom_components.cloud_voice_assistants.providers.groq import (
    CHAT_MODELS as GROQ_CHAT_MODELS,
    STT_MODELS as GROQ_STT_MODELS,
)
from custom_components.cloud_voice_assistants.providers.mistral import (
    CHAT_MODELS as MISTRAL_CHAT_MODELS,
    STT_MODELS as MISTRAL_STT_MODELS,
)
from homeassistant import config_entries
from homeassistant.const import CONF_LLM_HASS_API
from homeassistant.helpers import llm, selector

_CHAT_MODELS_BY_PROVIDER: dict[str, list[str]] = {
    PROVIDER_GROQ: GROQ_CHAT_MODELS,
    PROVIDER_MISTRAL: MISTRAL_CHAT_MODELS,
}

_STT_MODELS_BY_PROVIDER: dict[str, list[str]] = {
    PROVIDER_GROQ: GROQ_STT_MODELS,
    PROVIDER_MISTRAL: MISTRAL_STT_MODELS,
}


def _get_conversation_schema(
    chat_models: list[str],
    hass_apis: list[selector.SelectOptionDict],
    defaults: dict[str, Any],
) -> vol.Schema:
    """Build the schema for the conversation sub-entry form."""
    return vol.Schema(
        {
            vol.Required(CONF_MODEL, default=defaults.get(CONF_MODEL, chat_models[0])): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=chat_models,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(CONF_PROMPT, default=defaults.get(CONF_PROMPT, DEFAULT_PROMPT)): selector.TemplateSelector(),
            vol.Optional(CONF_LLM_HASS_API, default=defaults.get(CONF_LLM_HASS_API, [])): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=hass_apis,
                    multiple=True,
                )
            ),
            vol.Optional(
                CONF_TEMPERATURE,
                default=defaults.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0.0,
                    max=1.0,
                    step=0.05,
                    mode=selector.NumberSelectorMode.SLIDER,
                )
            ),
            vol.Optional(
                CONF_MAX_TOKENS,
                default=defaults.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=64,
                    max=8192,
                    step=64,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
        }
    )


def _get_stt_schema(
    stt_models: list[str],
    defaults: dict[str, Any],
) -> vol.Schema:
    """Build the schema for the STT sub-entry form."""
    return vol.Schema(
        {
            vol.Required(
                CONF_STT_MODEL,
                default=defaults.get(CONF_STT_MODEL, stt_models[0]),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=stt_models,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        }
    )


def _clean_conversation_data(data: dict[str, Any]) -> dict[str, Any]:
    """Remove empty LLM HASS API list and ensure numeric types."""
    result = dict(data)
    # CONF_LLM_HASS_API is stored as a list; remove key when empty
    llm_apis = result.get(CONF_LLM_HASS_API)
    if not llm_apis:
        result.pop(CONF_LLM_HASS_API, None)
    result[CONF_TEMPERATURE] = float(result.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE))
    result[CONF_MAX_TOKENS] = int(result.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS))
    return result


class ConversationSubentryFlow(config_entries.ConfigSubentryFlow):
    """Sub-entry flow for adding or reconfiguring a conversation assistant."""

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.SubentryFlowResult:
        """Show form to configure a conversation model."""
        entry = self._get_entry()
        provider_id: str = str(entry.data[CONF_PROVIDER])
        chat_models = _CHAT_MODELS_BY_PROVIDER.get(provider_id, [])
        hass_apis = [selector.SelectOptionDict(label=api.name, value=api.id) for api in llm.async_get_apis(self.hass)]

        if user_input is not None:
            data = _clean_conversation_data(user_input)
            title = str(data[CONF_MODEL])
            LOGGER.debug("Creating conversation sub-entry: %s", title)
            return self.async_create_entry(title=title, data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=_get_conversation_schema(chat_models, hass_apis, {}),
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.SubentryFlowResult:
        """Handle reconfiguration of an existing conversation sub-entry."""
        entry = self._get_entry()
        subentry = entry.subentries[self._reconfigure_subentry_id]
        provider_id: str = str(entry.data[CONF_PROVIDER])
        chat_models = _CHAT_MODELS_BY_PROVIDER.get(provider_id, [])
        hass_apis = [selector.SelectOptionDict(label=api.name, value=api.id) for api in llm.async_get_apis(self.hass)]

        if user_input is not None:
            data = _clean_conversation_data(user_input)
            title = str(data[CONF_MODEL])
            return self.async_update_reload_and_abort(
                entry,
                subentry,
                title=title,
                data=data,
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_get_conversation_schema(chat_models, hass_apis, dict(subentry.data)),
        )


class SttSubentryFlow(config_entries.ConfigSubentryFlow):
    """Sub-entry flow for adding or reconfiguring an STT assistant."""

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.SubentryFlowResult:
        """Show form to select an STT model."""
        entry = self._get_entry()
        provider_id: str = str(entry.data[CONF_PROVIDER])
        stt_models = _STT_MODELS_BY_PROVIDER.get(provider_id, [])

        if user_input is not None:
            model = str(user_input[CONF_STT_MODEL])
            LOGGER.debug("Creating STT sub-entry: %s", model)
            return self.async_create_entry(title=model, data={CONF_STT_MODEL: model})

        return self.async_show_form(
            step_id="user",
            data_schema=_get_stt_schema(stt_models, {}),
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.SubentryFlowResult:
        """Handle reconfiguration of an existing STT sub-entry."""
        entry = self._get_entry()
        subentry = entry.subentries[self._reconfigure_subentry_id]
        provider_id: str = str(entry.data[CONF_PROVIDER])
        stt_models = _STT_MODELS_BY_PROVIDER.get(provider_id, [])

        if user_input is not None:
            model = str(user_input[CONF_STT_MODEL])
            return self.async_update_reload_and_abort(
                entry,
                subentry,
                title=model,
                data={CONF_STT_MODEL: model},
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_get_stt_schema(stt_models, dict(subentry.data)),
        )


def _get_ai_task_schema(
    chat_models: list[str],
    defaults: dict[str, Any],
) -> vol.Schema:
    """Build the schema for the AI task sub-entry form."""
    return vol.Schema(
        {
            vol.Required(
                CONF_MODEL,
                default=defaults.get(CONF_MODEL, chat_models[0]),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=chat_models,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_TEMPERATURE,
                default=defaults.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0.0,
                    max=1.0,
                    step=0.05,
                    mode=selector.NumberSelectorMode.SLIDER,
                )
            ),
            vol.Optional(
                CONF_MAX_TOKENS,
                default=defaults.get(CONF_MAX_TOKENS, DEFAULT_AI_TASK_MAX_TOKENS),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=64,
                    max=8192,
                    step=64,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
        }
    )


def _clean_ai_task_data(data: dict[str, Any]) -> dict[str, Any]:
    """Ensure numeric types for AI task sub-entry data."""
    result = dict(data)
    result[CONF_TEMPERATURE] = float(result.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE))
    result[CONF_MAX_TOKENS] = int(result.get(CONF_MAX_TOKENS, DEFAULT_AI_TASK_MAX_TOKENS))
    return result


class AiTaskSubentryFlow(config_entries.ConfigSubentryFlow):
    """Sub-entry flow for adding or reconfiguring an AI task assistant."""

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.SubentryFlowResult:
        """Show form to configure an AI task model."""
        entry = self._get_entry()
        provider_id: str = str(entry.data[CONF_PROVIDER])
        chat_models = _CHAT_MODELS_BY_PROVIDER.get(provider_id, [])

        if user_input is not None:
            data = _clean_ai_task_data(user_input)
            title = str(data[CONF_MODEL])
            LOGGER.debug("Creating AI task sub-entry: %s", title)
            return self.async_create_entry(title=title, data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=_get_ai_task_schema(chat_models, {}),
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.SubentryFlowResult:
        """Handle reconfiguration of an existing AI task sub-entry."""
        entry = self._get_entry()
        subentry = entry.subentries[self._reconfigure_subentry_id]
        provider_id: str = str(entry.data[CONF_PROVIDER])
        chat_models = _CHAT_MODELS_BY_PROVIDER.get(provider_id, [])

        if user_input is not None:
            data = _clean_ai_task_data(user_input)
            title = str(data[CONF_MODEL])
            return self.async_update_reload_and_abort(
                entry,
                subentry,
                title=title,
                data=data,
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_get_ai_task_schema(chat_models, dict(subentry.data)),
        )


__all__ = ["AiTaskSubentryFlow", "ConversationSubentryFlow", "SttSubentryFlow"]
