"""Volume and price spike classifiers."""

import numpy as np
import pandas as pd


def _numeric_series(
    series: pd.Series,
    name: str,
    index: pd.Index | None = None,
) -> pd.Series:
    if not isinstance(series, pd.Series):
        raise TypeError(f"{name} must be a pandas Series")
    if not pd.api.types.is_numeric_dtype(series):
        raise TypeError(f"{name} must contain numeric values")
    if series.index.has_duplicates:
        raise ValueError(f"{name} index must not contain duplicates")
    if index is not None and not series.index.equals(index):
        raise ValueError(f"{name} index must match prices index")
    values = series.astype(float)
    if np.isinf(values.dropna().to_numpy()).any():
        raise ValueError(f"{name} must not contain infinite values")
    return values


def _positive_window(value: int, name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _positive_number(value: float, name: str) -> None:
    if not np.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be positive and finite")


def volume_spike_ratio(
    prices: pd.Series,
    volume: pd.Series,
    *,
    vol_window: int = 20,
    price_window: int = 20,
    spike_threshold: float = 1.5,
    reversal_threshold: float = 2.5,
    trend_slope_threshold: float = 0.1,
    consecutive_days: int = 3,
) -> pd.DataFrame:
    """Classify volume spikes as trend continuations or reversals.

    A continuation is moderate relative volume in the established trend
    direction. A reversal is extreme relative volume with price moving against
    the established trend.

    Event codes in ``vsr_spike_type`` are 0 for no spike, 1 for continuation,
    and 2 for reversal. Trend codes in ``vsr_trending`` are 0 for no trend, 1
    for uptrend, and 2 for downtrend.

    Args:
        prices: Close prices for one instrument.
        volume: Volume observations aligned exactly to ``prices``.
        vol_window: Window used for average volume.
        price_window: Window used for the price SMA.
        spike_threshold: Lower exclusive relative-volume continuation bound.
        reversal_threshold: Lower inclusive relative-volume reversal bound.
        trend_slope_threshold: Minimum absolute SMA percentage change.
        consecutive_days: Consecutive slope observations required for a trend.

    Returns:
        DataFrame containing ``vsr``, ``vsr_spike_type``, and ``vsr_trending``.
    """
    _positive_window(vol_window, "vol_window")
    _positive_window(price_window, "price_window")
    _positive_window(consecutive_days, "consecutive_days")
    _positive_number(spike_threshold, "spike_threshold")
    _positive_number(reversal_threshold, "reversal_threshold")
    if reversal_threshold <= spike_threshold:
        raise ValueError("reversal_threshold must be greater than spike_threshold")
    if not np.isfinite(trend_slope_threshold) or trend_slope_threshold < 0:
        raise ValueError("trend_slope_threshold must be non-negative and finite")

    close = _numeric_series(prices, "prices")
    volumes = _numeric_series(volume, "volume", close.index)
    if (volumes.dropna() < 0).any():
        raise ValueError("volume must not contain negative values")

    rolling_volume = volumes.rolling(window=vol_window).mean()
    ratio = volumes.div(rolling_volume).replace([np.inf, -np.inf], 0).fillna(0)
    average = close.rolling(window=price_window).mean()
    slope = average.pct_change(fill_method=None) * 100

    slope_up = slope > trend_slope_threshold
    slope_down = slope < -trend_slope_threshold
    consecutive_up = (
        slope_up.rolling(window=consecutive_days).sum().eq(consecutive_days)
    )
    consecutive_down = (
        slope_down.rolling(window=consecutive_days).sum().eq(consecutive_days)
    )
    uptrend = consecutive_up & close.gt(average)
    downtrend = consecutive_down & close.lt(average)

    continuation_volume = ratio.gt(spike_threshold) & ratio.lt(reversal_threshold)
    reversal_volume = ratio.ge(reversal_threshold)
    price_up = close.diff().gt(0)
    price_down = close.diff().lt(0)
    spike_type = np.select(
        [
            continuation_volume & uptrend & price_up,
            continuation_volume & downtrend & price_down,
            reversal_volume & uptrend & price_down,
            reversal_volume & downtrend & price_up,
        ],
        [1, 1, 2, 2],
        default=0,
    )
    trending = np.select([uptrend, downtrend], [1, 2], default=0)

    return pd.DataFrame(
        {
            "vsr": ratio,
            "vsr_spike_type": spike_type,
            "vsr_trending": trending,
        },
        index=close.index,
    )


def price_spikes(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    *,
    atr_window: int = 20,
    volume_window: int = 20,
    atr_multiplier: float = 1.7,
    volume_threshold: float = 1.5,
) -> pd.DataFrame:
    """Classify close-to-close price spikes by volume confirmation.

    A price spike is an absolute close-to-close move greater than a multiple of
    simple rolling average true range. Event code 1 is a spike with high volume,
    event code 2 is a spike without high volume, and 0 means no spike.

    Args:
        high: High prices for one instrument.
        low: Low prices aligned exactly to ``high``.
        close: Close prices aligned exactly to ``high``.
        volume: Volume observations aligned exactly to ``high``.
        atr_window: Window for simple rolling average true range.
        volume_window: Window for average volume.
        atr_multiplier: ATR multiple required for a price spike.
        volume_threshold: Relative-volume boundary for confirmation.

    Returns:
        DataFrame containing ``price_spike_event`` and ``relative_volume``.
    """
    _positive_window(atr_window, "atr_window")
    _positive_window(volume_window, "volume_window")
    _positive_number(atr_multiplier, "atr_multiplier")
    _positive_number(volume_threshold, "volume_threshold")

    highs = _numeric_series(high, "high")
    lows = _numeric_series(low, "low", highs.index)
    closes = _numeric_series(close, "close", highs.index)
    volumes = _numeric_series(volume, "volume", highs.index)
    if (highs < lows).fillna(False).any():
        raise ValueError("high must be greater than or equal to low")
    if (volumes.dropna() < 0).any():
        raise ValueError("volume must not contain negative values")

    previous_close = closes.shift(1)
    true_range = pd.concat(
        [
            highs - lows,
            (highs - previous_close).abs(),
            (lows - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    average_true_range = true_range.rolling(
        window=atr_window, min_periods=atr_window
    ).mean()
    spike = closes.diff().abs().gt(atr_multiplier * average_true_range)

    rolling_volume = volumes.rolling(window=volume_window).mean()
    relative_volume = volumes.div(rolling_volume.replace(0, np.nan))
    high_volume = relative_volume.gt(volume_threshold)
    event = np.select(
        [spike & high_volume, spike & ~high_volume],
        [1, 2],
        default=0,
    )

    return pd.DataFrame(
        {
            "price_spike_event": event,
            "relative_volume": relative_volume,
        },
        index=highs.index,
    )
