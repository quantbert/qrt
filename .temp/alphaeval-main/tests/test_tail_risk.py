import numpy as np
import pandas as pd
import pytest

from alphaeval.tail_risk import (
    compute_var,
    compute_cvar,
    compute_max_drawdown,
    compute_max_dd_contribution,
    compute_distribution_stats,
)


class TestVaR:
    def test_basic(self):
        losses = pd.Series([-0.10, -0.05, -0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.03, 0.05])
        var = compute_var(losses, percentile=5.0)
        # 5th percentile of 10 values should be close to the worst value
        assert var < 0

    def test_empty(self):
        var = compute_var(pd.Series(dtype=float))
        assert np.isnan(var)


class TestCVaR:
    def test_basic(self):
        losses = pd.Series(np.linspace(-0.10, 0.10, 100))
        cvar = compute_cvar(losses, percentile=5.0)
        var = compute_var(losses, percentile=5.0)
        # CVaR should be worse (more negative) than VaR
        assert cvar <= var

    def test_empty(self):
        cvar = compute_cvar(pd.Series(dtype=float))
        assert np.isnan(cvar)


class TestMaxDrawdown:
    def test_simple_drawdown(self):
        # Cumulative: [1, 3, 2, 4] -> max DD = 2-3 = -1
        cum_pnl = pd.Series([1.0, 3.0, 2.0, 4.0])
        dd = compute_max_drawdown(cum_pnl)
        assert dd == pytest.approx(-1.0)

    def test_no_drawdown(self):
        cum_pnl = pd.Series([1.0, 2.0, 3.0, 4.0])
        dd = compute_max_drawdown(cum_pnl)
        assert dd == pytest.approx(0.0)

    def test_empty(self):
        dd = compute_max_drawdown(pd.Series(dtype=float))
        assert dd == 0.0


class TestDistributionStats:
    def test_normal_ish(self):
        rng = np.random.default_rng(42)
        returns = pd.Series(rng.normal(0, 1, 1000))
        stats = compute_distribution_stats(returns)
        # Normal dist: skewness ~0, kurtosis ~0
        assert abs(stats["skewness"]) < 0.5
        assert abs(stats["excess_kurtosis"]) < 1.0

    def test_too_few(self):
        stats = compute_distribution_stats(pd.Series([1.0, 2.0]))
        assert np.isnan(stats["skewness"])


class TestMaxDDContribution:
    def test_basic(self):
        losses = pd.Series([-0.10, -0.05, -0.03, -0.01])
        contrib = compute_max_dd_contribution(losses, total_max_dd=-0.15, worst_pct=25.0)
        # Worst 25% = worst 1 value = -0.10
        # Contribution = 0.10 / 0.15
        assert contrib == pytest.approx(0.10 / 0.15, abs=0.1)

    def test_zero_dd(self):
        losses = pd.Series([-0.01])
        contrib = compute_max_dd_contribution(losses, total_max_dd=0.0)
        assert np.isnan(contrib)
