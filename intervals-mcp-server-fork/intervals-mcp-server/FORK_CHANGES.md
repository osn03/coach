# Fork changes — write tools for the Adaptive Endurance Coach

This fork adds four write capabilities to the upstream
[mvilanova/intervals-mcp-server](https://github.com/mvilanova/intervals-mcp-server)
so an AI coaching skill can manage an athlete on Intervals.icu, not just read it.
The generic HTTP client already supported authenticated PUT/POST; these changes
only add tool wrappers around existing Intervals.icu API endpoints.

Licensed under GPL-3.0, same as upstream.

## New / changed tools

1. **`add_or_update_event` — new `category` argument.**
   Previously hardcoded `category="WORKOUT"`, so it could only create planned
   workouts. Now accepts `category` (default `"WORKOUT"`, backwards-compatible),
   enabling `RACE_A` / `RACE_B` / `RACE_C` goal events plus NOTE, HOLIDAY, SICK,
   INJURED, SET_EFTP, FITNESS_DAYS, SEASON_START, TARGET. Invalid categories are
   rejected. (`src/intervals_mcp_server/tools/events.py`)

2. **`add_nutrition_targets` — new tool.**
   Writes a day's calorie + macro *targets* as a structured, idempotent
   "Nutrition Target" calendar note (Intervals.icu has no planned-nutrition field;
   wellness carbs/protein/kcal are consumed actuals). Update in place via `event_id`.
   POSTs/PUTs `/athlete/{id}/events`. (`tools/events.py`)

3. **`update_wellness` — new tool.**
   Partial-update a day's wellness entry: weight, HRV, resting HR, sleep,
   soreness/fatigue/stress/mood, comments, plus an `extra_fields` escape hatch.
   Only provided fields are sent. `PUT /athlete/{id}/wellness/{date}`.
   Computed fitness fields (ctl/atl/rampRate/readiness) are read-only and not settable.
   (`tools/wellness.py`)

4. **`get_sport_settings` / `update_sport_settings` — new tools.**
   Read and write per-sport thresholds and zones (FTP, indoor FTP, W', threshold
   pace, LTHR, max/resting HR, and arbitrary zone arrays via `extra_fields`).
   `GET /athlete/{id}/sport-settings`, `PUT /athlete/{id}/sport-settings/{id-or-type}`
   (pass a sport type like "Run" instead of an ID). (`tools/athlete.py` — new file)

`server.py` imports and re-exports the new tools so they register.

## Verified
- Existing test suite passes unchanged.
- All 4 additions emit the correct method + URL + body (checked against the
  Intervals.icu API: wellness PUT to `/wellness/{date}`, sport-settings PUT to
  `/sport-settings/{sport}`, events POST with the chosen category).

## Not added (remain gaps)
- No annual-plan (ATP) object exists in the Intervals.icu API — season structure
  is kept in the skill's own memory.
- Power curve only (`get_athlete_power_curves`); run pace-curves / HR-curves are
  not wrapped, so non-cycling PRs are tracked from activity data in skill memory.
