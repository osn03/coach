"""
Athlete sport-settings MCP tools for Intervals.icu.

This module adds read/write access to per-sport settings (FTP, threshold pace,
LTHR, and zones). Intervals.icu stores these separately per discipline, so an
athlete typically has one settings object per sport (Ride, Run, Swim, ...).

Endpoints:
    GET  /athlete/{id}/sport-settings
    PUT  /athlete/{id}/sport-settings/{id-or-type}   e.g. {"ftp": 300}

Passing an activity type ("Ride", "Run", "Swim", ...) in place of an ID updates
the settings for the matching sport. Requires SETTINGS:WRITE scope, which a
personal API key has.
"""

from typing import Any

from intervals_mcp_server.api.client import make_intervals_request
from intervals_mcp_server.config import get_config
from intervals_mcp_server.utils.validation import resolve_athlete_id

# Import mcp instance from shared module for tool registration
from intervals_mcp_server.mcp_instance import mcp  # noqa: F401

config = get_config()


def _format_sport_settings(entry: dict[str, Any]) -> str:
    """Render a single sport-settings object as a compact readable block."""
    sid = entry.get("id", "N/A")
    types = entry.get("types") or entry.get("type") or "N/A"
    lines = [
        f"Sport settings id: {sid}  (types: {types})",
        f"  FTP: {entry.get('ftp', 'N/A')}  indoor FTP: {entry.get('indoor_ftp', 'N/A')}",
        f"  W': {entry.get('w_prime', 'N/A')}",
        f"  Threshold pace (m/s): {entry.get('threshold_pace', 'N/A')}",
        f"  LTHR: {entry.get('lthr', 'N/A')}  max HR: {entry.get('max_hr', 'N/A')}  resting HR: {entry.get('resting_hr', 'N/A')}",
    ]
    if entry.get("power_zones") is not None:
        lines.append(f"  Power zones: {entry.get('power_zones')} (names: {entry.get('power_zone_names', 'N/A')})")
    if entry.get("hr_zones") is not None:
        lines.append(f"  HR zones: {entry.get('hr_zones')} (names: {entry.get('hr_zone_names', 'N/A')})")
    if entry.get("pace_zones") is not None:
        lines.append(f"  Pace zones: {entry.get('pace_zones')}")
    return "\n".join(lines)


@mcp.tool()
async def get_sport_settings(
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """Get per-sport settings (FTP, threshold pace, LTHR, zones) for an athlete.

    Returns one block per sport. Use the ``id`` shown here (or the sport type, e.g.
    "Run") when calling ``update_sport_settings``.

    Args:
        athlete_id: The Intervals.icu athlete ID (optional, uses ATHLETE_ID from .env)
        api_key: The Intervals.icu API key (optional, uses API_KEY from .env)
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/sport-settings", api_key=api_key
    )

    if isinstance(result, dict) and result.get("error"):
        return f"Error fetching sport settings: {result.get('message')}"
    if not result:
        return f"No sport settings found for athlete {athlete_id_to_use}."

    entries = result if isinstance(result, list) else [result]
    blocks = [_format_sport_settings(e) for e in entries if isinstance(e, dict)]
    return "Sport Settings:\n\n" + "\n\n".join(blocks)


@mcp.tool()
async def update_sport_settings(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    sport: str,
    athlete_id: str | None = None,
    api_key: str | None = None,
    ftp: int | None = None,
    indoor_ftp: int | None = None,
    w_prime: int | None = None,
    threshold_pace: float | None = None,
    lthr: int | None = None,
    max_hr: int | None = None,
    resting_hr: int | None = None,
    extra_fields: dict[str, Any] | None = None,
) -> str:
    """Update per-sport settings (FTP / threshold pace / LTHR / etc.) for an athlete.

    Only the fields you pass are sent; everything else for that sport is left as-is.

    Args:
        sport: The sport settings id, OR an activity type to match ("Ride", "Run",
            "Swim", "Row", "Walk"). Passing the type is usually easiest.
        athlete_id: The Intervals.icu athlete ID (optional, uses ATHLETE_ID from .env)
        api_key: The Intervals.icu API key (optional, uses API_KEY from .env)
        ftp: Functional Threshold Power (watts)
        indoor_ftp: Indoor/trainer FTP (watts)
        w_prime: W' anaerobic work capacity (joules)
        threshold_pace: Threshold pace in meters/second (Intervals.icu stores pace
            as m/s; convert from min/km or min/mile before calling)
        lthr: Lactate threshold heart rate (bpm)
        max_hr: Maximum heart rate (bpm)
        resting_hr: Resting heart rate (bpm)
        extra_fields: Any other sport-settings fields to set, as a dict using
            Intervals.icu field names (e.g. power/HR/pace zone arrays). Merged last.
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    if not sport:
        return "Error: 'sport' (a sport-settings id or activity type like 'Run') is required."

    candidate_fields: dict[str, Any] = {
        "ftp": ftp,
        "indoor_ftp": indoor_ftp,
        "w_prime": w_prime,
        "threshold_pace": threshold_pace,
        "lthr": lthr,
        "max_hr": max_hr,
        "resting_hr": resting_hr,
    }
    data: dict[str, Any] = {k: v for k, v in candidate_fields.items() if v is not None}
    if extra_fields:
        data.update(extra_fields)

    if not data:
        return "Error: no settings fields provided to update."

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/sport-settings/{sport}",
        api_key=api_key,
        data=data,
        method="PUT",
    )

    if isinstance(result, dict) and result.get("error"):
        return f"Error updating sport settings: {result.get('message')}"

    updated = ", ".join(data.keys())
    return f"Sport settings updated for '{sport}' (fields: {updated})."
