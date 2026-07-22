import math

import numpy as np
import pandas as pd
from plotly.graph_objects import Figure as PlotlyFigure
import pytest

import qrt as q


def test_import():
    assert q.__version__


def test_datasets_load_bundled_offline():
    for name in q.data.datasets.AVAILABLE:
        if name in q.data.datasets.TRADE_LOGS:
            continue
        df = q.data.datasets.load(name)
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        assert df.index.name == "datetime"
        assert len(df) > 0


def test_datasets_load_trade_logs():
    reserved = [
        "symbol", "entry_time", "exit_time", "direction", "entry_reason",
        "exit_reason", "entry_price", "exit_price", "return", "mae", "mfe",
        "size", "fees",
    ]
    for name in q.data.datasets.TRADE_LOGS:
        trades = q.data.datasets.load(name)
        assert list(trades.columns[: len(reserved)]) == reserved
        assert len(trades) > 0
        assert trades["direction"].isin([1, -1]).all()
        assert (trades["exit_time"] >= trades["entry_time"]).all()
        # returns are decimal fractions, direction-adjusted
        sign = trades["direction"]
        expected = sign * (trades["exit_price"] / trades["entry_price"] - 1)
        assert np.allclose(trades["return"], expected)
        # MAE/MFE bracket the trade return
        assert (trades["mae"] <= trades["return"] + 1e-12).all()
        assert (trades["mfe"] >= trades["return"] - 1e-12).all()
        # trades never overlap (single position at a time)
        assert (trades["entry_time"].iloc[1:].values
                >= trades["exit_time"].iloc[:-1].values).all()


def test_datasets_load_unknown_raises():
    with pytest.raises(KeyError):
        q.data.datasets.load("not-a-real-dataset")


def test_trades_to_returns():
    trades = q.data.datasets.load("spy_rsi2")
    spy = q.data.datasets.load("spy")

    # without prices: attributed at exit_time, compounds to the trade total
    r = q.stats.trades_to_returns(trades)
    assert r.index.is_monotonic_increasing
    assert np.isclose((1 + r).prod(), (1 + trades["return"]).prod())

    # with prices: mark-to-market on the full prices index, flat bars are 0
    r_mtm = q.stats.trades_to_returns(trades, prices=spy["close"])
    assert r_mtm.index.equals(spy.index)
    assert (r_mtm == 0).sum() > len(spy) / 2  # mostly flat strategy
    # long-only: daily compounding reproduces the trade-level total exactly
    assert np.isclose((1 + r_mtm).prod(), (1 + trades["return"]).prod())

    with pytest.raises(ValueError):
        q.stats.trades_to_returns(trades.drop(columns=["direction"]))


def test_trades_to_positions():
    spy = q.data.datasets.load("spy")
    trades = q.data.datasets.load("spy_random")
    pos = q.stats.trades_to_positions(trades, spy.index)
    assert set(pos.unique()) <= {-1, 0, 1}
    assert (pos != 0).any() and (pos == 0).any()
    # every entry bar carries the trade's sign
    first = trades.iloc[0]
    assert pos.loc[first["entry_time"]] == first["direction"]


def test_trade_stats():
    trades = q.data.datasets.load("spy_breakout")
    table = q.stats.trade_stats(trades, by="direction")
    assert "All" in table.columns and "1" in table.columns
    assert table.loc["Trades", "All"] == len(trades)
    assert 0 <= table.loc["Win Rate", "All"] <= 1
    assert 0 < table.loc["Exposure", "All"] <= 1
    assert table.loc["Avg MAE", "All"] < 0 < table.loc["Avg MFE", "All"]
    assert np.isclose(table.loc["Total Return", "All"], (1 + trades["return"]).prod() - 1)
    with pytest.raises(ValueError):
        q.stats.trade_stats(trades, by="not-a-column")


def test_trade_plots():
    spy = q.data.datasets.load("spy")
    trades = q.data.datasets.load("spy_breakout")
    feats = pd.DataFrame({"ema50": spy["close"].ewm(span=50, adjust=False).mean()})
    assert isinstance(q.plot.trades(trades, spy["close"], features=feats), PlotlyFigure)
    assert isinstance(q.plot.trades(trades, spy), PlotlyFigure)  # OHLCV frame accepted
    assert isinstance(q.plot.mae_mfe(trades), PlotlyFigure)
    assert isinstance(q.plot.trade_distribution(trades, by="exit_reason"), PlotlyFigure)
    with pytest.raises(ValueError):
        q.plot.trade_distribution(trades, by="not-a-column")


def test_sma():
    s = pd.Series([1.0, 2.0, 3.0, 4.0])
    out = q.indicator.sma(s, 2)
    assert out.iloc[-1] == 3.5


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
    assert figure.data[0].y[-1] == pytest.approx((1.0 + simple_returns).prod() - 1.0)


