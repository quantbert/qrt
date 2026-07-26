"""Generate deterministic synthetic XSTO equity data in native LEAN format."""

from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
import pandas as pd

import qrt as q


MARKET = "sweden"
EXCHANGE = "XSTO"
CUSTOM_MARKET_ID = 900
ASSET_COUNT = 100
DAILY_UNIVERSE_NAME = "sweden100"
INDEX_UNIVERSE_TICKER = "OMXS30"
INDEX_MEMBER_COUNT = 30
INDEX_RECONSTITUTION_DATE = pd.Timestamp("2024-07-01")
START_DATE = "2023-12-01"
BACKTEST_START_DATE = "2024-01-02"
END_DATE = "2024-12-31"
TICK_HISTORY_DATE = "2023-12-28"
SEED = 20240726
PRICE_SCALE = 10_000


def _ticker_name(number: int) -> str:
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return "".join(
        (
            letters[number // (26 * 26)],
            letters[(number // 26) % 26],
            letters[number % 26],
        )
    )


TICKERS = tuple(_ticker_name(number) for number in range(ASSET_COUNT))

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EQUITY = DATA / "equity" / MARKET


def _write_zip(path: Path, member: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(member, "\n".join(lines) + "\n")


def _milliseconds_since_midnight(index: pd.DatetimeIndex) -> pd.Index:
    local = index.tz_localize(None)
    return ((local - local.normalize()).total_seconds() * 1_000).astype("int64")


def _format_date(date: pd.Timestamp) -> str:
    return f"{date.month}/{date.day}/{date.year}"


def _encode_base36(value: int) -> str:
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    encoded = ""
    while value:
        value, remainder = divmod(value, 36)
        encoded = digits[remainder] + encoded
    return encoded or "0"


def _equity_sid(ticker: str, first_session: pd.Timestamp) -> str:
    oa_days = (first_session.date() - date(1899, 12, 30)).days
    properties = oa_days * 100_000_000_000_000 + CUSTOM_MARKET_ID * 100 + 1
    return f"{ticker} {_encode_base36(properties)}"


def _build_tick_times(schedule: pd.DataFrame) -> pd.DatetimeIndex:
    return pd.DatetimeIndex(
        [
            timestamp
            for row in schedule.itertuples()
            for timestamp in pd.date_range(
                row.open,
                row.close,
                freq="30s",
                inclusive="left",
            )
        ],
        name="time",
    )


def _build_price_paths(
    tick_times: pd.DatetimeIndex,
    tickers: tuple[str, ...],
) -> np.ndarray:
    prices = q.stats.random_walk(
        periods=len(tick_times),
        paths=len(tickers),
        start=100.0,
        drift=np.linspace(0.02, 0.12, len(tickers)),
        volatility=np.linspace(0.15, 0.35, len(tickers)),
        periods_per_year=252 * 17 * 60 * 2,
        names=tickers,
        seed=SEED,
    )
    return np.rint(prices.to_numpy() * PRICE_SCALE).astype("int64")


def _build_ticks(
    tick_times: pd.DatetimeIndex,
    scaled_prices: np.ndarray,
    asset_number: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(SEED + 1 + asset_number)
    return pd.DataFrame(
        {
            "price": scaled_prices,
            "volume": rng.integers(1, 21, size=len(tick_times), dtype="int64") * 10,
        },
        index=tick_times,
    )


def _aggregate(ticks: pd.DataFrame, frequency: str) -> pd.DataFrame:
    local_times = ticks.index.tz_localize(None).floor(frequency)
    grouped = ticks.assign(period=local_times).groupby("period", sort=True)
    return grouped.agg(
        open=("price", "first"),
        high=("price", "max"),
        low=("price", "min"),
        close=("price", "last"),
        volume=("volume", "sum"),
    )


def _write_asset_prices(ticker: str, ticks: pd.DataFrame) -> tuple[int, int, int, int]:
    lean_ticker = ticker.lower()
    local_dates = ticks.index.tz_localize(None).normalize()
    for date, frame in ticks.assign(session=local_dates).groupby("session", sort=True):
        date_text = date.strftime("%Y%m%d")
        times = _milliseconds_since_midnight(frame.index)
        lines = [
            f"{time},{price},{volume},,0,0"
            for time, price, volume in zip(
                times,
                frame["price"],
                frame["volume"],
                strict=True,
            )
        ]
        _write_zip(
            EQUITY / "tick" / lean_ticker / f"{date_text}_trade.zip",
            f"{date_text}_{lean_ticker}_Trade_Tick.csv",
            lines,
        )
        quote_lines = [
            f"{time},{price - 100},{volume},{price + 100},{volume},,0,0"
            for time, price, volume in zip(
                times,
                frame["price"],
                frame["volume"],
                strict=True,
            )
        ]
        _write_zip(
            EQUITY / "tick" / lean_ticker / f"{date_text}_quote.zip",
            f"{date_text}_{lean_ticker}_Quote_Tick.csv",
            quote_lines,
        )

    minute = _aggregate(ticks, "min")
    for date, frame in minute.groupby(minute.index.normalize(), sort=True):
        date_text = date.strftime("%Y%m%d")
        times = ((frame.index - frame.index.normalize()).total_seconds() * 1_000).astype(
            "int64"
        )
        lines = [
            f"{time},{open_},{high},{low},{close},{volume}"
            for time, open_, high, low, close, volume in zip(
                times,
                frame["open"],
                frame["high"],
                frame["low"],
                frame["close"],
                frame["volume"],
                strict=True,
            )
        ]
        _write_zip(
            EQUITY / "minute" / lean_ticker / f"{date_text}_trade.zip",
            f"{date_text}_{lean_ticker}_minute_trade.csv",
            lines,
        )
        quote_lines = [
            f"{time},{open_ - 100},{high - 100},{low - 100},{close - 100},{volume},"
            f"{open_ + 100},{high + 100},{low + 100},{close + 100},{volume}"
            for time, open_, high, low, close, volume in zip(
                times,
                frame["open"],
                frame["high"],
                frame["low"],
                frame["close"],
                frame["volume"],
                strict=True,
            )
        ]
        _write_zip(
            EQUITY / "minute" / lean_ticker / f"{date_text}_quote.zip",
            f"{date_text}_{lean_ticker}_minute_quote.csv",
            quote_lines,
        )

    hour = _aggregate(ticks, "h")
    hour_lines = [
        f"{time:%Y%m%d %H:%M},{row.open},{row.high},{row.low},{row.close},{row.volume}"
        for time, row in hour.iterrows()
    ]
    _write_zip(
        EQUITY / "hour" / f"{lean_ticker}.zip",
        f"{lean_ticker}.csv",
        hour_lines,
    )

    daily = _aggregate(ticks, "D")
    daily_lines = [
        f"{time:%Y%m%d} 00:00,{row.open},{row.high},{row.low},{row.close},{row.volume}"
        for time, row in daily.iterrows()
    ]
    _write_zip(
        EQUITY / "daily" / f"{lean_ticker}.zip",
        f"{lean_ticker}.csv",
        daily_lines,
    )

    first_session = daily.index[0].strftime("%Y%m%d")
    first_close = daily.iloc[0]["close"] / PRICE_SCALE
    map_directory = EQUITY / "map_files"
    factor_directory = EQUITY / "factor_files"
    map_directory.mkdir(parents=True, exist_ok=True)
    factor_directory.mkdir(parents=True, exist_ok=True)
    (map_directory / f"{lean_ticker}.csv").write_text(
        f"{first_session},{lean_ticker}\n20501231,{lean_ticker}\n",
        encoding="utf-8",
    )
    (factor_directory / f"{lean_ticker}.csv").write_text(
        f"{first_session},1,1,{first_close:.4f}\n20501231,1,1,0\n",
        encoding="utf-8",
    )
    return len(ticks), len(minute), len(hour), len(daily)


def _write_prices(
    schedule: pd.DataFrame,
    tickers: tuple[str, ...],
) -> tuple[int, int, int, int]:
    if EQUITY.exists():
        shutil.rmtree(EQUITY)

    tick_times = _build_tick_times(schedule)
    price_paths = _build_price_paths(tick_times, tickers)
    counts: tuple[int, int, int, int] | None = None
    for asset_number, ticker in enumerate(tickers):
        ticks = _build_ticks(tick_times, price_paths[:, asset_number], asset_number)
        counts = _write_asset_prices(ticker, ticks)
        if (asset_number + 1) % 10 == 0 or asset_number + 1 == len(tickers):
            print(f"Generated assets: {asset_number + 1}/{len(tickers)}")

    if counts is None:
        raise RuntimeError("at least one ticker is required")
    return counts


def _write_market_hours(schedule: pd.DataFrame) -> tuple[int, int]:
    path = DATA / "market-hours" / "market-hours-database.json"
    database = json.loads(path.read_text(encoding="utf-8"))
    weekdays = pd.date_range(START_DATE, END_DATE, freq="B")
    holidays = weekdays.difference(schedule.index)
    regular_close = pd.Timestamp("17:30").time()
    early_closes = {
        _format_date(session): close.strftime("%H:%M:%S")
        for session, close in schedule["close"].items()
        if close.time() != regular_close
    }
    market_segment = [{"start": "09:00:00", "end": "17:30:00", "state": "market"}]
    entry = {
        "dataTimeZone": "Europe/Stockholm",
        "exchangeTimeZone": "Europe/Stockholm",
        "sunday": [],
        "monday": market_segment,
        "tuesday": market_segment,
        "wednesday": market_segment,
        "thursday": market_segment,
        "friday": market_segment,
        "saturday": [],
        "holidays": [_format_date(date) for date in holidays],
        "earlyCloses": early_closes,
        "lateOpens": {},
        "bankHolidays": [],
    }
    database["entries"]["Equity-sweden-[*]"] = entry
    database["entries"]["Index-sweden-[*]"] = entry
    path.write_text(json.dumps(database, indent=2) + "\n", encoding="utf-8")
    return len(holidays), len(early_closes)


def _write_universes(
    schedule: pd.DataFrame,
    tickers: tuple[str, ...],
) -> tuple[int, int]:
    sid_by_ticker = {
        ticker: _equity_sid(ticker, schedule.index[0])
        for ticker in tickers
    }

    daily_directory = EQUITY / "universes" / "daily" / DAILY_UNIVERSE_NAME
    index_market_directory = DATA / "index" / MARKET
    index_directory = (
        index_market_directory
        / "universes"
        / "etf"
        / INDEX_UNIVERSE_TICKER.lower()
    )
    shutil.rmtree(daily_directory, ignore_errors=True)
    shutil.rmtree(index_directory, ignore_errors=True)
    daily_directory.mkdir(parents=True, exist_ok=True)
    index_directory.mkdir(parents=True, exist_ok=True)
    index_map_directory = index_market_directory / "map_files"
    index_map_directory.mkdir(parents=True, exist_ok=True)
    first_session_text = schedule.index[0].strftime("%Y%m%d")
    (index_map_directory / f"{INDEX_UNIVERSE_TICKER.lower()}.csv").write_text(
        f"{first_session_text},{INDEX_UNIVERSE_TICKER.lower()}\n"
        f"20501231,{INDEX_UNIVERSE_TICKER.lower()}\n",
        encoding="utf-8",
    )

    first_members = tickers[:INDEX_MEMBER_COUNT]
    second_members = tickers[5 : 5 + INDEX_MEMBER_COUNT]
    ranks = np.arange(INDEX_MEMBER_COUNT, 0, -1, dtype="float64")
    weights = ranks / ranks.sum()

    source_dates = pd.date_range(schedule.index[0], schedule.index[-1], freq="D")
    sessions = set(schedule.index)
    for source_date in source_dates:
        date_text = source_date.strftime("%Y%m%d")
        daily_path = daily_directory / f"{date_text}.csv"
        index_path = index_directory / f"{date_text}.csv"
        if source_date not in sessions:
            daily_path.write_text("", encoding="utf-8")
            index_path.write_text("", encoding="utf-8")
            continue

        daily_lines = [
            f"{ticker},{sid_by_ticker[ticker]}"
            for ticker in tickers
        ]
        daily_path.write_text(
            "\n".join(daily_lines) + "\n",
            encoding="utf-8",
        )

        if source_date < INDEX_RECONSTITUTION_DATE:
            members = first_members
            last_update = schedule.index[0].strftime("%Y%m%d")
        else:
            members = second_members
            last_update = INDEX_RECONSTITUTION_DATE.strftime("%Y%m%d")
        index_lines = [
            f"{ticker},{sid_by_ticker[ticker]},{last_update},"
            f"{weight:.12f},{1_000_000 - rank * 10_000},"
            for rank, (ticker, weight) in enumerate(
                zip(members, weights, strict=True)
            )
        ]
        index_path.write_text(
            "\n".join(index_lines) + "\n",
            encoding="utf-8",
        )

    return len(source_dates), len(source_dates)


def _write_results_analyzer_benchmark() -> int:
    schedule = q.calendar.schedule(START_DATE, END_DATE, exchange="XNYS")
    prices = q.stats.random_walk(
        periods=len(schedule),
        paths=1,
        start=450.0,
        drift=0.10,
        volatility=0.18,
        periods_per_year=252,
        names=["SPY"],
        seed=SEED + 2,
    )["SPY"]
    scaled = np.rint(prices.to_numpy() * PRICE_SCALE).astype("int64")
    generated_lines = [
        f"{session:%Y%m%d} 00:00,{price},{price},{price},{price},1000000"
        for session, price in zip(schedule.index, scaled, strict=True)
    ]

    path = DATA / "equity" / "usa" / "daily" / "spy.zip"
    existing_lines: list[str] = []
    if path.exists():
        with ZipFile(path) as archive:
            existing_lines = archive.read("spy.csv").decode("utf-8").splitlines()
    first_generated_date = schedule.index[0].strftime("%Y%m%d")
    retained_lines = [line for line in existing_lines if line[:8] < first_generated_date]
    _write_zip(path, "spy.csv", retained_lines + generated_lines)
    return len(generated_lines)


def _write_symbol_properties(tickers: tuple[str, ...]) -> None:
    path = DATA / "symbol-properties" / "symbol-properties-database.csv"
    ticker_set = set(tickers)
    lines = [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if not line.lower().startswith(f"{MARKET},")
        and not (
            len(parts := line.split(",")) > 3
            and parts[0].lower() == "usa"
            and parts[1].upper() in ticker_set
            and parts[2].lower() == "equity"
            and parts[3].startswith("Synthetic Sweden report alias")
        )
    ]
    lines.append("sweden,[*],equity,Synthetic Stockholm equity,SEK,1,0.01,1")
    lines.extend(
        f"sweden,{ticker},equity,Synthetic Sweden Equity {ticker},SEK,1,0.01,1,{ticker}"
        for ticker in tickers
    )
    lines.append("sweden,[*],index,Synthetic Stockholm index,SEK,1,0.01,1")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _configure_workspace() -> None:
    path = ROOT / "lean.json"
    config = json.loads(path.read_text(encoding="utf-8"))
    config.update(
        {
            "map-file-provider": "QuantConnect.Data.Auxiliary.LocalDiskMapFileProvider",
            "factor-file-provider": "QuantConnect.Data.Auxiliary.LocalDiskFactorFileProvider",
            "show-missing-data-logs": True,
            "file-database-last-update": "12/31/2099 00:00:00",
        }
    )
    temporary_path = path.with_suffix(".json.tmp")
    temporary_path.write_text(json.dumps(config, indent=4) + "\n", encoding="utf-8")
    temporary_path.replace(path)


def _configure_project(
    schedule: pd.DataFrame,
    tickers: tuple[str, ...],
) -> None:
    backtest_schedule = schedule.loc[BACKTEST_START_DATE:]
    path = ROOT / "config.json"
    config = json.loads(path.read_text(encoding="utf-8"))
    parameters = dict(config.get("parameters", {}))
    parameters.pop("expected-minute-bars", None)
    parameters.pop("expected-consolidated-hour-bars", None)
    parameters.update({
        "backtest-start": BACKTEST_START_DATE,
        "backtest-end": schedule.index[-1].date().isoformat(),
        "tick-history-date": TICK_HISTORY_DATE,
        "symbols": ",".join(tickers),
        "asset-count": str(len(tickers)),
        "expected-session-count": str(len(backtest_schedule)),
        "expected-daily-bars": str(len(backtest_schedule) * len(tickers)),
        "expected-minute-history-rows": str(60 * len(tickers)),
        "expected-quote-history-rows": str(60 * len(tickers)),
        "expected-tick-history-rows": str(242 * len(tickers)),
        "expected-hour-history-rows": str(5 * len(tickers)),
        "expected-daily-history-rows": str(5 * len(tickers)),
        "daily-universe-name": DAILY_UNIVERSE_NAME,
        "index-universe-ticker": INDEX_UNIVERSE_TICKER,
        "expected-daily-universe-members": str(len(tickers)),
        "expected-index-universe-members": str(INDEX_MEMBER_COUNT),
        "expected-index-compositions": "2",
    })
    config["parameters"] = parameters
    temporary_path = path.with_suffix(".json.tmp")
    temporary_path.write_text(json.dumps(config, indent=4) + "\n", encoding="utf-8")
    temporary_path.replace(path)


def main() -> None:
    schedule = q.calendar.schedule(START_DATE, END_DATE, exchange=EXCHANGE)
    closed_days = q.calendar.non_trading_days_after(
        pd.Series(schedule.index, index=schedule.index),
        exchange=EXCHANGE,
    )
    tick_count, minute_count, hour_count, daily_count = _write_prices(schedule, TICKERS)
    daily_universe_files, index_universe_files = _write_universes(schedule, TICKERS)
    benchmark_count = _write_results_analyzer_benchmark()
    holiday_count, early_close_count = _write_market_hours(schedule)
    _write_symbol_properties(TICKERS)
    _configure_workspace()
    _configure_project(schedule, TICKERS)

    print(
        f"Generated {len(TICKERS)} assets ({TICKERS[0]}-{TICKERS[-1]}) "
        f"for {len(schedule)} XSTO sessions"
    )
    print(
        f"Rows per asset: tick={tick_count}, minute={minute_count}, "
        f"hour={hour_count}, daily={daily_count}"
    )
    print(
        f"Rows total: tick={tick_count * len(TICKERS)}, "
        f"minute={minute_count * len(TICKERS)}, "
        f"hour={hour_count * len(TICKERS)}, daily={daily_count * len(TICKERS)}"
    )
    print(
        f"Calendar: holidays={holiday_count}, early_closes={early_close_count}, "
        f"max_closed_days_after={closed_days.max()}"
    )
    print(
        f"Universes: daily/{DAILY_UNIVERSE_NAME}={daily_universe_files}, "
        f"index/{INDEX_UNIVERSE_TICKER}={index_universe_files}"
    )
    print(f"LEAN ResultsAnalyzer benchmark: SPY daily={benchmark_count}")
    print(f"LEAN data root: {DATA}")


if __name__ == "__main__":
    main()