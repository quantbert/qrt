from __future__ import annotations

from copy import deepcopy
import json

import pandas as pd
import pytest

import qrt as q


def _lean_result() -> dict:
    day = 1_704_067_200
    chart_days = [day + offset * 86_400 for offset in range(8)]
    equity = [[timestamp, value, value, value, value] for timestamp, value in zip(
        chart_days,
        [100_000, 101_000, 100_500, 102_000, 103_000, 102_500, 104_000, 105_000],
    )]
    # An intraday update must not become a separate return observation.
    equity.insert(2, [chart_days[1] + 3_600, 101_200, 101_200, 101_200, 101_200])
    return {
        "algorithmConfiguration": {
            "name": "custom-sweden",
            "accountCurrency": "SEK",
            "startDate": "2024-01-01T00:00:00Z",
            "endDate": "2024-01-08T23:59:59Z",
            "tradingDaysPerYear": 252,
            "parameters": {"fast": "20", "slow": "100"},
        },
        "charts": {
            "Strategy Equity": {"series": {"Equity": {"values": equity}}},
            "Benchmark": {
                "series": {
                    "Benchmark": {
                        "values": [[timestamp, value] for timestamp, value in zip(
                            chart_days,
                            [0.0, 0.2, -0.1, 0.1, 0.0, 0.3, -0.2, 0.1],
                        )]
                    }
                }
            },
            "Exposure": {
                "series": {
                    "Equity - Long Ratio": {
                        "values": [[timestamp, 0.5] for timestamp in chart_days]
                    }
                }
            },
            "Portfolio Margin": {
                "series": {
                    "AAA": {"values": [[timestamp, 0.35] for timestamp in chart_days]},
                    "BBB": {"values": [[timestamp, 0.15] for timestamp in chart_days]},
                    "OTHERS": {"values": [[timestamp, 0.5] for timestamp in chart_days]},
                }
            },
            "Asset Returns": {
                "series": {
                    "AAA": {"values": [[chart_days[1], 0.01], [chart_days[2], 0.02]]},
                    "BBB": {"values": [[chart_days[2], -0.01]]},
                }
            },
            "Asset Weights": {
                "series": {
                    "AAA": {"values": [[chart_days[1], 1.0], [chart_days[2], 0.6]]},
                    "BBB": {"values": [[chart_days[2], 0.4]]},
                }
            },
        },
        "orders": {
            "1": {
                "id": 1,
                "symbol": {"value": "AAA", "id": "AAA CUSTOM900SID"},
                "time": "2024-01-02T09:00:00Z",
                "lastFillTime": "2024-01-02T09:00:00Z",
                "quantity": 10,
                "price": 100,
                "priceCurrency": "SEK",
                "status": 3,
                "tag": "entry",
            }
        },
        "statistics": {
            "Net Profit": "5.000%",
            "Compounding Annual Return": "12.000%",
            "Sharpe Ratio": "1.2",
            "Drawdown": "2.000%",
            "Total Orders": "1",
            "Win Rate": "100%",
        },
        "runtimeStatistics": {"Equity": "SEK105,000"},
        "totalPerformance": {
            "closedTrades": [
                {
                    "symbols": [{"value": "AAA", "id": "AAA CUSTOM900SID"}],
                    "entryTime": "2024-01-02T09:00:00Z",
                    "exitTime": "2024-01-08T09:00:00Z",
                    "entryPrice": 100,
                    "exitPrice": 105,
                    "direction": 0,
                    "quantity": 10,
                    "profitLoss": 50,
                    "totalFees": 0,
                    "mae": 10,
                    "mfe": 60,
                    "isWin": True,
                }
            ],
            "portfolioStatistics": {},
            "tradeStatistics": {},
        },
    }


def test_bt_report_reads_original_lean_result_without_sid_decoding(tmp_path):
    source = tmp_path / "result.json"
    source.write_text(json.dumps(_lean_result()), encoding="utf-8")

    result = q.bt.report(source)

    assert isinstance(result, q.bt.BacktestReport)
    assert result.title == "custom-sweden"
    assert len(result.equity) == 6
    assert len(result.returns) == 5
    assert result.orders.loc[0, "symbol"] == "AAA"
    assert result.trades.loc[0, "symbol"] == "AAA"
    assert result.trades.loc[0, "direction"] == 1
    assert result.trades.loc[0, "return"] == pytest.approx(0.05)
    assert result.trade_statistics.loc["Trades", "All"] == 1
    assert result.trade_excursions is not None
    assert result.trade_returns is not None
    assert result.configuration["accountCurrency"] == "SEK"
    assert result.diagnostics is not None
    assert result.margin_allocation is not None
    assert result.performance_treemap is not None
    assert list(result.performance_treemap.frames[0].data[0].labels) == ["AAA"]
    assert list(result.performance_treemap.frames[1].data[0].labels) == ["AAA", "BBB"]
    assert list(result.performance_treemap.frames[1].data[0].values) == [0.8, 0.2]
    assert list(result.performance_treemap.frames[1].data[0].customdata) == pytest.approx([0.0302, -0.01])
    assert result.trade_returns.layout.title.text == "Returns per Trade"
    assert result.trade_returns.data[0].type == "bar"
    assert "Confidence That Sharpe Exceeds Threshold" in [annotation.text for annotation in result.figure.layout.annotations]
    assert "Confidence That Sortino Exceeds Threshold" in [annotation.text for annotation in result.figure.layout.annotations]
    psr_trace = next(trace for trace in result.figure.data if trace.name == "PSR")
    psor_trace = next(trace for trace in result.figure.data if trace.name == "PSoR")
    assert psr_trace.x[0] == 0.0
    assert psr_trace.x[-1] >= 3.0
    assert psr_trace.y[0] >= psr_trace.y[-1]
    assert psor_trace.x[0] == 0.0
    assert psor_trace.x[-1] >= 3.0