def test_performance_calculates_standard_metrics_and_infers_frequency():
    returns = pd.Series([0.01, -0.02, 0.03], index=pd.date_range("2025-01-01", periods=3), name="strategy")
    stats = q.stats.performance(returns)
    assert stats["Total Return"] == pytest.approx((1.0 + returns).prod() - 1.0)
    assert stats["Periods"] == 3
    assert q.stats.infer_periods_per_year(returns.index) == 252
    assert {"Sharpe", "Sortino", "Calmar", "Max Drawdown"}.issubset(stats.index)


def test_metrics_builds_full_quantstats_table():
    rng = pd.date_range("2024-01-01", periods=300, freq="B")
    returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.003] * 60, index=rng, name="strategy")
    benchmark = (returns * 0.5).rename("SPY")

    frame = q.stats.metrics(returns, benchmark)
    assert list(frame.columns) == ["SPY", "strategy"]
    assert frame.index.names == ["Section", "Metric"]
    metric_names = frame.index.get_level_values("Metric")
    assert {"Cumulative Return", "Prob. Sharpe Ratio", "Kelly Criterion", "Gain/Pain (1M)", "MTD", "Best Month", "Win Year"}.issubset(metric_names)
    assert frame.loc[("Returns", "Cumulative Return"), "strategy"] == pytest.approx((1.0 + returns).prod() - 1.0)
    # vs. Benchmark rows are strategy-only
    assert pd.isna(frame.loc[("vs. Benchmark", "Beta"), "SPY"])
    assert frame.loc[("vs. Benchmark", "Beta"), "strategy"] == pytest.approx(2.0)

    basic = q.stats.metrics(returns, benchmark, mode="basic")
    assert len(basic) < len(frame)
    assert "Prob. Sharpe Ratio" not in basic.index.get_level_values("Metric")

    no_benchmark = q.stats.metrics(returns)
    assert list(no_benchmark.columns) == ["strategy"]
    assert "vs. Benchmark" not in no_benchmark.index.get_level_values("Section")


def test_period_and_expected_and_aggregate_helpers():
    rng = pd.date_range("2024-01-01", periods=300, freq="B")
    returns = pd.Series(np.random.default_rng(0).normal(0.0005, 0.01, 300), index=rng, name="strategy")

    periods = q.stats.period_returns(returns)
    assert list(periods.index) == ["MTD", "3M", "6M", "YTD", "1Y", "3Y (ann.)", "5Y (ann.)", "10Y (ann.)", "All-time (ann.)"]
    monthly = q.stats.aggregate_returns(returns, "M")
    assert q.stats.expected_return(returns, aggregate="M") == pytest.approx(q.stats.geometric_mean(monthly))
    assert q.stats.best(returns, aggregate="M") == pytest.approx(monthly.max())
    assert q.stats.worst(returns, aggregate="M") == pytest.approx(monthly.min())
    assert q.stats.win_rate(returns, aggregate="M") == pytest.approx((monthly[monthly != 0] > 0).mean())
    assert q.stats.avg_win(returns, aggregate="M") == pytest.approx(monthly[monthly > 0].mean())
    assert q.stats.avg_loss(returns, aggregate="M") == pytest.approx(monthly[monthly < 0].mean())


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


def test_sharpe_sortino_smart_and_adjusted_variants():
    returns = pd.Series(
        [0.01, -0.02, 0.03, 0.01, -0.01, 0.02, -0.03, 0.02], index=pd.date_range("2025-01-01", periods=8), name="s"
    )
    plain = q.stats.sharpe(returns)
    smart = q.stats.sharpe(returns, smart=True)
    assert q.stats.autocorr_penalty(returns) >= 1.0
    assert smart != plain

    assert q.stats.adjusted_sortino(returns) == pytest.approx(q.stats.sortino(returns) / math.sqrt(2))

    for base in ("sharpe", "sortino", "adjusted_sortino"):
        prob = q.stats.probabilistic_ratio(returns, base=base)
        assert 0.0 <= prob <= 1.0
    with pytest.raises(ValueError):
        q.stats.probabilistic_ratio(returns, base="not-a-ratio")

    stats = q.stats.performance(returns, smart=True)
    assert stats["Sharpe"] == pytest.approx(q.stats.sharpe(returns, smart=True))
    assert stats["Sortino"] == pytest.approx(q.stats.sortino(returns, smart=True))


def test_treynor_omega_gain_to_pain_and_rar():
    benchmark = pd.Series([0.01, -0.01, 0.02, 0.01, -0.01], index=pd.date_range("2025-01-01", periods=5), name="SPY")
    returns = (benchmark * 2).rename("strategy")

    assert q.stats.treynor_ratio(returns, benchmark) > 0
    assert q.stats.omega(returns) > 1.0
    assert q.stats.gain_to_pain_ratio(returns) > 0
    assert q.stats.exposure(returns) == pytest.approx(1.0)
    assert q.stats.rar(returns) == pytest.approx(q.stats.performance(returns)["CAGR"] / q.stats.exposure(returns))

    with_zeros = pd.Series([0.01, 0.0, 0.02, 0.0], index=pd.date_range("2025-01-01", periods=4))
    assert q.stats.exposure(with_zeros) == pytest.approx(0.5)


