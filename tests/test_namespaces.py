import importlib
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

import qrt as q


TRANSFORM_NAMESPACES = [
    "encode",
    "impute",
    "outlier",
    "reduction",
    "scale",
    "selection",
]


def test_transform_namespaces_are_lightweight_packages():
    expected_exports = {
        "encode": [],
        "impute": [
            "IterativeImputer",
            "KNNImputer",
            "MissingIndicator",
            "SimpleImputer",
        ],
        "outlier": [],
        "reduction": [],
        "scale": ["StandardScaler"],
        "selection": [],
    }

    for name in TRANSFORM_NAMESPACES:
        namespace = getattr(q.transform, name)
        assert namespace.__all__ == expected_exports[name]


def test_imputation_transformers_are_available_from_q_transform():
    assert q.transform.impute.SimpleImputer(strategy="median").strategy == "median"
    assert isinstance(q.transform.impute.KNNImputer(), q.transform.impute.KNNImputer)
    assert isinstance(
        q.transform.impute.IterativeImputer(),
        q.transform.impute.IterativeImputer,
    )
    assert isinstance(
        q.transform.impute.MissingIndicator(),
        q.transform.impute.MissingIndicator,
    )


def test_preprocess_namespace_is_removed():
    assert not hasattr(q, "preprocess")
    with pytest.raises(ModuleNotFoundError, match=r"qrt\.preprocess"):
        importlib.import_module("qrt.preprocess")


def test_indicator_providers_are_lazy_on_root_import():
    code = """
import sys
import qrt
assert 'talib' not in sys.modules
assert 'pandas_ta_classic' not in sys.modules
assert 'qrt.indicator.talib' not in sys.modules
assert 'qrt.indicator.pandas_ta' not in sys.modules
"""

    subprocess.run([sys.executable, "-c", code], check=True)


def test_ray_namespace_is_lazy_and_delegates_to_ray():
    code = """
import sys
import qrt as q
assert 'ray' not in sys.modules
assert q.ray.__all__ == ['data', 'rllib', 'serve', 'train', 'tune']
assert q.ray.__version__
assert 'ray' in sys.modules
"""

    subprocess.run([sys.executable, "-c", code], check=True)


def test_indicator_and_cross_section_boundaries():
    series = pd.Series([1.0, 2.0, 3.0, 4.0], name="close")

    assert q.indicator.sma(series, 2).iloc[-1] == 3.5
    assert q.cross_section.__all__ == [
        "compute_elo",
        "group_weighted_return",
        "neutralize",
        "percentile_rank",
        "rank",
        "relative_strength",
        "zscore",
    ]
    assert q.signal.__all__ == []

def test_feature_namespace_is_removed():
    assert not hasattr(q, "feature")
    with pytest.raises(ModuleNotFoundError, match=r"qrt\.feature"):
        importlib.import_module("qrt.feature")


def test_non_trading_days_after_requires_an_exchange_session():
    index = pd.Index(["friday", "monday"])
    dates = pd.Series(pd.to_datetime(["2026-07-17", "2026-07-20"]), index=index)

    result = q.calendar.non_trading_days_after(dates, exchange="XNYS")

    assert result.index.equals(index)
    assert result.name == "non_trading_days_after"
    assert result.tolist() == [2, 0]


def test_non_trading_days_after_treats_early_close_as_a_session():
    dates = pd.Series(pd.to_datetime(["2026-11-27"]))

    result = q.calendar.non_trading_days_after(dates, exchange="XNYS")

    assert result.tolist() == [2]


def test_non_trading_days_after_rejects_unknown_exchange_and_non_session():
    dates = pd.Series(pd.to_datetime(["2026-07-18"]))

    try:
        q.calendar.non_trading_days_after(dates, exchange="NOPE")
    except ValueError as exc:
        assert "unknown exchange calendar" in str(exc)
    else:
        raise AssertionError("unknown exchange should raise ValueError")

    try:
        q.calendar.non_trading_days_after(dates, exchange="XNYS")
    except ValueError as exc:
        assert "must be sessions" in str(exc)
    else:
        raise AssertionError("non-session date should raise ValueError")


