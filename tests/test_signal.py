import numpy as np
import pandas as pd
import pytest

import qrt as q


def _series(values, name="score"):
    return pd.Series(
        values,
        index=pd.date_range("2026-01-01", periods=len(values)),
        name=name,
    )


def _panel(values, columns=("A", "B", "C")):
    return pd.DataFrame(
        values,
        index=pd.date_range("2026-01-01", periods=len(values)),
        columns=columns,
    )


def test_as_signal_preserves_labels_converts_to_float_and_copies():
    values = _panel([[1, 2, np.nan], [3, 4, 5]])

    result = q.signal.as_signal(values)

    pd.testing.assert_frame_equal(result, values.astype(float))
    assert result is not values
    result.iloc[0, 0] = 99.0
    assert values.iloc[0, 0] == 1


@pytest.mark.parametrize(
    ("values", "error", "message"),
    [
        ([1.0, 2.0], TypeError, "pandas Series or DataFrame"),
        (pd.Series(dtype=float), ValueError, "must not be empty"),
        (pd.Series([1.0, 2.0], index=[1, 1]), ValueError, "duplicates"),
        (pd.Series([1.0, 2.0], index=[2, 1]), ValueError, "sorted"),
        (pd.Series(["up", "down"]), TypeError, "numeric"),
        (pd.Series([True, False]), TypeError, "numeric"),
        (pd.Series([1.0, np.inf]), ValueError, "finite"),
    ],
)
def test_as_signal_rejects_invalid_contract(values, error, message):
    with pytest.raises(error, match=message):
        q.signal.as_signal(values)


def test_threshold_maps_scores_and_preserves_missing_values():
    values = _series([0.2, 0.4, 0.5, 0.6, 0.8, np.nan])

    result = q.signal.threshold(values, long_above=0.6, short_below=0.4)

    expected = _series([-1.0, -1.0, 0.0, 1.0, 1.0, np.nan])
    pd.testing.assert_series_equal(result, expected)


def test_threshold_supports_long_only_and_rejects_overlapping_levels():
    result = q.signal.threshold(_series([-1.0, 0.0, 1.0]), long_above=0.5)
    pd.testing.assert_series_equal(result, _series([0.0, 0.0, 1.0]))

    with pytest.raises(ValueError, match="less than"):
        q.signal.threshold(_series([0.0]), long_above=0.5, short_below=0.5)


def test_hysteresis_uses_separate_entry_and_exit_levels():
    values = _series([0.5, 0.7, 0.55, 0.4, 0.3, 0.65, np.nan, 0.45])

    result = q.signal.hysteresis(
        values,
        long_enter=0.6,
        long_exit=0.5,
        short_enter=0.4,
        short_exit=0.5,
    )

    expected = _series([0.0, 1.0, 1.0, -1.0, -1.0, 1.0, np.nan, 0.0])
    pd.testing.assert_series_equal(result, expected)


def test_hysteresis_validates_level_order_and_enabled_initial_state():
    with pytest.raises(ValueError, match="provided together"):
        q.signal.hysteresis(
            _series([0.0]),
            long_enter=1.0,
            long_exit=0.5,
            short_enter=-1.0,
        )
    with pytest.raises(ValueError, match="enabled directional state"):
        q.signal.hysteresis(
            _series([0.0]),
            long_enter=1.0,
            long_exit=0.5,
            initial=-1,
        )


def test_normalize_percentile_maps_each_cross_section_to_centered_ranks():
    values = _panel([[1.0, 2.0, 3.0], [np.nan, 5.0, np.nan]])

    result = q.signal.normalize(values, method="percentile")

    expected = _panel([[-1.0, 0.0, 1.0], [np.nan, 0.0, np.nan]])
    pd.testing.assert_frame_equal(result, expected)


def test_normalize_zscore_delegates_cross_sectional_measurement():
    values = _panel([[1.0, 2.0, 3.0], [3.0, 3.0, 3.0]])

    result = q.signal.normalize(values, method="zscore")

    pd.testing.assert_frame_equal(result, q.cross_section.zscore(values))
    with pytest.raises(TypeError, match="time-by-asset"):
        q.signal.normalize(values["A"])


def test_select_chooses_exact_counts_and_resolves_ties_by_column_order():
    values = _panel([[2.0, 2.0, 1.0, 0.0]], columns=("A", "B", "C", "D"))

    result = q.signal.select(values, long_count=1, short_count=1)

    expected = _panel(
        [[0.0, 1.0, 0.0, -1.0]],
        columns=("A", "B", "C", "D"),
    )
    pd.testing.assert_frame_equal(result, expected)


