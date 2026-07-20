# Adaptive Endurance Coach

A world-class endurance coaching **skill** for agentic AI tools (Claude Code, and likely other MCP-capable agents) — swimming, cycling, running, and triathlon. It manages long-term athlete development the way a real coach + sports nutritionist would: periodized training plans, readiness-guided daily adjustments, evidence-tiered methods, written race plans with individualized tapers, and a nutrition engine that writes daily calorie/macro targets straight onto your Intervals.icu calendar.

Intervals.icu is the source of truth; Strava/Garmin/Wahoo data arrives natively through Intervals.icu's own device sync.

## What it does

- **Periodized training plans** built backward from your A-race, using evidence-tiered methods (proven vs. promising vs. unsupported — labeled honestly, not sold as all equally solid).
- **Daily readiness logic** — HRV/sleep/soreness trend rules that decide whether today's session proceeds, gets softened, or becomes a rest day.
- **Injury-aware programming** — rehab loading, pain-monitor rules, and a strength program that adapts around what's actually healing.
- **Race execution planning** — written race plans with pacing, fueling, and a taper individualized to your own history, not a generic template.
- **Nutrition as a core function, on by default** — daily calorie and macro targets computed from your actual training load and written to your Intervals.icu calendar automatically (as dated "Nutrition Target" notes).
- **Persistent athlete memory** — the skill maintains a structured history (`~/.training/`) across sessions: profile, race calendar, injuries, nutrition history, decision log, and versioned plans, so every coaching call is grounded in your own data, not a fresh guess each time.

## What this repo does NOT include

**The Intervals.icu MCP server is a separate open-source project and is not vendored here.** This skill targets a fork of [mvilanova/intervals-mcp-server](https://github.com/mvilanova/intervals-mcp-server) that adds the write tools the coach needs (`update_wellness`, `update_sport_settings`, `add_nutrition_targets`, and a RACE category on events). All credit for the original server goes to its author. See `AGENT.md` for setup. The server is GPL-3.0; running your own modified copy privately is unrestricted, and publishing a modified copy requires releasing it under GPL-3.0.

Strava is not a separate integration here — Intervals.icu already ingests Strava/Garmin/Wahoo activities via its own sync.

## Setup

The fastest path: point an agentic coding assistant (Claude Code or similar) at **[`AGENT.md`](./AGENT.md)** and ask it to read the file and set everything up. It will:

1. Clone and install the Intervals.icu MCP server (the forked one)
2. Walk you through configuring the Intervals.icu API key + athlete ID in the server's .env (never typed into chat)
3. Register the MCP server with your agent
4. Install this skill into your agent's skills directory
5. Hand off to the skill's own onboarding flow

`AGENT.md` has full step-by-step instructions (with explicit commands for macOS, Linux, and Windows) if you'd rather do it by hand.

### Prerequisites

- An agentic AI coding tool with MCP support (Claude Code, etc.) — a $20/mo tier subscription is generally sufficient.
- An [Intervals.icu](https://intervals.icu/) account (free tier is fine) plus a personal API key and your athlete ID (from Settings → Developer, and your profile URL).
- Python 3.10+ and [`uv`](https://docs.astral.sh/uv/) (installed automatically if missing — see `AGENT.md`).

## A note on data privacy

Setting this up means giving an AI assistant a lot of personal health and fitness information — training history, injury history, age, weight, goals, and optionally things like sweat-test results or bloodwork. That data goes to whichever AI provider you're using (e.g. Anthropic, if using Claude), subject to their data policies at the time. You're never obligated to provide everything the skill asks for; you can decline or substitute adjacent-but-inexact information (e.g., stating an approximate age) for anything you're not comfortable sharing. Go in with that tradeoff in mind.

## Repo structure

```
adaptive-endurance-coach/
  README.md
  AGENT.md                          <- give this to your agent for automated setup
  skills/adaptive-endurance-coach/
    SKILL.md                        <- core skill definition, loaded every session
    references/                     <- loaded on demand, by topic
      onboarding.md                 <- first-run setup, intake, tone selection
      load-and-recovery.md          <- readiness rules, HRV/illness/injury logic
      training-methods.md           <- evidence-tiered periodization, key sessions
      race-execution.md             <- race plans, taper design, pacing
      nutrition.md                  <- daily targets, fueling, supplements, safety floors
```

## Feedback

This is a work in progress — if you try it, feedback on what's missing or what could be sharper is welcome via issues/PRs.

## Disclaimer

Not a replacement for a human coach. If you can afford one, a good coach brings dynamic adjustment, deep sport-specific experience, and accountability that this can't fully replicate. This exists as an option for when that isn't accessible — not as a claim that it's better.
