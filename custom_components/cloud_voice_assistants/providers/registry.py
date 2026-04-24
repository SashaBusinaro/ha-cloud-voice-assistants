"""Provider registry — maps provider IDs to their implementation classes."""

from __future__ import annotations

from custom_components.cloud_voice_assistants.const import PROVIDER_GROQ, PROVIDER_MISTRAL

from . import CloudProvider
from .groq import GroqProvider
from .mistral import MistralProvider

PROVIDER_CLASSES: dict[str, type] = {
    PROVIDER_GROQ: GroqProvider,
    PROVIDER_MISTRAL: MistralProvider,
}


def build_provider(provider_id: str, api_key: str) -> CloudProvider:
    """Instantiate a provider by its ID with the given API key."""
    cls = PROVIDER_CLASSES.get(provider_id)
    if cls is None:
        raise ValueError(f"Unknown provider {provider_id!r}. Valid providers: {list(PROVIDER_CLASSES)}")
    return cls(api_key=api_key)
