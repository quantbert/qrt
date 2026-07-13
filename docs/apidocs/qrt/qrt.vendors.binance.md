# {py:mod}`qrt.vendors.binance`

```{py:module} qrt.vendors.binance
```

```{autodoc2-docstring} qrt.vendors.binance
:parser: docstring_parser
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`BinanceVendor <qrt.vendors.binance.BinanceVendor>`
  - ```{autodoc2-docstring} qrt.vendors.binance.BinanceVendor
    :parser: docstring_parser
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <qrt.vendors.binance.logger>`
  - ```{autodoc2-docstring} qrt.vendors.binance.logger
    :parser: docstring_parser
    :summary:
    ```
````

### API

````{py:data} logger
:canonical: qrt.vendors.binance.logger
:value: >
   'getLogger(...)'

```{autodoc2-docstring} qrt.vendors.binance.logger
:parser: docstring_parser
```

````

`````{py:class} BinanceVendor(download_dir: str | pathlib.Path = 'data', cache_dir: str | pathlib.Path = DEFAULT_CACHE_DIR)
:canonical: qrt.vendors.binance.BinanceVendor

Bases: {py:obj}`qrt.vendors.base.DataVendor`

```{autodoc2-docstring} qrt.vendors.binance.BinanceVendor
:parser: docstring_parser
```

```{rubric} Initialization
```

```{autodoc2-docstring} qrt.vendors.binance.BinanceVendor.__init__
:parser: docstring_parser
```

````{py:attribute} name
:canonical: qrt.vendors.binance.BinanceVendor.name
:value: >
   'binance'

```{autodoc2-docstring} qrt.vendors.binance.BinanceVendor.name
:parser: docstring_parser
```

````

````{py:method} fetch_trades_day(symbol: str, date: str | datetime.datetime) -> pandas.DataFrame
:canonical: qrt.vendors.binance.BinanceVendor.fetch_trades_day

```{autodoc2-docstring} qrt.vendors.binance.BinanceVendor.fetch_trades_day
:parser: docstring_parser
```

````

````{py:method} fetch_trades(symbol: str, start_date: str | datetime.datetime, end_date: str | datetime.datetime) -> pandas.DataFrame
:canonical: qrt.vendors.binance.BinanceVendor.fetch_trades

```{autodoc2-docstring} qrt.vendors.binance.BinanceVendor.fetch_trades
:parser: docstring_parser
```

````

````{py:method} fetch_ohlc(symbol: str, start_date: str | datetime.datetime, end_date: str | datetime.datetime, time_interval: str = '1h') -> pandas.DataFrame
:canonical: qrt.vendors.binance.BinanceVendor.fetch_ohlc

```{autodoc2-docstring} qrt.vendors.binance.BinanceVendor.fetch_ohlc
:parser: docstring_parser
```

````

`````
