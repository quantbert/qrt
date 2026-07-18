"""Refresh qrt's prepackaged sample datasets (AAPL, SPY, BTC-USD) from Yahoo
Finance and overwrite their bundled parquet files.

Usage:
    uv run python tools/update_datasets.py
    uv run python tools/update_datasets.py aapl spy   # refresh a subset

Run this before cutting a release (``make datasets``, wired into ``make
publish``) so published versions of qrt ship reasonably current data.
"""

import sys

from qrt.data import datasets


def main() -> None:
    names = sys.argv[1:] or None
    datasets.refresh(names)


if __name__ == "__main__":
    main()
