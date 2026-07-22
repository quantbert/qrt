import numpy as np
import pandas as pd
import pytest

import qrt as q


def test_rank_percentile_rank_and_zscore_preserve_panel_labels():
    values = pd.DataFrame(
        [[1.0, 3.0, 2.0], [4.0, 4.0, np.nan]],
        index=["t1", "t2"],
        columns=["A", "B", "C"],
    )

    ranks = q.cross_section.rank(values)
    percentiles = q.cross_section.percentile_rank(values)
    standardized = q.cross_section.zscore(values)

    assert ranks.loc["t1"].tolist() == [1.0, 3.0, 2.0]
    assert percentiles.loc["t1"].tolist() == pytest.approx([1 / 3, 1.0, 2 / 3])
    assert standardized.loc["t1"].mean() == pytest.approx(0.0)
    assert standardized.loc["t1"].std(ddof=0) == pytest.approx(1.0)
    assert ranks.index.equals(values.index)
    assert ranks.columns.equals(values.columns)


def test_rank_supports_one_snapshot_and_descending_order():
    values = pd.Series([5.0, 1.0, 3.0], index=["A", "B", "C"], name="value")

    result = q.cross_section.rank(values, ascending=False)

    pd.testing.assert_series_equal(
        result, pd.Series([1.0, 3.0, 2.0], index=values.index, name="value")
    )


def test_neutralize_removes_numeric_and_categorical_exposures():
    index = pd.Index(["A", "B", "C", "D", "E", "F"], name="symbol")
    exposures = pd.DataFrame(
        {
            "beta": [0.5, 1.0, 1.5, 0.7, 1.2, 1.7],
            "sector": ["tech", "tech", "tech", "health", "health", "health"],
        },
        index=index,
    )
    values = pd.Series(
        0.2 + 2.0 * exposures["beta"] + (exposures["sector"] == "tech") * 0.5,
        index=index,
        name="signal",
    )
    values.iloc[-1] += 0.3

    result = q.cross_section.neutralize(values, exposures)

    assert result.name == "signal"
    assert result.sum() == pytest.approx(0.0, abs=1e-12)
    assert result.cov(exposures["beta"]) == pytest.approx(0.0, abs=1e-12)
    assert result.groupby(exposures["sector"]).mean().abs().max() < 1e-12


def test_neutralize_preserves_missing_rows():
    values = pd.Series([1.0, 2.0, np.nan, 4.0], index=list("ABCD"))
    exposures = pd.Series([1.0, 2.0, 3.0, 5.0], index=values.index)

    result = q.cross_section.neutralize(values, exposures)

    assert np.isnan(result.loc["C"])


def test_neutralize_preserves_missing_categorical_exposures():
    values = pd.Series([1.0, 2.0, 3.0, 4.0], index=list("ABCD"))
    sectors = pd.Series(["x", "x", None, "y"], index=values.index)

    result = q.cross_section.neutralize(values, sectors)

    assert np.isnan(result.loc["C"])


def test_relative_strength_ranks_trailing_returns_by_date():
    prices = pd.DataFrame(
        {
            "A": [100.0, 110.0, 121.0],
            "B": [100.0, 100.0, 105.0],
            "C": [100.0, 90.0, 81.0],
        },
        index=pd.date_range("2026-01-01", periods=3),
    )

    result = q.cross_section.relative_strength(prices, lookback=1)

    assert result.iloc[0].isna().all()
    assert result.iloc[1].tolist() == pytest.approx([1.0, 2 / 3, 1 / 3])
    assert result.iloc[2].tolist() == pytest.approx([1.0, 2 / 3, 1 / 3])


def test_cross_section_transforms_reject_non_numeric_values():
    with pytest.raises(TypeError, match="numeric"):
        q.cross_section.zscore(pd.Series(["a", "b"]))