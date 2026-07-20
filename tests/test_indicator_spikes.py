import numpy as np
import pandas as pd
import pytest

import qrt as q


@pytest.fixture
def market_data() -> pd.DataFrame:
    close = pd.Series(
        [10, 11, 12, 13, 14, 15, 13, 12, 11, 13],
        index=pd.date_range("2026-01-01", periods=10),
        dtype=float,
    )
    return pd.DataFrame(
        {
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": [100, 100, 100, 160, 100, 300, 100, 100, 170, 300],
        },
        index=close.index,
    )


def test_madev_matches_reviewed_two_stage_formula():
    prices = pd.Series(
        [10, 11, 13, 12, 15, 14, 16, 18, 17, 20, 19, 21],
        index=pd.date_range("2026-01-01", periods=12),
        dtype=float,
    )
    original = prices.copy(deep=True)
    window = 4

    result = q.indicator.madev(prices, window)

    average = prices.rolling(window, min_periods=window).mean()
    expected = (
        (prices - average)
        .abs()
        .rolling(window, min_periods=window)
        .mean()
        .rename("madev")
    )
    pd.testing.assert_series_equal(result, expected)
    pd.testing.assert_series_equal(prices, original)
    assert result.first_valid_index() == prices.index[2 * window - 2]


def test_volume_spike_ratio_matches_reviewed_classification(market_data):
    close = market_data["close"]
    volume = market_data["volume"]
    original = market_data.copy(deep=True)

    result = q.indicator.volume_spike_ratio(
        close,
        volume,
        vol_window=3,
        price_window=3,
        consecutive_days=2,
    )

    rolling_volume = volume.rolling(3).mean()
    ratio = volume.div(rolling_volume).replace([np.inf, -np.inf], 0).fillna(0)
    average = close.rolling(3).mean()
    slope = average.pct_change(fill_method=None) * 100
    uptrend = (slope > 0.1).rolling(2).sum().eq(2) & close.gt(average)
    downtrend = (slope < -0.1).rolling(2).sum().eq(2) & close.lt(average)
    continuation = ratio.gt(1.5) & ratio.lt(2.5)
    reversal = ratio.ge(2.5)
    expected = pd.DataFrame(
        {
            "vsr": ratio,
            "vsr_spike_type": np.select(
                [
                    continuation & uptrend & close.diff().gt(0),
                    continuation & downtrend & close.diff().lt(0),
                    reversal & uptrend & close.diff().lt(0),
                    reversal & downtrend & close.diff().gt(0),
                ],
                [1, 1, 2, 2],
                default=0,
            ),
            "vsr_trending": np.select([uptrend, downtrend], [1, 2], default=0),
        },
        index=close.index,
    )
    pd.testing.assert_frame_equal(result, expected)
    pd.testing.assert_frame_equal(market_data, original)


def test_price_spikes_matches_reviewed_atr_classification(market_data):
    original = market_data.copy(deep=True)
    high = market_data["high"]
    low = market_data["low"]
    close = market_data["close"]
    volume = market_data["volume"]

    result = q.indicator.price_spikes(
        high,
        low,
        close,
        volume,
        atr_window=3,
        volume_window=3,
        atr_multiplier=0.8,
        volume_threshold=1.2,
    )

    previous_close = close.shift(1)
    true_range = pd.concat(
        [high - low, (high - previous_close).abs(), (low - previous_close).abs()],
        axis=1,
    ).max(axis=1)
    average_true_range = true_range.rolling(3, min_periods=3).mean()
    spike = close.diff().abs().gt(0.8 * average_true_range)
    relative_volume = volume / volume.rolling(3).mean().replace(0, np.nan)
    high_volume = relative_volume.gt(1.2)
    expected = pd.DataFrame(
        {
            "price_spike_event": np.select(
                [spike & high_volume, spike & ~high_volume],
                [1, 2],
                default=0,
            ),
            "relative_volume": relative_volume,
        },
        index=high.index,
    )
    pd.testing.assert_frame_equal(result, expected)
    pd.testing.assert_frame_equal(market_data, original)
    assert set(result["price_spike_event"]) == {0, 1, 2}


def test_spike_indicators_require_aligned_series(market_data):
    shifted_volume = market_data["volume"].set_axis(
        market_data.index + pd.Timedelta(days=1)
    )

    with pytest.raises(ValueError, match="index must match"):
        q.indicator.volume_spike_ratio(market_data["close"], shifted_volume)
    with pytest.raises(ValueError, match="index must match"):
        q.indicator.price_spikes(
            market_data["high"],
            market_data["low"],
            market_data["close"],
            shifted_volume,
        )


def test_reviewed_indicators_reject_invalid_parameters(market_data):
    with pytest.raises(ValueError, match="positive integer"):
        q.indicator.madev(market_data["close"], 0)
    with pytest.raises(ValueError, match="greater than spike_threshold"):
        q.indicator.volume_spike_ratio(
            market_data["close"],
            market_data["volume"],
            spike_threshold=2.5,
            reversal_threshold=1.5,
        )
    with pytest.raises(ValueError, match="greater than or equal to low"):
        q.indicator.price_spikes(
            market_data["low"],
            market_data["high"],
            market_data["close"],
            market_data["volume"],
        )
