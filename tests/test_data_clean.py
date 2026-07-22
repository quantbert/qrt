import pandas as pd
import pytest

import qrt as q


def _raw_ohlcv() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Ticker": ["A", "A", "A"],
            "Date": ["2026-01-03", "2026-01-01", "2026-01-01"],
            "Open": [12, 10, 10],
            "High": [13, 12, 12],
            "Low": [11, 9, 9],
            "Close": [12, 11, 11.5],
            "Volume": [120, 100, 110],
        }
    )


def test_canonicalize_ohlcv_normalizes_deduplicates_sorts_and_validates():
    raw = _raw_ohlcv()
    original = raw.copy(deep=True)

    result = q.data.clean.canonicalize_ohlcv(raw)

    pd.testing.assert_frame_equal(raw, original)
    assert result.columns.tolist() == [
        "symbol", "datetime", "open", "high", "low", "close", "volume"
    ]
    assert str(result["datetime"].dtype) == "datetime64[us, UTC]"
    assert result["datetime"].is_monotonic_increasing
    assert result["close"].tolist() == [11.5, 12.0]


def test_normalize_timestamps_supports_named_datetime_index():
    data = pd.DataFrame(
        {"close": [1.0]},
        index=pd.Index(["2026-01-01"], name="datetime"),
    )

    result = q.data.clean.normalize_timestamps(data)

    assert isinstance(result.index, pd.DatetimeIndex)
    assert str(result.index.dtype) == "datetime64[us, UTC]"


def test_deduplicate_can_drop_every_duplicate():
    data = pd.DataFrame(
        {
            "symbol": ["A", "A", "B"],
            "datetime": pd.to_datetime(["2026-01-01"] * 3),
        }
    )

    result = q.data.clean.deduplicate(data, keep=False)

    assert result["symbol"].tolist() == ["B"]


def test_detect_gaps_reports_missing_regular_periods_per_entity():
    data = pd.DataFrame(
        {
            "symbol": ["A", "A", "B", "B"],
            "datetime": pd.to_datetime(
                ["2026-01-01", "2026-01-04", "2026-01-01", "2026-01-02"]
            ),
        }
    )

    result = q.data.clean.detect_gaps(data, "1D")

    assert result.to_dict("records") == [
        {
            "symbol": "A",
            "gap_start": pd.Timestamp("2026-01-02"),
            "gap_end": pd.Timestamp("2026-01-03"),
            "missing_count": 2,
        }
    ]


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("high", 8.0, "high must be"),
        ("low", 14.0, "low must be"),
        ("volume", -1.0, "volume must be non-negative"),
    ],
)
def test_validate_ohlcv_rejects_market_invariant_violations(column, value, message):
    data = q.data.clean.canonicalize_ohlcv(_raw_ohlcv())
    data.loc[data.index[0], column] = value

    with pytest.raises(ValueError, match=message):
        q.data.clean.validate_ohlcv(data)


def test_validate_ohlcv_checks_available_prices_when_other_values_are_missing():
    data = q.data.clean.canonicalize_ohlcv(_raw_ohlcv())
    data.loc[data.index[0], ["high", "volume"]] = [8.0, float("nan")]

    with pytest.raises(ValueError, match="high must be"):
        q.data.clean.validate_ohlcv(data, allow_missing=True)