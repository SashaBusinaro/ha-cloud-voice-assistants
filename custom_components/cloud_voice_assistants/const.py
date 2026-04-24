"""Constants for cloud_voice_assistants."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "cloud_voice_assistants"

# Provider identifiers
PROVIDER_GROQ = "groq"
PROVIDER_MISTRAL = "mistral"

# Config entry data keys (stored at setup, not changeable without reconfiguration)
# Note: CONF_API_KEY is homeassistant.const.CONF_API_KEY ("api_key")
CONF_PROVIDER = "provider"

# Sub-entry type identifiers
SUBENTRY_TYPE_CONVERSATION = "conversation"
SUBENTRY_TYPE_STT = "stt"
SUBENTRY_TYPE_AI_TASK = "ai_task_data"

# Sub-entry data keys
# Note: CONF_LLM_HASS_API is homeassistant.const.CONF_LLM_HASS_API ("llm_hass_api")
CONF_MODEL = "model"
CONF_PROMPT = "prompt"
CONF_TEMPERATURE = "temperature"
CONF_MAX_TOKENS = "max_tokens"
CONF_STT_MODEL = "stt_model"

# Option defaults
DEFAULT_TEMPERATURE = 1.0
DEFAULT_MAX_TOKENS = 1024
DEFAULT_AI_TASK_MAX_TOKENS = 4096
DEFAULT_PROMPT = (
    "You are a helpful voice assistant for a smart home called {{ ha_name }}.\n"
    "Answer in the same language the user speaks.\n"
    "Be concise and friendly.\n"
    "Today is {{ now().strftime('%A, %B %d, %Y') }}."
)

# Max tool-call round-trips to prevent infinite loops
MAX_TOOL_ITERATIONS = 10