def test_bt_report_selects_latest_completed_result_from_directory(tmp_path):
    backtests = tmp_path / "backtests"
    older = backtests / "2024-01-01_10-00-00"
    latest = backtests / "2024-01-02_10-00-00"
    incomplete = backtests / "2024-01-03_10-00-00"
    older.mkdir(parents=True)
    latest.mkdir()
    incomplete.mkdir()

    older_result = deepcopy(_lean_result())
    older_result["algorithmConfiguration"]["name"] = "older"
    (older / "111.json").write_text(json.dumps(older_result), encoding="utf-8")
    latest_result = deepcopy(_lean_result())
    latest_result["algorithmConfiguration"]["name"] = "latest"
    (latest / "222.json").write_text(json.dumps(latest_result), encoding="utf-8")
    (latest / "222-summary.json").write_text(json.dumps({"charts": {}}), encoding="utf-8")
    (incomplete / "data-monitor-report.json").write_text(json.dumps({"status": "running"}), encoding="utf-8")

    result = q.bt.report(backtests)

    assert result.title == "latest"
    assert result.source == latest / "222.json"


def test_bt_report_accepts_timestamp_directory(tmp_path):
    run = tmp_path / "2024-01-02_10-00-00"
    run.mkdir()
    source = run / "222.json"
    source.write_text(json.dumps(_lean_result()), encoding="utf-8")

    assert q.bt.report(run).source == source


def test_bt_report_directory_requires_completed_result(tmp_path):
    with pytest.raises(FileNotFoundError, match="No completed LEAN result JSON"):
        q.bt.report(tmp_path)


def test_bt_report_writes_self_contained_html(tmp_path):
    destination = tmp_path / "report.html"

    result = q.bt.report(
        _lean_result(),
        title="Stockholm strategy",
        description="Native report for custom market 900",
        output=destination,
    )

    html = destination.read_text(encoding="utf-8")
    assert result.save(destination) == destination
    assert "<!doctype html>" in html
    assert "Stockholm strategy" in html
    assert "Native report for custom market 900" in html
    assert "<span>CAGR</span>" in html
    assert "<span>PSR @ Th = 0</span>" in html
    assert "<span>PSoR @ Th = 0</span>" in html
    assert "<span>Sortino</span>" in html
    assert "<span>Calmar</span>" in html
    assert "<span>Volatility</span>" in html
    assert html.count('class="card ') == 11
    assert "grid-template-columns: repeat(auto-fit, minmax(108px, 1fr))" in html
    assert "min-height: 108px" in html
    assert "plotly.js" in html
    assert "Closed Trades" in html
    assert "Trade Analytics" in html
    assert "Latest Portfolio Margin Usage" in html
    assert "margin usage, not market-value asset allocation" in html
    assert "AAA" in html
    assert "CUSTOM900SID" not in html


def test_bt_report_embeds_supplied_asset_performance_treemap():
    index = pd.date_range("2024-01-02", periods=3)
    asset_returns = pd.DataFrame(
        {"AAA": [0.01, 0.02, float("nan")], "BBB": [float("nan"), -0.01, 0.03]},
        index=index,
    )

    result = q.bt.report(_lean_result(), asset_returns=asset_returns)
    html = result.to_html()

    assert result.performance_treemap is not None
    assert result.performance_treemap.layout.title.text == "Portfolio Performance Treemap"
    assert "Portfolio Performance Treemap" in html
    assert "As of " in html
    assert "Plotly.animate(document.getElementById" not in html


def test_bt_report_displays_in_isolated_iframe(monkeypatch):
    displayed = []

    def capture(value, **kwargs):
        displayed.append((value, kwargs))

    monkeypatch.setattr("IPython.display.display", capture)
    result = q.bt.report(_lean_result(), title="Stockholm strategy")

    assert result.display(height=720) is None
    assert len(displayed) == 1
    value, kwargs = displayed[0]
    html = value["text/html"]
    assert kwargs == {"raw": True}
    assert html.startswith('<div class="qrt-backtest-report" style="width:100%"></div><script>')
    assert 'document.createElement("iframe")' in html
    assert "frame.srcdoc" in html
    assert "<iframe" not in html
    assert "height:720px" in html
    assert "<style>" not in html


def test_bt_report_rejects_non_lean_json():
    with pytest.raises(ValueError, match="Not a supported LEAN result"):
        q.bt.report({"charts": {}})


def test_bt_report_exposes_naive_daily_datetime_index():
    result = q.bt.report(_lean_result())

    assert isinstance(result.returns.index, pd.DatetimeIndex)
    assert result.returns.index.tz is None
