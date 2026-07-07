import numpy as np
import pandas as pd
import pytest

from alphaeval.matrix import build_matrix
from alphaeval.metrics import compute_aggregate_metrics


def _build_test_matrix():
    """Build a matrix from known data with clear winners and losers."""
    # 10 trades: mix of Buy/Sell with Up/Down outcomes
    fwd_returns = [
        0.05,
        0.03,
        -0.02,
        -0.04,  # Buy predictions
        -0.06,
        -0.02,
        0.03,
        0.01,  # Sell predictions
        0.04,
        -0.03,  # Hold predictions
    ]
    y_pred = [
        1,
        1,
        1,
        1,
        -1,
        -1,
        -1,
        -1,
        0,
        0,
    ]
    df = pd.DataFrame({"fwd_return_1": fwd_returns, "y_pred": y_pred})
    return build_matrix(df, "fwd_return_1", flat_threshold=0.005, position_size=1.0, transaction_cost=0.0)


class TestAggregateMetrics:
    def test_profit_factor(self):
        matrix = _build_test_matrix()
        m = compute_aggregate_metrics(matrix, 1.0, 0.0)
        # Gross profit and gross loss should both be positive/negative
        assert m["profit_factor"] is not None
        assert m["profit_factor"] > 0

    def test_rwa_between_0_and_1(self):
        matrix = _build_test_matrix()
        m = compute_aggregate_metrics(matrix, 1.0, 0.0)
        assert 0.0 <= m["return_weighted_accuracy"] <= 1.0

    def test_expectancy_values_exist(self):
        matrix = _build_test_matrix()
        m = compute_aggregate_metrics(matrix, 1.0, 0.0)
        assert "expectancy_long" in m
        assert "expectancy_short" in m
        assert isinstance(m["expectancy_long"], float)
        assert isinstance(m["expectancy_short"], float)

    def test_no_losses_profit_factor_none(self):
        # All correct predictions
        df = pd.DataFrame(
            {
                "fwd_return_1": [0.05, 0.03],
                "y_pred": [1, 1],
            }
        )
        matrix = build_matrix(df, "fwd_return_1", flat_threshold=0.005, position_size=1.0, transaction_cost=0.0)
        m = compute_aggregate_metrics(matrix, 1.0, 0.0)
        assert m["profit_factor"] is None  # No losses

    def test_empty_matrix(self):
        # All hold
        df = pd.DataFrame(
            {
                "fwd_return_1": [0.01, -0.01],
                "y_pred": [0, 0],
            }
        )
        matrix = build_matrix(df, "fwd_return_1", flat_threshold=0.005, position_size=1.0, transaction_cost=0.0)
        m = compute_aggregate_metrics(matrix, 1.0, 0.0)
        assert m["total_active"] == 0
        assert m["return_weighted_accuracy"] == 0.0
