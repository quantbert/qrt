import numpy as np
import pandas as pd
import pytest

from alphaeval.matrix import classify_actual, assign_cells, compute_pnl, build_matrix


class TestClassifyActual:
    def test_basic_classification(self):
        fwd = pd.Series([0.02, -0.03, 0.001, -0.002, 0.0])
        result = classify_actual(fwd, flat_threshold=0.005)
        expected = ["Up", "Down", "Flat", "Flat", "Flat"]
        assert list(result) == expected

    def test_threshold_boundary(self):
        fwd = pd.Series([0.005, -0.005, 0.0051, -0.0051])
        result = classify_actual(fwd, flat_threshold=0.005)
        # Exactly at threshold = Flat (not strictly greater/less)
        assert list(result) == ["Flat", "Flat", "Up", "Down"]

    def test_zero_threshold(self):
        fwd = pd.Series([0.01, -0.01, 0.0])
        result = classify_actual(fwd, flat_threshold=0.0)
        assert list(result) == ["Up", "Down", "Flat"]


class TestAssignCells:
    def test_all_nine_cells(self):
        actual = pd.Series(["Up", "Up", "Up", "Flat", "Flat", "Flat", "Down", "Down", "Down"])
        y_pred = pd.Series([1, 0, -1, 1, 0, -1, 1, 0, -1])
        result = assign_cells(actual, y_pred)
        expected = [
            "TP_Long",
            "FN_Up",
            "FP_Short",
            "CD_Long",
            "TN",
            "CD_Short",
            "FP_Long",
            "FN_Down",
            "TP_Short",
        ]
        assert list(result) == expected


class TestComputePnl:
    def test_buy_positive(self):
        fwd = pd.Series([0.05])
        y_pred = pd.Series([1])
        pnl = compute_pnl(fwd, y_pred, position_size=1.0, transaction_cost=0.0)
        assert float(pnl.iloc[0]) == pytest.approx(0.05)

    def test_sell_negative_return(self):
        # Sell when price goes down = profit
        fwd = pd.Series([-0.03])
        y_pred = pd.Series([-1])
        pnl = compute_pnl(fwd, y_pred, position_size=1.0, transaction_cost=0.0)
        assert float(pnl.iloc[0]) == pytest.approx(0.03)

    def test_hold_is_zero(self):
        fwd = pd.Series([0.05])
        y_pred = pd.Series([0])
        pnl = compute_pnl(fwd, y_pred, position_size=1.0, transaction_cost=0.0)
        assert float(pnl.iloc[0]) == pytest.approx(0.0)

    def test_transaction_cost(self):
        fwd = pd.Series([0.05])
        y_pred = pd.Series([1])
        pnl = compute_pnl(fwd, y_pred, position_size=1.0, transaction_cost=0.001)
        assert float(pnl.iloc[0]) == pytest.approx(0.049)

    def test_position_size(self):
        fwd = pd.Series([0.05])
        y_pred = pd.Series([1])
        pnl = compute_pnl(fwd, y_pred, position_size=2.0, transaction_cost=0.0)
        assert float(pnl.iloc[0]) == pytest.approx(0.10)


class TestBuildMatrix:
    def _make_df(self):
        """Construct data where we know cell assignments."""
        fwd_returns = [0.05, -0.03, 0.001, 0.04, -0.002, -0.04, -0.05, 0.002, 0.03]
        y_pred = [1, 1, 1, 0, 0, 0, -1, -1, -1]
        return pd.DataFrame(
            {
                "fwd_return_1": fwd_returns,
                "y_pred": y_pred,
            }
        )

    def test_cell_counts(self):
        df = self._make_df()
        matrix = build_matrix(df, "fwd_return_1", flat_threshold=0.005, position_size=1.0, transaction_cost=0.0)

        # Buy predictions: 0.05 (Up→TP_Long), -0.03 (Down→FP_Long), 0.001 (Flat→CD_Long)
        assert matrix["TP_Long"].count == 1
        assert matrix["FP_Long"].count == 1
        assert matrix["CD_Long"].count == 1

        # Hold predictions: 0.04 (Up→FN_Up), -0.002 (Flat→TN), -0.04 (Down→FN_Down)
        assert matrix["FN_Up"].count == 1
        assert matrix["TN"].count == 1
        assert matrix["FN_Down"].count == 1

        # Sell predictions: -0.05 (Down→TP_Short), 0.002 (Flat→CD_Short), 0.03 (Up→FP_Short)
        assert matrix["TP_Short"].count == 1
        assert matrix["CD_Short"].count == 1
        assert matrix["FP_Short"].count == 1

    def test_tp_long_pnl(self):
        df = self._make_df()
        matrix = build_matrix(df, "fwd_return_1", flat_threshold=0.005, position_size=1.0, transaction_cost=0.0)
        assert matrix["TP_Long"].total_pnl == pytest.approx(0.05)

    def test_tp_short_pnl(self):
        df = self._make_df()
        matrix = build_matrix(df, "fwd_return_1", flat_threshold=0.005, position_size=1.0, transaction_cost=0.0)
        # Sell × -0.05 = +0.05
        assert matrix["TP_Short"].total_pnl == pytest.approx(0.05)

    def test_fp_long_pnl_negative(self):
        df = self._make_df()
        matrix = build_matrix(df, "fwd_return_1", flat_threshold=0.005, position_size=1.0, transaction_cost=0.0)
        # Buy × -0.03 = -0.03
        assert matrix["FP_Long"].total_pnl == pytest.approx(-0.03)
