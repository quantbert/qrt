# {py:mod}`qrt.dataload`

```{py:module} qrt.dataload
```

```{autodoc2-docstring} qrt.dataload
:parser: docstring_parser
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`load_ohlc_timeseries_range <qrt.dataload.load_ohlc_timeseries_range>`
  - ```{autodoc2-docstring} qrt.dataload.load_ohlc_timeseries_range
    :parser: docstring_parser
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <qrt.dataload.logger>`
  - ```{autodoc2-docstring} qrt.dataload.logger
    :parser: docstring_parser
    :summary:
    ```
````

### API

````{py:data} logger
:canonical: qrt.dataload.logger
:value: >
   'getLogger(...)'

```{autodoc2-docstring} qrt.dataload.logger
:parser: docstring_parser
```

````

````{py:function} load_ohlc_timeseries_range(sym: str, time_interval: str, start_date: datetime.datetime, end_date: datetime.datetime, data_path: str | pathlib.Path = './cache') -> pandas.DataFrame
:canonical: qrt.dataload.load_ohlc_timeseries_range

```{autodoc2-docstring} qrt.dataload.load_ohlc_timeseries_range
:parser: docstring_parser
```
````
