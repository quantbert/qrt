"""Cross-sectional Elo ratings for equity universes."""

import numpy as np
import pandas as pd


def _expected_score(rating_a: float, rating_b: float) -> float:
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def _update_elo(
    rating_a: float,
    rating_b: float,
    score_a: float,
    k_a: float,
) -> float:
    return rating_a + k_a * (score_a - _expected_score(rating_a, rating_b))


def _run_matches(
    snapshot: pd.DataFrame,
    *,
    epsilon: float,
    matches_per_stock: int,
) -> pd.DataFrame:
    new_elos: dict[object, float] = {}
    matches_played: dict[object, int] = {}

    for symbol, row in snapshot.iterrows():
        candidates = snapshot[
            (snapshot["sectorid"] == row["sectorid"])
            & (snapshot.index != symbol)
        ].copy()

        if candidates.empty:
            new_elos[symbol] = row["elo"]
            matches_played[symbol] = 0
            continue

        candidates["elo_diff"] = (candidates["elo"] - row["elo"]).abs()
        count = min(matches_per_stock, len(candidates))
        opponents = candidates.nsmallest(count, "elo_diff")
        matches_played[symbol] = len(opponents)
        new_rating = row["elo"]

        for _, opponent in opponents.iterrows():
            difference = row["match_return"] - opponent["match_return"]
            if abs(difference) < epsilon:
                score = 0.5
            elif difference > 0:
                score = 1.0
            else:
                score = 0.0
            new_rating = _update_elo(
                new_rating,
                opponent["elo"],
                score,
                row["k_factor"],
            )

        new_elos[symbol] = new_rating

    result = snapshot.copy()
    result["elo_new"] = result.index.map(new_elos)
    result["elo_change"] = result["elo_new"] - result["elo"]
    result["matches_played"] = result.index.map(matches_played)
    result["elo_new"] = result["elo_new"].fillna(result["elo"])
    result["elo_change"] = result["elo_change"].fillna(0.0)
    result["matches_played"] = result["matches_played"].fillna(0).astype(int)
    return result


def _prepare_daily_data(
    data: pd.DataFrame,
    risk_free: pd.DataFrame | None,
    use_excess_returns: bool,
    daily_vol_window: int,
) -> tuple[pd.DataFrame, str]:
    frame = data.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    frame["sectorid"] = frame["sectorid"].fillna("UnknownSector")
    frame["close"] = frame.groupby("symbol")["close"].ffill(limit=3)
    frame["log_return"] = frame.groupby("symbol")["close"].transform(
        lambda values: np.log(values / values.shift(1))
    )
    match_return = "log_return"

    if use_excess_returns and risk_free is not None:
        missing = {"date", "rate"} - set(risk_free.columns)
        if missing:
            raise ValueError(
                f"risk_free is missing required columns: {sorted(missing)}"
            )
        rates = risk_free.loc[:, ["date", "rate"]].copy()
        rates["date"] = pd.to_datetime(rates["date"])
        frame = frame.merge(rates, on="date", how="left")
        frame["daily_rf_rate"] = frame["rate"].fillna(0)
        frame["excess_return"] = frame["log_return"] - frame["daily_rf_rate"]
        match_return = "excess_return"

    frame["vol"] = frame.groupby("symbol")[match_return].transform(
        lambda values: values.rolling(daily_vol_window).std()
    )
    return frame, match_return


def _assign_k(
    snapshot: pd.DataFrame,
    *,
    high_qt: float,
    low_qt: float,
) -> pd.Series:
    values = np.select(
        [
            snapshot["days_since_ipo"] < 60,
            snapshot["elo"] > high_qt,
            snapshot["elo"] < low_qt,
        ],
        [40, 10, 30],
        default=20,
    )
    return pd.Series(values, index=snapshot.index, dtype=float)


