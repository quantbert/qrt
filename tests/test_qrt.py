import pandas as pd

import qrt as q


def test_import():
    assert q.__version__


def test_sma():
    s = pd.Series([1.0, 2.0, 3.0, 4.0])
    out = q.feat.qta.sma(s, 2)
    assert out.iloc[-1] == 3.5


def test_lags_series():
    s = pd.Series([1.0, 2.0, 3.0, 4.0], name="close")
    out = q.feat.qta.lags(s, 2)
    assert list(out.columns) == ["close_lag1", "close_lag2"]
    assert out["close_lag1"].iloc[-1] == 3.0
    assert out["close_lag2"].iloc[-1] == 2.0


def test_lags_dataframe_explicit_periods():
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [10.0, 20.0, 30.0]})
    out = q.feat.qta.lags(df, [1, 2])
    assert list(out.columns) == ["a_lag1", "a_lag2", "b_lag1", "b_lag2"]
    assert out["b_lag2"].iloc[-1] == 10.0


def _ohlc(n: int = 60) -> pd.DataFrame:
    idx = pd.date_range("2025-01-01", periods=n, freq="D")
    close = pd.Series(range(1, n + 1), index=idx, dtype=float)
    return pd.DataFrame(
        {"open": close, "high": close + 1, "low": close - 1, "close": close, "volume": 100.0}
    )


def test_talib_single_output():
    ohlc = _ohlc()
    out = q.feat.talib.RSI(ohlc, timeperiod=14)
    assert out.name == "rsi"
    assert out.index.equals(ohlc.index)
    assert out.iloc[-1] == 100.0  # strictly rising close

    # a plain Series is treated as close
    from_series = q.feat.talib.RSI(ohlc["close"], timeperiod=14)
    assert from_series.equals(out)


def test_talib_multi_output():
    out = q.feat.talib.MACD(_ohlc())
    assert list(out.columns) == ["macd", "macdsignal", "macdhist"]


def test_talib_unknown_indicator():
    import pytest

    with pytest.raises(AttributeError):
        q.feat.talib.NOT_AN_INDICATOR


def test_pandas_ta_single_output():
    ohlc = _ohlc()
    out = q.feat.pandas_ta.rsi(ohlc, length=14)
    assert out.name == "RSI_14"
    assert out.index.equals(ohlc.index)

    # a plain Series is treated as close
    from_series = q.feat.pandas_ta.rsi(ohlc["close"], length=14)
    assert from_series.equals(out)


def test_pandas_ta_multi_output():
    out = q.feat.pandas_ta.macd(_ohlc())
    assert list(out.columns) == ["MACD_12_26_9", "MACDh_12_26_9", "MACDs_12_26_9"]


def test_pandas_ta_unknown_indicator():
    import pytest

    with pytest.raises(AttributeError):
        q.feat.pandas_ta.not_an_indicator


def test_load_ohlc_timeseries_range(tmp_path):
    from datetime import datetime

    for day, prices in [("2025-01-01", [100, 105, 95, 102]), ("2025-01-02", [102, 110])]:
        pd.DataFrame(
            {
                "datetime": pd.date_range(f"{day} 00:00", periods=len(prices), freq="10min"),
                "price": prices,
                "qty": [1.0] * len(prices),
            }
        ).to_csv(tmp_path / f"TEST-trades-{day}.csv", index=False)

    out = q.dataload.load_ohlc_timeseries_range(
        "TEST", "1h", datetime(2025, 1, 1), datetime(2025, 1, 2), data_path=tmp_path
    )
    assert list(out.columns) == ["open", "high", "low", "close", "volume"]
    assert len(out) == 2  # one bar per day
    first = out.iloc[0]
    assert (first.open, first.high, first.low, first.close) == (100, 105, 95, 102)
    assert first.volume == 4.0
