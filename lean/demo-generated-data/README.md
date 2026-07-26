# Synthetic Nasdaq Stockholm LEAN Test

This tracked Lean CLI demo proves that a custom `sweden` equity market can load
and trade native LEAN data without modifying the engine. Generated market data,
backtests, reports, storage, and the organization-bound `lean.json` remain
local and are ignored by Git.

The dataset contains 100 fictional symbols from `AAA` through `ADV` over 270
real XSTO sessions from 2023-12-01 through 2024-12-30:

- 27,270,000 30-second trade ticks and matching quote ticks
- 13,635,000 minute trade bars and matching quote bars
- 240,500 precompiled hour trade bars
- 27,000 precompiled daily trade bars
- 100 identity map files and 100 factor files
- A 100-member `sweden100` daily universe
- A weighted 30-member `OMXS30` Index universe with a July reconstitution
- Stockholm market hours, 13 holidays, and five early closes

The native Sweden tree is about 1.1 GB across 108,400 files. The backtest covers
all 251 XSTO sessions in 2024 and verifies 100 simultaneous daily subscriptions,
multi-symbol tick/minute/quote/hour/daily history, SEK metadata, complete slices,
and one filled holding per asset.

## Run

```bash
cd /home/hi/qrt
cd lean/demo-generated-data
uv run lean init --organization <organization-name-or-id> --language python
cd /home/hi/qrt
uv run python lean/demo-generated-data/source/generate_data.py
cd lean/demo-generated-data
uv run lean backtest demo.py --no-update
```

Run `lean init` only once per checkout. It creates the local `lean.json` and
base `data/` tree required by the generator.

A successful run includes:

```text
SWEDEN_MULTI_ASSET_VERIFIED {'assets': 100, 'sessions': 251,
'daily_bars': 25100, 'daily_history': 500, 'hour_history': 500,
'minute_history': 6000, 'quote_history': 6000, 'tick_history': 24200,
'invested': 100}
```

It should also report 602 successful data requests, zero failed requests, and
store output under `backtests/<timestamp>`.

See `source/README.md` and `source/generate_data.py` for generation details.

## Universe APIs

Run the native broad daily and index constituent test with:

```bash
uv run lean backtest universe_demo.py --no-update
```

A successful run includes:

```text
SWEDEN_UNIVERSES_VERIFIED {'broad_updates': 251, 'index_updates': 251,
'broad_sizes': [100], 'index_sizes': [30], 'index_compositions': 2,
'index_last_updates': ['20231201', '20240701'], 'added_symbols': 100,
'price_symbols': 100, 'daily_bars': 25100}
```

It should report 618 successful universe requests and zero failed requests.

## 20/100 SMA Crossover

`demo_sma.py` applies a long-only 20/100-day simple moving-average crossover
to the native `sweden100` universe. It:

- Tracks one fast/slow SMA pair per selected asset.
- Lets the indicators warm naturally from daily bars; no extra history request
	is made.
- Enters when the 20-day SMA crosses above the 100-day SMA.
- Exits when the 20-day SMA crosses below the 100-day SMA.
- Rebalances bullish assets equally to 95% gross exposure in one batch.
- Uses `ConstantFeeModel(0)` because these are synthetic assets in a custom
	market.

Run it with:

```bash
uv run lean backtest demo_sma.py --no-update
```

The verified 2024 run produced:

```text
SWEDEN_SMA_CROSS_VERIFIED {'assets': 100, 'ready': 100,
'entry_signals': 154, 'exit_signals': 106, 'rebalances': 107,
'filled_orders': 448, 'final_positions': 47}
```

It finished at +1.806% with a 1.4% drawdown and zero failed data requests.
Three orders submitted on the final session remain market-on-open because the
backtest contains no following session; there were zero invalid orders.

## Generate The SMA Report

Multiple Python source files in this project do not affect `lean report`.
Reports consume a result JSON and never import the algorithm source. The
standalone Report Creator also cannot register custom market ID `900`, so it
cannot deserialize Sweden SIDs directly.

Create a report-only compatibility copy, then pass that exact JSON to Report:

```bash
uv run python source/prepare_report.py \
	backtests/2026-07-26_13-41-40/1641330887.json \
	report-results/1641330887-report.json

uv run lean report \
	--backtest-results report-results/1641330887-report.json \
	--report-destination sma-report.html \
	--strategy-name "Sweden 20/100 SMA" \
	--strategy-description "Synthetic 100-asset XSTO daily-universe SMA crossover" \
	--overwrite
```

`prepare_report.py` changes only the copied result. It aliases custom Sweden
SIDs to built-in USA SIDs for deserialization and uses USD only for Report's
internal 1:1 order replay. Original SEK charts, runtime statistics, and numeric
results remain unchanged.

By default the helper omits the copied result's order dictionary because the
current Report `PortfolioLooper` leaves `TradingDaysPerYear` unset during a
large replay. Closed trades, returns, charts, statistics, and parameters remain;
only the reconstructed asset-allocation chart has no order input. Use
`--keep-orders` to retain allocation replay if that upstream warning is
acceptable.

The standard Report template is valid. A custom `--html` changes layout only:
Report deserializes orders and runs `PortfolioLooper` before compiling any
template placeholders. Also note that `lean report` has `--update`, but no
`--no-update`; it uses the local image unless `--update` is supplied.