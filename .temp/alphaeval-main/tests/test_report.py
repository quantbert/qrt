import numpy as np
import pandas as pd
import pytest

from alphaeval import evaluate


def _make_dataset(n_instruments=2, n_days=60, seed=42):
    """Generate a synthetic multi-instrument dataset."""
    rng = np.random.default_rng(seed)
    rows = []
    for instr in range(n_instruments):
        dates = pd.bdate_range("2024-01-01", periods=n_days)
        returns = rng.normal(0.0005, 0.02, n_days)
        preds = rng.choice([1, 0, -1], size=n_days, p=[0.3, 0.4, 0.3])
        for i, d in enumerate(dates):
            rows.append(
                {
                    "datetime": d,
                    "instrument_id": f"INSTR_{instr}",
                    "return": returns[i],
                    "y_pred": int(preds[i]),
                }
            )
    return pd.DataFrame(rows)


class TestIntegration:
    def test_basic_evaluate(self):
        df = _make_dataset()
        report = evaluate(df, return_horizons=[1, 5], flat_threshold=0.01)
        assert report.matrix is not None
        assert len(report.matrix) == 9
        assert "expectancy_long" in report.metrics
        assert "FP_Long" in report.tail_risk

    def test_summary_output(self):
        df = _make_dataset()
        report = evaluate(df, return_horizons=[1])
        text = report.summary()
        assert "alphaeval" in text
        assert "Expectancy" in text

    def test_to_dict(self):
        df = _make_dataset()
        report = evaluate(df, return_horizons=[1])
        d = report.to_dict()
        assert "matrix" in d
        assert "metrics" in d
        assert "tail_risk" in d

    def test_cell_counts_sum_to_total(self):
        df = _make_dataset(n_instruments=1, n_days=30)
        report = evaluate(df, return_horizons=[1])
        total = sum(cm.count for cm in report.matrix.values())
        # Should equal number of rows with valid forward returns
        assert total == len(report.data)

    def test_log_returns(self):
        df = _make_dataset()
        report = evaluate(df, return_horizons=[1], return_type="log")
        assert report.config["return_type"] == "log"
        assert len(report.matrix) == 9

    def test_transaction_cost(self):
        df = _make_dataset()
        report_no_cost = evaluate(df, return_horizons=[1], transaction_cost=0.0)
        report_with_cost = evaluate(df, return_horizons=[1], transaction_cost=0.001)
        # With costs, total P&L should be lower
        total_no = sum(cm.total_pnl for cm in report_no_cost.matrix.values())
        total_with = sum(cm.total_pnl for cm in report_with_cost.matrix.values())
        assert total_with < total_no

    def test_single_instrument(self):
        df = _make_dataset(n_instruments=1, n_days=20)
        report = evaluate(df, return_horizons=[1])
        assert len(report.matrix) == 9

    def test_repr(self):
        df = _make_dataset()
        report = evaluate(df, return_horizons=[1])
        r = repr(report)
        assert "EvalReport" in r

    def test_time_decay_multiple_horizons(self):
        df = _make_dataset(n_days=50)
        report = evaluate(df, return_horizons=[1, 5, 10])
        assert report.time_decay is not None
        # At least some cells should have data for multiple horizons
        multi = [c for c, hdata in report.time_decay.items() if len(hdata) > 1]
        assert len(multi) > 0
