# Quantfeatures migration

Tracker for migrating `.temp/quantfeatures` into qrt's public architecture.

Status: the feature-domain migration is mostly complete, but the entire legacy
package is not. Of 44 root exports, 16 have native qrt migrations, 6 have
explicit provider replacements, 3 are review-blocked, 1 is explicitly rejected,
and 18 data/benchmark/utility exports still need migrate-or-reject decisions.

## Whole-package audit

Audited on 2026-07-20: 16 Python files, 44 root exports, 7 additional internal
helpers, 6 example notebooks, and the bundled `assets/omxn40.csv` file.

### Accounted root exports

- [x] 16 native migrations: 14 indicators, one calendar operation, and Elo.
- [x] 6 explicit provider replacements: RSI, MACD, stochastic oscillator,
  Bollinger Bands, ATR, and OBV. The legacy pure-pandas formulas are not
  preserved and the replacements require an explicit `talib` or `pandas_ta`
  namespace.
- [ ] 3 review-blocked formulas: `calculate_madev`, `volume_spike_ratio`, and
  `price_spikes`.
- [x] 1 explicit rejection: `process_and_merge_fundamentals`.

### Data exports awaiting a decision

These eight functions use private PostgreSQL schemas and environment-specific
connections. Current `q.data.sources` providers are not equivalent migrations.

- [ ] `fetch_ohlcv`
- [ ] `fetch_data_by_sector`
- [ ] `fetch_data_by_industry`
- [ ] `fetch_market_benchmark_symbol`
- [ ] `fetch_swedish_risk_free_rate`
- [ ] `fetch_quarterly_reports_fundamentals`
- [ ] `fetch_intraday_trades`
- [ ] `fetch_vix`

For each function, decide whether to reject it as organization-specific, move a
private adapter outside pyqrt, or design a public provider contract without the
legacy database assumptions.

### Benchmark exports awaiting a decision

The calculation-only parts are candidates for `q.factor`; the `get_*` and
cache-clear functions mix calculation with proprietary fetching and process-wide
pickle caches and should not be copied intact.

- [ ] `benchmark_sector`
- [ ] `benchmark_industry`
- [ ] `sector_weighted_returns`
- [ ] `get_sector_benchmark`
- [ ] `get_industry_benchmark`
- [ ] `clear_sector_benchmark_cache`
- [ ] `clear_industry_benchmark_cache`

### Cleaning and asset exports awaiting a decision

- [ ] `fill_close_nan`: decide explicit symbol, ordering, and gap/calendar
  semantics before placing it under `q.data` or `q.preprocess`.
- [ ] `apply_mad_filter`: verify the legacy implementation, which is described
  as MAD but computes a rolling mean absolute deviation around a rolling median,
  then design its `q.preprocess.outlier` contract.
- [ ] `load_omxn40_data`: reject the hardcoded `insref`/Nordic metadata or move
  the OMXN40 asset and merge behavior behind a general dataset/provider API.

### Non-root code and examples

- [x] Migrated the five Elo implementation helpers used by `compute_elo` as
  private qrt helpers.
- [x] Removed `_count_closures`; direct calendar session navigation makes the
  capped loop unnecessary.
- [ ] `fill_close_nan_gaps` is not a standalone qrt API. Elo retains limited
  three-row filling internally, with its unresolved calendar semantics tracked
  on the factor roadmap.
- [x] The six example notebooks call the root exports above and add no library
  API beyond a notebook-local `plot_elo_vs_close` helper.
- [ ] The example workflows and `assets/omxn40.csv` remain tied to the pending
  proprietary data/benchmark decisions; they have not been migrated wholesale.

## Architecture decision

Code is organized by what an operation *is*, not by every downstream use of its
output:

| Namespace | Responsibility |
|---|---|
| `q.data` | Acquire and persist observations |
| `q.calendar` | Exchange sessions and market-time semantics |
| `q.indicator` | Stateless, single-instrument market measurements |
| `q.factor` | Cross-sectional characteristics and rankings |
| `q.feature` | Named/versioned feature definitions, computation, and materialization |
| `q.preprocess` | Transformations fitted at the model-training boundary |
| `q.model` | Validation and model lifecycle |
| `q.signal` | Investment intent |
| `q.portfolio` | Positions, weights, and constraints |
| `q.bt` | Historical simulation |
| `q.stats`, `q.plot` | Evaluation and presentation |

Consequences:

- [x] Use `symbol`, never the legacy `insref` identifier.
- [x] Keep one canonical public path; do not add compatibility aliases.
- [x] Keep provider formulas explicit under `q.indicator.talib` and
  `q.indicator.pandas_ta`.
- [x] Keep TA-Lib, pandas-ta-classic, and PyTorch optional at runtime.
- [x] Compute single-instrument indicators independently per entity when used
  through `q.feature`.
- [x] Preserve entity/time keys and reject unsorted histories rather than
  silently sorting them.
- [x] Keep fitted transformations out of materialized raw-feature computation.
- [x] Keep data/network access outside indicator and factor functions.

## Completed moves

### Market time

- [x] `upcoming_market_closure_days` ->
  `q.calendar.non_trading_days_after`
  - Requires an explicit ISO 10383 exchange identifier.
  - Uses direct session navigation; the legacy arbitrary 30-day loop cap was
    removed.
  - Treats an early close as a trading session and validates input sessions.

