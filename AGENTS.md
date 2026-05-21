# AGENTS.md

Guidance for AI agents (Claude Code, Copilot, Cursor, etc.) working in this repository.

## What this repo is

A GitHub template for **HACS-compatible Home Assistant custom integrations**.
The integration source lives in `custom_components/integration_blueprint/` (rename
to the target domain before first commit when the template is used).

If `integration_blueprint` is still present after a clone, the user has not
finished bootstrapping the template yet. Point them at the **placeholder table
in `README.md`** (single source of truth — under "Replace the placeholders") and
walk them through the find-and-replace + `git mv` before doing any real work.
Do not duplicate the placeholder list here; keep `README.md` authoritative.

## Hard rules

- **Write everything in English** — code, comments, docstrings, commit messages,
  PR descriptions, documentation.
- **Never edit `CHANGELOG.md` manually** — it is managed by `release-please`.
- **Never bump `version` in `manifest.json` manually** — `release-please` does it.
- **Never edit `.release-please-manifest.json`** — same reason.
- **Use Conventional Commits** (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`,
  `perf:`, `ci:`, `test:`). Bumps and changelog entries depend on the prefix.
  See README "Releases (release-please)" for the bump table.
- **Pin Ruff in both places**: `.pre-commit-config.yaml` and `requirements.txt`
  must share the same Ruff version. Bump together.
- **Do not commit secrets** or files under `config/` other than
  `config/configuration.yaml` (enforced by `.gitignore`).

## Project layout

```text
custom_components/integration_blueprint/   # integration source (rename per README placeholder table)
  __init__.py        # async_setup_entry / async_unload_entry — entry point
  api.py             # API client + typed exceptions
  config_flow.py     # UI config flow
  coordinator.py     # DataUpdateCoordinator
  const.py           # DOMAIN, LOGGER, attribution
  data.py            # runtime_data dataclass + typed ConfigEntry alias
  entity.py          # shared base entity
  binary_sensor.py / sensor.py / switch.py   # platform entities
  manifest.json      # HA integration metadata
  translations/      # UI strings (en.json is canonical)
config/              # HA dev config loaded by scripts/develop
scripts/             # lint / develop / setup wrappers
```

## Common tasks

Three shell entry points cover the dev loop:

- `scripts/setup` — create `venv/` (recreates it on platform mismatch), install dev deps (`requirements.txt`), install pre-commit hooks
- `scripts/lint` — auto-calls `scripts/setup` if the venv is missing or invalid, then runs `pre-commit run --all-files` (same pipeline as CI)
- `scripts/develop` — auto-calls `scripts/setup` if the venv is missing or invalid, then starts Home Assistant on port 8123 with the integration loaded

For CI parity, `scripts/lint` and the `lint.yml` workflow both run `pre-commit run --all-files` — no separate ruff invocation needed.

VS Code users have equivalent **tasks** (`Setup`, `Lint`, `Run Home Assistant`)
and an **F5 debug** configuration — see README sections "Start developing"
and "Pre-commit" for details. Do not duplicate task definitions; extend
`.vscode/tasks.json` if a new common task is genuinely needed.

## Bootstrap repo setup (CLI helpers)

Two one-off actions are documented as manual steps in `README.md`. When the user
has the GitHub CLI available, run them as:

```bash
# Replace OWNER/REPO with the freshly bootstrapped repo
OWNER=your-github-username
REPO=your-repo-name

# 1. Allow release-please to open the Release PR
#    (equivalent to ticking "Allow GitHub Actions to create and approve pull
#    requests" under Settings → Actions → General → Workflow permissions)
gh api -X PUT "/repos/$OWNER/$REPO/actions/permissions/workflow" \
  -F default_workflow_permissions=write \
  -F can_approve_pull_request_reviews=true

# 2. Add the HACS-required repository topics (HACS validation fails without them)
gh repo edit "$OWNER/$REPO" \
  --add-topic home-assistant \
  --add-topic hacs \
  --add-topic home-assistant-custom \
  --add-topic integration
```

Run both after the placeholder substitution and the first push. Without (1) the
release-please workflow fails with `403` when it tries to open a PR; without (2)
the `Validate` workflow's HACS job fails with
`<Validation topics> failed: The repository has no valid topics`.

## Adding a new platform / entity type

1. Create `custom_components/<domain>/<platform>.py`.
2. Subclass the relevant HA entity (e.g. `SensorEntity`) and the shared
   `IntegrationBlueprintEntity` in `entity.py` for coordinator wiring.
3. Append the `Platform` enum value to the `PLATFORMS` list in `__init__.py`.
4. Add translation keys to `translations/en.json` if the entity is user-facing.

## Validation

CI runs three workflows on every push and PR (see `.github/workflows/`):

- **lint.yml** — `ruff check` + `ruff format --check` on Python 3.14.
- **validate.yml** — `hassfest` (manifest, structure, translations) and HACS
  validation. Runs daily on cron too.
- **release-please.yml** — opens / updates the Release PR on `main`. Requires
  the repo setting *"Allow GitHub Actions to create and approve pull requests"*.

A change that touches `manifest.json`, `hacs.json`, or `translations/` will fail
fast if the JSON shape is wrong — fix locally with `pre-commit run --all-files`
before pushing.

## Python 3.14 syntax

The template targets Python 3.14 (`target-version = "py314"` in `.ruff.toml`). Do not flag 3.14-native syntax as an issue or suggest workarounds for older versions.

- **PEP 649 — lazy annotations**: forward references in annotations do not need to be quoted and `from __future__ import annotations` is not required. Names defined later in the module can be referenced in annotations without quoting.
- **`except TypeA, TypeB:`** without parentheses is valid Python 3.14 syntax.

## Ruff configuration

Defined in `.ruff.toml`, deliberately mirroring `home-assistant/core`
(`target-version = "py314"`, `select = ["ALL"]`, narrow `ignore` list). Do not
relax rules globally — prefer `# noqa: <code>` with a one-line justification
when a single line genuinely needs to break a rule.

## Dependencies

- `requirements.txt` is the single source of truth for dev / CI deps.
  Dependabot updates it weekly with grouped PRs (see `.github/dependabot.yml`).
- `homeassistant` is **excluded** from Dependabot — it must stay in sync with
  the `homeassistant` key in `hacs.json`. Bump them together manually.
  When bumping the minimum HA version, update all three places in lockstep:
  `hacs.json → homeassistant`, `requirements.txt → homeassistant==`, and the
  `## Requirements` section in `README.md`.

## Extension points

Lines starting with `# NOTE:` in the Python source mark places where the
template is deliberately minimal. Each note explains what is missing, when to
add it, and links to the relevant HA developer doc. Grep for `# NOTE:` before
asking the user where to extend — the answer is usually already inline.

## When in doubt

- Match patterns already in the repo before introducing new ones.
- Prefer editing existing files over creating new ones.
- Keep the template lightweight — every added file is friction for a first-time
  user. Only add what materially improves a common workflow.
