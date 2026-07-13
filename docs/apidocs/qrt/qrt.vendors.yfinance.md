# {py:mod}`qrt.vendors.yfinance`

```{py:module} qrt.vendors.yfinance
```

```{autodoc2-docstring} qrt.vendors.yfinance
:parser: docstring_parser
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`YFinanceVendor <qrt.vendors.yfinance.YFinanceVendor>`
  - ```{autodoc2-docstring} qrt.vendors.yfinance.YFinanceVendor
    :parser: docstring_parser
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <qrt.vendors.yfinance.logger>`
  - ```{autodoc2-docstring} qrt.vendors.yfinance.logger
    :parser: docstring_parser
    :summary:
    ```
````

### API

````{py:data} logger
:canonical: qrt.vendors.yfinance.logger
:value: >
   'getLogger(...)'

```{autodoc2-docstring} qrt.vendors.yfinance.logger
:parser: docstring_parser
```

````

`````{py:class} YFinanceVendor(cache_dir: str | pathlib.Path = DEFAULT_CACHE_DIR)
:canonical: qrt.vendors.yfinance.YFinanceVendor

Bases: {py:obj}`qrt.vendors.base.DataVendor`

```{autodoc2-docstring} qrt.vendors.yfinance.YFinanceVendor
:parser: docstring_parser
```

```{rubric} Initialization
```

```{autodoc2-docstring} qrt.vendors.yfinance.YFinanceVendor.__init__
:parser: docstring_parser
```

````{py:attribute} name
:canonical: qrt.vendors.yfinance.YFinanceVendor.name
:value: >
   'yfinance'

```{autodoc2-docstring} qrt.vendors.yfinance.YFinanceVendor.name
:parser: docstring_parser
```

````

````{py:method} fetch_ohlc(symbol: str, start_date: str | datetime.datetime, end_date: str | datetime.datetime, time_interval: str = '1D') -> pandas.DataFrame
:canonical: qrt.vendors.yfinance.YFinanceVendor.fetch_ohlc

```{autodoc2-docstring} qrt.vendors.yfinance.YFinanceVendor.fetch_ohlc
:parser: docstring_parser
```

````

`````
