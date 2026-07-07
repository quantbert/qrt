import numpy as np
import pandas as pd
import pytest

from alphaeval.forward_returns import compute_forward_returns, validate_data


def _make_data(returns, y_pred=None, instrument_id="A"):
    """Helper to build a simple DataFrame."""
    n = len(returns)
    if y_pred is None:
        y_pred = [0] * n
    return pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=n, freq="B"),
            "instrument_id": instrument_id,
            "return": returns,
            "y_pred": y_pred,
        }
    )


class TestValidation:
    def test_missing_columns(self):
        df = pd.DataFrame({"datetime": [1], "return": [0.01]})
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_data(df, "simple")

    def test_invalid_return_type(self):
        df = _make_data([0.01])
        with pytest.raises(ValueError, match="return_type must be"):
            validate_data(df, "linear")

    def test_invalid_predictions(self):
        df = _make_data([0.01], y_pred=[2])
        with pytest.raises(ValueError, match="y_pred must contain only"):
            validate_data(df, "simple")

    def test_duplicate_datetime_instrument(self):
        df = pd.DataFrame(
            {
                "datetime": ["2024-01-01", "2024-01-01"],
                "instrument_id": ["A", "A"],
                "return": [0.01, 0.02],
                "y_pred": [1, -1],
            }
        )
        with pytest.raises(ValueError, match="duplicate"):
            validate_data(df, "simple")


class TestForwardReturns:
    def test_simple_1d(self):
        # Returns: [1%, 2%, 3%, -1%]
        # fwd_return_1 at index 0 = return[1] = 0.02
        # fwd_return_1 at index 1 = return[2] = 0.03
        # fwd_return_1 at index 2 = return[3] = -0.01
        # index 3 = NaN (dropped)
        df = _make_data([0.01, 0.02, 0.03, -0.01])
        result = compute_forward_returns(df, [1], "simple")
        assert len(result) == 3
        np.testing.assert_almost_equal(result["fwd_return_1"].values, [0.02, 0.03, -0.01])

    def test_simple_2d(self):
        # Returns: [1%, 2%, 3%, -1%]
        # fwd_return_2 at index 0 = (1+0.02)*(1+0.03) - 1 = 0.0506
        # fwd_return_2 at index 1 = (1+0.03)*(1-0.01) - 1 = 0.0197
        df = _make_data([0.01, 0.02, 0.03, -0.01])
        result = compute_forward_returns(df, [2], "simple")
        assert len(result) == 2
        np.testing.assert_almost_equal(result["fwd_return_2"].values[0], 0.0506)
        np.testing.assert_almost_equal(result["fwd_return_2"].values[1], 0.0197)

    def test_log_1d(self):
        df = _make_data([0.01, 0.02, 0.03, -0.01])
        result = compute_forward_returns(df, [1], "log")
        assert len(result) == 3
        np.testing.assert_almost_equal(result["fwd_return_1"].values, [0.02, 0.03, -0.01])

    def test_log_2d(self):
        # Log: fwd_return_2 at index 0 = 0.02 + 0.03 = 0.05
        df = _make_data([0.01, 0.02, 0.03, -0.01])
        result = compute_forward_returns(df, [2], "log")
        np.testing.assert_almost_equal(result["fwd_return_2"].values[0], 0.05)

    def test_multi_instrument(self):
        df_a = _make_data([0.01, 0.02, 0.03], instrument_id="A")
        df_b = _make_data([0.05, -0.02, 0.01], instrument_id="B")
        df = pd.concat([df_a, df_b], ignore_index=True)
        result = compute_forward_returns(df, [1], "simple")
        # Each instrument drops its last row
        assert len(result) == 4  # 2 per instrument

    def test_multiple_horizons(self):
        df = _make_data([0.01, 0.02, 0.03, -0.01, 0.05])
        result = compute_forward_returns(df, [1, 2], "simple")
        assert "fwd_return_1" in result.columns
        assert "fwd_return_2" in result.columns

    def test_horizon_exceeds_data(self):
        df = _make_data([0.01, 0.02])
        with pytest.warns(UserWarning, match="Dropped"):
            result = compute_forward_returns(df, [5], "simple")
        assert len(result) == 0
