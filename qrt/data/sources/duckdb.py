"""Generic DuckDB-backed data source.

Unlike the network vendors, this reads/writes arbitrary tables in a DuckDB
database rather than a fixed schema -- point :func:`connect` at a database
file (or ``:memory:``) and pass a ``table`` name to ``read``/``write``.

Multiple independent connections are just multiple :func:`connect` calls --
there is no shared/cached registry::

    prod = q.data.sources.duckdb.connect(path="prod.duckdb")
    paper = q.data.sources.duckdb.connect(path="paper.duckdb")
"""

import re
from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_identifier(name: str) -> str:
    """Guard against SQL injection via a dynamic table name."""
    if not _IDENTIFIER_RE.match(name):
        raise ValueError(f"Invalid table name: {name!r}")
    return name


def connect(path: str | Path = ":memory:", **connect_kwargs) -> "DuckDBConnection":
    """Open a DuckDB connection for reading/writing OHLC(V) tables.

    Args:
        path: Database file, or ``:memory:`` for an in-memory database.
        **connect_kwargs (Any): Passed to :func:`duckdb.connect`.
    """
    return DuckDBConnection(duckdb.connect(str(path), **connect_kwargs))


class DuckDBConnection:
    """A single DuckDB connection, opened via :func:`connect`."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def read(
        self,
        symbol: str,
        start_date: str | datetime,
        end_date: str | datetime,
        *,
        table: str = "ohlc",
    ) -> pd.DataFrame:
        """Read OHLC(V) rows for one symbol from ``table``."""
        table = _validate_identifier(table)
        return self._conn.execute(
            f"select * from {table} where symbol = ? and datetime between ? and ?",  # noqa: S608
            [symbol, start_date, end_date],
        ).df()

    def write(self, df: pd.DataFrame, *, table: str = "ohlc") -> None:
        """Insert ``df`` into ``table`` (created on first write)."""
        table = _validate_identifier(table)
        self._conn.register("_qrt_write_tmp", df)
        try:
            self._conn.execute(
                f"create table if not exists {table} as select * from _qrt_write_tmp limit 0"  # noqa: S608
            )
            self._conn.execute(f"insert into {table} select * from _qrt_write_tmp")  # noqa: S608
        finally:
            self._conn.unregister("_qrt_write_tmp")

    def close(self) -> None:
        """Close the underlying connection."""
        self._conn.close()

    def __enter__(self) -> "DuckDBConnection":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
