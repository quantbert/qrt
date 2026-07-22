import pandas as pd
import pytest

import qrt as q


@pytest.fixture
def market_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "close": [10.0, 11.0, 12.0, 10.0, 13.0, 15.0],
            "volume": [100.0, 120.0, 80.0, 140.0, 160.0, 180.0],
        },
        index=pd.date_range("2026-01-01", periods=6),
    )


def test_return_and_momentum_match_pandas(market_data):
    pd.testing.assert_series_equal(
        q.indicator.returns(market_data["close"], periods=2),
        market_data["close"].pct_change(2, fill_method=None).rename("returns"),
    )
    pd.testing.assert_series_equal(
        q.indicator.momentum(market_data["close"], window=3),
        market_data["close"].pct_change(3, fill_method=None).rename("momentum"),
    )


def test_rolling_volatility_exposes_window_min_periods_and_ddof(market_data):
    returns = market_data["close"].pct_change(fill_method=None)

    result = q.indicator.rolling_volatility(
        returns, window=3, min_periods=2, ddof=0
    )

    expected = returns.rolling(3, min_periods=2).std(ddof=0).rename(
        "rolling_volatility"
    )
    pd.testing.assert_series_equal(result, expected)


@pytest.mark.parametrize("statistic", ["mean", "median"])
def test_volume_ratio_supports_rolling_baselines(market_data, statistic):
    volume = market_data["volume"]

    result = q.indicator.volume_ratio(volume, window=3, statistic=statistic)

    rolling = volume.rolling(3)
    baseline = getattr(rolling, statistic)()
    expected = (volume / baseline).rename("volume_ratio")
    pd.testing.assert_series_equal(result, expected)


def test_feature_indicators_reject_invalid_inputs(market_data):
    with pytest.raises(ValueError, match="positive integer"):
        q.indicator.returns(market_data["close"], periods=0)
    with pytest.raises(ValueError, match="must not exceed"):
        q.indicator.rolling_volatility(
            market_data["close"], window=2, min_periods=3
        )
    with pytest.raises(ValueError, match="mean.*median"):
        q.indicator.volume_ratio(
            market_data["volume"], statistic="maximum"  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="negative"):
        q.indicator.volume_ratio(-market_data["volume"])