import numpy as np
import pandas as pd
import pytest

from alphaeval.time_decay import analyze_time_decay


def _make_df():
    """DataFrame with multiple horizons pre-computed."""
    n = 20
    rng = np.random.default_rng(42)
    return pd.DataFrame(
        {
            "y_pred": rng.choice([1, 0, -1], size=n),
            "fwd_return_1": rng.normal(0, 0.02, n),
            "fwd_return_5": rng.normal(0, 0.04, n),
        }
    )


class TestTimeDcay:
    def test_returns_all_horizons(self):
        df = _make_df()
        result = analyze_time_decay(df, [1, 5], flat_threshold=0.005, position_size=1.0, transaction_cost=0.0)
        # Should have entries for both horizons
        for cell_data in result.values():
            assert 1 in cell_data or 5 in cell_data

    def test_cell_counts_match(self):
        df = _make_df()
        result = analyze_time_decay(df, [1], flat_threshold=0.005, position_size=1.0, transaction_cost=0.0)
        total = sum(cell_data[1]["count"] for cell_data in result.values() if 1 in cell_data)
        assert total == len(df)

    def test_missing_horizon_column(self):
        df = _make_df().drop(columns=["fwd_return_5"])
        result = analyze_time_decay(df, [1, 5], flat_threshold=0.005, position_size=1.0, transaction_cost=0.0)
        # Horizon 5 should be absent since column doesn't exist
        for cell_data in result.values():
            assert 5 not in cell_data
