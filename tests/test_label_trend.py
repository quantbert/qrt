import numpy as np
import pandas as pd
import pytest

import qrt as q


def test_trend_scanning_labels_rising_falling_and_flat_paths():
    index = pd.date_range("2026-01-01", periods=12, name="datetime")
    prices = pd.Series(
        np.exp([0.00, 0.01, 0.02, 0.03, 0.03, 0.02, 0.01, 0.00, 0, 0, 0, 0]),
        index=index,
        name="close",
    )
    events = index[[0, 4, 8]]

    result = q.label.trend_scanning(
        prices,
        events=events,
        horizons=[2, 3],
    )

    assert result["label"].tolist() == [1, -1, 0]
    assert result["horizon"].tolist() == [2, 2, 2]
    assert result.loc[events[0], "slope"] == pytest.approx(0.01)
    assert result.loc[events[1], "slope"] == pytest.approx(-0.01)


def test_trend_scanning_applies_t_threshold_and_censoring():
    index = pd.date_range("2026-01-01", periods=6)
    prices = pd.Series([100, 101, 99, 101, 100, 102], index=index, dtype=float)
    events = index[[0, 4]]

    result = q.label.trend_scanning(
        prices,
        events=events,
        horizons=[2, 3],
        min_t_value=100,
        drop_censored=False,
    )

    assert result["label"].tolist() == [0, pd.NA]
    assert pd.isna(result.loc[events[1], "end_time"])


def test_trend_scanning_preserves_period_index_metadata():
    index = pd.period_range("2026-01", periods=6, freq="M", name="period")
    prices = pd.Series([100, 101, 102, 103, 104, 105], index=index, dtype=float)

    result = q.label.trend_scanning(
        prices,
        events=index[[0, 3, 5]],
        horizons=[2],
        drop_censored=False,
    )

    assert isinstance(result.index, pd.PeriodIndex)
    assert result.index.freq == index.freq
    assert result.index.name == "event_time"


def test_trend_scanning_requires_positive_prices_even_without_logs():
    prices = pd.Series(
        [0, 1, 2],
        index=pd.RangeIndex(3),
        dtype=float,
    )

    with pytest.raises(ValueError, match="only positive"):
        q.label.trend_scanning(prices, horizons=[2], log_prices=False)


@pytest.mark.parametrize("horizons", [[], [1, 2], [3, 2], [2, 2]])
def test_trend_scanning_rejects_invalid_horizons(horizons):
    prices = pd.Series(
        [100, 101, 102, 103],
        index=pd.date_range("2026-01-01", periods=4),
        dtype=float,
    )

    with pytest.raises(ValueError, match="horizons|trend horizon"):
        q.label.trend_scanning(prices, horizons=horizons)