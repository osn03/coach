# Adaptive Endurance Coach + Intervals.icu MCP server

An AI endurance coach (swim / bike / run / triathlon) for Claude Code and other MCP-capable agents, backed by [Intervals.icu](https://intervals.icu/) as the source of truth.

This repo has two parts:

| Folder | What it is | License |
|---|---|---|
| [`adaptive-endurance-coach/`](./adaptive-endurance-coach) | The coaching **skill**: periodized plans, daily readiness logic, race plans, and nutrition targets written to your Intervals.icu calendar. | MIT |
| [`intervals-mcp-server/`](./intervals-mcp-server) | A fork of [mvilanova/intervals-mcp-server](https://github.com/mvilanova/intervals-mcp-server) that adds the write tools the coach needs (`update_wellness`, `get_/update_sport_settings`, `add_nutrition_targets`, and a `category` argument on `add_or_update_event` for RACE_A/B/C events). See [`FORK_CHANGES.md`](./intervals-mcp-server/FORK_CHANGES.md). | GPL-3.0 |

All credit for the original MCP server goes to its author.

---

## Quick start (let your agent do it)

Clone the repo, open Claude Code (or a similar agent) in it, and say:

> Read `adaptive-endurance-coach/AGENT.md` and set everything up. The MCP server is already in `intervals-mcp-server/` in this repo.

The agent will install the server, register it, install the skill, and start onboarding. You still need to do the [Intervals.icu setup](#1-set-up-intervalsicu) yourself, because the agent can't create accounts or API keys for you.

---

## 1. Set up Intervals.icu

### 1.1 Create an account
Sign up at <https://intervals.icu/>. The free tier works.

### 1.2 Connect your data sources
Go to **Settings → Connections** and link the devices and platforms you use:

- **Garmin Connect, Wahoo, Coros, Suunto, Polar, Zwift, etc.** Connect these **directly**. Activities and (for Garmin/Oura/Whoop and similar) wellness data like HRV, resting HR, sleep, and weight sync in automatically.
- **Strava: don't rely on it as your only source.** Strava's API terms stop Intervals.icu from sharing Strava-imported activities with third-party apps, so the API returns them as stubs with no data (`"STRAVA activities are not available via the API"`). The coach can't see them. Connect your device platform directly, or upload `.fit` files manually.

### 1.3 Turn on wellness sync
Readiness decisions depend on daily wellness data. Under **Settings → Connections**, enable wellness import for your source (Garmin, Oura, Whoop, Polar, HRV4Training, etc.) so **HRV, resting HR, sleep, and weight** show up on the calendar every day. If you have no wearable, the coach can still log these manually with `update_wellness`.

### 1.4 Check sport settings (thresholds and zones)
Under **Settings → Sport Settings**, make sure each sport you do (Ride, Run, Swim) has:

- **Ride:** FTP (plus indoor FTP if it's different), and power zones
- **Run:** threshold pace and LTHR, and pace/HR zones
- **Swim:** threshold pace (CSS)
- **All sports:** max HR, resting HR, LTHR

Rough numbers are fine. The coach reads them with `get_sport_settings` during onboarding and corrects them with `update_sport_settings` after tests.

### 1.5 Get your API key and athlete ID
1. Go to **Settings → Developer Settings** (near the bottom of the settings page) and click **Generate API key**.
2. Your **athlete ID** appears on that page and in your profile URL: `https://intervals.icu/athlete/i12345/...` → `i12345`. Include the leading `i`.

> Treat the API key like a password: it gives full read/write access to your account. It goes **only** in `intervals-mcp-server/.env`. Never paste it into a chat, and never commit it (`.env` is gitignored).

---

## 2. Install the MCP server

Requires **Python 3.12+** and **[uv](https://docs.astral.sh/uv/)**.

```bash
# install uv if needed
# macOS / Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows (PowerShell):
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

git clone <this-repo-url> coach
cd coach/intervals-mcp-server
uv venv --python 3.12
uv sync
```

Create your `.env` from the template:

```bash
cp .env.example .env        # Windows: copy .env.example .env
```

Then edit `.env`:

```
API_KEY=your_intervals_api_key_here
ATHLETE_ID=i12345
```

## 3. Register the server with your agent

**Claude Code:**

```bash
claude mcp add intervals -- uv run --directory /full/path/to/coach/intervals-mcp-server python src/intervals_mcp_server/server.py
```

**Claude Desktop / other clients:** add this under `"mcpServers"` in the client config. If the client can't find `uv`, use its full path (`which uv` / `where.exe uv`):

```json
{
  "mcpServers": {
    "intervals": {
      "command": "uv",
      "args": ["run", "--directory", "/full/path/to/coach/intervals-mcp-server",
               "python", "src/intervals_mcp_server/server.py"]
    }
  }
}
```

Restart the client afterwards.

## 4. Install the skill

**macOS / Linux:**
```bash
mkdir -p ~/.claude/skills
cp -R adaptive-endurance-coach/skills/adaptive-endurance-coach ~/.claude/skills/
```

**Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\skills" | Out-Null
Copy-Item -Recurse -Force "adaptive-endurance-coach\skills\adaptive-endurance-coach" "$env:USERPROFILE\.claude\skills\"
```

## 5. Start coaching

Open your agent and say something like *"I want to start training for a half marathon in April."* On first run the skill:

1. Checks the Intervals.icu connection with a cheap read (`get_wellness_data`)
2. Pulls your thresholds and zones (`get_sport_settings`)
3. Asks intake questions: goals, availability, injuries, equipment
4. Builds your plan and writes workouts, race events, and daily **Nutrition Target** notes to your Intervals.icu calendar

Athlete memory is stored locally in `~/.training/` (Windows: `%USERPROFILE%\.training\`), outside this repo.

## Sanity check

- [ ] `get_wellness_data` returns real data, not a 401
- [ ] `update_wellness`, `update_sport_settings`, `add_nutrition_targets` show up in the agent's tool list (if not, you're running the stock upstream server)
- [ ] The skill shows up as available in your agent
- [ ] Recent activities come back with real data, not Strava stubs (see 1.2)

## Troubleshooting

| Problem | Fix |
|---|---|
| `401 Unauthorized` | Wrong or missing `API_KEY` in `.env`. Regenerate it in Developer Settings. |
| Activities have no data / "not available via the API" | They were imported from Strava. Connect Garmin/Wahoo/etc. directly (see 1.2). |
| No HRV or sleep data | Wellness sync is off for your device (see 1.3). |
| Agent can't find `uv` | Use the absolute path to `uv` in the MCP config. |
| Athlete ID errors | Include the leading `i`, e.g. `i12345`. |

More detail: [`adaptive-endurance-coach/AGENT.md`](./adaptive-endurance-coach/AGENT.md) and [`intervals-mcp-server/README.md`](./intervals-mcp-server/README.md).

## Privacy

The coach works with personal health data (training, injuries, weight, HRV). That data is sent to whichever AI provider your agent uses. Share only what you're comfortable with. This repo contains no athlete data, and `.env`, `activities.json`, and `.training/` are gitignored.

## Disclaimer

This is not a replacement for a qualified coach or medical professional.
