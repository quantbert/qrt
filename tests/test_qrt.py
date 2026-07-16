import math

import pandas as pd
from plotly.graph_objects import Figure as PlotlyFigure
import pytest

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


def test_log_preserves_pandas_series():
    values = pd.Series([1.0, math.e], index=pd.date_range("2025-01-01", periods=2))
    out = q.utils.log(values)
    assert out.index.equals(values.index)
    assert out.iloc[1] == pytest.approx(1.0)


def test_plot_col_expands_wildcard_columns():
    df = pd.DataFrame({"a_log_ret": [0.01, -0.02], "b_log_ret": [0.02, 0.01], "close": [100, 101]})
    figure = q.plot.col(df, "*_log_ret")
    assert isinstance(figure, PlotlyFigure)
    assert [trace.name for trace in figure.data] == ["a_log_ret", "b_log_ret"]


def test_plot_creates_interactive_performance_report():
    returns = pd.Series([0.01, -0.02, 0.03], index=pd.date_range("2025-01-01", periods=3), name="strategy")
    figure = q.plot.plot(returns)
    assert isinstance(figure, PlotlyFigure)
    assert [trace.name for trace in figure.data] == ["strategy", "Drawdown"]
    assert figure.layout.title.text == "strategy"


def test_plot_accepts_log_returns():
    simple_returns = pd.Series([0.01, -0.02, 0.03], name="strategy")
    log_returns = (1.0 + simple_returns).apply(math.log)
    figure = q.plot.plot(log_returns, return_type="log")
    assert figure.data[0].y[-1] == pytest.approx((1.0 + simple_returns).prod())


def test_performance_calculates_standard_metrics_and_infers_frequency():
    returns = pd.Series([0.01, -0.02, 0.03], index=pd.date_range("2025-01-01", periods=3), name="strategy")
    stats = q.stats.performance(returns)
    assert stats["Total Return"] == pytest.approx((1.0 + returns).prod() - 1.0)
    assert stats["Periods"] == 3
    assert q.stats.infer_periods_per_year(returns.index) == 252
    assert {"Sharpe", "Sortino", "Calmar", "Max Drawdown"}.issubset(stats.index)


def test_rolling_diagnostics_and_benchmark_stats():
    benchmark = pd.Series([0.01, -0.01, 0.02, 0.01, -0.01], index=pd.date_range("2025-01-01", periods=5), name="SPY")
    returns = (benchmark * 2).rename("strategy")
    assert q.stats.rolling_volatility(returns, window=3).iloc[-1] > 0
    assert q.stats.rolling_sharpe(returns, window=3).iloc[-1] != 0
    assert q.stats.rolling_beta(returns, benchmark, window=3).iloc[-1] == pytest.approx(2.0)
    assert q.stats.rolling_alpha(returns, benchmark, window=3).iloc[-1] == pytest.approx(0.0)
    assert q.stats.beta(returns, benchmark) == pytest.approx(2.0)
    assert q.stats.alpha(returns, benchmark) == pytest.approx(0.0)

    stats = q.stats.benchmark_stats(returns, benchmark)
    assert stats["Beta"] == pytest.approx(2.0)
    assert stats["Periods"] == len(returns)


def test_monthly_returns_and_heatmap():
    returns = pd.Series(
        [0.01, 0.02, -0.01], index=pd.to_datetime(["2025-01-02", "2025-01-31", "2025-02-03"]), name="strategy"
    )
    table = q.stats.monthly_returns(returns)
    assert table.loc[2025, 1] == pytest.approx((1.01 * 1.02) - 1.0)
    assert table.loc[2025, 2] == pytest.approx(-0.01)

    figure = q.plot.monthly_heatmap(returns)
    assert isinstance(figure, PlotlyFigure)
    assert figure.layout.title.text == "Monthly returns"


def test_stats_returns_chains_bound_stats_and_plotting():
    benchmark = pd.Series([0.01, -0.01, 0.02, 0.01, -0.01], index=pd.date_range("2025-01-01", periods=5), name="SPY")
    returns = (benchmark * 2).rename("strategy")

    bound = q.stats.returns(returns, benchmark=benchmark)
    assert isinstance(bound, q.stats.Returns)
    assert bound.beta() == pytest.approx(2.0)
    assert bound.alpha() == pytest.approx(0.0)
    assert bound.performance()["Periods"] == len(returns)
    assert bound.rolling_beta(window=3).iloc[-1] == pytest.approx(2.0)

    figure = bound.plot("equity")
    assert isinstance(figure, PlotlyFigure)

    unbenchmarked = q.stats.returns(returns)
    with pytest.raises(ValueError):
        unbenchmarked.beta()


def test_plotly_figures_are_available_at_root_and_interactive_namespace():
    index = pd.date_range("2025-01-01", periods=3)
    benchmark = pd.Series([0.01, -0.01, 0.02], index=index, name="SPY")
    returns = pd.Series([0.02, -0.02, 0.03], index=index, name="strategy")

    line_figure = q.plot.col(pd.concat([returns, benchmark], axis=1))
    equity_figure = q.plot.equity(returns)
    drawdown_figure = q.plot.drawdown(returns)
    report_figure = q.plot.plot(returns, benchmark=benchmark)
    heatmap_figure = q.plot.monthly_heatmap(returns)

    assert isinstance(line_figure, PlotlyFigure)
    assert len(line_figure.data) == 2
    assert isinstance(equity_figure, PlotlyFigure)
    assert isinstance(drawdown_figure, PlotlyFigure)
    assert isinstance(report_figure, PlotlyFigure)
    assert len(report_figure.data) == 3
    assert isinstance(heatmap_figure, PlotlyFigure)
    assert heatmap_figure.data[0].type == "heatmap"


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