### Native indicators

- [x] `calculate_simple_moving_average` -> `q.indicator.sma`
- [x] `calculate_exponential_moving_average` -> `q.indicator.ema`
- [x] `log_returns` -> `q.indicator.log_returns`
- [x] `realized_variance` -> `q.indicator.realized_variance`
- [x] `realized_quarticity` -> `q.indicator.realized_quarticity`
- [x] `bipower_variation` -> `q.indicator.bipower_variation`
- [x] `med_rv` -> `q.indicator.med_rv`
- [x] `min_rv` -> `q.indicator.min_rv`
- [x] `apply_realized_volatility_calcs` ->
  `q.indicator.realized_volatility`
- [x] `relative_strength` -> `q.indicator.relative_strength`
- [x] `rs_days` -> `q.indicator.rs_days`
- [x] `rsma` -> `q.indicator.rsma`
- [x] `rs_phase` -> `q.indicator.rs_phase`
- [x] `rsnhbp` -> `q.indicator.rsnhbp`

Native indicators accept one instrument per call, preserve pandas indexes, do
not mutate inputs, and do not fetch benchmark or market data internally.

### Standard provider indicators

- [x] `calculate_rsi` -> `q.indicator.talib.RSI` or
  `q.indicator.pandas_ta.rsi`
- [x] `calculate_macd` -> `q.indicator.talib.MACD` or
  `q.indicator.pandas_ta.macd`
- [x] `calculate_stochastic_oscillator` -> `q.indicator.talib.STOCH` or
  `q.indicator.pandas_ta.stoch`
- [x] `calculate_bollinger_bands` -> `q.indicator.talib.BBANDS` or
  `q.indicator.pandas_ta.bbands`
- [x] `calculate_atr` -> `q.indicator.talib.ATR` or
  `q.indicator.pandas_ta.atr`
- [x] `calculate_on_balance_volume` -> `q.indicator.talib.OBV` or
  `q.indicator.pandas_ta.obv`

These are explicit provider adoptions, not claims of exact compatibility with
the legacy pure-pandas formulas, smoothing, warm-up behavior, or output names.

### Feature lifecycle

- [x] Add `q.feature.Feature` metadata definitions.
- [x] Add contract-enforcing `q.feature.FeatureSet` collections.
- [x] Add per-entity `q.feature.compute`.
- [x] Add sink-based `q.feature.materialize`.
- [x] Move generic lags and rolling percentile rank to `q.feature.ops`.
- [x] Add tests for entity isolation, ordering, required columns, metadata
  conflicts, callable outputs, and sink writes.

### Training boundary

- [x] Reserve `q.preprocess.impute`, `scale`, `outlier`, `encode`, `reduction`,
  and `selection` for fitted model-input transformations.
- [x] Distinguish `q.preprocess.selection` (feature columns) from
  `q.model.selection` (validation rows/splits).

### Cross-sectional Elo

- [x] Move `compute_elo` to `q.factor.compute_elo`.
- [x] Replace the legacy `insref` identifier with required `symbol` input.
- [x] Keep `sectorid` required because matches occur within sectors.
- [x] Accept aligned risk-free-rate data explicitly and perform no fetching.
- [ ] Resolve match scheduling, K-factor, demo-sector, and missing-price
  semantics tracked in `docs/factor/roadmap.qmd`.

### Explicit non-goal

- [x] Do not migrate `process_and_merge_fundamentals`.
  - It combines proprietary fetching with computation and lacks safe
    point-in-time publication semantics.
  - A future fundamentals API must be designed independently under `q.data`
    and `q.feature` contracts.

## Review-gated formulas

These functions are intentionally absent until their semantics are approved.

### MADEV

- [ ] Decide whether the legacy two-stage rolling mean of deviations from a
  rolling SMA is intentional.
- [ ] If retained, choose an explicit name such as `madev_from_sma`; it needs
  `2n - 1` observations and is not the usual mean absolute deviation.

Destination after review: `q.indicator`.

### Volume spike

- [ ] Confirm trend-slope units, thresholds, zero-volume behavior, warm-up
  behavior, and event labels.
- [ ] Decide whether ratio computation and event classification are separate
  functions.

Destination after review: `q.indicator`.

### Price spike

- [ ] Decide whether a spike uses absolute close-to-close movement or intraday
  high/low range.
- [ ] Choose the ATR provider/formula explicitly and avoid temporary-column
  mutation.

Destination after review: `q.indicator`.

## Remaining completion work

- [x] Migrate approved feature-scope source packages and remove old feature
  import paths physically.
- [x] Update authored guides and execute affected notebooks.
- [x] Convert the documentation home page from notebook to QMD and document
  every namespace's role and boundary.
- [x] Regenerate provider stubs and the dependency lockfile.
- [x] Regenerate Quartodoc references for the new roots.
- [x] Render the complete Quarto site.
- [x] Run the full test suite after documentation/dependency regeneration
  (102 tests passing).
- [ ] Review and implement the three blocked indicator formula families above.
- [ ] Resolve the migrated Elo issues on the factor roadmap.
- [ ] Resolve the 18 whole-package data, benchmark, utility, and asset decisions
  in the audit above.

The feature-domain migration is complete when each blocked formula has an
approved implementation contract or explicit rejection. The whole-package
migration is complete only after every item in the audit above has a migrated
replacement or recorded rejection.