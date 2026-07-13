# {py:mod}`qrt.plot.core`

```{py:module} qrt.plot.core
```

```{autodoc2-docstring} qrt.plot.core
:parser: docstring_parser
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`infer_periods_per_year <qrt.plot.core.infer_periods_per_year>`
  - ```{autodoc2-docstring} qrt.plot.core.infer_periods_per_year
    :parser: docstring_parser
    :summary:
    ```
* - {py:obj}`performance <qrt.plot.core.performance>`
  - ```{autodoc2-docstring} qrt.plot.core.performance
    :parser: docstring_parser
    :summary:
    ```
* - {py:obj}`rolling_volatility <qrt.plot.core.rolling_volatility>`
  - ```{autodoc2-docstring} qrt.plot.core.rolling_volatility
    :parser: docstring_parser
    :summary:
    ```
* - {py:obj}`rolling_sharpe <qrt.plot.core.rolling_sharpe>`
  - ```{autodoc2-docstring} qrt.plot.core.rolling_sharpe
    :parser: docstring_parser
    :summary:
    ```
* - {py:obj}`rolling_beta <qrt.plot.core.rolling_beta>`
  - ```{autodoc2-docstring} qrt.plot.core.rolling_beta
    :parser: docstring_parser
    :summary:
    ```
* - {py:obj}`rolling_alpha <qrt.plot.core.rolling_alpha>`
  - ```{autodoc2-docstring} qrt.plot.core.rolling_alpha
    :parser: docstring_parser
    :summary:
    ```
* - {py:obj}`monthly_returns <qrt.plot.core.monthly_returns>`
  - ```{autodoc2-docstring} qrt.plot.core.monthly_returns
    :parser: docstring_parser
    :summary:
    ```
* - {py:obj}`monthly_heatmap <qrt.plot.core.monthly_heatmap>`
  - ```{autodoc2-docstring} qrt.plot.core.monthly_heatmap
    :parser: docstring_parser
    :summary:
    ```
* - {py:obj}`benchmark_stats <qrt.plot.core.benchmark_stats>`
  - ```{autodoc2-docstring} qrt.plot.core.benchmark_stats
    :parser: docstring_parser
    :summary:
    ```
* - {py:obj}`col <qrt.plot.core.col>`
  - ```{autodoc2-docstring} qrt.plot.core.col
    :parser: docstring_parser
    :summary:
    ```
* - {py:obj}`equity <qrt.plot.core.equity>`
  - ```{autodoc2-docstring} qrt.plot.core.equity
    :parser: docstring_parser
    :summary:
    ```
* - {py:obj}`drawdown <qrt.plot.core.drawdown>`
  - ```{autodoc2-docstring} qrt.plot.core.drawdown
    :parser: docstring_parser
    :summary:
    ```
* - {py:obj}`plot <qrt.plot.core.plot>`
  - ```{autodoc2-docstring} qrt.plot.core.plot
    :parser: docstring_parser
    :summary:
    ```
* - {py:obj}`tearsheet <qrt.plot.core.tearsheet>`
  - ```{autodoc2-docstring} qrt.plot.core.tearsheet
    :parser: docstring_parser
    :summary:
    ```
* - {py:obj}`show <qrt.plot.core.show>`
  - ```{autodoc2-docstring} qrt.plot.core.show
    :parser: docstring_parser
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`ReturnType <qrt.plot.core.ReturnType>`
  - ```{autodoc2-docstring} qrt.plot.core.ReturnType
    :parser: docstring_parser
    :summary:
    ```
````

### API

````{py:data} ReturnType
:canonical: qrt.plot.core.ReturnType
:value: >
   None

```{autodoc2-docstring} qrt.plot.core.ReturnType
:parser: docstring_parser
```

````

````{py:function} infer_periods_per_year(index: pandas.Index) -> int
:canonical: qrt.plot.core.infer_periods_per_year

```{autodoc2-docstring} qrt.plot.core.infer_periods_per_year
:parser: docstring_parser
```
````

````{py:function} performance(returns: pandas.Series, *, return_type: qrt.plot.core.ReturnType = 'simple', periods_per_year: int | None = None) -> pandas.Series
:canonical: qrt.plot.core.performance

```{autodoc2-docstring} qrt.plot.core.performance
:parser: docstring_parser
```
````

````{py:function} rolling_volatility(returns: pandas.Series, window: int = 63, *, return_type: qrt.plot.core.ReturnType = 'simple', periods_per_year: int | None = None) -> pandas.Series
:canonical: qrt.plot.core.rolling_volatility

