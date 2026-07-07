# Quant Research Tools (qrt)

QRT is an umbrella library of quantitative research tools we use internally — one consistent API over the fragmented quant Python ecosystem.

```python
import qrt as q
```

## Features (planned / in progress)

- **Model wrappers** — thin, opinionated wrappers around PyTorch models for training, checkpointing and inference on financial time series (`q.models`)
- **Data splitting** — leakage-aware splits: walk-forward, purged K-fold and combinatorial purged CV with embargo (à la López de Prado) (`q.splits`)
- **Tearsheets** — performance reports for return streams: Sharpe/Sortino/Calmar, drawdowns, rolling stats, monthly heatmaps, benchmark comparison (`q.tearsheet`)
- **Portfolio analysis** — attribution, exposure, turnover and risk decomposition (`q.portfolio`)
- **Backtesting** — event-driven backtesting of model signals, connected to the master securities database (DuckDB) (`q.bt`)
- **Feature engineering** — unified interface wrapping tsfresh and other time-series feature libraries, plus classic indicators, e.g. `q.feat.SMA()`, `q.feat.tsfresh.*` (`q.feat`)

## Installation

We use [uv](https://github.com/astral-sh/uv) for environment and dependency management.

```bash
# create the environment and install qrt with dev extras
uv sync --extra dev

# run anything inside the environment
uv run python -c "import qrt as q"
```

To add a dependency:

```bash
uv add tsfresh
uv add --dev pytest
```

> Not yet published to PyPI — install from source for now.

To use qrt from another uv project (with the optional PyTorch extra):

```toml
dependencies = ["qrt[torch]"]

[tool.uv.sources]
qrt = { git = "https://github.com/quantbert/qrt" }
```

## Quickstart (target API sketch)

```python
import qrt as q

# leakage-safe splits
splits = q.splits.walk_forward(X, n_splits=5, embargo="5D")

# features
X["sma_20"] = q.feat.SMA(prices, 20)

# backtest + tearsheet
result = q.bt.run(signal, prices)
q.tearsheet.report(result.returns, benchmark="SPY")
```

## Project layout (proposed)

```
qrt/
├── qrt/
│   ├── models/      # pytorch wrappers
│   ├── splits/      # CV, embargo, purging
│   ├── tearsheet/   # performance reports
│   ├── portfolio/   # portfolio analysis
│   ├── bt/          # backtesting engine
│   ├── feat/        # feature engineering
│   └── data/        # DuckDB securities-master access
├── tests/
├── examples/        # notebooks
└── pyproject.toml
```

## Roadmap

- [ ] Package scaffolding (`pyproject.toml`, CI, tests)
- [ ] `q.feat` — indicator + tsfresh wrappers
- [ ] `q.splits` — walk-forward and purged CV with embargo
- [ ] `q.tearsheet` — MVP report from a returns series
- [ ] `q.bt` — DuckDB securities-master connector + event-driven backtester
- [ ] `q.portfolio` — attribution and risk decomposition
- [ ] `q.models` — PyTorch training loop wrappers

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


## License

See [LICENSE](LICENSE).

