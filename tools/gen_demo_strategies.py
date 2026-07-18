"""Generate qrt's bundled demo strategy trade-log datasets from the bundled
SPY data and overwrite their parquet files.

Each strategy produces a trade log in qrt's canonical trades format (one row
per round-trip trade), so docs/tests/tutorials can showcase realistic
trade-based equity curves instead of passing raw daily returns off as a
"strategy":

    spy_ema_cross  -- EMA 50/200 golden/death cross, long-only trend follower
    spy_rsi2       -- Connors RSI-2 mean reversion above SMA(200)
    spy_random     -- seeded random entries/exits (long & short), null baseline
    spy_breakout   -- 252-day-high breakout with a 3x ATR(14) trailing stop

Reserved columns (in order): ``symbol``, ``entry_time``, ``exit_time``,
``direction``, ``entry_reason``, ``exit_reason``, ``entry_price``,
``exit_price``, ``return``, ``mae``, ``mfe``, ``size``, ``fees``. Any
further columns are entry-time feature snapshots (e.g. ``rsi2``,
``atr14_pct``) -- free-form trade metadata.

Conventions:
    * Signals are evaluated on the close of day ``t`` and executed at the
      open of day ``t + 1`` (no look-ahead). The breakout's trailing stop is
      the exception: it exits intraday at the stop price (or at the open on
      a gap through it).
    * ``direction`` is an integer sign: ``1`` = long, ``-1`` = short.
    * ``return`` is a decimal fraction, direction-adjusted: a short that
      falls 3% has ``return`` +0.03. No costs applied (``fees`` is NaN).
    * ``mae``/``mfe`` are the direction-adjusted max adverse/favorable
      excursions vs the entry price, from intra-trade highs/lows.
    * A position still open on the last bar is closed at the final close
      with ``exit_reason="end_of_data"`` (no NaT exits).
    * Cumulative return is intentionally NOT stored -- derive it via
      ``(1 + trades["return"]).cumprod() - 1`` so filtered/sliced trade
      logs never carry stale columns.

Usage:
    uv run python tools/gen_demo_strategies.py
    uv run python tools/gen_demo_strategies.py spy_rsi2   # a subset

Run this after refreshing the bundled OHLCV datasets (``make datasets``
runs both) so the trade logs always match the shipped SPY data.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from qrt.data import datasets
from qrt.data.local import save as _save_file
from qrt.stats import TRADE_COLUMNS

_DIR = Path(datasets.__file__).parent

#: Reserved trades-format columns, in canonical order.
COLUMNS = list(TRADE_COLUMNS)


def _rsi(close: pd.Series, period: int) -> pd.Series:
    """Wilder-smoothed RSI."""
    delta = close.diff()
    gain = delta.clip(lower=0.0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0.0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss
    return 100 - 100 / (1 + rs)


def _atr(df: pd.DataFrame, period: int) -> pd.Series:
    """Wilder-smoothed Average True Range."""
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def _excursions(
    df: pd.DataFrame, entry_i: int, exit_i: int, entry_price: float, sign: int
) -> tuple[float, float]:
    """Direction-adjusted (MAE, MFE) vs entry price over bars [entry_i, exit_i]."""
    highs = df["high"].iloc[entry_i : exit_i + 1]
    lows = df["low"].iloc[entry_i : exit_i + 1]
    up = highs.max() / entry_price - 1
    down = lows.min() / entry_price - 1
    if sign > 0:
        return float(down), float(up)
    return float(-up), float(-down)


def _trade(
    df: pd.DataFrame,
    entry_i: int,
    exit_i: int,
    direction: int,
    entry_reason: str,
    exit_reason: str,
    entry_price: float,
    exit_price: float,
    **snapshots: float,
) -> dict:
    """Build one canonical trade record."""
    sign = direction
    mae, mfe = _excursions(df, entry_i, exit_i, entry_price, sign)
    return {
        "symbol": "SPY",
        "entry_time": df.index[entry_i],
        "exit_time": df.index[exit_i],
        "direction": direction,
        "entry_reason": entry_reason,
        "exit_reason": exit_reason,
        "entry_price": float(entry_price),
        "exit_price": float(exit_price),
        "return": sign * (exit_price / entry_price - 1),
        "mae": mae,
        "mfe": mfe,
        "size": np.nan,
        "fees": np.nan,
        **snapshots,
    }


def _frame(records: list[dict]) -> pd.DataFrame:
    """Assemble trade records into a trades-format DataFrame."""
    df = pd.DataFrame.from_records(records)
    snapshots = [c for c in df.columns if c not in COLUMNS]
    return df[COLUMNS + snapshots]


def ema_cross(df: pd.DataFrame) -> pd.DataFrame:
    """EMA 50/200 golden/death cross, long-only. Few, multi-year trades."""
    close, open_ = df["close"], df["open"]
    ema50 = close.ewm(span=50, adjust=False).mean()
    ema200 = close.ewm(span=200, adjust=False).mean()
    above = (ema50 > ema200).to_numpy()

    records, entry_i, spread = [], None, np.nan
    for t in range(200, len(df) - 1):
        crossed = above[t] != above[t - 1]
        if entry_i is None and crossed and above[t]:
            entry_i = t + 1
            spread = ema50.iloc[t] / ema200.iloc[t] - 1
        elif entry_i is not None and crossed and not above[t]:
            records.append(
                _trade(df, entry_i, t + 1, 1, "golden_cross", "death_cross",
                       open_.iloc[entry_i], open_.iloc[t + 1], ema_spread=spread)
            )
            entry_i = None
    if entry_i is not None:
        last = len(df) - 1
        records.append(
            _trade(df, entry_i, last, 1, "golden_cross", "end_of_data",
                   open_.iloc[entry_i], close.iloc[last], ema_spread=spread)
        )
    return _frame(records)


def rsi2(df: pd.DataFrame) -> pd.DataFrame:
    """Connors RSI-2 mean reversion: RSI(2) < 10 above SMA(200), exit on
    close > SMA(5). Many short-duration long trades."""
    close, open_ = df["close"], df["open"]
    rsi = _rsi(close, 2)
    sma200 = close.rolling(200).mean()
    sma5 = close.rolling(5).mean()
    enter = ((rsi < 10) & (close > sma200)).to_numpy()
    leave = (close > sma5).to_numpy()

    records, entry_i, snap = [], None, {}
    for t in range(200, len(df) - 1):
        if entry_i is None and enter[t]:
            entry_i = t + 1
            snap = {"rsi2": float(rsi.iloc[t]),
                    "sma200_gap": float(close.iloc[t] / sma200.iloc[t] - 1)}
        elif entry_i is not None and t >= entry_i and leave[t]:
            records.append(
                _trade(df, entry_i, t + 1, 1, "rsi2_oversold", "above_sma5",
                       open_.iloc[entry_i], open_.iloc[t + 1], **snap)
            )
            entry_i = None
    if entry_i is not None:
        last = len(df) - 1
        records.append(
            _trade(df, entry_i, last, 1, "rsi2_oversold", "end_of_data",
                   open_.iloc[entry_i], close.iloc[last], **snap)
        )
    return _frame(records)


def random(df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Seeded random entries (3%/day when flat, 50/50 long/short) held for a
    random 5-20 trading days. The null-hypothesis baseline."""
    open_, close = df["open"], df["close"]
    rng = np.random.default_rng(seed)

    records, t = [], 1
    while t < len(df) - 1:
        if rng.random() < 0.03:
            entry_i = t + 1
            direction = 1 if rng.random() < 0.5 else -1
            exit_i = min(entry_i + int(rng.integers(5, 21)), len(df) - 1)
            if exit_i == len(df) - 1:
                exit_reason, exit_price = "end_of_data", close.iloc[exit_i]
            else:
                exit_reason, exit_price = "time_exit", open_.iloc[exit_i]
            records.append(
                _trade(df, entry_i, exit_i, direction, "random_entry", exit_reason,
                       open_.iloc[entry_i], exit_price)
            )
            t = exit_i
        t += 1
    return _frame(records)


