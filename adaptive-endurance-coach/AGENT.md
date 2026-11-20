# Setup Instructions — Adaptive Endurance Coach (Intervals.icu edition)

You are an agentic coding assistant (Claude Code or similar) helping a user set up a personal AI endurance coaching system backed by **Intervals.icu**. This document contains everything you need. It supports macOS, Linux, and Windows — detect the user's OS first and follow the matching command block. Check in with the user at the marked decision points; don't silently skip steps.

## What this repo contains

```
adaptive-endurance-coach/
  AGENT.md                          <- this file
  README.md                         <- human-facing overview
  skills/adaptive-endurance-coach/  <- the coaching skill (copy to the user's Claude skills dir)
    SKILL.md
    references/
      onboarding.md
      load-and-recovery.md
      training-methods.md
      race-execution.md
      nutrition.md
```

This is a coaching **skill** for swimming, cycling, running, and triathlon. **Intervals.icu is the source of truth.** Strava/Garmin/Wahoo data flows into Intervals.icu through its own device sync, so there is no separate Strava connector to configure. The skill includes a nutrition engine that writes daily calorie/macro targets to the Intervals.icu calendar automatically (as dated "Nutrition Target" notes).

**This repo does NOT include the Intervals.icu MCP server.** It relies on a fork of [mvilanova/intervals-mcp-server](https://github.com/mvilanova/intervals-mcp-server) that adds four write tools the coach needs (`update_wellness`, `update_sport_settings`, `add_nutrition_targets`, and a `category` argument on `add_or_update_event` for RACE_A/B/C events). Use that fork; the stock server is read-mostly and the coach will lose metric-logging, threshold updates, race events, and nutrition-to-calendar without it.

> **License note:** the MCP server is GPL-3.0. Running your own modified copy for personal use is unrestricted. If you *publish* your modified server, you must release the source under GPL-3.0. This skill is MIT.

---

## Step 1 — Prerequisites

Ask or check for:

- **Claude Code (or another MCP-capable agentic client)** installed and working.
- **Python 3.12+** and **[`uv`](https://docs.astral.sh/uv/)**:
  - macOS / Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
  - Open a **new** terminal afterward so PATH updates.
- **An Intervals.icu account** (free tier is fine).
- The user's **Intervals.icu API key** and **athlete ID** (collected in Step 3 — do NOT have them paste the API key into chat; it goes only into the server's `.env`).

## Step 2 — Clone and install the Intervals.icu MCP server (forked)

If this skill was cloned as part of the combined `coach` repo, the forked server is already in `../intervals-mcp-server` — just `cd` there and skip the clone. Otherwise use the fork that includes the coach's write tools:

```
git clone <your-fork-of-intervals-mcp-server>.git
cd intervals-mcp-server
uv venv --python 3.12
uv sync
```

## Step 3 — Configure credentials

1. **API key:** in Intervals.icu, go to Settings → Developer and generate an API key.
2. **Athlete ID:** it's the `i12345` in the profile URL, e.g. `https://intervals.icu/athlete/i12345/...`.
3. Create a `.env` file in the `intervals-mcp-server` directory:

```
API_KEY=your_intervals_api_key_here
ATHLETE_ID=i12345
# INTERVALS_API_BASE_URL=https://intervals.icu/api/v1   # optional, this is the default
```

The API key grants full read/write to the account — treat it like a password. It stays in `.env`; it must never appear in the chat.

## Step 4 — Register the MCP server with the client

**Claude Code** (adjust the path to where you cloned the server; use the full path to `uv` if the client can't find it — `which uv` / `where.exe uv`):

```
claude mcp add intervals -- uv run --directory /full/path/to/intervals-mcp-server \
  python src/intervals_mcp_server/server.py
```

**Claude Desktop or other MCP clients:** add an entry under `"mcpServers"` in the client config, pointing `command` at `uv` (full path) with args `run --directory /full/path/to/intervals-mcp-server python src/intervals_mcp_server/server.py`, and put `API_KEY` / `ATHLETE_ID` in an `"env"` block (or rely on the `.env`). Config file locations:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json` (Store installs: `%LOCALAPPDATA%\Packages\Claude_*\LocalCache\Roaming\Claude\claude_desktop_config.json`)
- Linux: `~/.config/Claude/claude_desktop_config.json`

Restart the client after editing config files.

## Step 5 — Install the skill

Copy the skill folder into the client's skills directory. For Claude Code that's `~/.claude/skills/`.

**macOS / Linux:**
```
mkdir -p ~/.claude/skills
cp -R skills/adaptive-endurance-coach ~/.claude/skills/adaptive-endurance-coach
```

**Windows (PowerShell):**
```
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\skills" | Out-Null
Copy-Item -Recurse -Force "skills\adaptive-endurance-coach" "$env:USERPROFILE\.claude\skills\adaptive-endurance-coach"
```

## Step 6 — First run / onboarding

Tell the user to just start talking to the skill ("I want to start training for a triathlon") or invoke the `adaptive-endurance-coach` skill. On first run with no profile, the skill runs its own onboarding (see `references/onboarding.md`): it confirms the Intervals.icu connection, warm-starts on thresholds via `get_sport_settings`, then does intake, threshold setup, and tone selection.

The skill keeps persistent athlete memory in `~/.training/` (macOS/Linux) or `%USERPROFILE%\.training\` (Windows), created automatically on first run. This repo contains no athlete data — the user starts clean.

## Step 7 — Sanity check

Confirm before declaring done:

- [ ] A read tool works — ask the client to run `get_wellness_data` (or `get_events`) and confirm it returns real data, not an auth error.
- [ ] The four write tools are present in the client's tool list: `update_wellness`, `update_sport_settings`, `add_nutrition_targets`, and `add_or_update_event` (which now accepts `category`). If they're missing, the client is pointed at the stock server, not the fork.
- [ ] The skill's `SKILL.md` exists in the client's skills directory for this OS and the client lists the skill as available.
- [ ] The API key was never pasted into chat — it lives only in `.env`.

If a read fails, debug it before telling the user they're ready — a broken MCP connection makes the coach fabricate or refuse to act on training data.

## Troubleshooting

- **`401 Unauthorized`:** wrong or missing API key. Check `.env`; regenerate the key in Intervals.icu settings if needed.
- **`403 / SETTINGS:WRITE`:** a personal API key has full scope; if `update_sport_settings` is rejected, confirm you're using a personal key (not a restricted OAuth token).
- **Client can't find `uv`:** use the absolute path to `uv` in the client config (`which uv` / `where.exe uv`).
- **Write tools missing:** you're on the stock upstream server. Point the client at the fork that adds them.
- **Athlete ID format:** include the leading `i` (e.g. `i12345`).
