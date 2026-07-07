# alphaeval — Specification v2

## Purpose

A Python library that replaces `sklearn.metrics.classification_report` with a finance-aware evaluation tool. It maps discrete three-way predictions (Buy/Hold/Sell) against continuous financial outcomes to produce a return-weighted 3×3 confusion matrix, aggregate trading metrics, tail risk analysis, visualizations, and time-decay drill-downs.

---

## API

### Entry Point

```python
from alphaeval import evaluate

report = evaluate(
    data=df,
    return_horizons=[1, 5, 10],
    flat_threshold=0.005,
    return_type='simple',
    benchmark=None,
    target_names=['BUY', 'HOLD', 'SELL'],
    position_size=1.0,
    transaction_cost=0.0,
)

print(report.summary())
report.plot()
```

### Input: `data` (pd.DataFrame)

Required columns:

| Column          | Type          | Description                                              |
|-----------------|---------------|----------------------------------------------------------|
| `datetime`      | datetime-like | Date/time of each observation                            |
| `instrument_id` | str or int    | Identifier for the instrument                            |
| `return`        | float         | Daily return for that instrument (simple or log)         |
| `y_pred`        | int           | Model prediction: 1 (Buy), 0 (Hold), -1 (Sell)          |

The library computes forward returns internally by looking ahead N trading days per instrument.

### Parameters

| Parameter          | Type                    | Default              | Description                                                                                           |
|--------------------|-------------------------|----------------------|-------------------------------------------------------------------------------------------------------|
| `return_horizons`  | `list[int]`             | `[1, 5, 10]`        | Forward return horizons in trading days. First is primary; others feed time-decay analysis.            |
| `flat_threshold`   | `float`                 | `0.005`              | Returns in `(-threshold, +threshold)` classified as Flat. Above = Up, below = Down.                   |
| `return_type`      | `str`                   | `'simple'`           | `'simple'`: compound returns. `'log'`: additive returns. Must be explicit.                            |
| `benchmark`        | `pd.Series \| None`     | `None`               | Optional benchmark returns for excess return calculation.                                             |
| `target_names`     | `list[str]`             | `['BUY','HOLD','SELL']` | Display names for predictions 1, 0, -1.                                                            |
| `position_size`    | `float`                 | `1.0`                | Equal-weight position size multiplier.                                                                |
| `transaction_cost` | `float`                 | `0.0`                | Round-trip transaction cost per trade (as a fraction, e.g. 0.001 = 10bps).                            |

### Output: `EvalReport`

- `report.summary()` — sklearn-style text report
- `report.matrix` — 3×3 matrix with per-cell metrics
- `report.metrics` — aggregate metrics dict
- `report.tail_risk` — tail risk metrics dict
- `report.time_decay` — per-cell metrics across horizons
- `report.plot()` — renders all visualizations
- `report.to_dict()` — full report as nested dict

---

## Forward Return Computation

The library computes forward returns per instrument by looking ahead from each observation date.

- **Simple returns:** $r_{t \to t+h} = \prod_{i=1}^{h}(1 + r_{t+i}) - 1$
- **Log returns:** $r_{t \to t+h} = \sum_{i=1}^{h} r_{t+i}$

Observations where the full horizon cannot be computed (end of series) are dropped with a warning.

---

## 3×3 Confusion Matrix

### Classification of Actual Market Movement

Forward return at primary horizon is classified using `flat_threshold`:

- **Up:** forward return > +flat_threshold
- **Flat:** -flat_threshold ≤ forward return ≤ +flat_threshold
- **Down:** forward return < -flat_threshold

### Matrix Cells

|                    | **Pred: Buy (1)**              | **Pred: Hold (0)**              | **Pred: Sell (-1)**              |
|--------------------|--------------------------------|---------------------------------|----------------------------------|
| **Actual: Up**     | **TP_Long** — correct long     | **FN_Up** — missed bull         | **FP_Short** — wrong direction   |
| **Actual: Flat**   | **CD_Long** — cost drag long   | **TN** — correct passivity      | **CD_Short** — cost drag short   |
| **Actual: Down**   | **FP_Long** — wrong direction  | **FN_Down** — missed bear       | **TP_Short** — correct short     |

### Cell Definitions

**Correct Positions (True Positives):**
- **TP_Long** (Buy + Up): Model predicted Buy, price went up. P&L = +forward_return × position_size - transaction_cost.
- **TP_Short** (Sell + Down): Model predicted Sell, price went down. P&L = -forward_return × position_size - transaction_cost (positive since return is negative).

Metrics: count, total profit, average profit per trade, max profit.

**Incorrect Positions (False Positives — Capital Killers):**
- **FP_Long** (Buy + Down): Model predicted Buy, price went down. P&L = +forward_return × position_size - transaction_cost (negative).
- **FP_Short** (Sell + Up): Model predicted Sell, price went up. P&L = -forward_return × position_size - transaction_cost (negative). Particularly dangerous due to asymmetric short risk.

