import pandas as pd

import qrt as q


def test_import():
    assert q.__version__


def test_sma():
    s = pd.Series([1.0, 2.0, 3.0, 4.0])
    out = q.feat.SMA(s, 2)
    assert out.iloc[-1] == 3.5


def test_lags_series():
    s = pd.Series([1.0, 2.0, 3.0, 4.0], name="close")
    out = q.feat.lags(s, 2)
    assert list(out.columns) == ["close_lag1", "close_lag2"]
    assert out["close_lag1"].iloc[-1] == 3.0
    assert out["close_lag2"].iloc[-1] == 2.0


def test_lags_dataframe_explicit_periods():
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [10.0, 20.0, 30.0]})
    out = q.feat.lags(df, [1, 2])
    assert list(out.columns) == ["a_lag1", "a_lag2", "b_lag1", "b_lag2"]
    assert out["b_lag2"].iloc[-1] == 10.0
