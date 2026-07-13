# {py:mod}`qrt.vendors.base`

```{py:module} qrt.vendors.base
```

```{autodoc2-docstring} qrt.vendors.base
:parser: docstring_parser
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`DataVendor <qrt.vendors.base.DataVendor>`
  - ```{autodoc2-docstring} qrt.vendors.base.DataVendor
    :parser: docstring_parser
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`trades_to_ohlc <qrt.vendors.base.trades_to_ohlc>`
  - ```{autodoc2-docstring} qrt.vendors.base.trades_to_ohlc
    :parser: docstring_parser
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <qrt.vendors.base.logger>`
  - ```{autodoc2-docstring} qrt.vendors.base.logger
    :parser: docstring_parser
    :summary:
    ```
* - {py:obj}`DEFAULT_CACHE_DIR <qrt.vendors.base.DEFAULT_CACHE_DIR>`
  - ```{autodoc2-docstring} qrt.vendors.base.DEFAULT_CACHE_DIR
    :parser: docstring_parser
    :summary:
    ```
````

### API

````{py:data} logger
:canonical: qrt.vendors.base.logger
:value: >
   'getLogger(...)'

```{autodoc2-docstring} qrt.vendors.base.logger
:parser: docstring_parser
```

````

````{py:data} DEFAULT_CACHE_DIR
:canonical: qrt.vendors.base.DEFAULT_CACHE_DIR
:value: >
   '.cache'

```{autodoc2-docstring} qrt.vendors.base.DEFAULT_CACHE_DIR
:parser: docstring_parser
```

````

`````{py:class} DataVendor(cache_dir: str | pathlib.Path = DEFAULT_CACHE_DIR)
:canonical: qrt.vendors.base.DataVendor

Bases: {py:obj}`abc.ABC`

```{autodoc2-docstring} qrt.vendors.base.DataVendor
:parser: docstring_parser
```

```{rubric} Initialization
```

```{autodoc2-docstring} qrt.vendors.base.DataVendor.__init__
:parser: docstring_parser
```

````{py:attribute} name
:canonical: qrt.vendors.base.DataVendor.name
:type: str
:value: >
   None

```{autodoc2-docstring} qrt.vendors.base.DataVendor.name
:parser: docstring_parser
```

````

````{py:method} fetch_ohlc(symbol: str, start_date: str | datetime.datetime, end_date: str | datetime.datetime, time_interval: str = '1h') -> pandas.DataFrame
:canonical: qrt.vendors.base.DataVendor.fetch_ohlc
:abstractmethod:

```{autodoc2-docstring} qrt.vendors.base.DataVendor.fetch_ohlc
:parser: docstring_parser
```

````

````{py:method} fetch_ohlc_many(symbols: list[str], start_date: str | datetime.datetime, end_date: str | datetime.datetime, time_interval: str = '1D') -> dict[str, pandas.DataFrame]
:canonical: qrt.vendors.base.DataVendor.fetch_ohlc_many

```{autodoc2-docstring} qrt.vendors.base.DataVendor.fetch_ohlc_many
:parser: docstring_parser
```

````

`````

````{py:function} trades_to_ohlc(trades: pandas.DataFrame, time_interval: str) -> pandas.DataFrame
:canonical: qrt.vendors.base.trades_to_ohlc

```{autodoc2-docstring} qrt.vendors.base.trades_to_ohlc
:parser: docstring_parser
```
````
