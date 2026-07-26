"""Native reports for backtest result artifacts."""

from __future__ import annotations

from base64 import b64encode
from collections.abc import Mapping
from dataclasses import dataclass, field
from html import escape
import json
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
from plotly.io import to_html as plotly_to_html
from plotly.subplots import make_subplots

from qrt.plot import mae_mfe, report as returns_report, trade_distribution
from qrt.stats import trade_stats


JsonObject = Mapping[str, Any]

_LEAN_REQUIRED_KEYS = frozenset({"charts", "orders", "statistics", "totalPerformance"})
_DIRECTION = {0: 1, 1: -1}
_DIAGNOSTIC_SERIES = (
    ("Exposure", ("Equity - Long Ratio", "Equity - Short Ratio"), "Exposure", ".0%"),
    ("Portfolio Turnover", ("Portfolio Turnover",), "Turnover", ".1%"),
    ("Capacity", ("Strategy Capacity",), "Capacity", None),
)
_HEADLINE_STATISTICS = (
    "Net Profit",
    "Compounding Annual Return",
    "Sharpe Ratio",
    "Drawdown",
    "Total Orders",
    "Win Rate",
)
_STATISTIC_LABELS = {
    "Compounding Annual Return": "CAGR",
}
_REPORT_BLUE = "#58B4E9"
_REPORT_GRAY = "#AEB8BD"
_REPORT_ORANGE = "#F5A623"
_REPORT_FILLS = {
    _REPORT_BLUE: "rgba(88, 180, 233, 0.60)",
    _REPORT_GRAY: "rgba(174, 184, 189, 0.60)",
    _REPORT_ORANGE: "rgba(245, 166, 35, 0.60)",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _result_in_directory(directory: Path) -> tuple[dict[str, Any], Path] | None:
    """Return the deterministic LEAN result candidate directly in a directory."""
    candidates: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(directory.glob("*.json")):
        try:
            value = _load_json(path)
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(value, dict) and _LEAN_REQUIRED_KEYS <= value.keys():
            candidates.append((path, value))
    if not candidates:
        return None
    path, result = max(candidates, key=lambda item: (item[0].stat().st_mtime_ns, item[0].name))
    return result, path


def _latest_result(directory: Path) -> tuple[dict[str, Any], Path]:
    """Find the newest completed LEAN result below a backtests directory."""
    if not directory.is_dir():
        raise FileNotFoundError(f"Backtest directory does not exist: {directory}")

    direct = _result_in_directory(directory)
    if direct is not None:
        return direct

    subdirectories = sorted(
        (path for path in directory.iterdir() if path.is_dir()),
        key=lambda path: (path.name, path.stat().st_mtime_ns),
        reverse=True,
    )
    for subdirectory in subdirectories:
        candidate = _result_in_directory(subdirectory)
        if candidate is not None:
            return candidate
    raise FileNotFoundError(f"No completed LEAN result JSON found in: {directory}")


def _read_result(source: str | Path | JsonObject) -> tuple[dict[str, Any], Path | None]:
    if isinstance(source, Mapping):
        result = dict(source)
        path = None
    else:
        path = Path(source)
        if path.suffix.lower() == ".json":
            result = _load_json(path)
        else:
            result, path = _latest_result(path)
    if not isinstance(result, dict):
        raise ValueError("Backtest result must be a JSON object")
    missing = sorted(_LEAN_REQUIRED_KEYS - result.keys())
    if missing:
        raise ValueError(f"Not a supported LEAN result: missing top-level keys {missing}")
    return result, path


def _series_values(result: JsonObject, chart: str, series: str) -> pd.Series:
    """Extract one LEAN chart series, using the close for OHLC chart points."""
    try:
        values = result["charts"][chart]["series"][series]["values"]
    except KeyError:
        return pd.Series(dtype=float, name=series)
    points: list[tuple[pd.Timestamp, float]] = []
    for point in values:
        if not isinstance(point, list) or len(point) < 2:
            continue
        timestamp = pd.to_datetime(point[0], unit="s", utc=True)
        value = point[-1] if len(point) >= 5 else point[1]
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            continue
        if pd.isna(numeric_value):
            continue
        points.append((timestamp, numeric_value))
    if not points:
        return pd.Series(dtype=float, name=series)
    extracted = pd.Series(
        (value for _, value in points),
        index=pd.DatetimeIndex(timestamp for timestamp, _ in points),
        name=series,
        dtype=float,
    )
    return extracted.groupby(level=0).last().sort_index()


def _returns(result: JsonObject) -> tuple[pd.Series, pd.Series, pd.Series | None]:
    raw_equity = _series_values(result, "Strategy Equity", "Equity")
    if raw_equity.empty:
        raise ValueError("LEAN result has no Strategy Equity / Equity chart values")
    observations_per_day = raw_equity.groupby(raw_equity.index.normalize()).size()
    equity = raw_equity.resample("1D").last().dropna()
    # LEAN's equity chart can contain one calendar snapshot every day plus a
    # second observation on actual exchange sessions. Prefer those session
    # dates when present, which excludes weekends and exchange holidays without
    # interpreting the result's market/SID.
    session_days = observations_per_day[observations_per_day > 1].index
    if len(session_days) >= 2:
        equity = equity[equity.index.normalize().isin(session_days)]
    else:
        periods_per_year = (result.get("algorithmConfiguration") or {}).get("tradingDaysPerYear")
        if periods_per_year and int(periods_per_year) <= 260:
            equity = equity[equity.index.weekday < 5]
    equity.index = equity.index.tz_convert(None)
    equity = equity.rename("Equity")
    returns = equity.pct_change(fill_method=None).dropna().rename("Strategy")

    benchmark = _series_values(result, "Benchmark", "Benchmark")
    if benchmark.empty:
        return equity, returns, None
    # LEAN's Benchmark chart is stored in percentage points per observation.
    benchmark = benchmark.resample("1D").sum().div(100.0)
    benchmark.index = benchmark.index.tz_convert(None)
    benchmark = benchmark.rename("Benchmark")
    benchmark = benchmark.reindex(returns.index).fillna(0.0)
    if benchmark.nunique() <= 1:
        return equity, returns, None
    return equity, returns, benchmark


def _symbol_value(value: Any) -> str:
    if isinstance(value, Mapping):
        return str(value.get("value") or value.get("permtick") or "")
    return str(value or "")


def _orders(result: JsonObject) -> pd.DataFrame:
    rows = []
    for order in result.get("orders", {}).values():
        quantity = float(order.get("quantity", 0.0))
        rows.append(
            {
                "id": order.get("id"),
                "symbol": _symbol_value(order.get("symbol")),
                "time": pd.to_datetime(order.get("time"), utc=True),
                "fill_time": pd.to_datetime(order.get("lastFillTime"), utc=True),
                "direction": "buy" if quantity > 0 else "sell" if quantity < 0 else "hold",
                "quantity": quantity,
                "price": float(order.get("price", 0.0)),
                "currency": order.get("priceCurrency", ""),
                "status": order.get("status"),
                "tag": order.get("tag", ""),
            }
        )
    if not rows:
        return pd.DataFrame(
            columns=("id", "symbol", "time", "fill_time", "direction", "quantity", "price", "currency", "status", "tag")
        )
    return pd.DataFrame(rows).sort_values(["time", "id"], ignore_index=True)


def _closed_trades(result: JsonObject) -> pd.DataFrame:
    rows = []
    for trade in result.get("totalPerformance", {}).get("closedTrades", []):
        entry_price = float(trade.get("entryPrice", 0.0))
        quantity = abs(float(trade.get("quantity", 0.0)))
        notional = entry_price * quantity
        profit_loss = float(trade.get("profitLoss", 0.0))
        symbols = trade.get("symbols", [])
        symbol = _symbol_value(symbols[0]) if symbols else ""
        rows.append(
            {
                "symbol": symbol,
                "entry_time": pd.to_datetime(trade.get("entryTime"), utc=True),
                "exit_time": pd.to_datetime(trade.get("exitTime"), utc=True),
                "direction": _DIRECTION.get(trade.get("direction"), 1),
                "entry_reason": "",
                "exit_reason": "",
                "entry_price": entry_price,
                "exit_price": float(trade.get("exitPrice", 0.0)),
                "return": profit_loss / notional if notional else 0.0,
                "mae": float(trade.get("mae", 0.0)) / notional if notional else 0.0,
                "mfe": float(trade.get("mfe", 0.0)) / notional if notional else 0.0,
                "size": quantity,
                "fees": float(trade.get("totalFees", 0.0)),
                "profit_loss": profit_loss,
                "is_win": bool(trade.get("isWin", profit_loss > 0)),
            }
        )
    if not rows:
        return pd.DataFrame(
            columns=(
                "symbol", "entry_time", "exit_time", "direction", "entry_reason", "exit_reason",
                "entry_price", "exit_price", "return", "mae", "mfe", "size", "fees",
                "profit_loss", "is_win",
            )
        )
    return pd.DataFrame(rows).sort_values("exit_time", ignore_index=True)


def _diagnostics_figure(result: JsonObject) -> go.Figure | None:
    panels: list[tuple[str, list[tuple[pd.Series, str, str | None]], str, str | None]] = []
    long = _series_values(result, "Exposure", "Equity - Long Ratio")
    short = _series_values(result, "Exposure", "Equity - Short Ratio")
    if not long.empty or not short.empty:
        exposure = pd.concat((long, short), axis=1).fillna(0.0)
        gross = exposure.abs().sum(axis=1).rename("Gross Exposure")
        panels.append(("Gross Exposure", [(gross, _REPORT_BLUE, "tozeroy")], "Exposure", ".0%"))
        directional: list[tuple[pd.Series, str, str | None]] = []
        if not long.empty:
            directional.append((long.rename("Long"), _REPORT_ORANGE, "tozeroy"))
        if not short.empty:
            directional.append(((-short.abs()).rename("Short"), _REPORT_GRAY, "tozeroy"))
        panels.append(("Long / Short Exposure", directional, "Exposure", ".0%"))

    for chart, names, axis_title, tickformat in _DIAGNOSTIC_SERIES[1:]:
        collection = [_series_values(result, chart, name) for name in names]
        collection = [series for series in collection if not series.empty and series.abs().max() > 0]
        if collection:
            panels.append((
                chart,
                [(series, _REPORT_ORANGE, "tozeroy" if chart == "Portfolio Turnover" else None) for series in collection],
                axis_title,
                tickformat,
            ))
    if not panels:
        return None

    figure = make_subplots(
        rows=len(panels),
        cols=1,
        shared_xaxes=True,
        subplot_titles=[title for title, _, _, _ in panels],
        vertical_spacing=0.12,
    )
    for row, (_, collection, axis_title, tickformat) in enumerate(panels, start=1):
        for series, color, fill in collection:
            figure.add_scatter(
                x=series.index,
                y=series,
                mode="lines",
                name=str(series.name),
                line={"color": color, "width": 1.5},
                fill=fill,
                fillcolor=_REPORT_FILLS.get(color) if fill else None,
                row=row,
                col=1,
            )
        figure.add_hline(y=0, line={"color": "#CBD5E1", "width": 1}, row=row, col=1)
        figure.update_yaxes(title_text=axis_title, tickformat=tickformat, row=row, col=1)
    figure.update_layout(
        template="plotly_white",
        title="Backtest Diagnostics",
        height=270 * len(panels) + 80,
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.02, "x": 0},
        margin={"l": 70, "r": 30, "t": 90, "b": 50},
        font={"family": "Inter, ui-sans-serif, system-ui, sans-serif", "color": "#1F2937"},
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    figure.update_xaxes(showgrid=False)
    figure.update_yaxes(showgrid=True, gridcolor="#E5E7EB", zeroline=False)
    return figure


def _margin_allocation_figure(result: JsonObject) -> go.Figure | None:
    """Summarize the latest positive Portfolio Margin values by asset."""
    chart = result.get("charts", {}).get("Portfolio Margin", {})
    raw_series = chart.get("series", {}) if isinstance(chart, Mapping) else {}
    values: dict[str, float] = {}
    for name in raw_series:
        series = _series_values(result, "Portfolio Margin", str(name)).dropna()
        if not series.empty and float(series.iloc[-1]) > 0:
            values[str(name)] = float(series.iloc[-1])
    if not values:
        return None

    ordered = sorted(values.items(), key=lambda item: item[1], reverse=True)
    named = [(name, value) for name, value in ordered if name.upper() != "OTHERS"]
    pregrouped_other = sum(value for name, value in ordered if name.upper() == "OTHERS")
    shown = named[:6]
    other = pregrouped_other + sum(value for _, value in named[6:])
    if other:
        shown.append(("Others", other))
    labels, amounts = zip(*shown)
    colors = ("#E58E26", "#F5A623", "#F7B955", "#F9CA83", "#FAD9AA", "#FCE7C8", "#D9DEE2")
    figure = go.Figure(go.Pie(
        labels=labels,
        values=amounts,
        hole=0.58,
        sort=False,
        marker={"colors": colors[:len(labels)], "line": {"color": "white", "width": 1}},
        textinfo="label+percent",
        hovertemplate="%{label}<br>%{value:.3f}<br>%{percent}<extra></extra>",
    ))
    figure.update_layout(
        template="plotly_white",
        title="Latest Portfolio Margin Usage",
        height=460,
        margin={"l": 30, "r": 30, "t": 75, "b": 30},
        font={"family": "Inter, ui-sans-serif, system-ui, sans-serif", "color": "#1F2937"},
        showlegend=False,
    )
    return figure


def _table(frame: pd.DataFrame, *, limit: int | None = None) -> str:
    if frame.empty:
        return '<p class="empty">No data recorded.</p>'
    shown = frame.tail(limit) if limit is not None else frame
    display = shown.copy()
    for column in display.columns:
        if pd.api.types.is_datetime64_any_dtype(display[column]):
            display[column] = display[column].dt.strftime("%Y-%m-%d %H:%M")
        elif column in {"return", "mae", "mfe"}:
            display[column] = display[column].map(lambda value: f"{value:.2%}")
        elif pd.api.types.is_float_dtype(display[column]):
            display[column] = display[column].map(lambda value: f"{value:,.4f}")
    headers = "".join(f"<th>{escape(str(column).replace('_', ' ').title())}</th>" for column in display.columns)
    body = "".join(
        "<tr>" + "".join(f"<td>{escape(str(value))}</td>" for value in row) + "</tr>"
        for row in display.itertuples(index=False, name=None)
    )
    note = ""
    if limit is not None and len(frame) > limit:
        note = f'<p class="table-note">Showing the latest {limit:,} of {len(frame):,} rows.</p>'
    return f'{note}<div class="table-scroll"><table><thead><tr>{headers}</tr></thead><tbody>{body}</tbody></table></div>'


def _mapping_table(values: Mapping[str, Any]) -> str:
    frame = pd.DataFrame(
        ((str(key), json.dumps(value) if isinstance(value, (dict, list)) else value) for key, value in values.items()),
        columns=("Name", "Value"),
    )
    return _table(frame)


@dataclass(slots=True)
class BacktestReport:
    """A normalized LEAN backtest plus its qrt-native report renderings."""

    title: str
    description: str
    source: Path | None
    equity: pd.Series
    returns: pd.Series
    benchmark: pd.Series | None
    statistics: dict[str, Any]
    runtime_statistics: dict[str, Any]
    parameters: dict[str, Any]
    configuration: dict[str, Any]
    orders: pd.DataFrame
    trades: pd.DataFrame
    trade_statistics: pd.DataFrame
    figure: go.Figure
    diagnostics: go.Figure | None = None
    margin_allocation: go.Figure | None = None
    trade_excursions: go.Figure | None = None
    trade_returns: go.Figure | None = None
    _raw: dict[str, Any] = field(default_factory=dict, repr=False)

    def to_html(self) -> str:
        """Render a standalone HTML document with embedded Plotly.js."""
        card_kinds = {
            "Net Profit": "positive",
            "Compounding Annual Return": "positive",
            "Sharpe Ratio": "positive",
            "Drawdown": "risk",
            "Win Rate": "positive",
        }
        cards = "".join(
            (
                f'<div class="card {card_kinds.get(name, "neutral")}">'
                f"<span>{escape(_STATISTIC_LABELS.get(name, name))}</span>"
                f"<strong>{escape(str(self.statistics.get(name, '—')))}</strong>"
                "</div>"
            )
            for name in _HEADLINE_STATISTICS
        )
        config_bits = [
            self.configuration.get("accountCurrency"),
            self.configuration.get("startDate", "")[:10],
            self.configuration.get("endDate", "")[:10],
        ]
        subtitle = " · ".join(str(bit) for bit in config_bits if bit)
        tearsheet = plotly_to_html(
            self.figure,
            full_html=False,
            include_plotlyjs=True,
            config={"responsive": True, "displaylogo": False},
        )
        diagnostics = (
            plotly_to_html(
                self.diagnostics,
                full_html=False,
                include_plotlyjs=False,
                config={"responsive": True, "displaylogo": False},
            )
            if self.diagnostics is not None
            else ""
        )
        margin_allocation = (
            plotly_to_html(
                self.margin_allocation,
                full_html=False,
                include_plotlyjs=False,
                config={"responsive": True, "displaylogo": False},
            )
            if self.margin_allocation is not None
            else ""
        )
        trade_figures = "".join(
            plotly_to_html(
                figure,
                full_html=False,
                include_plotlyjs=False,
                config={"responsive": True, "displaylogo": False},
            )
            for figure in (self.trade_excursions, self.trade_returns)
            if figure is not None
        )
        description = f"<p>{escape(self.description)}</p>" if self.description else ""
        source = f"<p class=\"source\">Source: {escape(str(self.source))}</p>" if self.source else ""
        return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(self.title)} · Backtest Report</title>
