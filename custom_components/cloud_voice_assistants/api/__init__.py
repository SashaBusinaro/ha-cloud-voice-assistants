"""
API package for cloud_voice_assistants.

Architecture:
    Three-layer data flow: Entities → Coordinator → API Client.
    Only the coordinator should call the API client. Entities must never
    import or call the API client directly.

Exception hierarchy:
    CloudVoiceAssistantsApiClientError (base)
    ├── CloudVoiceAssistantsApiClientCommunicationError (network/timeout)
    └── CloudVoiceAssistantsApiClientAuthenticationError (401/403)

Coordinator exception mapping:
    ApiClientAuthenticationError → ConfigEntryAuthFailed (triggers reauth)
    ApiClientCommunicationError → UpdateFailed (auto-retry)
    ApiClientError             → UpdateFailed (auto-retry)
"""

from .client import (
    CloudVoiceAssistantsApiClient,
    CloudVoiceAssistantsApiClientAuthenticationError,
    CloudVoiceAssistantsApiClientCommunicationError,
    CloudVoiceAssistantsApiClientError,
)

__all__ = [
    "CloudVoiceAssistantsApiClient",
    "CloudVoiceAssistantsApiClientAuthenticationError",
    "CloudVoiceAssistantsApiClientCommunicationError",
    "CloudVoiceAssistantsApiClientError",
]
