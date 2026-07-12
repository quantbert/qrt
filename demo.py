import qrt as q

btc = q.vendors.get_vendor("binance").fetch_ohlc("BTCUSDT", "2025-01-01", "2025-01-07", "1h")
aapl = q.vendors.get_vendor("yfinance").fetch_ohlc("ERIC", "2025-01-01", "2025-06-30", "1h")

dfs = q.vendors.get_vendor("yfinance").fetch_ohlc_many(
    ["AAPL", "MSFT", "NVDA"], "2025-01-01", "2025-06-30", "1h"
)