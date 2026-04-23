"""
Entity package for cloud_voice_assistants.

Architecture:
    All platform entities inherit from (PlatformEntity, CloudVoiceAssistantsEntity).
    MRO order matters — platform-specific class first, then the integration base.
    Entities read data from coordinator.data and NEVER call the API client directly.
    Unique IDs follow the pattern: {entry_id}_{description.key}

See entity/base.py for the CloudVoiceAssistantsEntity base class.
"""

from .base import CloudVoiceAssistantsEntity

__all__ = ["CloudVoiceAssistantsEntity"]