def compute_elo(
    data: pd.DataFrame,
    daily_vol_window: int = 20,
    matches_per_stock: int = 1,
    initial_elo: int = 1500,
    epsilon: float = 0.001,
    rf_data: pd.DataFrame | None = None,
    low_qt: float = 0.2,
    high_qt: float = 0.8,
    use_excess_returns: bool = True,
) -> pd.DataFrame:
    """Compute daily cross-sectional Elo ratings within sectors.

    Call this function once for a complete long-form universe. It calculates
    each symbol's daily return, pairs symbols with nearby Elo ratings inside
    the same ``sectorid``, and carries ratings forward through time.

    Args:
        data: Daily observations with required ``date``, ``symbol``, ``close``,
            and ``sectorid`` columns. Missing sector values are grouped into an
            ``"UnknownSector"`` bucket.
        daily_vol_window: Rolling return-volatility window.
        matches_per_stock: Maximum opponents selected per symbol and date.
        initial_elo: Starting rating for every symbol.
        epsilon: Absolute return difference treated as a draw.
        rf_data: Optional frame with ``date`` and decimal daily ``rate``.
        low_qt: Legacy lower K-factor threshold. Its semantics require review;
            see the factor roadmap.
        high_qt: Legacy upper K-factor threshold. Its semantics require review;
            see the factor roadmap.
        use_excess_returns: Use returns minus ``rf_data`` when both are
            supplied. If no risk-free frame is supplied, use log returns.

    Returns:
        A new DataFrame containing the prepared return columns plus ``elo``,
        daily ``elo_change``, and cumulative ``matches_played``.

    Raises:
        TypeError: If ``data`` is not a DataFrame.
        ValueError: If required columns are absent or parameters are invalid.

    Notes:
        This is a migration of the legacy algorithm. Match scheduling,
        K-factor thresholds, and missing-price semantics remain under review
        and are tracked in the q.factor roadmap.
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError("data must be a pandas DataFrame")
    required = {"date", "symbol", "close", "sectorid"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"data is missing required columns: {sorted(missing)}")
    if data.duplicated(["symbol", "date"]).any():
        raise ValueError("data must contain at most one row per symbol and date")
    if not isinstance(daily_vol_window, int) or daily_vol_window < 2:
        raise ValueError("daily_vol_window must be an integer of at least 2")
    if not isinstance(matches_per_stock, int) or matches_per_stock < 1:
        raise ValueError("matches_per_stock must be a positive integer")
    if epsilon < 0:
        raise ValueError("epsilon must be non-negative")

    frame, match_return = _prepare_daily_data(
        data,
        rf_data,
        use_excess_returns,
        daily_vol_window,
    )
    frame = frame.sort_values(["symbol", "date"])
    ipo_dates = frame.groupby("symbol")["date"].min().to_dict()
    all_dates = sorted(frame["date"].unique())
    static_data = frame.groupby("symbol").first()[["sectorid"]]
    current_elos = static_data.copy()
    current_elos["elo"] = float(initial_elo)
    elo_history: list[pd.DataFrame] = []

    for current_date in all_dates:
        data_on_date = frame[frame["date"] == current_date].set_index("symbol")
        if data_on_date.empty:
            continue

        snapshot = current_elos.join(
            data_on_date[[match_return, "vol"]],
            how="left",
        ).rename(columns={match_return: "match_return"})
        ipo_dates_mapped = pd.Series(
            snapshot.index.map(ipo_dates),
            index=snapshot.index,
        )
        snapshot["days_since_ipo"] = (
            pd.Timestamp(current_date) - ipo_dates_mapped
        ).dt.days
        players = snapshot.dropna(
            subset=["match_return", "vol", "elo", "sectorid"]
        ).copy()
        if players.empty:
            continue

        players["k_factor"] = _assign_k(
            players,
            high_qt=high_qt,
            low_qt=low_qt,
        )
        results = _run_matches(
            players,
            epsilon=epsilon,
            matches_per_stock=matches_per_stock,
        )
        results["date"] = current_date
        elo_history.append(results)
        current_elos["elo"] = results["elo_new"].reindex(
            current_elos.index
        ).fillna(current_elos["elo"])

    if not elo_history:
        frame["elo"] = float(initial_elo)
        frame["elo_change"] = 0.0
        frame["matches_played"] = 0
        return frame

    elo_timeseries = pd.concat(elo_history)
    elo_to_merge = elo_timeseries.reset_index(names="symbol")[
        ["symbol", "date", "elo_new", "elo_change", "matches_played"]
    ].rename(columns={"elo_new": "elo"})
    result = frame.merge(elo_to_merge, on=["symbol", "date"], how="left")
    result = result.sort_values(["symbol", "date"])
    result["elo"] = result.groupby("symbol")["elo"].ffill()
    result["elo"] = result["elo"].fillna(float(initial_elo))
    result["elo_change"] = result["elo_change"].fillna(0.0)
    result["matches_played"] = result["matches_played"].fillna(0).astype(int)
    result["matches_played"] = result.groupby("symbol")[
        "matches_played"
    ].cumsum()
    return result