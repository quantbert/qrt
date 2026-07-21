import numpy as np
import pandas as pd
import pytest

import qrt as q


@pytest.fixture
def barrier_prices() -> pd.Series:
    index = pd.date_range("2026-01-01", periods=9, name="datetime")
    return pd.Series(
        [100, 103, 104, 100, 97, 96, 100, 101, 101],
        index=index,
        dtype=float,
        name="close",
    )


def test_vertical_barriers_support_bars_and_wall_clock_time(barrier_prices):
    index = barrier_prices.index
    events = index[[0, 3, 7]]

    by_bars = q.label.vertical_barriers(index, 2, events=events)
    by_time = q.label.vertical_barriers(index, "2D", events=events)

    expected = pd.Series(
        [index[2], index[5], pd.NaT],
        index=events.rename("event_time"),
        name="vertical_barrier",
    )
    pd.testing.assert_series_equal(by_bars, expected)
    pd.testing.assert_series_equal(by_time, expected)


def test_vertical_barriers_preserve_timezone(barrier_prices):
    index = barrier_prices.index.tz_localize("UTC")
    events = index[[0, 7]]

    result = q.label.vertical_barriers(index, "2D", events=events)

    assert isinstance(result.dtype, pd.DatetimeTZDtype)
    assert result.dtype.tz == index.tz
    assert result.tolist() == [index[2], pd.NaT]


def test_fixed_horizon_returns_directional_and_neutral_labels(barrier_prices):
    events = barrier_prices.index[[0, 3, 6, 7]]

    result = q.label.fixed_horizon(
        barrier_prices,
        2,
        events=events,
        threshold=0.015,
        drop_censored=False,
    )

    assert result["label"].tolist() == [1, -1, 0, pd.NA]
    assert result.loc[events[0], "return"] == pytest.approx(0.04)
    assert result.loc[events[1], "return"] == pytest.approx(-0.04)
    assert pd.isna(result.loc[events[3], "end_time"])


def test_fixed_horizon_excludes_missing_dynamic_thresholds(barrier_prices):
    events = barrier_prices.index[[0, 3]]
    thresholds = pd.Series([np.nan, 0.015], index=events)

    result = q.label.fixed_horizon(
        barrier_prices,
        2,
        events=events,
        threshold=thresholds,
    )

    pd.testing.assert_index_equal(result.index, events[[1]].rename("event_time"))
    assert result["label"].tolist() == [-1]


def test_triple_barrier_reports_upper_lower_and_vertical_touches(barrier_prices):
    events = barrier_prices.index[[0, 3, 6]]
    original = barrier_prices.copy(deep=True)

    result = q.label.triple_barrier(
        barrier_prices,
        0.02,
        events=events,
        horizon=2,
    )

    assert result["barrier"].tolist() == ["upper", "lower", "vertical"]
    assert result["touch_time"].tolist() == [
        barrier_prices.index[1],
        barrier_prices.index[4],
        barrier_prices.index[8],
    ]
    assert result["label"].tolist() == [1, -1, 1]
    assert result["return"].to_numpy() == pytest.approx([0.03, -0.03, 0.01])
    pd.testing.assert_series_equal(barrier_prices, original)


def test_triple_barrier_uses_side_for_binary_meta_labels(barrier_prices):
    events = barrier_prices.index[[0, 3]]
    sides = pd.Series([-1, -1], index=events)

    result = q.label.triple_barrier(
        barrier_prices,
        0.02,
        events=events,
        horizon=2,
        side=sides,
    )

    assert result["barrier"].tolist() == ["lower", "upper"]
    assert result["label"].tolist() == [0, 1]
    assert result["adjusted_return"].to_numpy() == pytest.approx([-0.03, 0.03])


def test_triple_barrier_filters_small_targets_and_censored_events(barrier_prices):
    events = barrier_prices.index[[0, 3, 7]]
    targets = pd.Series([0.02, 0.001, 0.02], index=events)

    dropped = q.label.triple_barrier(
        barrier_prices,
        targets,
        events=events,
        horizon=2,
        min_target=0.005,
    )
    retained = q.label.triple_barrier(
        barrier_prices,
        targets,
        events=events,
        horizon=2,
        min_target=0.005,
        drop_censored=False,
    )

    pd.testing.assert_index_equal(dropped.index, events[[0]].rename("event_time"))
    assert retained.index.tolist() == events[[0, 2]].tolist()
    assert retained["barrier"].tolist() == ["upper", "censored"]
    assert retained["label"].tolist() == [1, pd.NA]


def test_triple_barrier_accepts_explicit_vertical_barriers(barrier_prices):
    events = barrier_prices.index[[0, 3]]
    vertical = pd.Series(barrier_prices.index[[2, 5]], index=events)

    result = q.label.triple_barrier(
        barrier_prices,
        0.20,
        events=events,
        vertical=vertical,
    )

    assert result["barrier"].tolist() == ["vertical", "vertical"]
    assert result["touch_time"].tolist() == vertical.tolist()


def test_triple_barrier_can_disable_both_horizontal_barriers(barrier_prices):
    events = barrier_prices.index[[0, 3]]

    result = q.label.triple_barrier(
        barrier_prices,
        0.02,
        events=events,
        horizon=2,
        upper=None,
        lower=None,
    )

    assert result["barrier"].tolist() == ["vertical", "vertical"]
    assert result["touch_time"].tolist() == barrier_prices.index[[2, 5]].tolist()


def test_meta_label_preserves_missing_values_and_rejects_bad_sides():
    index = pd.date_range("2026-01-01", periods=4)
    returns = pd.Series([0.03, -0.02, 0.10, np.nan], index=index)
    sides = pd.Series([1, -1, 0, 1], index=index)

    result = q.label.meta_label(returns, sides, threshold=0.01)

    expected = pd.Series([1, 1, 0, pd.NA], index=index, dtype="Int8", name="meta_label")
    pd.testing.assert_series_equal(result, expected)
    with pytest.raises(ValueError, match="only -1, 0, or 1"):
        q.label.meta_label(returns, pd.Series([1, 2, 0, 1], index=index))


def test_barrier_labeling_rejects_ambiguous_or_invalid_inputs(barrier_prices):
    events = barrier_prices.index[[0, 3]]

    with pytest.raises(ValueError, match="exactly one"):
        q.label.triple_barrier(barrier_prices, 0.02, events=events)
    with pytest.raises(ValueError, match="exactly one"):
        q.label.triple_barrier(
            barrier_prices,
            0.02,
            events=events,
            horizon=2,
            vertical=pd.Series(barrier_prices.index[[2, 5]], index=events),
        )
    with pytest.raises(ValueError, match="every event"):
        q.label.fixed_horizon(
            barrier_prices,
            2,
            events=pd.DatetimeIndex([pd.Timestamp("2030-01-01")]),
        )
    with pytest.raises(ValueError, match="side must contain only"):
        q.label.triple_barrier(
            barrier_prices,
            0.02,
            events=events,
            horizon=2,
            side=0,
        )
    with pytest.raises(TypeError, match="side must be a number"):
        q.label.triple_barrier(
            barrier_prices,
            0.02,
            events=events,
            horizon=2,
            side=True,
        )