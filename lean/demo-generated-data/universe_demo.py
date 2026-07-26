# region imports
from datetime import datetime

from AlgorithmImports import *
# endregion


SWEDEN = "sweden"
CUSTOM_SWEDEN_MARKET_ID = 900


class SwedenUniverseDataAlgorithm(QCAlgorithm):
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

        self._expected_broad_members = int(
            self.get_parameter("expected-daily-universe-members")
        )
        self._expected_index_members = int(
            self.get_parameter("expected-index-universe-members")
        )
        self._expected_compositions = int(
            self.get_parameter("expected-index-compositions")
        )

        self._broad_updates = 0
        self._index_updates = 0
        self._broad_sizes: set[int] = set()
        self._index_sizes: set[int] = set()
        self._index_compositions: set[tuple[str, ...]] = set()
        self._index_last_updates: set[str] = set()
        self._index_weight_failures: list[tuple[datetime, float]] = []
        self._added_symbols: set[Symbol] = set()
        self._price_symbols: set[Symbol] = set()
        self._daily_bars = 0

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
            ConstituentsUniverse(
                universe_symbol,
                self.universe_settings,
                self._select_broad_universe,
            )
        )

        self.add_universe(
            self.universe.index(
                self.get_parameter("index-universe-ticker"),
                market=SWEDEN,
                universe_settings=self.universe_settings,
                universe_filter_func=self._select_index_universe,
            )
        )

    def _select_broad_universe(
        self,
        constituents: list[ConstituentsUniverseData],
    ) -> list[Symbol]:
        values = list(constituents)
        self._broad_updates += 1
        self._broad_sizes.add(len(values))
        return [constituent.symbol for constituent in values]

    def _select_index_universe(
        self,
        constituents: list[ETFConstituentUniverse],
    ) -> list[Symbol]:
        values = list(constituents)
        self._index_updates += 1
        self._index_sizes.add(len(values))
        self._index_compositions.add(
            tuple(sorted(constituent.symbol.value for constituent in values))
        )
        self._index_last_updates.update(
            constituent.last_update.strftime("%Y%m%d")
            for constituent in values
            if constituent.last_update is not None
        )
        total_weight = sum(
            float(constituent.weight or 0)
            for constituent in values
        )
        if abs(total_weight - 1) > 1e-9:
            self._index_weight_failures.append((self.time, total_weight))
        return [constituent.symbol for constituent in values]

    def on_securities_changed(self, changes: SecurityChanges) -> None:
        self._added_symbols.update(
            security.symbol for security in changes.added_securities
        )

    def on_data(self, data: Slice) -> None:
        for symbol in data.bars.keys():
            if symbol.security_type == SecurityType.EQUITY and symbol.id.market == SWEDEN:
                self._price_symbols.add(symbol)
                self._daily_bars += 1

    def on_end_of_algorithm(self) -> None:
        counts = {
            "broad_updates": self._broad_updates,
            "index_updates": self._index_updates,
            "broad_sizes": sorted(self._broad_sizes),
            "index_sizes": sorted(self._index_sizes),
            "index_compositions": len(self._index_compositions),
            "index_last_updates": sorted(self._index_last_updates),
            "added_symbols": len(self._added_symbols),
            "price_symbols": len(self._price_symbols),
            "daily_bars": self._daily_bars,
        }
        self.debug(f"SWEDEN_UNIVERSES_VERIFIED {counts}")

        expected = {
            "broad_sizes": [self._expected_broad_members],
            "index_sizes": [self._expected_index_members],
            "index_compositions": self._expected_compositions,
            "index_last_updates": ["20231201", "20240701"],
            "added_symbols": self._expected_broad_members,
            "price_symbols": self._expected_broad_members,
            "daily_bars": int(self.get_parameter("expected-daily-bars")),
        }
        actual = {name: counts[name] for name in expected}
        expected_minimum_updates = int(self.get_parameter("expected-session-count"))
        invalid_update_counts = (
            self._broad_updates < expected_minimum_updates
            or self._index_updates != self._broad_updates
        )
        if (
            actual != expected
            or invalid_update_counts
            or self._index_weight_failures
        ):
            raise RuntimeError(
                f"Sweden universe verification failed: {actual} != {expected}; "
                f"updates={self._broad_updates}/{self._index_updates}; "
                f"weight failures={self._index_weight_failures[:5]}"
            )