"""STT entity for Cloud Voice Assistants.

Buffers PCM audio from the HA Assist pipeline, wraps it in a WAV container,
then delegates transcription to the configured cloud provider.
"""

from __future__ import annotations

from collections.abc import AsyncIterable
from typing import TYPE_CHECKING

from custom_components.cloud_voice_assistants.const import CONF_STT_MODEL, DOMAIN, LOGGER
from custom_components.cloud_voice_assistants.providers.base import CloudProviderBase
from homeassistant.components.stt import (
    AudioBitRates,
    AudioChannels,
    AudioCodecs,
    AudioFormats,
    AudioSampleRates,
    SpeechMetadata,
    SpeechResult,
    SpeechResultState,
    SpeechToTextEntity,
)
from homeassistant.config_entries import ConfigSubentry
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

if TYPE_CHECKING:
    from custom_components.cloud_voice_assistants.data import CloudVoiceAssistantsConfigEntry
    from homeassistant.core import HomeAssistant

# BCP-47 language codes supported by Whisper-compatible endpoints
SUPPORTED_LANGUAGES: list[str] = [
    "af",
    "ar",
    "az",
    "be",
    "bg",
    "bs",
    "ca",
    "cs",
    "cy",
    "da",
    "de",
    "el",
    "en",
    "es",
    "et",
    "fa",
    "fi",
    "fr",
    "gl",
    "he",
    "hi",
    "hr",
    "hu",
    "hy",
    "id",
    "is",
    "it",
    "ja",
    "kk",
    "kn",
    "ko",
    "lt",
    "lv",
    "mk",
    "ml",
    "mr",
    "ms",
    "mt",
    "my",
    "nb",
    "ne",
    "nl",
    "pl",
    "pt",
    "ro",
    "ru",
    "sk",
    "sl",
    "sr",
    "sv",
    "sw",
    "ta",
    "th",
    "tl",
    "tr",
    "uk",
    "ur",
    "vi",
    "zh",
]


class CloudVoiceAssistantsSttEntity(SpeechToTextEntity):
    """STT entity that delegates transcription to the configured cloud provider."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        hass: HomeAssistant,
        entry: CloudVoiceAssistantsConfigEntry,
        subentry: ConfigSubentry,
    ) -> None:
        """Initialize the STT entity."""
        self.hass = hass
        self._entry = entry
        self._subentry = subentry
        self._attr_unique_id = subentry.subentry_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this STT entity."""
        provider = self._entry.runtime_data.provider
        return DeviceInfo(
            identifiers={(DOMAIN, self._subentry.subentry_id)},
            name=self._subentry.title,
            manufacturer=self._entry.title,
            model=self._subentry.data.get(CONF_STT_MODEL, provider.default_stt_model),
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def supported_languages(self) -> list[str]:
        """Return the list of supported languages."""
        return SUPPORTED_LANGUAGES

    @property
    def supported_formats(self) -> list[AudioFormats]:
        """Return the list of supported audio formats."""
        return [AudioFormats.WAV]

    @property
    def supported_codecs(self) -> list[AudioCodecs]:
        """Return the list of supported audio codecs."""
        return [AudioCodecs.PCM]

    @property
    def supported_bit_rates(self) -> list[AudioBitRates]:
        """Return the list of supported bit rates."""
        return [AudioBitRates.BITRATE_16]

    @property
    def supported_sample_rates(self) -> list[AudioSampleRates]:
        """Return the list of supported sample rates."""
        return [AudioSampleRates.SAMPLERATE_16000]

    @property
    def supported_channels(self) -> list[AudioChannels]:
        """Return the list of supported audio channels."""
        return [AudioChannels.CHANNEL_MONO]

    async def async_process_audio_stream(
        self,
        metadata: SpeechMetadata,
        stream: AsyncIterable[bytes],
    ) -> SpeechResult:
        """Buffer PCM audio, wrap in WAV, and transcribe via the provider."""
        pcm_data = b"".join([chunk async for chunk in stream])

        if not pcm_data:
            LOGGER.warning("STT: received empty audio stream")
            return SpeechResult("", SpeechResultState.ERROR)

        lang_code = (metadata.language or "").strip() or None

        LOGGER.debug(
            "STT: %d bytes PCM — rate=%s channels=%s bits=%s lang=%s",
            len(pcm_data),
            metadata.sample_rate,
            metadata.channel,
            metadata.bit_rate,
            lang_code or "auto",
        )

        data = self._entry.runtime_data
        provider = data.provider
        session = data.session

        wav_bytes = CloudProviderBase.pcm_to_wav(
            pcm_data,
            sample_rate=int(metadata.sample_rate),
            channels=int(metadata.channel),
            sample_width=int(metadata.bit_rate) // 8,
        )

        model = self._subentry.data.get(CONF_STT_MODEL, provider.default_stt_model)

        try:
            text = await provider.transcribe(
                session=session,
                wav_bytes=wav_bytes,
                language=lang_code,
                model=model,
            )
        except Exception as err:  # noqa: BLE001
            LOGGER.error("STT transcription failed: %s", err)
            return SpeechResult("", SpeechResultState.ERROR)

        if not text:
            LOGGER.warning("STT: provider returned empty transcription")
            return SpeechResult("", SpeechResultState.ERROR)

        return SpeechResult(text, SpeechResultState.SUCCESS)
