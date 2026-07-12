"""Market data vendors.

Each vendor implements the :class:`~qrt.vendors.base.DataVendor` interface,
so downstream code can stay vendor-agnostic:

    import qrt as q

    vendor = q.vendors.get_vendor("binance")
    ohlc = vendor.fetch_ohlc("BTCUSDT", "2025-01-01", "2025-01-07", "1h")

To add a new vendor, subclass ``DataVendor`` in a new module and register
it in ``_VENDORS`` below.
"""

from qrt.vendors.base import DataVendor
from qrt.vendors.binance import BinanceVendor
from qrt.vendors.yfinance import YFinanceVendor

_VENDORS: dict[str, type[DataVendor]] = {
    BinanceVendor.name: BinanceVendor,
    YFinanceVendor.name: YFinanceVendor,
}


def get_vendor(name: str, **kwargs) -> DataVendor:
    """Instantiate a vendor by name.

    Args:
        name: Registered vendor name (e.g. ``"binance"``, ``"yfinance"``).
        **kwargs: Passed to the vendor constructor (e.g. ``cache_dir``).

    Raises:
        KeyError: If no vendor is registered under ``name``.
    """
    try:
        return _VENDORS[name](**kwargs)
    except KeyError:
        raise KeyError(
            f"Unknown vendor {name!r}. Available: {sorted(_VENDORS)}"
        ) from None


__all__ = ["DataVendor", "BinanceVendor", "YFinanceVendor", "get_vendor"]
