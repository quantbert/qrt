---
title: Getting Started
---

# Getting Started

QRT is an umbrella library of Quantitative Research Tools

```{warning}
STILL IN ALPHA! DONT USE!
```

## Quickstart

```bash
uv add pyqrt
```

```python
import qrt as q

# fetch OHLCV data (cached as parquet)
vendor = q.vendors.YFinance()
ohlc = vendor.fetch_ohlc("SPY", "2024-01-01", "2025-01-01", "1d")

# features
X = q.feat.qta.lags(ohlc["close"], [1, 5, 21])
X["sma_20"] = q.feat.qta.sma(ohlc["close"], 20)
X["rsi_14"] = q.feat.talib.RSI(ohlc)
```

## Library layout

| Module | Purpose |
|---|---|
| `q.feat` | feature engineering: own indicators + TA-Lib + pandas-ta-classic |
| `q.vendors` | market data vendors (Yahoo Finance, Binance) with parquet caching |
| `q.dataload` | loading and aggregating raw trade data into OHLC bars |
| `q.data` | master securities database (DuckDB) |
| `q.splits` | leakage-aware CV splits (walk-forward, purged K-fold, embargo) |
| `q.models` | PyTorch model wrappers |
| `q.bt` | event-driven backtesting |
| `q.plot` | plotting + performance reports (tearsheets) |
| `q.portfolio` | portfolio analysis |

## Development

```bash
make install   # sync the environment
make test      # run the test suite
make stubs     # regenerate .pyi stubs for the dynamic feat wrappers
make docs      # serve these docs locally
```

```{toctree}
:hidden:
:maxdepth: 2

feat
apidocs/index
```
