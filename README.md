# Quant Research Tools (qrt)

QRT is an umbrella library of quantitative research tools

## Warning ⚠️

Library is still under early development. Come back later. 

## Install:
```bash
uv add pyqrt
```

## Use:
```python
import qrt as q

# leakage-safe splits
splits = q.splits.walk_forward(X, n_splits=5, embargo="5D")

# features
X["sma_20"] = q.feat.qta.sma(prices, 20)

# backtest + tearsheet
result = q.bt.run(signal, prices)
q.plot.tearsheet(result.returns, benchmark="SPY")
```

## Features (planned / in progress)

- **Model wrappers** — thin, opinionated wrappers around PyTorch models for training, checkpointing and inference on financial time series (`q.models`)
- **Data splitting** — leakage-aware splits: walk-forward, purged K-fold and combinatorial purged CV with embargo (à la López de Prado) (`q.splits`)
- **Plotting & tearsheets** — interactive Plotly reports for return streams: Sharpe/Sortino/Calmar, drawdowns, rolling stats, monthly heatmaps, benchmark comparison (`q.plot`)
- **Portfolio analysis** — attribution, exposure, turnover and risk decomposition (`q.portfolio`)
- **Backtesting** — event-driven backtesting of model signals, connected to the master securities database (DuckDB) (`q.bt`)
- **Feature engineering** — feature submodules under one namespace: hand-rolled primitives (`q.feat.qta.sma()`, `q.feat.qta.lags()`), all TA-Lib indicators (`q.feat.talib.RSI(ohlc)`) and all pandas-ta-classic indicators (`q.feat.pandas_ta.bbands(ohlc)`) with a pandas-friendly interface (`q.feat`)

## Libraries used

Notable libraries qrt is built on and/or wraps:

| Library | Used for | Docs |
|---|---|---|
| [pandas](https://github.com/pandas-dev/pandas) | DataFrames/Series as the common data format throughout | [docs](https://pandas.pydata.org/docs/) |
| [TA-Lib](https://github.com/ta-lib/ta-lib-python) | technical indicators, wrapped in `q.feat.talib` | [docs](https://ta-lib.github.io/ta-lib-python/) |
| [pandas-ta-classic](https://github.com/xgboosted/pandas-ta-classic) | technical indicators & candlestick patterns, wrapped in `q.feat.pandas_ta` | [docs](https://xgboosted.github.io/pandas-ta-classic/) |
| [PyTorch](https://github.com/pytorch/pytorch) | model training and inference (`q.models`) | [docs](https://docs.pytorch.org/docs/stable/) |
| [DuckDB](https://github.com/duckdb/duckdb) | In process database (`q.data`, `q.bt`) | [docs](https://duckdb.org/docs/) |
| [yfinance](https://github.com/ranaroussi/yfinance) | Yahoo Finance market data (`q.vendors`) | [docs](https://ranaroussi.github.io/yfinance/) |
| [Plotly](https://github.com/plotly/plotly.py) | interactive charts, tearsheets, and image export | [docs](https://plotly.com/python/) |


## Project layout

```
qrt/
├── qrt/
│   ├── models/      # pytorch wrappers
│   ├── splits/      # CV, embargo, purging
│   ├── plot/        # plotting + performance reports
│   ├── portfolio/   # portfolio analysis
│   ├── bt/          # backtesting engine
│   ├── feat/        # feature engineering
│   └── data/        # DuckDB securities-master access
├── tests/
├── examples/        # notebooks
└── pyproject.toml
```