# Adaptive Endurance Coach

An AI endurance coach and sports nutritionist for **swimming, cycling, running, and triathlon**. It runs inside Claude Code (or another MCP-capable AI agent) and uses your [Intervals.icu](https://intervals.icu/) account as the single source of truth. It reads your training and recovery data, then writes workouts, races, and daily nutrition targets back to your Intervals.icu calendar.

The repo has two parts, and the setup script installs both:

| Folder | What it is | License |
|---|---|---|
| [`adaptive-endurance-coach/`](./adaptive-endurance-coach) | The coaching **skill**: the training philosophy, decision rules, and reference modules the AI follows. | MIT |
| [`intervals-mcp-server/`](./intervals-mcp-server) | A fork of [mvilanova/intervals-mcp-server](https://github.com/mvilanova/intervals-mcp-server) that connects the AI to Intervals.icu. It adds the write tools the coach needs (see [`FORK_CHANGES.md`](./intervals-mcp-server/FORK_CHANGES.md)). All credit for the original server goes to its author. | GPL-3.0 |

---

## Setup (about 10 minutes)

### Step 1: Set up Intervals.icu (in your browser)

1. **Create an account** at <https://intervals.icu/>. The free tier is enough.
2. **Connect your devices** under **Settings → Connections**. See [what to connect](#what-to-connect-to-intervalsicu) below. Connect your watch or bike-computer platform **directly**, not only through Strava.
3. **Turn on wellness sync** for the device or app that tracks your HRV, resting HR, sleep, and weight, if you have one.
4. **Check sport settings** under **Settings → Sport Settings**. Rough values are fine, since the coach tests and corrects them later:
   - **Ride:** FTP (and indoor FTP if it's different)
   - **Run:** threshold pace and LTHR
   - **Swim:** threshold pace (CSS)
   - **All sports:** max HR and resting HR
5. **Get your API key and athlete ID.** Under **Settings → Developer Settings**, click **Generate API key**. Your athlete ID is shown there and in your profile URL (`https://intervals.icu/athlete/i123456/...` → `i123456`).

### Step 2: Run the setup script

You need [git](https://git-scm.com/) and [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) (or Claude Desktop). You don't need to install Python yourself.

**Windows (PowerShell):**
```powershell
git clone https://github.com/osn03/coach.git
cd coach
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

**macOS / Linux:**
```bash
git clone https://github.com/osn03/coach.git
cd coach
chmod +x setup.sh && ./setup.sh
```

The script:
1. Installs [uv](https://docs.astral.sh/uv/) if it's missing. uv then downloads Python 3.12 automatically.
2. Installs the MCP server's dependencies.
3. Asks for your **athlete ID** and **API key** (typing is hidden), checks them against Intervals.icu, and saves them to `intervals-mcp-server/.env`.
4. Installs the skill, with all its reference modules, into `~/.claude/skills/adaptive-endurance-coach/`.
5. Registers the `intervals` MCP server with Claude Code. Without Claude Code, it prints the JSON block to paste into Claude Desktop's config.

The script is safe to re-run. Run it again after `git pull` to update the installed skill.

### Step 3: Start coaching

Restart Claude and say something like *"I want to start training for a half marathon in April."* On first run the coach:

1. Checks the Intervals.icu connection.
2. Reads your thresholds, recent activities, and fitness trend.
3. Asks about your goals, weekly hours, injuries, equipment, and body data (weight, height, age, sex). It needs these for the calorie math.
4. Asks you to pick a coaching tone: **Mentor**, **Catalyst**, **Motivator**, **Wingman**, or **Straight-Shooter**.
5. Builds your plan and puts it on your Intervals.icu calendar.

> **Keep your API key secret.** It gives full read/write access to your Intervals.icu account. It lives only in `intervals-mcp-server/.env`, which is gitignored. Never paste it into a chat.

---

## What to connect to Intervals.icu

| Connect | Why the coach needs it | Required? |
|---|---|---|
| **Your training device platform:** Garmin Connect, Wahoo, Coros, Suunto, Polar, Zwift, TrainingPeaks Virtual, etc. | Completed activities with power, HR, pace, and GPS streams. The coach analyses every session against what it prescribed. | **Yes** |
| **A wellness source:** Garmin, Oura, Whoop, Polar, HRV4Training, etc. | Daily HRV, resting HR, sleep, and weight. These drive the green/amber/red readiness decisions. | Strongly recommended. Without it, the coach falls back to resting HR, sleep, and how you feel, which you report yourself. |
| **Calendar sync to your device** (Garmin, Wahoo, Zwift, etc.) | Structured workouts the coach writes to Intervals.icu get pushed to your watch, bike computer, or trainer. | Recommended |
| **A power meter / HR strap** | More accurate load, zones, and nutrition math | Optional |

### ⚠️ Strava alone is not enough
Strava's API terms stop Intervals.icu from passing Strava-imported activities to other apps. Through the API they come back as empty stubs (`"STRAVA activities are not available via the API"`), so **the coach can't see them**. You can keep Strava for social sharing, but connect your device platform to Intervals.icu directly. You can also upload `.fit` files manually.

---

## How data flows

```
 ┌────────────────────────┐   activities, HRV,     ┌──────────────────────┐
 │ Garmin / Wahoo / Coros │   sleep, weight        │                      │
 │ Oura / Whoop / Zwift … │ ─────────────────────► │     Intervals.icu    │
 └────────────────────────┘                        │  (source of truth)   │
            ▲                                      │                      │
            │   planned workouts sync to device    │ computes CTL / ATL / │
            └───────────────────────────────────── │ Form, zones, load    │
                                                   └──────────┬───────────┘
                                                        reads │ ▲ writes
                                                  (REST API + │ │ your API key)
                                                              ▼ │
                                                   ┌──────────────────────┐
                                                   │ intervals-mcp-server │  runs locally
                                                   │  (this repo)         │  on your machine
                                                   └──────────┬───────────┘
                                                              │ MCP tools
                                                              ▼
 ┌────────────────────────┐   reads/writes         ┌──────────────────────┐
 │   ~/.training/         │ ◄────────────────────► │  Claude + coaching   │ ◄──► you (chat)
 │ profile, plans, race   │   long-term memory     │  skill               │
 │ plans, decision log    │                        └──────────────────────┘
 └────────────────────────┘
```

**The coach reads** from Intervals.icu: completed activities (with intervals and streams), the planned calendar, fitness/fatigue/form (CTL/ATL/TSB), ramp rate, wellness (HRV, resting HR, sleep, weight, soreness), per-sport thresholds and zones, power curves, and gear.

**The coach writes** to Intervals.icu:
- **Structured workouts** with stepped targets (%FTP, watts, %HR, pace, zones), which sync to your device
- **Races** as `RACE_A` / `RACE_B` / `RACE_C` goal events
- **Daily "Nutrition Target" notes** with calories, carbs, protein, and fat matched to that day's training
- **Threshold and zone updates** after tests (FTP, threshold pace, LTHR)
- **Wellness entries** you report in chat (weight, HRV, sleep, soreness)

**The coach stores locally** in `~/.training/` (Windows: `%USERPROFILE%\.training\`): athlete profile, race calendar, injuries, nutrition plan, versioned training plans, race plans, progress reviews, and a decision log. This covers what Intervals.icu's API can't hold, such as the season plan and run/swim PR history. None of it leaves your machine except through your conversations with the AI provider.

---

## Training philosophy and principles

The coach's philosophy is part of the skill itself: [`SKILL.md`](./adaptive-endurance-coach/skills/adaptive-endurance-coach/SKILL.md) plus five reference modules that the AI loads before acting in each area. The setup script installs all of them, so everyone who clones the repo gets the same rules.

| Module | Covers |
|---|---|
| [`training-methods.md`](./adaptive-endurance-coach/skills/adaptive-endurance-coach/references/training-methods.md) | Evidence tiers, periodization, intensity distribution, key sessions, strength, heat/altitude, testing, female and masters athletes |
| [`load-and-recovery.md`](./adaptive-endurance-coach/skills/adaptive-endurance-coach/references/load-and-recovery.md) | Load metrics, daily readiness rules, sleep, illness, injury, data hygiene, overtraining |
| [`race-execution.md`](./adaptive-endurance-coach/skills/adaptive-endurance-coach/references/race-execution.md) | Taper, written race plans, pacing, race week, post-race recovery |
| [`nutrition.md`](./adaptive-endurance-coach/skills/adaptive-endurance-coach/references/nutrition.md) | Daily calorie and macro targets, in-session fueling, hydration, supplements, REDs safety floor |
| [`onboarding.md`](./adaptive-endurance-coach/skills/adaptive-endurance-coach/references/onboarding.md) | First-run intake, threshold setup, coaching tones |

### Core rules (non-negotiable)
1. **The primary goal comes first.** Every decision traces back to your A-race or A-goal. Trade-offs, such as B-races or group rides, are stated openly and settled in the A-goal's favour unless you override.
2. **The coach never makes up data.** When data is missing or suspect, it says so and states how confident it is.
3. **Health before performance.** It screens for under-fueling (REDs), illness, and injury before optimizing anything.
4. **Methods are tiered by evidence.**
   - **Tier A (proven)** is the default.
   - **Tier B (promising)** is used deliberately and labelled as Tier B.
   - **Tier C (unsupported)** is never presented as effective.
   - When your own logged response contradicts population research, your data wins.
5. **Nutrition is on by default.** Daily targets go on your calendar whenever training is planned. You can opt out.
6. **It is a coach, not a doctor.** Red flags such as chest pain, fainting, non-resolving injury, or signs of disordered eating get referred to a professional.
7. **Every decision is logged:** trigger → data → decision → expected outcome. The log is reviewed against what actually happened.
8. **Everything is individualized.** Intensity split, volume, taper length, and fueling depend on you, your sport, and your phase.

### Key facts the coach works from
**Periodization and intensity**
- Plans are built **backward from the A-race**: Base → Build → Peak → Taper → Transition.
- Recovery weeks come every 3–5 weeks, or every 3–4 for masters athletes (about 45+).
- About **80% easy / 20% hard** is the default. Intensity shifts from **pyramidal toward polarized** as the race gets closer. The "moderate-intensity rut" (easy days too hard, hard days too easy) is policed with actual time-in-zone data.

**Key sessions**
- Long aerobic sessions with **durability work**: quality efforts placed late, after hours of load.
- VO2max intervals: 4–8 × 3–6 min, or 30/15s.
- Threshold / sweet spot: 2–4 × 10–20 min at 88–100% FTP.
- Strides and sprints, and race-specific bricks for triathletes.

**Strength training is Tier A and not optional**
- Base phase: 2×/week heavy, low-rep lifting (3–5 × 3–6).
- Build/peak: 1×/week maintenance. The last heavy session is 7–10 days before the race.
- Runners also do plyometrics.

**Load management**
- Fitness (CTL) ramp is capped at roughly **+3 to +7 per week**.
- ACWR (acute:chronic workload ratio) is used only as one heuristic among several, because its evidence is contested.
- Run load is tracked separately, because musculoskeletal tolerance usually limits run volume before aerobic fitness does.

**Daily readiness: green / amber / red**
Based on your **7-day HRV average** against your own ~60-day baseline, plus resting HR, sleep, and soreness. A single bad reading never cancels a key session, and a red day is never trained through.
- **Green:** train as planned.
- **Amber:** keep the duration, drop the intensity to easy.
- **Red:** rest or 30–45 min very easy, and cut next week's load by 20–30%.

**Illness: the "neck check"**
- Symptoms above the neck only and no fever: easy training only.
- Fever, chest symptoms, body aches, or GI illness: full rest until 24 h symptom-free.

**Taper**
- Volume drops **40–60%**, tapering off progressively.
- **Intensity and frequency are kept.**
- About **2 weeks** by default (range 1–3), adjusted from how your past tapers went.
- Race-day form (TSB) targets: about **+15 to +25** for an A-race and **+5 to +10** for a B-race.

**Pacing**
- Even or slightly negative splits, with explicit **early caps**.
- Bike targets by intensity factor (IF, average power as a fraction of FTP): **0.83–0.87** for a 70.3, **0.70–0.78** for an Ironman.
- In triathlon, the first 1–2 km of the run is deliberately slower than goal pace.
- In heat, pace expectations are adjusted down; effort caps stay the same.

**Nutrition**
- Calories: BMR from the Mifflin-St Jeor equation × 1.2, plus the energy of that day's sessions.
- Protein: **1.6–2.2 g/kg**.
- Carbs follow the day's load: **3–5 g/kg** on rest days, **5–7** on moderate days, **8–10** on heavy days, and **8–12** when carb-loading.
- No calorie deficit during heavy build blocks, taper, or race week.
- **Hard floor:** energy availability never goes below 30 kcal/kg of fat-free mass.

**Fueling during sessions**
- 30–60 g carbs/hour for 1–2.5 h sessions.
- 60–90 g/hour, up to 90–120 g/hour, for long races, using glucose:fructose mixes.
- The gut is trained to these rates over 4+ weeks. Nothing new is tried on race day.

**Supplements**
Only caffeine, creatine, nitrate (beetroot), sodium bicarbonate, and beta-alanine are treated as Tier A. Third-party-tested products are recommended.

**Testing and limiters**
- Retests every 4–8 weeks: FTP or critical power, run threshold or critical speed, swim CSS, and a durability test.
- The coach identifies your current **limiter** and puts extra training there.

---

## Manual setup and troubleshooting

To set things up by hand, or to have an AI agent do it, follow [`adaptive-endurance-coach/AGENT.md`](./adaptive-endurance-coach/AGENT.md). The manual MCP registration for Claude Code is:

```bash
claude mcp add intervals --scope user -- uv run --directory /full/path/to/coach/intervals-mcp-server python src/intervals_mcp_server/server.py
```

| Problem | Fix |
|---|---|
| `401 Unauthorized` | The API key or athlete ID in `intervals-mcp-server/.env` is wrong. Re-run the setup script. |
| Activities have no data / "not available via the API" | They came in via Strava. Connect your device platform to Intervals.icu directly. |
| No HRV or sleep data | Turn on wellness sync for your device under Settings → Connections. |
| The coach doesn't know its write tools (`update_wellness`, `add_nutrition_targets`, …) | Claude is pointed at the stock upstream server. Re-run the setup script. |
| The skill doesn't show up | Check that `~/.claude/skills/adaptive-endurance-coach/SKILL.md` exists, then restart Claude. |
| `uv` not found after install | Open a new terminal and re-run the script. |

To check that everything works, ask Claude to *"run get_wellness_data for the last 7 days"*. You should see real numbers, not an auth error.

## Privacy

The coach works with personal health data: training, injuries, weight, HRV, and optionally bloodwork. That data is sent to whichever AI provider your agent uses. Share only what you're comfortable with; every optional question can be skipped or answered approximately. This repo contains no athlete data, and `.env`, `activities.json`, and `.training/` are gitignored.

## Disclaimer

This is not a replacement for a qualified coach or medical professional. It exists for when a human coach isn't accessible, not as a claim that it's better.
