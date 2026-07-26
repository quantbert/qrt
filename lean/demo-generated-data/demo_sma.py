# region imports
from datetime import datetime

from AlgorithmImports import *
# endregion


SWEDEN = "sweden"
CUSTOM_SWEDEN_MARKET_ID = 900
FAST_PERIOD = 20
SLOW_PERIOD = 100
TARGET_GROSS_EXPOSURE = 0.95


class SmaPair:
    def __init__(self) -> None:
        self.fast = SimpleMovingAverage(FAST_PERIOD)
        self.slow = SimpleMovingAverage(SLOW_PERIOD)
        self.fast_above: bool | None = None

    def update(self, time: datetime, price: float) -> bool:
        self.fast.update(time, price)
        self.slow.update(time, price)
        return self.slow.is_ready


class SwedenSmaCrossAlgorithm(QCAlgorithm):
    def initialize(self) -> None:
        if Market.encode(SWEDEN) is None:
            Market.add(SWEDEN, CUSTOM_SWEDEN_MARKET_ID)

        start = datetime.fromisoformat(self.get_parameter("backtest-start"))
        end = datetime.fromisoformat(self.get_parameter("backtest-end"))
        self.set_start_date(start.year, start.month, start.day)
        self.set_end_date(end.year, end.month, end.day)
        self.set_time_zone("Europe/Stockholm")
        self.set_account_currency("SEK")
        self.set_cash(1_000_000)
        self.set_benchmark(lambda _: 0)

        self.universe_settings.resolution = Resolution.DAILY
        self.universe_settings.data_normalization_mode = DataNormalizationMode.RAW

        self._expected_assets = int(
            self.get_parameter("expected-daily-universe-members")
        )
        self._states: dict[Symbol, SmaPair] = {}
        self._target_symbols: set[Symbol] = set()
        self._seen_symbols: set[Symbol] = set()
        self._ready_symbols: set[Symbol] = set()
        self._entry_signals = 0
        self._exit_signals = 0
        self._rebalances = 0
        self._filled_orders = 0

        daily_name = self.get_parameter("daily-universe-name")
        universe_ticker = f"constituents-universe-{daily_name}"
        universe_symbol = Symbol(
            SecurityIdentifier.generate_constituent_identifier(
                universe_ticker,
                SecurityType.EQUITY,
                SWEDEN,
            ),
            universe_ticker,
        )
        self.add_universe(
            ConstituentsUniverse(universe_symbol, self.universe_settings)
        )

    def on_securities_changed(self, changes: SecurityChanges) -> None:
        for security in changes.added_securities:
            if security.symbol.security_type != SecurityType.EQUITY:
                continue
            security.set_fee_model(ConstantFeeModel(0))
            self._states.setdefault(security.symbol, SmaPair())
            self._seen_symbols.add(security.symbol)

        for security in changes.removed_securities:
            symbol = security.symbol
            if self.portfolio[symbol].invested:
                self.liquidate(symbol, tag="Removed from Sweden universe")
            self._states.pop(symbol, None)
            self._target_symbols.discard(symbol)
            self._ready_symbols.discard(symbol)

    def on_data(self, data: Slice) -> None:
        regime_changed = False

        for symbol, state in self._states.items():
            bar = data.bars.get(symbol)
            if bar is None or not state.update(bar.end_time, bar.close):
                continue

            self._ready_symbols.add(symbol)
            fast_above = state.fast.current.value > state.slow.current.value
            if state.fast_above is None:
                state.fast_above = fast_above
                if fast_above:
                    self._entry_signals += 1
                    regime_changed = True
            elif fast_above != state.fast_above:
                state.fast_above = fast_above
                regime_changed = True
                if fast_above:
                    self._entry_signals += 1
                else:
                    self._exit_signals += 1

        if regime_changed:
            self._rebalance()

    def _rebalance(self) -> None:
        bullish = {
            symbol
            for symbol, state in self._states.items()
            if state.slow.is_ready and state.fast_above
        }
        if bullish == self._target_symbols:
            return

        targets: list[PortfolioTarget] = [
            PortfolioTarget(symbol, 0, "20/100 bearish cross")
            for symbol in self._target_symbols - bullish
        ]
        if bullish:
            target_weight = TARGET_GROSS_EXPOSURE / len(bullish)
            for symbol in sorted(bullish, key=lambda item: item.value):
                targets.append(PortfolioTarget(
                    symbol,
                    target_weight,
                    "20/100 bullish cross",
                ))

        if targets:
            self.set_holdings(targets, tag="20/100 SMA rebalance")
        self._target_symbols = bullish
        self._rebalances += 1

    def on_order_event(self, order_event: OrderEvent) -> None:
        if order_event.status == OrderStatus.FILLED:
            self._filled_orders += 1

    def on_end_of_algorithm(self) -> None:
        counts = {
            "assets": len(self._seen_symbols),
            "ready": len(self._ready_symbols),
            "entry_signals": self._entry_signals,
            "exit_signals": self._exit_signals,
            "rebalances": self._rebalances,
            "filled_orders": self._filled_orders,
            "final_positions": sum(
                self.portfolio[symbol].invested for symbol in self._seen_symbols
            ),
        }
        self.debug(f"SWEDEN_SMA_CROSS_VERIFIED {counts}")

        if (
            counts["assets"] != self._expected_assets
            or counts["ready"] != self._expected_assets
            or counts["entry_signals"] == 0
            or counts["exit_signals"] == 0
            or counts["rebalances"] == 0
            or counts["filled_orders"] == 0
        ):
            raise RuntimeError(f"Sweden SMA crossover verification failed: {counts}")