def test_distribution_shape_and_risk_measures():
    returns = pd.Series(
        [0.01, -0.02, 0.03, 0.01, -0.01, 0.02, -0.03, 0.02, 0.15, -0.15],
        index=pd.date_range("2025-01-01", periods=10),
        name="s",
    )
    assert q.stats.skew(returns) == pytest.approx(returns.skew())
    assert q.stats.kurtosis(returns) == pytest.approx(returns.kurtosis())
    assert q.stats.ulcer_index(returns) >= 0
    assert q.stats.value_at_risk(returns) < 0
    assert q.stats.conditional_value_at_risk(returns) <= q.stats.value_at_risk(returns)
    assert q.stats.risk_of_ruin(returns) >= 0
    assert q.stats.tail_ratio(returns) > 0
    assert 0.0 <= q.stats.risk_of_ruin(returns) <= 1.0
    assert q.stats.serenity_index(returns) == q.stats.serenity_index(returns)  # not NaN
    assert q.stats.ulcer_performance_index(returns) == q.stats.ulcer_performance_index(returns)

    dist = q.stats.distribution(returns)
    assert set(dist) == {"Daily", "Weekly", "Monthly", "Quarterly", "Yearly"}
    assert len(dist["Daily"]["values"]) + len(dist["Daily"]["outliers"]) == len(returns)


def test_win_loss_ratios_and_kelly_criterion():
    returns = pd.Series(
        [0.02, 0.03, -0.01, 0.01, -0.02, 0.04, -0.01, 0.02],
        index=pd.date_range("2025-01-01", periods=8),
        name="s",
    )
    assert q.stats.avg_win(returns) > 0
    assert q.stats.avg_loss(returns) < 0
    assert q.stats.avg_return(returns) == pytest.approx(returns[returns != 0].mean())
    assert q.stats.payoff_ratio(returns) == pytest.approx(q.stats.avg_win(returns) / abs(q.stats.avg_loss(returns)))
    assert q.stats.profit_ratio(returns) == pytest.approx(5 / 3)
    assert q.stats.profit_factor(returns) > 0
    assert q.stats.cpc_index(returns) > 0
    assert q.stats.common_sense_ratio(returns) > 0
    assert q.stats.outlier_win_ratio(returns) > 0
    assert q.stats.outlier_loss_ratio(returns) > 0
    assert q.stats.recovery_factor(returns) > 0
    assert q.stats.risk_return_ratio(returns) == pytest.approx(returns.mean() / returns.std(ddof=1))
    assert q.stats.kelly_criterion(returns) == q.stats.kelly_criterion(returns)  # not NaN

    assert q.stats.best(returns) == pytest.approx(returns.max())
    assert q.stats.worst(returns) == pytest.approx(returns.min())
    assert q.stats.consecutive_wins(returns) == 2
    assert q.stats.consecutive_losses(returns) == 1


def test_r_squared_and_compare_vs_benchmark():
    benchmark = pd.Series([0.01, -0.01, 0.02, 0.01, -0.01], index=pd.date_range("2025-01-01", periods=5), name="SPY")
    returns = (benchmark * 2).rename("strategy")

    assert q.stats.r_squared(returns, benchmark) == pytest.approx(1.0)

    table = q.stats.compare(returns, benchmark)
    assert list(table.columns) == ["Strategy", "Benchmark", "Multiplier", "Won"]
    assert len(table) == len(returns)
    assert table["Multiplier"].iloc[0] == pytest.approx(2.0)
    assert table["Won"].dtype == bool
    assert bool(table["Won"].iloc[0])  # positive benchmark period: 2x return still wins


