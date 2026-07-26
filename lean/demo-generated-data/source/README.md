# Synthetic Sweden Data Generator

`generate_data.py` creates deterministic native LEAN equity files for 100
fictional Nasdaq Stockholm (`XSTO`) listings named `AAA` through `ADV`. It uses:

- `q.stats.random_walk` for the 30-second synthetic trade-price path.
- `q.calendar.schedule` for XSTO sessions, local opens, and half-day closes.
- `q.calendar.non_trading_days_after` to validate all generated session dates.

The generated Sweden data covers 270 XSTO sessions from 2023-12-01 through
2024-12-30. The 2023 sessions provide history before a full-2024 backtest.

Initialize the demo once, then regenerate the data with:

```bash
cd /home/hi/qrt
cd lean/demo-generated-data
uv run lean init --organization <organization-name-or-id> --language python
cd /home/hi/qrt
uv run python lean/demo-generated-data/source/generate_data.py
```

The initialization command creates the ignored, organization-bound `lean.json`
and base `data/` tree. Do not rerun it before every generation.

The script replaces only `data/equity/sweden`, then patches this isolated
workspace's market-hours, symbol-properties, and `lean.json` files. It writes
tick, minute, hour, and daily trade data plus matching intraday quotes and one
identity map/factor pair per asset. Generation requires roughly 1.1 GB and
creates 108,400 files.

The generator also writes two point-in-time universe products:

```text
data/equity/sweden/universes/daily/sweden100/
data/index/sweden/universes/etf/omxs30/
```

`sweden100` contains all 100 assets. `OMXS30` is a synthetic weighted
30-member composite with one July reconstitution, designed to exercise
`self.universe.index`. Non-session dates contain zero-byte files so LEAN's
custom-data scheduler can resolve every requested source without deselecting
members or reporting missing data.

It also appends a synthetic 2023-2024 `SPY` daily series to the initialized USA
sample data. LEAN 2.5's post-backtest `ResultsAnalyzer` unconditionally requests
SPY, even when the algorithm uses another benchmark. This auxiliary series
prevents a non-fatal analyzer error in an otherwise offline Sweden backtest; it
is not part of the Swedish data format.

Run the backtest with:

```bash
cd lean/demo-generated-data
uv run lean backtest demo.py --no-update
```

For custom-market reports, use `prepare_report.py` to create a separate
Report-compatible JSON. See the parent `README.md` for the full command and
the Report Creator limitations this handles.