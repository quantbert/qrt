import numpy as np
import pandas as pd
import pytest

import qrt as q


def _returns() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-01"] * 2 + ["2026-01-02"] * 2),
            "symbol": ["A", "B", "A", "B"],
            "sectorid": ["TECH"] * 4,
            "return": [0.02, -0.01, 0.10, 0.00],
            "close": [100.0, 100.0, 1.0, 1.0],
            "market_cap": [100.0, 300.0, 150.0, 300.0],
            "volume": [10.0, 30.0, 20.0, 20.0],
        }
    )


def test_group_weighted_return_prefers_return_and_does_not_mutate_input():
    data = _returns()
    original = data.copy(deep=True)

    result = q.cross_section.group_weighted_return(data)

    pd.testing.assert_frame_equal(data, original)
    assert result["weighted_return"].tolist() == pytest.approx([0.005, 0.05])
    assert result["asset_count"].tolist() == [2, 2]
    assert result["weight_sum"].tolist() == [2.0, 2.0]


def test_group_weighted_return_falls_back_to_close_by_symbol():
    data = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-01"] * 2 + ["2026-01-02"] * 2),
            "symbol": ["A", "B", "A", "B"],
            "sectorid": ["TECH"] * 4,
            "close": [100.0, 200.0, 110.0, 180.0],
        }
    )

    result = q.cross_section.group_weighted_return(data)

    assert np.isnan(result.iloc[0]["weighted_return"])
    assert result.iloc[0]["asset_count"] == 0
    assert result.iloc[1]["weighted_return"] == pytest.approx(0.0)


def test_group_weighted_return_uses_lagged_market_cap():
    result = q.cross_section.group_weighted_return(
        _returns(), weighting="market_cap"
    )

    assert np.isnan(result.iloc[0]["weighted_return"])
    assert result.iloc[1]["weighted_return"] == pytest.approx(0.025)
    assert result.iloc[1]["weight_sum"] == 400.0


@pytest.mark.parametrize(
    ("weighting", "weight_field"),
    [("volume", None), ("custom", "volume")],
)
def test_group_weighted_return_supports_column_weights(weighting, weight_field):
    result = q.cross_section.group_weighted_return(
        _returns(),
        weighting=weighting,
        weight_field=weight_field,
        weight_lag=0,
    )

    assert result.iloc[0]["weighted_return"] == pytest.approx(-0.0025)
    assert result.iloc[1]["weighted_return"] == pytest.approx(0.05)


def test_group_weighted_return_converts_explicit_log_returns():
    data = _returns().drop(columns=["return"]).assign(
        log_return=np.log1p([0.02, -0.01, 0.10, 0.00])
    )

    result = q.cross_section.group_weighted_return(
        data,
        field="log_return",
        field_type="log_return",
    )

    assert result["weighted_return"].tolist() == pytest.approx([0.005, 0.05])


def test_group_weighted_return_renormalizes_valid_assets_and_groups_unknowns():
    data = _returns()
    data.loc[0, "sectorid"] = None
    data.loc[1, "sectorid"] = None
    data.loc[1, "return"] = np.nan

    result = q.cross_section.group_weighted_return(data)

    first = result[result["date"] == pd.Timestamp("2026-01-01")].iloc[0]
    assert first["sectorid"] == "UnknownSector"
    assert first["weighted_return"] == pytest.approx(0.02)
    assert first["asset_count"] == 1


def test_group_weighted_return_enforces_minimum_assets():
    data = _returns()
    data.loc[1, "return"] = np.nan

    result = q.cross_section.group_weighted_return(data, min_assets=2)

    assert np.isnan(result.iloc[0]["weighted_return"])
    assert result.iloc[0]["asset_count"] == 1


def test_group_weighted_return_inverse_volatility_uses_trailing_returns():
    dates = pd.date_range("2026-01-01", periods=4)
    data = pd.DataFrame(
        {
            "date": np.repeat(dates, 2),
            "symbol": ["A", "B"] * 4,
            "sectorid": ["TECH"] * 8,
            "return": [0.01, 0.01, 0.03, 0.05, 0.02, 0.01, 0.04, 0.03],
        }
    )

    result = q.cross_section.group_weighted_return(
        data,
        weighting="inverse_volatility",
        volatility_window=2,
    )

    assert result["asset_count"].tolist() == [0, 0, 2, 2]
    assert np.isfinite(result.iloc[-1]["weighted_return"])


def test_group_weighted_return_rejects_zero_inverse_volatility():
    data = _returns()
    data["return"] = 0.01

    with pytest.raises(ValueError, match="non-finite weights"):
        q.cross_section.group_weighted_return(
            data,
            weighting="inverse_volatility",
            volatility_window=2,
            weight_lag=0,
        )


def test_group_weighted_return_requires_explicit_field_and_type_without_defaults():
    data = _returns().drop(columns=["return", "close"])

    with pytest.raises(ValueError, match="both field and field_type"):
        q.cross_section.group_weighted_return(data)
    with pytest.raises(ValueError, match="field_type is required"):
        q.cross_section.group_weighted_return(data, field="volume")


def test_group_weighted_return_rejects_duplicates_and_negative_weights():
    duplicate = pd.concat([_returns(), _returns().iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="at most one row"):
        q.cross_section.group_weighted_return(duplicate)

    negative = _returns()
    negative.loc[0, "market_cap"] = -1
    with pytest.raises(ValueError, match="negative weights"):
        q.cross_section.group_weighted_return(
            negative, weighting="market_cap"
        )