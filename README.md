# Cloud Voice Assistants

[![Validate][validate-badge]][validate-url]
[![HACS Custom][hacs-badge]][hacs-url]
[![Release][release-badge]][release-url]
[![License][license-badge]][license-url]

[validate-badge]: https://img.shields.io/github/actions/workflow/status/SashaBusinaro/ha-cloud-voice-assistants/validate.yml?style=for-the-badge&label=Validate
[validate-url]: https://github.com/SashaBusinaro/ha-cloud-voice-assistants/actions/workflows/validate.yml
[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5?style=for-the-badge&logo=homeassistantcommunitystore&logoColor=white
[hacs-url]: https://www.hacs.xyz/docs/faq/custom_repositories/
[release-badge]: https://img.shields.io/github/v/release/SashaBusinaro/ha-cloud-voice-assistants?style=for-the-badge&color=blue
[release-url]: https://github.com/SashaBusinaro/ha-cloud-voice-assistants/releases
[license-badge]: https://img.shields.io/github/license/SashaBusinaro/ha-cloud-voice-assistants?style=for-the-badge
[license-url]: https://github.com/SashaBusinaro/ha-cloud-voice-assistants/blob/main/LICENSE

A Home Assistant custom integration that connects **Groq** and **Mistral** cloud APIs to your smart home. Each provider entry creates a ready-to-use conversation agent, speech-to-text provider, and AI task entity — all configurable from the UI.

**Requires Home Assistant 2025.6 or newer.**

---

## Features

- **Conversation agent** — streaming LLM assistant that understands your home and can control devices when the HA LLM API is enabled
- **Speech-to-text (STT)** — Whisper-compatible transcription in 57+ languages, plugs directly into the Assist pipeline
- **AI Task** — structured and unstructured data generation for automations and scripts
- **Two providers out of the box** — Groq and Mistral, each with multiple model choices
- **Fully UI-configured** — model, system prompt, temperature, and token limit all editable without YAML

---

## Supported providers and models

### Groq

| Type | Models |
|---|---|
| Chat | `llama-3.3-70b-versatile` *(default)*, `llama-3.1-8b-instant`, `llama3-8b-8192`, `gemma2-9b-it` |
| STT | `whisper-large-v3-turbo` *(default)*, `whisper-large-v3`, `distil-whisper-large-v3-en` |

Get a free API key at [console.groq.com](https://console.groq.com/).

### Mistral

| Type | Models |
|---|---|
| Chat | `ministral-8b-latest` *(default)*, `ministral-3b-latest`, `mistral-small-latest`, `mistral-large-latest` |
| STT | `voxtral-mini-latest` *(default)* |

Get an API key at [console.mistral.ai](https://console.mistral.ai/).

---

## Installation

### Step 1 — Install via HACS

**Prerequisite:** [HACS](https://hacs.xyz/) must be installed.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=SashaBusinaro&repository=ha-cloud-voice-assistants&category=integration)

1. Click **Download**
2. **Restart Home Assistant**

<details>
<summary>Manual installation</summary>

1. Download the `custom_components/cloud_voice_assistants/` folder from this repository
2. Copy it into your Home Assistant `custom_components/` directory
3. Restart Home Assistant

</details>

### Step 2 — Add the integration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=cloud_voice_assistants)

Or go to **Settings → Devices & Services → + Add Integration** and search for **Cloud Voice Assistants**.

The setup wizard will ask you to:

1. Select a provider (Groq or Mistral)
2. Enter your API key — it is validated immediately against the provider's API

Once saved, three sub-entries are created automatically:

| Sub-entry | What it creates |
|---|---|
| `<Provider> Conversation` | A `conversation` entity for the Assist pipeline |
| `<Provider> STT` | An `stt` entity for speech-to-text |
| `<Provider> AI Task` | An `ai_task` entity for data generation |

You can add more sub-entries of any type later from the integration's options.

---

## Configuration

### Conversation sub-entry

| Option | Default | Description |
|---|---|---|
| Model | `llama-3.3-70b-versatile` / `ministral-8b-latest` | LLM model to use |
| System prompt | Built-in template | Jinja2 template sent as the system message |
| HA LLM APIs | *(none)* | Enable to let the assistant control Home Assistant devices via tool calls |
| Temperature | `1.0` | Creativity (0 = deterministic, 1 = most varied) |
| Max tokens | `1024` | Maximum length of each reply |

The default system prompt introduces the assistant, asks it to match the user's language, and injects the current date and the home's name via Jinja2:

```
You are a helpful voice assistant for a smart home called {{ ha_name }}.
Answer in the same language the user speaks.
Be concise and friendly.
Today is {{ now().strftime('%A, %B %d, %Y') }}.
```

### STT sub-entry

| Option | Default | Description |
|---|---|---|
| STT model | `whisper-large-v3-turbo` / `voxtral-mini-latest` | Transcription model to use |

The STT entity accepts 16-bit PCM audio at 16 kHz (mono) — the standard format produced by the HA Assist pipeline.

**Supported languages:** Afrikaans, Arabic, Azerbaijani, Belarusian, Bulgarian, Bosnian, Catalan, Czech, Welsh, Danish, German, Greek, English, Spanish, Estonian, Persian, Finnish, French, Galician, Hebrew, Hindi, Croatian, Hungarian, Armenian, Indonesian, Icelandic, Italian, Japanese, Kazakh, Kannada, Korean, Lithuanian, Latvian, Macedonian, Malayalam, Marathi, Malay, Maltese, Burmese, Norwegian Bokmål, Nepali, Dutch, Polish, Portuguese, Romanian, Russian, Slovak, Slovenian, Serbian, Swedish, Swahili, Tamil, Thai, Filipino, Turkish, Ukrainian, Urdu, Vietnamese, Chinese.

### AI Task sub-entry

| Option | Default | Description |
|---|---|---|
| Model | `llama-3.3-70b-versatile` / `ministral-8b-latest` | LLM model to use |
| Temperature | `1.0` | Creativity |
| Max tokens | `4096` | Maximum output length |

The AI Task entity can generate free-form text or structured JSON. Use it in automations with the `ai_task.generate_data` action.

---

## Using the conversation agent with Assist

1. Go to **Settings → Voice Assistants**
2. Create or edit an assistant
3. Set the **Conversation agent** to your `<Provider> Conversation` entity
4. Set the **Speech-to-text** engine to your `<Provider> STT` entity
5. Talk to your home

### Enabling device control

To allow the assistant to turn lights on, control the thermostat, and so on:

1. Open **Settings → Devices & Services → Cloud Voice Assistants**
2. Click **Configure** on the Conversation sub-entry
3. Under **HA LLM APIs**, select **Assist** (or any other HA LLM API)

The assistant will then use function calling to interact with Home Assistant entities, limited to 10 tool-call round-trips per turn.

---

## Diagnostics

Download diagnostics from **Settings → Devices & Services → Cloud Voice Assistants → Download diagnostics**. The report includes the provider name, enabled models, and sub-entry configuration. **The API key is always redacted.**

---

## Reconfiguring an API key

If your key expires or is rotated:

1. Go to **Settings → Devices & Services → Cloud Voice Assistants**
2. Click the three-dot menu → **Reconfigure**
3. Enter the new API key

Home Assistant will re-validate the key before saving.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The short version:

```bash
# one-time setup
scripts/setup

# run linters
scripts/lint

# start a live HA instance with the integration loaded
scripts/develop
```

---

## License

MIT — see [LICENSE](LICENSE).