Metrics: count, total loss, average loss per trade, max loss.

**Missed Opportunities (False Negatives):**
- **FN_Up** (Hold + Up): Model said Hold, market rallied. Opportunity cost = forward_return × position_size.
- **FN_Down** (Hold + Down): Model said Hold, market dropped. Opportunity cost = |forward_return| × position_size (missed short profit).

Metrics: count, total opportunity cost, average opportunity cost.

**Correct Passivity (True Negative):**
- **TN** (Hold + Flat): Model said Hold, market went nowhere. Capital preserved.

Metrics: count, capital preserved = sum of |forward_return| (the whipsaw avoided).

**Cost Drag (New — Directional Prediction During Flat Market):**
- **CD_Long** (Buy + Flat): Model predicted bullish move, market was flat. No directional profit. Incurs transaction_cost × 2 (entry + exit) per trade. Represents overconfident long signals during consolidation.
- **CD_Short** (Sell + Flat): Model predicted bearish move, market was flat. Same as CD_Long but in practice worse due to funding/borrow costs. Incurs transaction_cost × 2 per trade.

Metrics: count, total cost drag, average cost per trade.

### P&L Calculation

For active positions (Buy or Sell predictions):

```
pnl = direction × forward_return × position_size - transaction_cost
```

Where `direction` = +1 for Buy, -1 for Sell.

---

## Aggregate Metrics

**Expectancy (per Long and Short separately):**

$$E = (W_r \times \bar{W}) - (L_r \times \bar{L})$$

Where $W_r$ = win rate, $\bar{W}$ = average win, $L_r$ = loss rate, $\bar{L}$ = average loss.

**Profit Factor:**

$$PF = \frac{\text{Gross Profit}}{\text{Gross Loss}}$$

Sum of all positive P&L divided by absolute sum of all negative P&L.

**Return-Weighted Accuracy:**

$$RWA = \frac{\sum_{i \in \text{correct}} |r_i|}{\sum_{i \in \text{all active}} |r_i|}$$

Measures whether the model captures large moves correctly. "Correct" includes TP_Long and TP_Short. "All active" includes all Buy and Sell predictions (excludes Hold).

---

## Tail Risk Metrics (Phase 3)

Computed separately for FP_Long and FP_Short distributions.

**Value at Risk (VaR):**
The loss threshold at a given percentile (default 5%). The worst 5% of losses begin at this value.

**Conditional Value at Risk (CVaR / Expected Shortfall):**
The average loss beyond VaR. If VaR at 5% = -3%, CVaR is the mean of all losses worse than -3%.

**Max Drawdown Contribution:**

$$MDC = \frac{\sum_{i \in \text{subset}} |loss_i|}{MDD_{\text{total}}}$$

Where subset = worst N% of false signals (default: worst 1%), and $MDD_{\text{total}}$ is the max drawdown of the full strategy's cumulative P&L curve.

**Excess Kurtosis & Skewness:**
Computed via `scipy.stats`. Reveals fat tails and asymmetry in loss distributions. Short FP losses often have positive skew (unbounded upside risk makes losses right-skewed).

---

## Time-Decay / Holding Period Analysis

For each matrix cell, compute metrics at every horizon in `return_horizons`:

| Pattern | Cell | Meaning |
|---------|------|---------|
| FP → profitable at longer horizon | FP_Long, FP_Short | Model entered too early; direction was eventually correct |
| TP → erodes at longer horizon | TP_Long, TP_Short | Model captured a short-term move but doesn't hold |
| FN grows over time | FN_Up, FN_Down | Missed opportunity gets worse; model should have been positioned |
| TN stays flat/volatile | TN | Confirms correct Hold decision across horizons |

Output: `{cell_name: {horizon: {count, mean_return, total_pnl, ...}}}`.

---

## Visualizations

1. **Violin Plots:** Forward returns for all 9 matrix cells side-by-side. Shows density, median, and tail shape.
2. **KDE Overlay:** Density of TP (correct positions) vs FP (incorrect positions). Reveals whether profit distribution outperforms loss distribution.
3. **Time-Decay Line Charts:** Mean return per cell across horizons. Reveals entry timing errors and holding period effects.

All plot functions return `matplotlib.Figure`.

---

## Defaults & Assumptions

- **Equal-weight positions:** All trades use the same `position_size` (default 1.0). Configurable.
- **Zero transaction costs:** Default `transaction_cost = 0.0`. Configurable as a fraction (e.g. 0.001 = 10bps round-trip).
- **No short-specific costs:** Borrow/funding costs not modeled separately (captured via `transaction_cost` if desired).
- **No compounding across trades:** Each observation is evaluated independently.
- **Fama-French regression:** Deferred to a future phase.

---

## Deferred (Future Phases)

- Fama-French Three-Factor regression on strategy returns
- statsmodels OLS integration for alpha estimation
- Short-specific cost modeling (borrow rate parameter)
- Portfolio-level analysis (cross-instrument correlations)