```{autodoc2-docstring} qrt.plot.core.rolling_volatility
:parser: docstring_parser
```
````

````{py:function} rolling_sharpe(returns: pandas.Series, window: int = 63, *, return_type: qrt.plot.core.ReturnType = 'simple', periods_per_year: int | None = None) -> pandas.Series
:canonical: qrt.plot.core.rolling_sharpe

```{autodoc2-docstring} qrt.plot.core.rolling_sharpe
:parser: docstring_parser
```
````

````{py:function} rolling_beta(returns: pandas.Series, benchmark: pandas.Series, window: int = 63, *, return_type: qrt.plot.core.ReturnType = 'simple') -> pandas.Series
:canonical: qrt.plot.core.rolling_beta

```{autodoc2-docstring} qrt.plot.core.rolling_beta
:parser: docstring_parser
```
````

````{py:function} rolling_alpha(returns: pandas.Series, benchmark: pandas.Series, window: int = 63, *, return_type: qrt.plot.core.ReturnType = 'simple', periods_per_year: int | None = None) -> pandas.Series
:canonical: qrt.plot.core.rolling_alpha

```{autodoc2-docstring} qrt.plot.core.rolling_alpha
:parser: docstring_parser
```
````

````{py:function} monthly_returns(returns: pandas.Series, *, return_type: qrt.plot.core.ReturnType = 'simple') -> pandas.DataFrame
:canonical: qrt.plot.core.monthly_returns

```{autodoc2-docstring} qrt.plot.core.monthly_returns
:parser: docstring_parser
```
````

````{py:function} monthly_heatmap(returns: pandas.Series, *, return_type: qrt.plot.core.ReturnType = 'simple', title: str = 'Monthly returns', height: int | None = None) -> plotly.graph_objects.Figure
:canonical: qrt.plot.core.monthly_heatmap

```{autodoc2-docstring} qrt.plot.core.monthly_heatmap
:parser: docstring_parser
```
````

````{py:function} benchmark_stats(returns: pandas.Series, benchmark: pandas.Series, *, return_type: qrt.plot.core.ReturnType = 'simple', periods_per_year: int | None = None) -> pandas.Series
:canonical: qrt.plot.core.benchmark_stats

```{autodoc2-docstring} qrt.plot.core.benchmark_stats
:parser: docstring_parser
```
````

````{py:function} col(data: pandas.Series | pandas.DataFrame, columns: str | collections.abc.Iterable[str] | None = None, *, title: str | None = None, ylabel: str | None = None, height: int = 450) -> plotly.graph_objects.Figure
:canonical: qrt.plot.core.col

```{autodoc2-docstring} qrt.plot.core.col
:parser: docstring_parser
```
````

````{py:function} equity(returns: pandas.Series, *, return_type: qrt.plot.core.ReturnType = 'simple', title: str = 'Equity curve', label: str | None = None, height: int = 450) -> plotly.graph_objects.Figure
:canonical: qrt.plot.core.equity

```{autodoc2-docstring} qrt.plot.core.equity
:parser: docstring_parser
```
````

````{py:function} drawdown(returns: pandas.Series, *, return_type: qrt.plot.core.ReturnType = 'simple', title: str = 'Drawdown', height: int = 320) -> plotly.graph_objects.Figure
:canonical: qrt.plot.core.drawdown

```{autodoc2-docstring} qrt.plot.core.drawdown
:parser: docstring_parser
```
````

````{py:function} plot(returns: pandas.Series, *, benchmark: pandas.Series | None = None, return_type: qrt.plot.core.ReturnType = 'simple', periods_per_year: int | None = None, title: str | None = None, height: int = 700) -> plotly.graph_objects.Figure
:canonical: qrt.plot.core.plot

```{autodoc2-docstring} qrt.plot.core.plot
:parser: docstring_parser
```
````

````{py:function} tearsheet(returns: pandas.Series, **kwargs: object) -> plotly.graph_objects.Figure
:canonical: qrt.plot.core.tearsheet

```{autodoc2-docstring} qrt.plot.core.tearsheet
:parser: docstring_parser
```
````

````{py:function} show(figure: object, name: str | None = None, *, save_to: str | None = None, formats: collections.abc.Iterable[str] = ('png', ), width: int = 1400, height: int = 800, scale: int = 2) -> None
:canonical: qrt.plot.core.show

```{autodoc2-docstring} qrt.plot.core.show
:parser: docstring_parser
```
````
