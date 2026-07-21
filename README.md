# qrt — Quant Research Tools

**One consistent `import qrt as q` API over the fragmented quant Python ecosystem** —
market data, technical indicators, return statistics, and interactive plotting,
wired together so the output of one is the input of the next.

```python
import qrt as q

aapl = q.data.sources.yfinance.read("AAPL", "2024-01-01", "2025-01-01", "1d")
spy = q.data.sources.yfinance.read("SPY", "2024-01-01", "2025-01-01", "1d")

strategy = aapl["close"].pct_change().rename("AAPL")
benchmark = spy["close"].pct_change().rename("SPY")

q.stats.benchmark_stats(strategy, benchmark)   # alpha, beta, Sharpe, tracking error, ...
q.plot.plot(strategy, benchmark=benchmark)      # interactive equity + drawdown report
```

## Why qrt

- **No more juggling five libraries with five conventions.** TA-Lib and
  pandas-ta-classic indicators (`q.indicator.talib`, `q.indicator.pandas_ta`), Yahoo
  Finance/Binance/DuckDB market data (`q.data.sources`), and 30+ risk/return
  metrics inspired by quantstats (`q.stats`) all speak the same plain
  pandas `DataFrame`/`Series` OHLCV and return-stream layout — chain them
  freely, no glue code, no format conversion.
- **A canonical trades format**, not just return streams. One row per
  round-trip trade (entry/exit price & time, direction, MAE/MFE, free-form
  feature snapshots) is a first-class citizen: `q.stats.trade_stats`,
  `q.stats.trades_to_returns`, and `q.plot.trades`/`mae_mfe`/
  `trade_distribution` all consume it directly.
- **Built-in robustness checks**, not just a backtest score. Bootstrap
  Monte Carlo, forward win-rate variance testing, and noise-sensitivity
  testing ship as first-class `q.stats`/`q.plot` functions, not an
  afterthought — ask "does this edge survive a different order of draws /
  a worse win rate / noisier data?" in one call.
- **Interactive by default.** Every chart is a real Plotly figure — zoom,
  hover, range-select — exportable to standalone HTML or PNG with
  `q.plot.show`.
- **Works offline.** Bundled sample OHLCV data (AAPL, SPY, BTC-USD) and demo
  strategy trade logs mean you can try every function with zero network
  calls or API keys.

## Library layout

| Module | Purpose |
|---|---|
| `q.data` | local parquet/csv I/O, market data sources (Yahoo Finance, Binance, DuckDB), bundled sample datasets |
| `q.env` | explicit `.env` loading and environment-variable access |
| `q.calendar` | exchange sessions, closures, and market-time semantics |
| `q.indicator` | native single-instrument measurements plus explicit TA-Lib and pandas-ta-classic providers |
| `q.cross_section` | cross-sectional characteristics and rankings *(planned)* |
| `q.feature` | named, versioned model inputs, computation, and materialization |
| `q.label` | future-aware target construction, event filtering, and overlap-aware sample weights |
| `q.preprocess` | fitted model-input transformations *(planned)* |
| `q.signal` | investment intent derived from measurements, factors, models, and rules *(planned)* |
| `q.stats` | return-stream & trade-level statistics: performance, alpha/beta, Monte Carlo, variance/noise testing |
| `q.plot` | interactive Plotly charts and performance reports, for both return streams and trade logs |
| `q.model` | leakage-aware validation and optional PyTorch helpers |
| `q.bt` | event-driven backtesting *(planned)* |
| `q.portfolio` | portfolio construction and analysis *(planned)* |

## Warning ⚠️

Still in early alpha — APIs may change without notice. Track progress on the [Roadmap](https://quantbert.github.io/qrt/roadmap.html).

## Install

```bash
uv add pyqrt
```

## Docs

Full documentation, tutorials, and API reference: https://quantbert.github.io/qrt/
