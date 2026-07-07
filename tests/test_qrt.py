import pandas as pd

import qrt as q


def test_import():
    assert q.__version__


def test_sma():
    s = pd.Series([1.0, 2.0, 3.0, 4.0])
    out = q.feat.SMA(s, 2)
    assert out.iloc[-1] == 3.5
