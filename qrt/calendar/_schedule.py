"""Exchange session schedules in local market time."""

import exchange_calendars as xcals
import pandas as pd
from exchange_calendars.errors import InvalidCalendarName


def schedule(
    start: str | pd.Timestamp,
    end: str | pd.Timestamp,
    exchange: str,
) -> pd.DataFrame:
    """Return exchange sessions and their local opening and closing times.

    Args:
        start: First calendar date to include.
        end: Last calendar date to include.
        exchange: ISO 10383 market identifier code, such as ``"XNYS"`` or
            ``"XSTO"``.

    Returns:
        DataFrame indexed by session date with timezone-aware ``open`` and
        ``close`` columns expressed in the exchange's local timezone.

    Raises:
        ValueError: If the exchange is unknown, a date is missing, or ``start``
            is after ``end``.
    """
    try:
        calendar = xcals.get_calendar(exchange)
    except InvalidCalendarName as exc:
        raise ValueError(f"unknown exchange calendar: {exchange!r}") from exc

    start_date = pd.Timestamp(start)
    end_date = pd.Timestamp(end)
    if pd.isna(start_date) or pd.isna(end_date):
        raise ValueError("start and end must not be missing")

    start_date = start_date.tz_localize(None).normalize()
    end_date = end_date.tz_localize(None).normalize()
    if start_date > end_date:
        raise ValueError("start must be on or before end")

    sessions = calendar.sessions_in_range(start_date, end_date)
    result = calendar.schedule.loc[sessions, ["open", "close"]].copy()
    result["open"] = result["open"].dt.tz_convert(calendar.tz)
    result["close"] = result["close"].dt.tz_convert(calendar.tz)
    result.index = pd.DatetimeIndex(result.index, name="session")
    return result