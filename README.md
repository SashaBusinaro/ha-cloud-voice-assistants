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

A production-ready GitHub template for building **HACS-compatible Home Assistant custom integrations** — CI/CD, automated releases, pre-commit hooks and Dependabot pre-configured out of the box.

---

## Installation

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

### Step 2: Configure the Integration

**Important:** Complete Step 1 and restart Home Assistant before proceeding.

#### Option 1: One-Click Setup

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=cloud_voice_assistants)

#### Option 2: Manual Setup

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for "Cloud Voice Assistants"
4. Follow the setup wizard

---

## What's included

| Tool | What it does |
|---|---|
| **hassfest** | Validates `manifest.json`, translations and component structure on every push |
| **HACS validation** | Checks that the integration meets [HACS requirements](https://hacs.xyz/docs/publish/requirements) |
| **Ruff** (CI) | Lint and format check on every push and PR |
| **Pre-commit** | Ruff + JSON/YAML/whitespace checks before every local commit |
| **release-please** | Opens a Release PR automatically on every Conventional Commit merged to `main`; bumps `manifest.json` version and generates `CHANGELOG.md` |
| **Dependabot** | Weekly grouped PRs for GitHub Actions and Python dev-deps |
| **devcontainer** | One-click Home Assistant dev environment in VS Code |

---

## File structure

| File / Directory | Purpose |
|---|---|
| `.devcontainer.json` | VS Code dev container — live HA instance for testing |
| `.editorconfig` | Editor-agnostic indentation and EOL rules |
| `.github/dependabot.yml` | Automated dependency updates (weekly, grouped) |
| `.github/ISSUE_TEMPLATE/*.yml` | Bug report and feature request templates |
| `.github/PULL_REQUEST_TEMPLATE.md` | Pull request checklist (Conventional Commits) |
| `.github/workflows/lint.yml` | Ruff lint + format check |
| `.github/workflows/validate.yml` | hassfest and HACS validation |
| `.github/workflows/release-please.yml` | Automated releases via Conventional Commits |
| `.pre-commit-config.yaml` | Pre-commit hooks (JSON/YAML, Ruff, codespell) |
| `.ruff.toml` | Ruff configuration (aligned with HA Core) |
| `.vscode/extensions.json` | Recommended VS Code extensions (mirrors devcontainer) |
| `.vscode/launch.json` | F5 debug configuration for Home Assistant |
| `.vscode/tasks.json` | VS Code tasks for Setup / Lint / Run Home Assistant |
| `release-please-config.json` | release-please configuration |
| `.release-please-manifest.json` | Current version tracking for release-please |
| `AGENTS.md` | Guidance for AI agents working in this repo |
| `CHANGELOG.md` | Auto-generated changelog (managed by release-please) |
| `config/configuration.yaml` | HA config loaded by the devcontainer |
| `custom_components/cloud_voice_assistants/` | Integration source — rename to your domain |
| `hacs.json` | HACS metadata (integration name, minimum HA version) |
| `scripts/` | Helper scripts: `setup` (install deps), `lint` (format + check), `develop` (run HA) |
| `requirements.txt` | Dev / lint Python dependencies |
| `CONTRIBUTING.md` | Contribution guidelines |

---

## Pre-commit

Pre-commit runs a set of fast checks before every `git commit`, catching issues locally
before they reach CI.

### Hooks included

| Hook | What it checks |
|---|---|
| `check-json` | Validates `manifest.json`, `translations/*.json`, `hacs.json` |
| `check-yaml` | Validates all workflow and config `.yml` files |
| `trailing-whitespace` | Removes trailing spaces |
| `end-of-file-fixer` | Ensures files end with a newline |
| `check-merge-conflict` | Blocks accidental merge-conflict markers |
| `ruff` | Lints Python and auto-fixes safe issues |
| `ruff-format` | Formats Python code |
| `codespell` | Catches common typos in code, comments and docs |

### Common commands

```bash
# Install hooks (once per clone — handled by scripts/setup)
scripts/setup

# Run manually on all files
pre-commit run --all-files

# Run a single hook
pre-commit run ruff --all-files

# Update hooks to latest pinned versions
pre-commit autoupdate
```

> The Ruff version in `.pre-commit-config.yaml` is pinned to match `requirements.txt`.
> When bumping Ruff via Dependabot, update both files together.

---

## Releases (release-please)

This template uses [release-please](https://github.com/googleapis/release-please)
to automate changelogs and GitHub Releases — no manual tagging required.

### How it works

1. Merge commits to `main` following the [Conventional Commits](https://www.conventionalcommits.org/) spec.
2. release-please opens (or updates) a **Release PR** that:
   - Bumps the version in `manifest.json`
   - Generates a `CHANGELOG.md` entry
3. Merge the Release PR → a GitHub Release and git tag are created automatically.

### Conventional Commits quick reference

| Commit prefix | Version bump | Appears in changelog |
|---|---|---|
| `feat: ...` | minor | Yes — **Features** |
| `fix: ...` | patch | Yes — **Bug Fixes** |
| `perf: ...` | patch | Yes — **Performance** |
| `feat!: ...` or `BREAKING CHANGE:` in footer | major | Yes |
| `refactor: ...` | none | Hidden |
| `chore: ...` | none | Hidden |
| `docs: ...` | none | Hidden |
| `ci: ...` | none | Hidden |

**Examples:**

```
feat: add sensor for battery level
fix: correct unit of measurement for weight sensor
feat!: drop support for HA < 2025.1
chore(deps): update ruff to v0.12.0
```

### Pre-major versioning

While the version is below `1.0.0`:
- `feat:` bumps the **patch** (e.g. `0.1.0` → `0.1.1`)
- `feat!:` bumps the **minor** (e.g. `0.1.0` → `0.2.0`)

This matches the `bump-minor-pre-major` / `bump-patch-for-minor-pre-major` flags
set in `release-please-config.json`. Remove them once you reach `1.0.0`.

---

## Dependabot

Dependabot opens **weekly grouped PRs** (every Monday) for:

| Ecosystem | PR strategy |
|---|---|
| GitHub Actions | Minor + patch versions bundled into one PR; major updates separate |
| Python (pip) | Minor + patch bundled; patch PRs wait 3 days, minor PRs 7 days before opening |
| Dev containers | Weekly, ungrouped |

`homeassistant` is excluded from automatic updates — it must stay in sync with
the `homeassistant` key in `hacs.json`. Bump them together manually.

---

## Keeping your fork in sync with the template

When the upstream template gets improvements you'd like to pull in, add it
as a `template` remote and merge selectively:

```bash
git remote add template https://github.com/SashaBusinaro/ha-hacs-template.git
git fetch template
git merge template/main --no-ff --allow-unrelated-histories
```

Resolve conflicts on the files you've customized (typically `manifest.json`,
`hacs.json`, `README.md`, `custom_components/<domain>/`), then commit.

---

## Next steps

- Add **tests** using [`pytest-homeassistant-custom-component`](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component)
- Add **brand images** (logo/icon) to `custom_components/<domain>/brand/`
- Publish to HACS as a [Custom Repository](https://www.hacs.xyz/docs/faq/custom_repositories/)
  or submit to the [HACS default store](https://hacs.xyz/docs/publish/start)
- Share on the [Home Assistant Community Forum](https://community.home-assistant.io/)

## License

MIT — see [LICENSE](LICENSE).
