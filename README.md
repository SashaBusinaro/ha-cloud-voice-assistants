# Cloud Voice Assistants

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

<!--
Uncomment and customize these badges if you want to use them:

[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]
[![Discord][discord-shield]][discord]
-->

**✨ Develop in the cloud:** Want to contribute or customize this integration? Open it directly in GitHub Codespaces - no local setup required!

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/SashaBusinaro/ha-cloud-voice-assistants?quickstart=1)

## ✨ Features

- **Conversation Agents**: Use fast cloud LLMs (Groq, Mistral AI) as your Home Assistant voice assistant
- **Speech-to-Text**: Transcribe voice commands using cloud Whisper models
- **Device Control**: Optionally allow your AI assistant to control Home Assistant entities
- **Multiple Assistants**: Add as many conversation or STT agents as you need from a single provider account
- **Customizable Prompts**: Personalize assistant behavior with system prompts and Home Assistant template support
- **Reconfigurable**: Update your API key anytime without removing the integration

**This integration sets up the following platforms.**

| Platform       | Description                                           |
| -------------- | ----------------------------------------------------- |
| `conversation` | AI conversation agent powered by a cloud LLM          |
| `stt`          | Speech-to-text using a cloud Whisper-compatible model |

## Supported Providers

| Provider       | Conversation models                                                                  | STT models                                                           |
| -------------- | ------------------------------------------------------------------------------------ | -------------------------------------------------------------------- |
| **Groq**       | llama-3.3-70b-versatile, llama-3.1-8b-instant, llama3-8b-8192, gemma2-9b-it          | whisper-large-v3, whisper-large-v3-turbo, distil-whisper-large-v3-en |
| **Mistral AI** | ministral-8b-latest, ministral-3b-latest, mistral-small-latest, mistral-large-latest | voxtral-mini-latest                                                  |

## 🚀 Quick Start

### Step 1: Install the Integration

**Prerequisites:** This integration requires [HACS](https://hacs.xyz/) (Home Assistant Community Store) to be installed.

Click the button below to open the integration directly in HACS:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=SashaBusinaro&repository=ha-cloud-voice-assistants&category=integration)

Then:

1. Click "Download" to install the integration
2. **Restart Home Assistant** (required after installation)

> [!NOTE]
> The My Home Assistant redirect will first take you to a landing page. Click the button there to open your Home Assistant instance.

<details>
<summary><strong>Manual Installation (Advanced)</strong></summary>

If you prefer not to use HACS:

1. Download the `custom_components/cloud_voice_assistants/` folder from this repository
2. Copy it to your Home Assistant's `custom_components/` directory
3. Restart Home Assistant

</details>

### Step 2: Add the Integration

**Important:** You must have installed the integration first (see Step 1) and restarted Home Assistant!

#### Option 1: One-Click Setup (Quick)

Click the button below to open the configuration dialog:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=cloud_voice_assistants)

Follow the setup wizard:

1. **Select your provider** — choose Groq or Mistral AI
2. **Enter your API key** — the key is validated before the entry is saved
3. Click **Submit**

#### Option 2: Manual Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for "Cloud Voice Assistants"
4. Follow the same setup steps as Option 1

### Step 3: Add Assistants

After adding the integration, you can configure individual conversation agents and STT providers using sub-entries:

1. Go to **Settings** → **Devices & Services** → **Cloud Voice Assistants**
2. Click **"+ Add"** and choose:
   - **Conversation agent** — adds an LLM-powered chat assistant
   - **Speech-to-text** — adds a Whisper STT provider
3. Configure the assistant:
   - For conversation: choose a model, set a system prompt, and optionally enable Home Assistant device control
   - For STT: choose a transcription model

You can add multiple conversation agents and STT providers from the same account.

### Step 4: Use Your Assistant

**As a conversation agent:**
Go to **Settings** → **Voice Assistants** and select your new conversation agent for any voice pipeline. It will appear as a selectable agent alongside the built-in Assist.

**As an STT provider:**
Go to **Settings** → **Voice Assistants** and select your new STT provider in a voice pipeline.

## Configuration Options

### During Provider Setup

| Name     | Required | Description                            |
| -------- | -------- | -------------------------------------- |
| Provider | Yes      | Cloud AI provider (Groq or Mistral AI) |
| API Key  | Yes      | Your provider API key                  |

### Conversation Agent Options