def test_select_rejects_cross_sections_with_too_few_available_assets():
    values = _panel([[1.0, np.nan, 2.0]])

    with pytest.raises(ValueError, match="2 valid assets; 3 required"):
        q.signal.select(values, long_count=2, short_count=1)


def test_neutralize_removes_static_exposures_from_every_timestamp():
    exposures = pd.Series([1.0, 2.0, 3.0, 4.0], index=["A", "B", "C", "D"])
    values = _panel(
        [[3.0, 5.0, 7.0, 9.0], [0.0, 1.0, 0.0, 1.0]],
        columns=("A", "B", "C", "D"),
    )

    result = q.signal.neutralize(values, exposures)

    assert np.allclose(result.iloc[0], 0.0, atol=1e-12)
    pd.testing.assert_index_equal(result.index, values.index)
    pd.testing.assert_index_equal(result.columns, values.columns)


def test_neutralize_requires_exposures_aligned_to_asset_columns():
    values = _panel([[1.0, 2.0, 3.0]])
    exposures = pd.Series([1.0, 2.0, 3.0], index=["B", "A", "C"])

    with pytest.raises(ValueError, match="exactly match"):
        q.signal.neutralize(values, exposures)


def test_combine_uses_weighted_available_mean_without_implicit_alignment():
    first = _series([1.0, np.nan, -1.0])
    second = _series([0.0, 0.5, np.nan])

    result = q.signal.combine([first, second], weights=[3.0, 1.0])

    expected = _series([0.75, 0.5, -1.0])
    pd.testing.assert_series_equal(result, expected)

    with pytest.raises(ValueError, match="matching indexes"):
        q.signal.combine([first, second.rename(index={second.index[0]: pd.Timestamp("2025-01-01")})])


def test_delay_makes_next_row_availability_the_default():
    values = _series([1.0, 0.0, -1.0])

    result = q.signal.delay(values)

    pd.testing.assert_series_equal(result, _series([np.nan, 1.0, 0.0]))
    pd.testing.assert_series_equal(q.signal.delay(values, periods=0), values)
    pd.testing.assert_series_equal(q.signal.delay(values, periods=np.int64(1)), result)


def test_decay_matches_causal_pandas_exponential_smoothing():
    values = _series([1.0, 0.0, 0.0, 1.0])

    result = q.signal.decay(values, half_life=2.0)

    expected = values.ewm(halflife=2.0, adjust=False, min_periods=1).mean()
    pd.testing.assert_series_equal(result, expected)


def test_hold_enforces_minimum_observations_between_state_changes():
    values = _series([1.0, 0.0, -1.0, -1.0, 0.0, np.nan])

    result = q.signal.hold(values, periods=2)

    expected = _series([1.0, 1.0, -1.0, -1.0, 0.0, np.nan])
    pd.testing.assert_series_equal(result, expected)


def test_hold_rejects_continuous_values():
    with pytest.raises(ValueError, match="only -1, 0, 1"):
        q.signal.hold(_series([0.2, 0.4]), periods=2)


def test_cooldown_exits_immediately_and_blocks_reentry():
    values = _series([1.0, 1.0, 0.0, 1.0, 1.0, -1.0, -1.0])

    result = q.signal.cooldown(values, periods=2)

    expected = _series([1.0, 1.0, 0.0, 0.0, 0.0, -1.0, -1.0])
    pd.testing.assert_series_equal(result, expected)


def test_cooldown_treats_sign_reversal_as_exit():
    values = _series([1.0, -1.0, -1.0])

    result = q.signal.cooldown(values, periods=0)

    pd.testing.assert_series_equal(result, _series([1.0, 0.0, -1.0]))


def test_limit_turnover_clips_each_change_and_preserves_missing_rows():
    values = _series([1.0, 1.0, -1.0, np.nan, 0.0])

    result = q.signal.limit_turnover(values, max_change=0.4)

    expected = _series([0.4, 0.8, 0.4, np.nan, 0.0])
    pd.testing.assert_series_equal(result, expected)


def test_target_exposure_maps_conviction_without_portfolio_normalization():
    values = _panel([[-2.0, -0.5, 2.0]])

    result = q.signal.target_exposure(values, maximum=0.25)

    expected = _panel([[-0.25, -0.125, 0.25]])
    pd.testing.assert_frame_equal(result, expected)
    with pytest.raises(ValueError, match=r"within \[-1, 1\]"):
        q.signal.target_exposure(values, clip=False)