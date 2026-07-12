
# Roadmap

Ideas and planned work per submodule. Checked items are done, unchecked are planned.

## General

- [ ] Package scaffolding (`pyproject.toml`, CI, tests)
- [ ] Examples folder with notebooks demonstrating each submodule
- [ ] Docs site (mkdocs) with API reference per submodule

## `q.plot` — plotting with premade quant-finance configs

Opinionated plotting helpers with sensible defaults for quant research.

- [ ] `q.plot.col(df, "cum_trade_log_return")` — quick single-column plot with clean defaults
- [ ] Multi-column rendering **with wildcards**: `q.plot.col(df, "*_log_ret")` plots all columns matching the pattern (e.g. multiple return fields at once)
- [ ] `q.plot.qplot(...)` — enriched plot variant with stats and graphical extras:
  - [ ] Underwater (drawdown) plot
  - [ ] Longest drawdown highlighted, with dates on drawdown periods
  - [ ] Annotations of notable historical events (Covid, wars, etc.)
  - [ ] Key metrics overlaid/inset (Sharpe, CAGR, max DD, ...)
- [ ] Interactive plots (plain plotly backend)
- [ ] Animated plots — play button / slider to watch values evolve over time
- [ ] Shared style/config presets (theme, figsize, grids) reused by `q.tearsheet`

## `q.feat` — feature engineering

- [ ] Indicator wrappers: TA-Lib (`q.feat.talib`) and pandas-ta-classic (`q.feat.pandas_ta`)
- [ ] Hand-rolled primitives in `q.feat.qta` (sma, lags, ...)
- [ ] tsfresh wrappers for automated feature extraction
- [ ] Feature pipelines: apply a set of features across a universe of symbols

## `q.splits` — leakage-safe data splitting

- [ ] Walk-forward splits
- [ ] Purged K-fold with embargo (López de Prado)
- [ ] Combinatorial purged CV
- [ ] Split visualization (plot which samples are train/test/embargo)

## `q.tearsheet` — performance reports

- [ ] MVP report from a returns series
- [ ] Sharpe/Sortino/Calmar, drawdowns, rolling stats
- [ ] Monthly returns heatmap
- [ ] Benchmark comparison (e.g. vs SPY)
- [ ] HTML export

## `q.bt` — backtesting

- [ ] DuckDB securities-master connector
- [ ] Event-driven backtester for model signals
- [ ] Transaction costs / slippage models
- [ ] Trade log output compatible with `q.tearsheet` and `q.plot`

## `q.portfolio` — portfolio analysis

- [ ] Attribution and risk decomposition
- [ ] Exposure and turnover analysis
- [ ] Portfolio optimization (skfolio/Riskfolio-style)

## `q.models` — model wrappers

- [ ] PyTorch training loop wrappers
- [ ] Checkpointing and inference helpers
- [ ] Time-series-aware dataloaders

## `q.data` / `q.dataload` — data access

- [ ] DuckDB securities-master schema and access layer
- [ ] Caching of vendor downloads

## `q.vendors` — market data vendors

- [ ] yfinance connector
- [ ] Binance connector
- [ ] Common `base` interface for adding new vendors

## `q.utils`

- [ ] `set_seed` and reproducibility helpers


## Inspiration

Libraries we take inspiration from (and in some cases wrap):

| Library | What we borrow |
|---|---|
| [quantstats](https://github.com/ranaroussi/quantstats) | tearsheets, return-stream metrics |
| [pyfolio-reloaded](https://github.com/stefan-jansen/pyfolio-reloaded) | portfolio/performance analysis |
| [alphalens-reloaded](https://github.com/stefan-jansen/alphalens-reloaded) | alpha-factor evaluation |
| [empyrical-reloaded](https://github.com/stefan-jansen/empyrical-reloaded) | risk/performance statistics |
| [tsfresh](https://github.com/blue-yonder/tsfresh) | automated time-series feature extraction |
| [skfolio](https://github.com/skfolio/skfolio) | sklearn-style portfolio optimization |
| [mlfinlab](https://github.com/hudson-and-thames/mlfinlab) | purged CV, embargo, financial ML (López de Prado) |
| [pandas-ta](https://github.com/twopirllc/pandas-ta) | technical indicators |
| [pandas-ta-classic](https://github.com/xgboosted/pandas-ta-classic) | maintained fork of pandas-ta indicators |
| [Riskfolio-Lib](https://github.com/dcajasn/Riskfolio-Lib) | portfolio optimization & risk measures |
| [qlib](https://github.com/microsoft/qlib) | end-to-end quant ML platform design |
| [pytorch-forecasting](https://github.com/sktime/pytorch-forecasting) | PyTorch time-series model wrappers |
| [sktime](https://github.com/sktime/sktime) | unified time-series API design |
| [alphatools](https://github.com/marketneutral/alphatools) | alpha research & factor tooling on a securities master |
| [PyStats](https://github.com/marcizhu/PyStats) | statistical distribution functions (pdf/cdf/quantile/sampling) |