def _synthetic_factor_data(n=400, seed=0):
    """Build a synthetic Fama-French-style factor set and a return stream with known betas."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2022-01-03", periods=n)
    factor_names = ["Mkt-RF", "SMB", "HML", "RMW", "CMA"]
    scales = [0.010, 0.005, 0.005, 0.004, 0.004]
    factor_frame = pd.DataFrame(
        {name: rng.normal(0.0002 if name == "Mkt-RF" else 0.0, scale, n) for name, scale in zip(factor_names, scales)},
        index=idx,
    )
    factor_frame["RF"] = 0.00006
    alpha_true = 0.0001
    betas_true = pd.Series({"Mkt-RF": 1.2, "SMB": -0.3, "HML": 0.4, "RMW": 0.2, "CMA": -0.1})
    noise = rng.normal(0.0, 0.003, n)
    excess = alpha_true + (factor_frame[factor_names] * betas_true).sum(axis=1) + noise
    returns = (excess + factor_frame["RF"]).rename("Strategy")
    return returns, factor_frame, alpha_true, betas_true


def test_factor_regression_recovers_synthetic_coefficients():
    returns, factors, alpha_true, betas_true = _synthetic_factor_data()

    table = q.stats.factor_regression(returns, factors)
    assert list(table.index) == ["Alpha", *betas_true.index]
    assert table.loc["Alpha", "Coefficient"] == pytest.approx(alpha_true, abs=5e-4)
    for factor, true_beta in betas_true.items():
        assert table.loc[factor, "Coefficient"] == pytest.approx(true_beta, abs=0.1)
        assert table.loc[factor, "CI Lower"] < table.loc[factor, "Coefficient"] < table.loc[factor, "CI Upper"]

    summary = q.stats.factor_regression_stats(returns, factors)
    assert summary["R²"] > 0.9
    assert summary["Periods"] == len(returns)
    assert summary["Alpha (ann.)"] == pytest.approx(summary["Alpha"] * q.stats.infer_periods_per_year(returns.index))


def test_factor_regression_rf_column_not_subtracted_twice():
    returns, factors, _, _ = _synthetic_factor_data()

    with_rf_column = q.stats.factor_regression(returns, factors, rf="RF")
    already_excess = q.stats.factor_regression(returns - factors["RF"], factors.drop(columns="RF"), rf=None)
    pd.testing.assert_series_equal(with_rf_column["Coefficient"], already_excess["Coefficient"])

    with pytest.raises(ValueError):
        q.stats.factor_regression(returns, factors, rf="NotAColumn")


def test_factor_regression_sorts_dates_and_rejects_duplicates():
    returns, factors, _, _ = _synthetic_factor_data(n=150)

    shuffle = np.random.default_rng(1).permutation(len(returns))
    rolling_sorted = q.stats.rolling_factor_regression(returns, factors, window=63)
    rolling_shuffled = q.stats.rolling_factor_regression(returns.iloc[shuffle], factors.iloc[shuffle], window=63)
    pd.testing.assert_frame_equal(rolling_sorted, rolling_shuffled, check_freq=False)

    duplicated = factors.index.to_numpy().copy()
    duplicated[1] = duplicated[0]
    factors_duplicated = factors.set_axis(pd.DatetimeIndex(duplicated))
    with pytest.raises(ValueError, match="duplicate dates"):
        q.stats.factor_regression(returns, factors_duplicated)


def test_rolling_factor_regression_window_alignment():
    returns, factors, _, betas_true = _synthetic_factor_data()
    window = 63

    rolling = q.stats.rolling_factor_regression(returns, factors, window=window)
    assert list(rolling.columns) == ["Alpha", *betas_true.index, "R²", "N Obs"]
    assert rolling.iloc[: window - 1].isna().all().all()
    first_valid = rolling.iloc[window - 1]
    assert first_valid.notna().all()
    assert first_valid["N Obs"] == window
    assert rolling["Mkt-RF"].dropna().mean() == pytest.approx(betas_true["Mkt-RF"], abs=0.2)

    with pytest.raises(ValueError):
        q.stats.rolling_factor_regression(returns, factors, window=window, min_observations=3)


def test_factor_contributions_sum_to_excess_return():
    returns, factors, _, _ = _synthetic_factor_data()

    contributions = q.stats.factor_contributions(returns, factors)
    assert list(contributions.columns) == ["Alpha", "Mkt-RF", "SMB", "HML", "RMW", "CMA", "Residual"]
    excess = returns - factors["RF"]
    total = contributions.sum(axis=1)
    assert total.to_numpy() == pytest.approx(excess.to_numpy(), abs=1e-9)


def test_factor_plots_build_without_error():
    returns, factors, _, _ = _synthetic_factor_data(n=150)

    loadings_figure = q.plot.factor_loadings(returns, factors)
    assert isinstance(loadings_figure, PlotlyFigure)
    assert [trace.name for trace in loadings_figure.data] == [None]  # single go.Bar trace

    rolling_figure = q.plot.rolling_factor_betas(returns, factors, window=63)
    assert isinstance(rolling_figure, PlotlyFigure)
    assert {trace.name for trace in rolling_figure.data} == {"Mkt-RF", "SMB", "HML", "RMW", "CMA"}

    contributions_figure = q.plot.factor_contributions(returns, factors)
    assert isinstance(contributions_figure, PlotlyFigure)
    assert "Total (Excess Return)" in {trace.name for trace in contributions_figure.data}


def test_standalone_metrics_match_performance_and_benchmark_stats():
    benchmark = pd.Series([0.01, -0.01, 0.02, 0.01, -0.01], index=pd.date_range("2025-01-01", periods=5), name="SPY")
    returns = (benchmark * 2).rename("strategy")

    stats = q.stats.performance(returns)
    assert q.stats.max_drawdown(returns) == pytest.approx(stats["Max Drawdown"])
    assert q.stats.volatility(returns) == pytest.approx(stats["Volatility"])
    assert q.stats.calmar(returns) == pytest.approx(stats["Calmar"])
    assert q.stats.win_rate(returns) == pytest.approx(stats["Win Rate"])
    assert q.stats.to_drawdown_series(returns).min() == pytest.approx(stats["Max Drawdown"])

    bstats = q.stats.benchmark_stats(returns, benchmark)
    assert q.stats.information_ratio(returns, benchmark) == pytest.approx(bstats["Information Ratio"])


def test_return_transform_and_descriptive_utilities():
    returns = pd.Series(
        [0.01, -0.02, 0.03, 0.01, -0.01, 0.02, -0.03, 0.02, 0.15, -0.15],
        index=pd.date_range("2025-01-01", periods=10),
        name="s",
    )

    excess = q.stats.excess_returns(returns, rf=0.02)
    assert excess.iloc[0] < returns.iloc[0]

    log_rets = q.stats.to_log_returns(returns)
    assert log_rets.iloc[0] == pytest.approx(math.log1p(returns.iloc[0]))

    ewm_vol = q.stats.exponential_volatility(returns, span=3)
    assert ewm_vol.dropna().gt(0).all()

    assert q.stats.geometric_mean(returns) == pytest.approx((1.0 + returns).prod() ** (1.0 / len(returns)) - 1.0)

    high = q.stats.outliers(returns, 0.8)
    low = q.stats.remove_outliers(returns, 0.8)
    assert len(high) + len(low) == len(returns)
    assert (high > returns.quantile(0.8)).all()
    assert (low < returns.quantile(0.8)).all()


def test_drawdown_details_matches_max_drawdown_and_sorting():
    idx = pd.date_range("2025-01-01", periods=8)
    returns = pd.Series([0.05, -0.10, -0.05, 0.20, -0.20, -0.02, 0.30, -0.01], index=idx, name="s")

    details = q.stats.drawdown_details(returns)
    assert list(details.columns) == ["Start", "Valley", "End", "Days", "Max Drawdown"]
    assert (details["Max Drawdown"] <= 0).all()
    assert details["Max Drawdown"].min() == pytest.approx(q.stats.max_drawdown(returns))
    assert details["Max Drawdown"].is_monotonic_increasing

    by_duration = q.stats.drawdown_details(returns, sort_by="duration")
    assert by_duration["Days"].is_monotonic_decreasing


def test_drawdown_details_empty_when_no_drawdown():
    idx = pd.date_range("2025-01-01", periods=3)
    returns = pd.Series([0.01, 0.02, 0.03], index=idx, name="s")
    details = q.stats.drawdown_details(returns)
    assert details.empty
    assert list(details.columns) == ["Start", "Valley", "End", "Days", "Max Drawdown"]


def test_return_prep_utilities():
    idx = pd.date_range("2025-01-01", periods=400, freq="D")
    returns = pd.Series([0.001] * 400, index=idx, name="s")

    monthly = q.stats.aggregate_returns(returns, "M")
    assert len(monthly) < len(returns)
    assert monthly.iloc[0] == pytest.approx((1.001) ** 31 - 1.0, rel=1e-6)

    yearly = q.stats.aggregate_returns(returns, "Y")
    assert len(yearly) == 2

    prices = q.stats.to_prices(returns, base=100.0)
    assert prices.iloc[0] == pytest.approx(100.0 * 1.001)
    assert prices.iloc[-1] == pytest.approx(100.0 * (1.001) ** 400, rel=1e-6)

    rebased = q.stats.rebase(prices, base=1.0)
    assert rebased.iloc[0] == pytest.approx(1.0)

    port_compound = q.stats.make_portfolio(returns, start_balance=1000.0, mode="compound")
    assert port_compound.iloc[-1] == pytest.approx(1000.0 * (1.001) ** 400, rel=1e-6)

    port_linear = q.stats.make_portfolio(returns, start_balance=1000.0, mode="linear")
    assert port_linear.iloc[-1] == pytest.approx(1000.0 * (1.0 + 400 * 0.001), rel=1e-6)

    with pytest.raises(ValueError):
        q.stats.make_portfolio(returns, mode="bogus")  # type: ignore[arg-type]


def test_montecarlo_shapes_and_probabilities():
    idx = pd.date_range("2025-01-01", periods=60, freq="D")
    returns = pd.Series([0.01, -0.01] * 30, index=idx, name="s")

    mc = q.stats.montecarlo(returns, sims=50, bust=-0.5, goal=100.0, seed=7)
    assert mc["paths"].shape == (60, 50)
    assert mc["bust_probability"] == pytest.approx(0.0)
    assert mc["goal_probability"] == pytest.approx(0.0)
    assert (mc["confidence_band"]["Lower"] <= mc["confidence_band"]["Upper"]).all()

    with pytest.raises(ValueError):
        q.stats.montecarlo(returns, sims=0)


def test_montecarlo_bootstrap_varies_terminal_value():
    # Bootstrap resampling (with replacement) must produce a genuine spread of terminal
    # outcomes, unlike plain permutation, whose compounded terminal value is order-invariant.
    idx = pd.date_range("2025-01-01", periods=250, freq="D")
    values = [0.01 if i % 3 else -0.015 for i in range(250)]
    returns = pd.Series(values, index=idx, name="s")

    mc = q.stats.montecarlo(returns, sims=200, seed=3)
    terminal = mc["paths"].iloc[-1]
    assert terminal.nunique() > 1
    assert terminal["sim_0"] == pytest.approx((1.0 + returns).prod() - 1.0)


def test_montecarlo_block_bootstrap_preserves_contiguity():
    # A stationary block bootstrap should resample contiguous (circularly-wrapped) runs whose
    # average length matches block_size, rather than shuffling individual periods independently.
    from qrt.stats.core import _stationary_bootstrap_indices

    rng = np.random.default_rng(11)
    n = 500
    idx = _stationary_bootstrap_indices(rng, n, n, block_size=20)
    assert idx.shape == (n,)
    assert idx.min() >= 0
    assert idx.max() < n

    run_lengths = []
    run = 1
    for prev, curr in zip(idx[:-1], idx[1:]):
        if curr == (prev + 1) % n:
            run += 1
        else:
            run_lengths.append(run)
            run = 1
    run_lengths.append(run)
    assert 10 <= (sum(run_lengths) / len(run_lengths)) <= 40


def test_montecarlo_block_size_validation_and_variation():
    idx = pd.date_range("2025-01-01", periods=250, freq="D")
    values = [0.01 if i % 3 else -0.015 for i in range(250)]
    returns = pd.Series(values, index=idx, name="s")

    with pytest.raises(ValueError):
        q.stats.montecarlo(returns, sims=5, block_size=0)

    mc = q.stats.montecarlo(returns, sims=200, seed=3, block_size=15)
    terminal = mc["paths"].iloc[-1]
    assert terminal.nunique() > 1
    assert terminal["sim_0"] == pytest.approx((1.0 + returns).prod() - 1.0)


def test_montecarlo_periods_decouples_horizon_from_pool():
    idx = pd.date_range("2025-01-01", periods=250, freq="D")
    values = [0.01 if i % 3 else -0.015 for i in range(250)]
    returns = pd.Series(values, index=idx, name="s")

    with pytest.raises(ValueError):
        q.stats.montecarlo(returns, sims=5, periods=0)
    with pytest.raises(ValueError):
        q.stats.montecarlo(returns, sims=5, periods=len(returns) + 1)

    for block_size in (None, 15):
        mc = q.stats.montecarlo(returns, sims=50, seed=3, periods=60, block_size=block_size)
        assert mc["paths"].shape == (60, 50)
        assert mc["paths"].index.equals(returns.index[-60:])
        terminal = mc["paths"].iloc[-1]
        expected = (1.0 + returns.tail(60)).prod() - 1.0
        assert terminal["sim_0"] == pytest.approx(expected)

    full = q.stats.montecarlo(returns, sims=10, seed=3, periods=len(returns))
    default = q.stats.montecarlo(returns, sims=10, seed=3)
    pd.testing.assert_frame_equal(full["paths"], default["paths"])


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


def test_montecarlo_plots():
    idx = pd.date_range("2025-01-01", periods=120, freq="D")
    returns = pd.Series([0.01, -0.008] * 60, index=idx, name="strategy")

    fan_figure = q.plot.montecarlo(returns, sims=40, bust=-0.3, goal=0.2, seed=1, sample=20)
    assert isinstance(fan_figure, PlotlyFigure)
    # band (2) + sampled paths (<=20) + original (1)
    assert 3 <= len(fan_figure.data) <= 23
    assert fan_figure.data[-1].name == "Original"

    dist_figure = q.plot.montecarlo_distribution(returns, sims=40, bust=-0.3, goal=0.2, seed=1)
    assert isinstance(dist_figure, PlotlyFigure)
    assert len(dist_figure.data) == 2
    assert {trace.type for trace in dist_figure.data} == {"histogram"}

    block_fan_figure = q.plot.montecarlo(returns, sims=40, seed=1, sample=20, block_size=15)
    assert isinstance(block_fan_figure, PlotlyFigure)

    horizon_figure = q.plot.montecarlo(returns, sims=40, seed=1, sample=20, periods=30)
    assert isinstance(horizon_figure, PlotlyFigure)

    horizon_dist_figure = q.plot.montecarlo_distribution(returns, sims=40, seed=1, periods=30)
    assert isinstance(horizon_dist_figure, PlotlyFigure)


def test_variance_test_shapes_and_probabilities():
    trades = pd.Series([0.05, -0.02] * 30, name="trades")

    vt = q.stats.variance_test(trades, periods=100, sims=50, seed=7)
    assert vt["paths"].shape == (100, 50)
    assert vt["real_path"].shape == (60,)
    assert len(vt["win_rates"]) == 50
    assert 0.0 <= vt["make_money_probability"] <= 1.0
    assert 0.0 <= vt["ruin_probability"] <= 1.0
    assert (vt["confidence_band"]["Lower"] <= vt["confidence_band"]["Upper"]).all()
    assert vt["pnldd_ratio"] == pytest.approx(vt["average_profit"] / abs(vt["average_drawdown"]))

    with pytest.raises(ValueError):
        q.stats.variance_test(trades, periods=0, sims=5)
    with pytest.raises(ValueError):
        q.stats.variance_test(trades, periods=10, sims=0)
    with pytest.raises(ValueError):
        q.stats.variance_test(trades, periods=10, sims=5, win_rate_variance=1.5)
    with pytest.raises(ValueError):
        q.stats.variance_test(pd.Series([0.05, 0.02, 0.03]), periods=10, sims=5)  # no losers


def test_variance_test_win_rate_varies_per_simulation():
    trades = pd.Series([0.05, -0.02] * 50, name="trades")

    vt = q.stats.variance_test(trades, periods=200, sims=100, seed=3, win_rate_variance=0.2)
    win_rates = vt["win_rates"]
    assert win_rates.min() >= 0.0
    assert win_rates.max() <= 1.0
    assert win_rates.std() > 0.0
    terminal = vt["paths"].iloc[-1]
    assert terminal.nunique() > 1


def test_variance_test_extrapolates_dates_when_indexed():
    idx = pd.date_range("2025-01-01", periods=60, freq="D")
    trades = pd.Series([0.05, -0.02] * 30, index=idx, name="trades")

    vt = q.stats.variance_test(trades, periods=30, sims=20, seed=3)
    assert isinstance(vt["real_path"].index, pd.DatetimeIndex)
    assert isinstance(vt["paths"].index, pd.DatetimeIndex)
    assert vt["real_path"].index.equals(idx[-30:])
    assert vt["paths"].index.min() > vt["real_path"].index.max()
    assert len(vt["paths"]) == 30


def test_variance_test_plot():
    trades = pd.Series([0.05, -0.02] * 30, name="strategy")

    fan_figure = q.plot.variance_test(trades, periods=100, sims=40, seed=1, sample=20)
    assert isinstance(fan_figure, PlotlyFigure)
    # band (2) + sampled paths (<=20) + real (1)
    assert 3 <= len(fan_figure.data) <= 23
    assert fan_figure.data[-1].name == "Real"


def test_variance_test_plot_uses_dates_when_indexed():
    idx = pd.date_range("2025-01-01", periods=60, freq="D")
    trades = pd.Series([0.05, -0.02] * 30, index=idx, name="strategy")

    fan_figure = q.plot.variance_test(trades, periods=30, sims=20, seed=1, sample=20)
    assert isinstance(fan_figure, PlotlyFigure)
    assert fan_figure.layout.xaxis.rangeselector is not None


def test_variance_test_plot_rebases_paths_onto_real_level():
    trades = pd.Series([0.05, -0.02] * 30, name="strategy")

    vt = q.stats.variance_test(trades, periods=100, sims=40, seed=1)
    real_last = vt["real_path"].iloc[-1]

    fan_figure = q.plot.variance_test(trades, periods=100, sims=40, seed=1, sample=40)
    real_trace = next(t for t in fan_figure.data if t.name == "Real")
    assert real_trace.y[-1] == pytest.approx(real_last)

    random_traces = [t for t in fan_figure.data if t.name in ("Random", "Ruined", "Profitable")]
    assert random_traces  # sanity: some simulated paths rendered
    first_ys = [t.y[0] for t in random_traces]
    # Rebased first simulated points should cluster near the real path's ending level,
    # not reset back down to 0.
    assert all(abs(y - real_last) < abs(y - 0.0) for y in first_ys)

    band_trace = next(t for t in fan_figure.data if t.name == "95% band")
    # The confidence band's first point should also be rebased near the real path's
    # ending level rather than left at its own 0-based starting value.
    assert abs(band_trace.y[0] - real_last) < abs(band_trace.y[0] - 0.0)


def test_noise_test_shapes_and_probabilities():
    idx = pd.date_range("2025-01-01", periods=60, freq="D")
    returns = pd.Series([0.01, -0.008] * 30, index=idx, name="strategy")

    nt = q.stats.noise_test(returns, sims=50, noise=0.1, bust=-0.5, goal=100.0, seed=7)
    assert nt["paths"].shape == (60, 50)
    assert isinstance(nt["paths"].index, pd.DatetimeIndex)
    assert nt["bust_probability"] == pytest.approx(0.0)
    assert nt["goal_probability"] == pytest.approx(0.0)
    assert (nt["confidence_band"]["Lower"] <= nt["confidence_band"]["Upper"]).all()

    real_path = (1.0 + returns).cumprod() - 1.0
    pd.testing.assert_series_equal(nt["paths"]["sim_0"], real_path.rename("sim_0"))

    with pytest.raises(ValueError):
        q.stats.noise_test(returns, sims=0)
    with pytest.raises(ValueError):
        q.stats.noise_test(returns, sims=5, noise=-0.1)


def test_noise_test_preserves_sign_and_varies_magnitude():
    idx = pd.date_range("2025-01-01", periods=100, freq="D")
    returns = pd.Series([0.01, -0.008] * 50, index=idx, name="strategy")

    nt = q.stats.noise_test(returns, sims=50, noise=0.2, seed=3)
    paths = nt["paths"]
    # Every simulated period's return should keep the same sign as the original (noise scales
    # magnitude, never flips direction), while terminal values still vary across simulations.
    period_returns = (1.0 + paths).pct_change().iloc[1:]
    original_sign = np.sign(returns.to_numpy()[1:])
    for column in paths.columns:
        assert (np.sign(period_returns[column].to_numpy()) == original_sign).all()
    terminal = paths.iloc[-1]
    assert terminal.nunique() > 1


def test_noise_test_zero_noise_collapses_to_real_path():
    idx = pd.date_range("2025-01-01", periods=40, freq="D")
    returns = pd.Series([0.01, -0.005] * 20, index=idx, name="strategy")

    nt = q.stats.noise_test(returns, sims=10, noise=0.0, seed=1)
    real_path = (1.0 + returns).cumprod() - 1.0
    for column in nt["paths"].columns:
        pd.testing.assert_series_equal(nt["paths"][column], real_path.rename(column))


def test_noise_test_plot():
    idx = pd.date_range("2025-01-01", periods=80, freq="D")
    returns = pd.Series([0.01, -0.008] * 40, index=idx, name="strategy")

    fan_figure = q.plot.noise_test(returns, sims=40, noise=0.1, seed=1, sample=20)
    assert isinstance(fan_figure, PlotlyFigure)
    assert fan_figure.layout.xaxis.rangeselector is not None
    real_trace = next(t for t in fan_figure.data if t.name == "Real")
    real_path = (1.0 + returns).cumprod() - 1.0
    assert real_trace.y[-1] == pytest.approx(real_path.iloc[-1])

    goal_figure = q.plot.noise_test(returns, sims=40, noise=0.1, bust=-0.2, goal=0.5, seed=1, sample=20)
    assert isinstance(goal_figure, PlotlyFigure)


def _ohlc(n: int = 60) -> pd.DataFrame:
    idx = pd.date_range("2025-01-01", periods=n, freq="D")
    close = pd.Series(range(1, n + 1), index=idx, dtype=float)
    return pd.DataFrame(
        {"open": close, "high": close + 1, "low": close - 1, "close": close, "volume": 100.0}
    )


def test_talib_single_output():
    ohlc = _ohlc()
    out = q.indicator.talib.RSI(ohlc, timeperiod=14)
    assert out.name == "rsi"
    assert out.index.equals(ohlc.index)
    assert out.iloc[-1] == 100.0  # strictly rising close

    # a plain Series is treated as close
    from_series = q.indicator.talib.RSI(ohlc["close"], timeperiod=14)
    assert from_series.equals(out)


def test_talib_multi_output():
    out = q.indicator.talib.MACD(_ohlc())
    assert list(out.columns) == ["macd", "macdsignal", "macdhist"]


def test_talib_unknown_indicator():
    import pytest

    with pytest.raises(AttributeError):
        q.indicator.talib.NOT_AN_INDICATOR


def test_pandas_ta_single_output():
    ohlc = _ohlc()
    out = q.indicator.pandas_ta.rsi(ohlc, length=14)
    assert out.name == "RSI_14"
    assert out.index.equals(ohlc.index)

    # a plain Series is treated as close
    from_series = q.indicator.pandas_ta.rsi(ohlc["close"], length=14)
    assert from_series.equals(out)


def test_pandas_ta_multi_output():
    out = q.indicator.pandas_ta.macd(_ohlc())
    assert list(out.columns) == ["MACD_12_26_9", "MACDh_12_26_9", "MACDs_12_26_9"]


def test_pandas_ta_unknown_indicator():
    import pytest

    with pytest.raises(AttributeError):
        q.indicator.pandas_ta.not_an_indicator


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

    out = q.data.load_ohlc_timeseries_range(
        "TEST", "1h", datetime(2025, 1, 1), datetime(2025, 1, 2), data_path=tmp_path
    )
    assert list(out.columns) == ["open", "high", "low", "close", "volume"]
    assert len(out) == 2  # one bar per day
    first = out.iloc[0]
    assert (first.open, first.high, first.low, first.close) == (100, 105, 95, 102)
    assert first.volume == 4.0
