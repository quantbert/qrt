# region imports
from datetime import datetime

from AlgorithmImports import *
# endregion


SWEDEN = "sweden"
CUSTOM_SWEDEN_MARKET_ID = 900


class SwedenMultiAssetDataAlgorithm(QCAlgorithm):
    def initialize(self) -> None:
        if Market.encode(SWEDEN) is None:
            Market.add(SWEDEN, CUSTOM_SWEDEN_MARKET_ID)

        start = datetime.fromisoformat(self.get_parameter("backtest-start"))
        end = datetime.fromisoformat(self.get_parameter("backtest-end"))
        history_date = datetime.fromisoformat(self.get_parameter("tick-history-date"))
        ticker_names = self.get_parameter("symbols").split(",")
        self._asset_count = int(self.get_parameter("asset-count"))
        if len(ticker_names) != self._asset_count:
            raise RuntimeError(
                f"Expected {self._asset_count} ticker names, got {len(ticker_names)}"
            )

        self.set_start_date(start.year, start.month, start.day)
        self.set_end_date(end.year, end.month, end.day)
        self.set_time_zone("Europe/Stockholm")
        self.set_account_currency("SEK")
        self.set_cash(1_000_000)
        self.set_benchmark(lambda _: 0)

        self._symbols: list[Symbol] = []
        for ticker in ticker_names:
            security = self.add_equity(
                ticker,
                Resolution.DAILY,
                market=SWEDEN,
                fill_forward=False,
                extended_market_hours=False,
                data_normalization_mode=DataNormalizationMode.RAW,
            )
            security.set_fee_model(ConstantFeeModel(0))
            if security.symbol_properties.quote_currency != "SEK":
                raise RuntimeError(
                    f"Expected SEK quote currency for {ticker}, "
                    f"got {security.symbol_properties.quote_currency}"
                )
            if security.exchange.time_zone.id != "Europe/Stockholm":
                raise RuntimeError(
                    f"Expected Europe/Stockholm exchange time for {ticker}, "
                    f"got {security.exchange.time_zone.id}"
                )
            self._symbols.append(security.symbol)

        daily_history = self.history(
            TradeBar,
            self._symbols,
            5,
            Resolution.DAILY,
            fill_forward=False,
            data_normalization_mode=DataNormalizationMode.RAW,
        )
        hour_history = self.history(
            TradeBar,
            self._symbols,
            5,
            Resolution.HOUR,
            fill_forward=False,
            data_normalization_mode=DataNormalizationMode.RAW,
        )
        history_start = history_date.replace(hour=9)
        history_end = history_date.replace(hour=10)
        minute_history = self.history(
            TradeBar,
            self._symbols,
            history_start,
            history_end,
            Resolution.MINUTE,
            fill_forward=False,
            data_normalization_mode=DataNormalizationMode.RAW,
        )
        quote_history = self.history(
            QuoteBar,
            self._symbols,
            history_start,
            history_end,
            Resolution.MINUTE,
            fill_forward=False,
            data_normalization_mode=DataNormalizationMode.RAW,
        )
        tick_history = self.history(
            Tick,
            self._symbols,
            history_start,
            history_end,
            Resolution.TICK,
            fill_forward=False,
            data_normalization_mode=DataNormalizationMode.RAW,
        )
        self._history_counts = {
            "daily_history": len(daily_history),
            "hour_history": len(hour_history),
            "minute_history": len(minute_history),
            "quote_history": len(quote_history),
            "tick_history": len(tick_history),
        }

        self._daily_bars = 0
        self._sessions = 0
        self._incomplete_sessions: list[tuple[datetime, int]] = []
        self._orders_submitted = False

    def on_data(self, data: Slice) -> None:
        bars_this_session = sum(
            1 for symbol in self._symbols if data.bars.get(symbol) is not None
        )
        if bars_this_session == 0:
            return

        self._sessions += 1
        self._daily_bars += bars_this_session
        if bars_this_session != self._asset_count:
            self._incomplete_sessions.append((self.time, bars_this_session))

        if not self._orders_submitted:
            for symbol in self._symbols:
                self.market_order(symbol, 1)
            self._orders_submitted = True

    def on_end_of_algorithm(self) -> None:
        counts = {
            "assets": len(self._symbols),
            "sessions": self._sessions,
            "daily_bars": self._daily_bars,
            **self._history_counts,
            "invested": sum(self.portfolio[symbol].invested for symbol in self._symbols),
        }
        self.debug(f"SWEDEN_MULTI_ASSET_VERIFIED {counts}")

        expected = {
            "assets": self._asset_count,
            "sessions": int(self.get_parameter("expected-session-count")),
            "daily_bars": int(self.get_parameter("expected-daily-bars")),
            "daily_history": int(self.get_parameter("expected-daily-history-rows")),
            "hour_history": int(self.get_parameter("expected-hour-history-rows")),
            "minute_history": int(self.get_parameter("expected-minute-history-rows")),
            "quote_history": int(self.get_parameter("expected-quote-history-rows")),
            "tick_history": int(self.get_parameter("expected-tick-history-rows")),
            "invested": self._asset_count,
        }
        if counts != expected or self._incomplete_sessions:
            raise RuntimeError(
                f"Sweden multi-asset verification failed: {counts} != {expected}; "
                f"incomplete sessions={self._incomplete_sessions[:5]}"
            )