<style>
:root {{ color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #1f2937; background: #f3f4f6; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; }}
main {{ width: min(1500px, calc(100% - 32px)); margin: 24px auto 64px; }}
header, section {{ background: white; border: 1px solid #e5e7eb; border-radius: 14px; box-shadow: 0 1px 2px rgba(0,0,0,.04); }}
header {{ position: relative; overflow: hidden; padding: 30px 34px; margin-bottom: 18px; border-top: 4px solid #f5a623; }}
header::after {{ content: ""; position: absolute; inset: 0 0 auto auto; width: 32%; height: 100%; background: linear-gradient(135deg, transparent, rgba(88,180,233,.09)); pointer-events: none; }}
h1 {{ margin: 0 0 8px; font-size: 30px; }}
h2 {{ margin: 0 0 18px; font-size: 21px; }}
p {{ color: #4b5563; }}
.subtitle, .source {{ margin: 5px 0; font-size: 14px; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin: 18px 0; }}
.card {{ background: white; border: 1px solid #e5e7eb; border-top: 3px solid #94a3b8; border-radius: 12px; padding: 16px; }}
.card.positive {{ border-top-color: #58b4e9; }}
.card.risk {{ border-top-color: #f5a623; }}
.card span {{ display: block; color: #6b7280; font-size: 13px; margin-bottom: 7px; }}
.card strong {{ font-size: 21px; }}
section {{ padding: 24px; margin: 18px 0; overflow: hidden; }}
.plot {{ padding: 4px; }}
.table-scroll {{ overflow: auto; max-height: 540px; border: 1px solid #e5e7eb; border-radius: 9px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th {{ position: sticky; top: 0; background: #475569; color: white; text-align: left; z-index: 1; }}
th, td {{ padding: 9px 11px; border-bottom: 1px solid #e5e7eb; white-space: nowrap; }}
tbody tr:nth-child(even) {{ background: #f8fafc; }}
tbody tr:hover {{ background: #eef6fb; }}
.empty, .table-note {{ font-size: 13px; }}
.trade-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 520px), 1fr)); gap: 12px; }}
details > summary {{ cursor: pointer; font-weight: 650; font-size: 18px; }}
details > div {{ margin-top: 18px; }}
@media (max-width: 700px) {{ main {{ width: min(100% - 16px, 1500px); margin-top: 8px; }} header, section {{ border-radius: 9px; padding: 16px; }} }}
</style>
</head>
<body>
<main>
<header>
  <h1>{escape(self.title)}</h1>
  <p class="subtitle">{escape(subtitle)}</p>
  {description}
  {source}
</header>
<div class="cards">{cards}</div>
<section class="plot">{tearsheet}</section>
{f'<section class="plot">{diagnostics}</section>' if diagnostics else ''}
{f'<section class="plot">{margin_allocation}<p class="chart-note">Based on the latest positive values recorded in LEAN’s Portfolio Margin chart; this is margin usage, not market-value asset allocation.</p></section>' if margin_allocation else ''}
{f'<section><h2>Trade Analytics</h2><div class="trade-grid">{trade_figures}</div>{_table(self.trade_statistics.reset_index(names="Metric"))}</section>' if trade_figures else ''}
<section><h2>Closed Trades</h2>{_table(self.trades, limit=500)}</section>
<section><h2>Orders</h2>{_table(self.orders, limit=500)}</section>
<section><details open><summary>LEAN Statistics</summary><div>{_mapping_table(self.statistics)}</div></details></section>
<section><details><summary>Algorithm Parameters</summary><div>{_mapping_table(self.parameters)}</div></details></section>
<section><details><summary>Runtime Statistics</summary><div>{_mapping_table(self.runtime_statistics)}</div></details></section>
</main>
</body>
</html>"""

    def display(
        self,
        *,
        width: str | int = "100%",
        height: str | int = 900,
    ) -> Any:
        """Display the report in an isolated iframe inside a notebook."""
        from IPython.display import display

        width_value = f"{width}px" if isinstance(width, int) else width
        height_value = f"{height}px" if isinstance(height, int) else height
        document = b64encode(self.to_html().encode("utf-8")).decode("ascii")
        output = (
            f'<div class="qrt-backtest-report" '
            f'style="width:{escape(width_value, quote=True)}"></div>'
            "<script>(() => {"
            "const host = document.currentScript.previousElementSibling;"
            'const frame = document.createElement("iframe");'
            f"frame.title = {json.dumps(self.title)};"
            "frame.srcdoc = new TextDecoder().decode("
            f'Uint8Array.from(atob("{document}"), c => c.charCodeAt(0)));'
            f"frame.style.cssText = {json.dumps(f'display:block;width:100%;height:{height_value};border:0')};"
            'frame.loading = "lazy";'
            "host.replaceChildren(frame);"
            "})();</script>"
        )
        return display({"text/html": output}, raw=True)

    def save(self, path: str | Path) -> Path:
        """Write the self-contained report HTML and return its path."""
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(self.to_html(), encoding="utf-8")
        return destination


def report(
    source: str | Path | JsonObject,
    *,
    title: str | None = None,
    description: str = "",
    output: str | Path | None = None,
) -> BacktestReport:
    """Create a native qrt report from an original LEAN backtest result.

    The adapter reads recorded result charts and tables directly. It never
    decodes LEAN security identifiers or replays orders, so custom markets are
    supported without preprocessing.

    Args:
        source: LEAN result JSON path, a backtests directory from which the
            newest completed result is selected, or an already loaded result
            mapping.
        title: Report title. Inferred from the project/configuration when omitted.
        description: Optional strategy description.
        output: Optional destination for a self-contained HTML report.

    Returns:
        A :class:`BacktestReport` containing normalized data and Plotly figures.
    """
    result, source_path = _read_result(source)
    configuration = dict(result.get("algorithmConfiguration") or {})
    equity, strategy_returns, benchmark = _returns(result)
    inferred_title = str(configuration.get("name") or "").strip()
    if not inferred_title or inferred_title == "local":
        inferred_title = source_path.parents[2].name if source_path is not None and len(source_path.parents) > 2 else "LEAN Backtest"
    periods_per_year = configuration.get("tradingDaysPerYear")
    figure = returns_report(
        strategy_returns,
        benchmark=benchmark,
        periods_per_year=int(periods_per_year) if periods_per_year else None,
        title=title or inferred_title,
    )
    trades = _closed_trades(result)
    normalized_trade_statistics = trade_stats(trades) if not trades.empty else pd.DataFrame()
    backtest_report = BacktestReport(
        title=title or inferred_title,
        description=description,
        source=source_path,
        equity=equity,
        returns=strategy_returns,
        benchmark=benchmark,
        statistics=dict(result.get("statistics") or {}),
        runtime_statistics=dict(result.get("runtimeStatistics") or {}),
        parameters=dict(configuration.get("parameters") or {}),
        configuration=configuration,
        orders=_orders(result),
        trades=trades,
        trade_statistics=normalized_trade_statistics,
        figure=figure,
        diagnostics=_diagnostics_figure(result),
        margin_allocation=_margin_allocation_figure(result),
        trade_excursions=mae_mfe(trades) if not trades.empty else None,
        trade_returns=trade_distribution(trades, by=None) if not trades.empty else None,
        _raw=result,
    )
    if output is not None:
        backtest_report.save(output)
    return backtest_report
