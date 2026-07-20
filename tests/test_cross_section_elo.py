import pandas as pd
import pytest

import qrt as q


def _daily_prices() -> pd.DataFrame:
    rows = []
    dates = pd.date_range("2026-01-01", periods=5)
    for date, a_close, b_close in zip(
        dates,
        [100.0, 102.0, 104.0, 106.0, 108.0],
        [100.0, 99.0, 98.0, 97.0, 96.0],
        strict=True,
    ):
        rows.extend(
            [
                {
                    "date": date,
                    "symbol": "A",
                    "close": a_close,
                    "sectorid": "TECH",
                },
                {
                    "date": date,
                    "symbol": "B",
                    "close": b_close,
                    "sectorid": "TECH",
                },
                {
                    "date": date,
                    "symbol": "C",
                    "close": 50.0,
                    "sectorid": "HEALTH",
                },
            ]
        )
    return pd.DataFrame(rows)


def test_compute_elo_rates_symbols_within_sector_without_mutating_input():
    data = _daily_prices()
    original = data.copy(deep=True)

    result = q.cross_section.compute_elo(
        data,
        daily_vol_window=2,
        use_excess_returns=False,
    )

    pd.testing.assert_frame_equal(data, original)
    latest = result.groupby("symbol").tail(1).set_index("symbol")
    assert latest.loc["A", "elo"] > 1500
    assert latest.loc["B", "elo"] < 1500
    assert latest.loc["A", "matches_played"] == 3
    assert latest.loc["B", "matches_played"] == 3
    assert latest.loc["C", "elo"] == 1500
    assert latest.loc["C", "matches_played"] == 0


@pytest.mark.parametrize("column", ["date", "symbol", "close", "sectorid"])
def test_compute_elo_requires_long_form_universe_columns(column):
    with pytest.raises(ValueError, match=column):
        q.cross_section.compute_elo(_daily_prices().drop(columns=column))


def test_compute_elo_uses_explicit_risk_free_rates():
    data = _daily_prices()
    risk_free = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=5),
            "rate": [0.0001] * 5,
        }
    )

    result = q.cross_section.compute_elo(
        data,
        daily_vol_window=2,
        rf_data=risk_free,
    )

    assert {"rate", "daily_rf_rate", "excess_return"} <= set(result.columns)
    assert result["daily_rf_rate"].eq(0.0001).all()