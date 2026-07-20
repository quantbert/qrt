"""Closed calendar dates following an exchange session."""

import exchange_calendars as xcals
import pandas as pd
from exchange_calendars.errors import InvalidCalendarName


def non_trading_days_after(dates: pd.Series, exchange: str) -> pd.Series:
    """Count closed calendar dates after each exchange session.

    An early close is still a trading session. For example, a Friday early
    close followed by a Monday session has two non-trading days after it.

    Args:
        dates: Session dates. Time components are ignored and the index is
            preserved.
        exchange: ISO 10383 market identifier code, such as ``"XNYS"`` or
            ``"XSTO"``.

    Returns:
        Integer Series named ``non_trading_days_after``.

    Raises:
        TypeError: If ``dates`` is not a Series.
        ValueError: If the exchange is unknown or a value is missing or is not
            an exchange session.
    """
    if not isinstance(dates, pd.Series):
        raise TypeError("dates must be a pandas Series")

    try:
        calendar = xcals.get_calendar(exchange)
    except InvalidCalendarName as exc:
        raise ValueError(f"unknown exchange calendar: {exchange!r}") from exc

    session_dates = pd.to_datetime(dates, errors="raise").dt.normalize()
    if session_dates.isna().any():
        raise ValueError("dates must not contain missing values")
    if session_dates.dt.tz is not None:
        session_dates = session_dates.dt.tz_localize(None)

    unique_dates = pd.DatetimeIndex(session_dates.unique())
    invalid_dates = [date for date in unique_dates if not calendar.is_session(date)]
    if invalid_dates:
        formatted = ", ".join(date.date().isoformat() for date in invalid_dates)
        raise ValueError(
            f"dates must be sessions for exchange {exchange!r}: {formatted}"
        )

    gaps = {
        date: (calendar.next_session(date) - date).days - 1
        for date in unique_dates
    }
    return session_dates.map(gaps).astype("int64").rename("non_trading_days_after")