# {py:mod}`qrt.plot.interactive`

```{py:module} qrt.plot.interactive
```

```{autodoc2-docstring} qrt.plot.interactive
:parser: docstring_parser
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`line <qrt.plot.interactive.line>`
  - ```{autodoc2-docstring} qrt.plot.interactive.line
    :parser: docstring_parser
    :summary:
    ```
* - {py:obj}`equity <qrt.plot.interactive.equity>`
  - ```{autodoc2-docstring} qrt.plot.interactive.equity
    :parser: docstring_parser
    :summary:
    ```
* - {py:obj}`drawdown <qrt.plot.interactive.drawdown>`
  - ```{autodoc2-docstring} qrt.plot.interactive.drawdown
    :parser: docstring_parser
    :summary:
    ```
* - {py:obj}`performance <qrt.plot.interactive.performance>`
  - ```{autodoc2-docstring} qrt.plot.interactive.performance
    :parser: docstring_parser
    :summary:
    ```
* - {py:obj}`monthly_heatmap <qrt.plot.interactive.monthly_heatmap>`
  - ```{autodoc2-docstring} qrt.plot.interactive.monthly_heatmap
    :parser: docstring_parser
    :summary:
    ```
* - {py:obj}`show <qrt.plot.interactive.show>`
  - ```{autodoc2-docstring} qrt.plot.interactive.show
    :parser: docstring_parser
    :summary:
    ```
````

### API

````{py:function} line(data: pandas.Series | pandas.DataFrame, columns: str | collections.abc.Iterable[str] | None = None, *, title: str | None = None, yaxis_title: str | None = None, height: int = 450) -> plotly.graph_objects.Figure
:canonical: qrt.plot.interactive.line

```{autodoc2-docstring} qrt.plot.interactive.line
:parser: docstring_parser
```
````

````{py:function} equity(returns: pandas.Series, *, return_type: qrt.plot.core.ReturnType = 'simple', title: str = 'Equity curve', label: str | None = None, height: int = 450) -> plotly.graph_objects.Figure
:canonical: qrt.plot.interactive.equity

```{autodoc2-docstring} qrt.plot.interactive.equity
:parser: docstring_parser
```
````

````{py:function} drawdown(returns: pandas.Series, *, return_type: qrt.plot.core.ReturnType = 'simple', title: str = 'Drawdown', height: int = 320) -> plotly.graph_objects.Figure
:canonical: qrt.plot.interactive.drawdown

```{autodoc2-docstring} qrt.plot.interactive.drawdown
:parser: docstring_parser
```
````

````{py:function} performance(returns: pandas.Series, *, benchmark: pandas.Series | None = None, return_type: qrt.plot.core.ReturnType = 'simple', periods_per_year: int | None = None, title: str | None = None, height: int = 700) -> plotly.graph_objects.Figure
:canonical: qrt.plot.interactive.performance

```{autodoc2-docstring} qrt.plot.interactive.performance
:parser: docstring_parser
```
````

````{py:function} monthly_heatmap(returns: pandas.Series, *, return_type: qrt.plot.core.ReturnType = 'simple', title: str = 'Monthly returns', height: int | None = None) -> plotly.graph_objects.Figure
:canonical: qrt.plot.interactive.monthly_heatmap

```{autodoc2-docstring} qrt.plot.interactive.monthly_heatmap
:parser: docstring_parser
```
````

````{py:function} show(figure: plotly.graph_objects.Figure, name: str | None = None, *, save_to: str | pathlib.Path | None = None, formats: collections.abc.Iterable[str] = ('png', ), width: int = 1400, height: int = 800, scale: int = 2) -> None
:canonical: qrt.plot.interactive.show

```{autodoc2-docstring} qrt.plot.interactive.show
:parser: docstring_parser
```
````