| Name                   | Default                    | Description                                            |
| ---------------------- | -------------------------- | ------------------------------------------------------ |
| Model                  | Provider default           | Language model used for conversation                   |
| System prompt          | Built-in smart-home prompt | Customizable prompt; supports HA templates             |
| Control Home Assistant | Off                        | Which HA LLM APIs the agent may use to control devices |
| Temperature            | 1.0                        | Sampling temperature (0 = deterministic, 1 = creative) |
| Maximum tokens         | 1024                       | Maximum tokens in the model response                   |

### STT Options

| Name  | Required | Description                                 |
| ----- | -------- | ------------------------------------------- |
| Model | Yes      | Speech-to-text model used for transcription |

## Troubleshooting

### Authentication Issues

If your API key is rejected or expires, Home Assistant will prompt you to reauthenticate:

1. Go to **Settings** → **Devices & Services**
2. Look for **"Action Required"** on the Cloud Voice Assistants entry
3. Click **"Reconfigure"** and enter a new API key

You can also update your key at any time without waiting for an error:

1. Go to **Settings** → **Devices & Services** → **Cloud Voice Assistants**
2. Click the **3 dots menu** → **Reconfigure**

### Enable Debug Logging

```yaml
logger:
  default: info
  logs:
    custom_components.cloud_voice_assistants: debug
```

### Common Issues

#### "Invalid API key" during setup

- Verify the key is correct and active in your provider's dashboard
- Make sure the key has the required scopes (Groq and Mistral AI use full-access keys by default)

#### Conversation agent not appearing in voice pipelines

- Ensure Home Assistant was restarted after installation
- Check that a conversation sub-entry was added under the integration

#### Slow or no response

- Groq provides very fast inference; Mistral AI may be slower for large models
- Check your network connection
- Enable debug logging and look for HTTP errors in the log

## 🤝 Contributing

Contributions are welcome! Please open an issue or pull request if you have suggestions or improvements.

You have two options to set up a development environment — expand below for full details.

<details>
<summary><strong>Development Setup</strong></summary>

Both options provide the same fully-configured environment with Home Assistant, Python 3.14, Node.js LTS, and all necessary tools.

### Option 1: GitHub Codespaces (Recommended) ☁️

Develop directly in your browser without installing anything locally!

1. Click the green **"Code"** button in this repository
2. Switch to the **"Codespaces"** tab
3. Click **"Create codespace on main"**
4. **Wait for setup** (2-3 minutes first time) — everything installs automatically
5. **Review and commit** your changes in the Source Control panel (`Ctrl+Shift+G`)

> [!TIP]
> Codespaces gives you **60 hours/month free** for personal accounts. When you start Home Assistant (`script/develop`), port 8123 forwards automatically.

### Option 2: Local Development with VS Code 💻

#### Prerequisites

You'll need these installed locally:

- **A Docker-compatible container engine** — see options by platform:

  | Option                                                                                                                   | 🍎 macOS | 🐧 Linux | 🪟 Windows | Notes                                                                                                                                                                                                                                     |
  | ------------------------------------------------------------------------------------------------------------------------ | :------: | :------: | :--------: | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | [Docker Desktop](https://www.docker.com/products/docker-desktop/)                                                        |    ✅    |    ✅    |     ✅     | **Easiest starting point for all platforms.** GUI-based, well-documented, one installer. Uses WSL2 as default backend on Windows (Hyper-V also available). Installation requires admin rights; daily use does not. Free for personal use. |
  | [OrbStack](https://orbstack.dev/) ⭐                                                                                     |    ✅    |    —     |     —      | **Recommended for macOS** once Docker Desktop feels slow. Starts in ~2s, much lighter on RAM/CPU, full Docker API compatibility. Free for personal use.                                                                                   |
  | [Docker CE](https://docs.docker.com/engine/install/) (native) ⭐                                                         |    —     |    ✅    |     —      | **Recommended for Linux.** Install directly via your package manager — no VM, no GUI, no overhead. Free.                                                                                                                                  |
  | [WSL2](https://learn.microsoft.com/windows/wsl/install) + [Docker CE](https://docs.docker.com/engine/install/ubuntu/) ⭐ |    —     |    —     |     ✅     | **Recommended for Windows** once you're comfortable with WSL2. Docker runs natively inside WSL2 — no GUI overhead. Requires one-time WSL2 setup. Free.                                                                                    |
  | [Rancher Desktop](https://rancherdesktop.io/)                                                                            |    ✅    |    ✅    |     ✅     | Open source by SUSE. GUI-based, uses WSL2 on Windows. Good alternative to Docker Desktop. Free.                                                                                                                                           |
  | [Colima](https://github.com/abiosoft/colima)                                                                             |    ✅    |    ✅    |     —      | CLI-only, very lightweight. Good for terminal-focused workflows. Free.                                                                                                                                                                    |

- **VS Code** with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- **Git** — macOS and Linux usually have it already; see below if not, or to get a newer version:
  - **🍎 macOS:** The system Git (`xcode-select --install`) works fine. Recommended: `brew install git` ([Homebrew](https://brew.sh/)) for a current version.
  - **🐧 Linux:** Usually pre-installed. If not: `sudo apt install git` (or your distro's equivalent).
  - **🪟 Windows + WSL2 ⭐:** Install Git _inside WSL2_ with `sudo apt install git`. Git on Windows itself is not needed — VS Code clones and operates entirely within WSL2.
  - **🪟 Windows + Docker Desktop:** Install via `winget install Git.Git` or download [Git for Windows](https://git-scm.com/download/win).
- **Hardware** — the devcontainer runs a full Home Assistant instance including Python tooling:

  |          | Minimum    | Recommended                           |
  | -------- | ---------- | ------------------------------------- |
  | **RAM**  | 8 GB       | 16 GB or more                         |
  | **CPU**  | 4 cores    | 8 cores or more                       |
  | **Disk** | 10 GB free | 20 GB free (SSD strongly recommended) |

> [!TIP]
> **Not sure which Docker option to pick?** Start with [Docker Desktop](https://www.docker.com/products/docker-desktop/) — it works on all platforms, has a GUI, and needs no extra setup. The ⭐ options are faster alternatives once you're comfortable. macOS and Linux offer the best devcontainer experience — containers run with no extra VM layer and file I/O is fast. Windows works well too; this integration uses named container volumes (files live inside WSL2, not on the Windows drive) to keep performance acceptable.

> [!NOTE]
> **New to Dev Containers?** See the [VS Code Dev Containers documentation](https://code.visualstudio.com/docs/devcontainers/containers#_system-requirements) for system requirements and how to install the extension. **Once the extension is installed, you're done** — this repository already ships a complete devcontainer configuration. You don't need to follow the rest of the VS Code guide; the setup steps below are all that's needed.

#### Setup Steps

1. **Clone in a Dev Container:**

   **🍎 macOS / 🐧 Linux:** Clone the repository and open the folder in VS Code → click **"Reopen in Container"** when prompted (or `F1` → **"Dev Containers: Reopen in Container"**).

   **🪟 Windows:** In VS Code, press `F1` → **"Dev Containers: Clone Repository in Named Container Volume..."** and enter the repository URL. This keeps files inside WSL2 for best I/O performance.

2. Wait for the container to build (2-3 minutes first time)

3. **Review and commit** changes in Source Control (`Ctrl+Shift+G`)

4. **Start developing**:

   ```bash
   script/develop  # Home Assistant runs at http://localhost:8123
   ```

> [!NOTE]
> Both Codespaces and local DevContainer provide the exact same experience. The only difference is where the container runs (GitHub's cloud vs. your machine).

</details>

---

## 🤖 AI-Assisted Development

> [!NOTE]
> **Transparency Notice:** This integration was developed with assistance from AI coding agents (GitHub Copilot, Claude, and others). While the codebase follows Home Assistant Core standards, AI-generated code may not be reviewed or tested to the same extent as manually written code. AI tools were used to generate boilerplate code, implement standard integration features (config flow, conversation entities, STT providers), ensure code quality and type safety, and write documentation. If you encounter unexpected behavior, please [open an issue](../../issues) on GitHub.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Made with ❤️ by [@SashaBusinaro][user_profile]**

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/SashaBusinaro/ha-cloud-voice-assistants.svg?style=for-the-badge
[commits]: https://github.com/SashaBusinaro/ha-cloud-voice-assistants/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/SashaBusinaro/ha-cloud-voice-assistants.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40SashaBusinaro-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/SashaBusinaro/ha-cloud-voice-assistants.svg?style=for-the-badge
[releases]: https://github.com/SashaBusinaro/ha-cloud-voice-assistants/releases
[user_profile]: https://github.com/SashaBusinaro

<!-- Optional badge definitions - uncomment if needed:
[buymecoffee]: https://www.buymeacoffee.com/SashaBusinaro
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
-->