def breakout(df: pd.DataFrame) -> pd.DataFrame:
    """252-day closing-high breakout with a 3x ATR(14) chandelier trailing
    stop. The stop triggers on the intraday low, so ``exit_reason`` and
    MAE/MFE exercise OHLC-dependent exits."""
    close, open_, high, low = df["close"], df["open"], df["high"], df["low"]
    atr = _atr(df, 14)
    prior_max = close.rolling(252).max().shift(1)
    enter = (close > prior_max).to_numpy()

    records, t = [], 252
    while t < len(df) - 1:
        if enter[t]:
            entry_i = t + 1
            entry_price = open_.iloc[entry_i]
            snap = {"atr14_pct": float(atr.iloc[t] / close.iloc[t])}
            highest = high.iloc[entry_i]
            stop = highest - 3 * atr.iloc[entry_i]
            exit_i, exit_price, exit_reason = None, np.nan, ""
            for u in range(entry_i + 1, len(df)):
                if open_.iloc[u] <= stop:  # gap through the stop
                    exit_i, exit_price, exit_reason = u, open_.iloc[u], "trail_stop"
                    break
                if low.iloc[u] <= stop:
                    exit_i, exit_price, exit_reason = u, stop, "trail_stop"
                    break
                highest = max(highest, high.iloc[u])
                stop = max(stop, highest - 3 * atr.iloc[u])
            if exit_i is None:
                exit_i, exit_price, exit_reason = len(df) - 1, close.iloc[-1], "end_of_data"
            records.append(
                _trade(df, entry_i, exit_i, 1, "high_252_breakout", exit_reason,
                       entry_price, exit_price, **snap)
            )
            t = exit_i
        t += 1
    return _frame(records)


STRATEGIES = {
    "spy_ema_cross": ema_cross,
    "spy_rsi2": rsi2,
    "spy_random": random,
    "spy_breakout": breakout,
}


def main() -> None:
    names = sys.argv[1:] or list(STRATEGIES)
    unknown = [n for n in names if n not in STRATEGIES]
    if unknown:
        raise SystemExit(
            f"Unknown strategy dataset(s): {unknown}. Available: {list(STRATEGIES)}"
        )

    spy = datasets.load("spy")
    for name in names:
        trades = STRATEGIES[name](spy)
        _save_file(trades, _DIR / f"{name}.parquet")
        total = (1 + trades["return"]).prod() - 1
        print(
            f"Updated {name}.parquet: {len(trades)} trades "
            f"({trades['entry_time'].iloc[0]:%Y-%m-%d} to "
            f"{trades['exit_time'].iloc[-1]:%Y-%m-%d}, "
            f"total return {total:+.1%})"
        )


if __name__ == "__main__":
    main()