def test_ema_matches_legacy_adjust_false_formula():
    series = pd.Series([1.0, 2.0, 3.0, 4.0])

    result = q.indicator.ema(series, 3)

    pd.testing.assert_series_equal(
        result, series.ewm(span=3, adjust=False).mean()
    )


def test_realized_volatility_estimators_match_formulas():
    returns = np.array([0.01, -0.02, 0.03])

    assert q.indicator.realized_variance(returns) == pytest.approx(
        np.sum(returns**2)
    )
    assert q.indicator.realized_quarticity(returns) == pytest.approx(
        np.sum(returns**4)
    )
    assert np.isfinite(q.indicator.bipower_variation(returns))
    assert np.isfinite(q.indicator.med_rv(returns))
    assert np.isfinite(q.indicator.min_rv(returns))


def test_realized_volatility_groups_without_mutating_input():
    data = pd.DataFrame(
        {
            "time": pd.to_datetime(
                [
                    "2026-01-02 09:03",
                    "2026-01-02 09:01",
                    "2026-01-02 09:02",
                    "2026-01-02 09:04",
                ]
            ),
            "price": [102.0, 100.0, 101.0, 103.0],
            "session": pd.to_datetime(["2026-01-02"] * 4),
        }
    )
    original = data.copy(deep=True)

    result = q.indicator.realized_volatility(data)

    pd.testing.assert_frame_equal(data, original)
    assert result.index.name == "session"
    assert list(result.columns) == [
        "realized_variance",
        "realized_quarticity",
        "bipower_variation",
        "med_rv",
        "min_rv",
    ]
    expected_returns = np.diff(np.log([100.0, 101.0, 102.0, 103.0]))
    assert result.iloc[0]["realized_variance"] == pytest.approx(
        np.sum(expected_returns**2)
    )


def test_realized_volatility_rejects_invalid_samples():
    with pytest.raises(ValueError, match="strictly positive"):
        q.indicator.log_returns([100.0, 0.0])
    with pytest.raises(ValueError, match="at least 3 returns"):
        q.indicator.med_rv([0.01, 0.02])


def test_realized_volatility_rejects_multiple_symbols():
    data = pd.DataFrame(
        {
            "time": pd.date_range("2026-01-02 09:01", periods=4, freq="min"),
            "price": [100.0, 101.0, 102.0, 103.0],
            "session": pd.to_datetime(["2026-01-02"] * 4),
            "symbol": ["AAPL", "AAPL", "MSFT", "MSFT"],
        }
    )

    with pytest.raises(ValueError, match="one symbol"):
        q.indicator.realized_volatility(data)


def test_relative_strength_aligns_benchmark_to_asset_index():
    index = pd.date_range("2026-01-01", periods=3)
    prices = pd.Series([100.0, 110.0, 121.0], index=index)
    benchmark = pd.Series([100.0, 105.0, 110.25], index=index)

    result = q.indicator.relative_strength(prices, benchmark, lookback=1)

    assert result.index.equals(index)
    assert result.iloc[1:].tolist() == pytest.approx([0.05, 0.05])


def test_relative_strength_family_uses_explicit_series():
    index = pd.date_range("2026-01-01", periods=4)
    strength = pd.Series([0.0, 0.1, 0.2, 0.15], index=index)

    average = q.indicator.rsma(strength, window=2, method="simple")
    phase = q.indicator.rs_phase(strength, average)
    signal = q.indicator.rsnhbp(
        pd.Series([10.0, 11.0, 10.5, 10.8], index=index),
        pd.Series([1.0, 1.1, 1.2, 1.3], index=index),
        window=3,
    )

    assert list(phase.columns) == ["rs_phase", "rs_phase_days"]
    assert phase["rs_phase"].dtype == bool
    assert signal.tolist() == [False, False, True, True]


def test_rs_days_counts_positive_strength_during_correction():
    index = pd.date_range("2026-01-01", periods=4)
    strength = pd.Series([1.0, 1.0, 1.0, -1.0], index=index)
    benchmark = pd.Series([100.0, 90.0, 89.0, 88.0], index=index)

    result = q.indicator.rs_days(
        strength, benchmark, window=2, correction_threshold=0.95
    )

    assert result.tolist() == pytest.approx([np.nan, 1.0, 1.0, 0.0], nan_ok=True)