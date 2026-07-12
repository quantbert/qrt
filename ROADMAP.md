
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

