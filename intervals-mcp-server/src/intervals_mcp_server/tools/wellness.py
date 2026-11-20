"""
Wellness-related MCP tools for Intervals.icu.

This module contains tools for retrieving athlete wellness data.
"""

from datetime import datetime
from typing import Any

from intervals_mcp_server.api.client import make_intervals_request
from intervals_mcp_server.config import get_config
from intervals_mcp_server.utils.formatting import format_wellness_entry
from intervals_mcp_server.utils.validation import (
    resolve_athlete_id,
    resolve_date_params,
    validate_date,
)

# Import mcp instance from shared module for tool registration
from intervals_mcp_server.mcp_instance import mcp  # noqa: F401

config = get_config()


@mcp.tool()
async def get_wellness_data(
    athlete_id: str | None = None,
    api_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    include_all_fields: bool = False,
) -> str:
    """Get wellness data for an athlete from Intervals.icu.

    By default returns standard wellness fields (training metrics, vitals, sleep,
    subjective scores, etc.). Set include_all_fields=True to also include any
    additional or custom fields configured by the user in Intervals.icu.

    Args:
        athlete_id: The Intervals.icu athlete ID (optional, will use ATHLETE_ID from .env if not provided)
        api_key: The Intervals.icu API key (optional, will use API_KEY from .env if not provided)
        start_date: Start date in YYYY-MM-DD format (optional, defaults to 30 days ago)
        end_date: End date in YYYY-MM-DD format (optional, defaults to today)
        include_all_fields: If True, include additional and custom fields beyond the standard set (optional, defaults to False)
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    start_date, end_date = resolve_date_params(start_date, end_date)

    params = {"oldest": start_date, "newest": end_date}

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/wellness", api_key=api_key, params=params
    )

    if isinstance(result, dict) and "error" in result:
        return f"Error fetching wellness data: {result.get('message')}"

    if not result:
        return (
            f"No wellness data found for athlete {athlete_id_to_use} in the specified date range."
        )

    wellness_summary = "Wellness Data:\n\n"

    if isinstance(result, dict):
        for date_str, data in result.items():
            if isinstance(data, dict) and "date" not in data:
                data["date"] = date_str
            wellness_summary += format_wellness_entry(data, include_all_fields=include_all_fields) + "\n\n"
    elif isinstance(result, list):
        for entry in result:
            if isinstance(entry, dict):
                wellness_summary += format_wellness_entry(entry, include_all_fields=include_all_fields) + "\n\n"

    return wellness_summary


@mcp.tool()
async def update_wellness(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    date: str | None = None,
    athlete_id: str | None = None,
    api_key: str | None = None,
    weight: float | None = None,
    resting_hr: int | None = None,
    hrv: float | None = None,
    sleep_secs: int | None = None,
    sleep_score: float | None = None,
    soreness: int | None = None,
    fatigue: int | None = None,
    stress: int | None = None,
    mood: int | None = None,
    comments: str | None = None,
    extra_fields: dict[str, Any] | None = None,
) -> str:
    """Create or update a wellness entry for a single day on Intervals.icu.

    Writes to PUT /athlete/{id}/wellness/{date}. Only the fields you pass are sent,
    so existing values for that day are preserved (partial update). Use this to log
    morning metrics the athlete reports (weight, HRV, resting HR, sleep, subjective
    soreness/fatigue/stress/mood) back to the platform.

    Note: computed fitness fields (ctl, atl, rampRate, readiness) are derived by
    Intervals.icu from activities and cannot be set here.

    Args:
        date: Day to update in YYYY-MM-DD format (optional, defaults to today)
        athlete_id: The Intervals.icu athlete ID (optional, uses ATHLETE_ID from .env)
        api_key: The Intervals.icu API key (optional, uses API_KEY from .env)
        weight: Body weight in kg
        resting_hr: Resting heart rate (bpm)
        hrv: Heart rate variability (rMSSD, ms)
        sleep_secs: Sleep duration in seconds (e.g. 8 h = 28800)
        sleep_score: Sleep quality score
        soreness: Subjective soreness (typically 1-4)
        fatigue: Subjective fatigue (typically 1-4)
        stress: Subjective stress (typically 1-4)
        mood: Subjective mood (typically 1-4)
        comments: Free-text note for the day
        extra_fields: Any other wellness fields to set, as a dict using Intervals.icu
            field names (e.g. {"steps": 12000, "spO2": 97}). Merged last, so it can
            override the named args above if needed.
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    try:
        validated_date = validate_date(date)
    except ValueError as e:
        return f"Error: {e}"

    # Intervals.icu wellness fields are camelCase and mirror what the GET returns.
    # The body's "id" is the date. Only non-None values are sent (partial update).
    candidate_fields: dict[str, Any] = {
        "id": validated_date,
        "weight": weight,
        "restingHR": resting_hr,
        "hrv": hrv,
        "sleepSecs": sleep_secs,
        "sleepScore": sleep_score,
        "soreness": soreness,
        "fatigue": fatigue,
        "stress": stress,
        "mood": mood,
        "comments": comments,
    }
    data: dict[str, Any] = {k: v for k, v in candidate_fields.items() if v is not None}
    if extra_fields:
        data.update(extra_fields)

    if len(data) <= 1:  # only "id" present
        return "Error: no wellness fields provided to update."

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/wellness/{validated_date}",
        api_key=api_key,
        data=data,
        method="PUT",
    )

    if isinstance(result, dict) and result.get("error"):
        return f"Error updating wellness: {result.get('message')}"

    updated = ", ".join(k for k in data if k != "id")
    return f"Wellness updated for {validated_date} (fields: {updated})."
