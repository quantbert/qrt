"""Create a LEAN Report-compatible copy of a custom-market backtest result."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


CUSTOM_MARKET_ID = 900
REPORT_MARKET_ID = 1
MARKET_OFFSET = 100
MARKET_WIDTH = 1_000
BASE36_DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
SID_PATTERN = re.compile(
    r"(?<![A-Z0-9.])(?P<ticker>[A-Z][A-Z0-9.-]*) "
    r"(?P<properties>[A-Z0-9]+)(?![A-Z0-9|])"
)


def _decode_base36(value: str) -> int:
    result = 0
    for character in value:
        result = result * 36 + BASE36_DIGITS.index(character)
    return result


def _encode_base36(value: int) -> str:
    encoded = ""
    while value:
        value, remainder = divmod(value, 36)
        encoded = BASE36_DIGITS[remainder] + encoded
    return encoded or "0"


def _remap_string(value: str) -> tuple[str, int]:
    replacements = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal replacements
        properties = _decode_base36(match.group("properties"))
        market = (properties // MARKET_OFFSET) % MARKET_WIDTH
        if market != CUSTOM_MARKET_ID:
            return match.group(0)

        properties += (REPORT_MARKET_ID - CUSTOM_MARKET_ID) * MARKET_OFFSET
        replacements += 1
        return f'{match.group("ticker")} {_encode_base36(properties)}'

    return SID_PATTERN.sub(replace, value), replacements


def _remap_value(value: Any) -> tuple[Any, int]:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        replacements = 0
        for key, item in value.items():
            remapped_key, key_replacements = _remap_string(str(key))
            remapped_item, item_replacements = _remap_value(item)
            result[remapped_key] = remapped_item
            replacements += key_replacements + item_replacements
        return result, replacements

    if isinstance(value, list):
        result = []
        replacements = 0
        for item in value:
            remapped_item, item_replacements = _remap_value(item)
            result.append(remapped_item)
            replacements += item_replacements
        return result, replacements

    if isinstance(value, str):
        return _remap_string(value)

    return value, 0


def prepare_report_result(
    source: Path,
    destination: Path,
    *,
    keep_orders: bool = False,
) -> tuple[int, int]:
    """Write a report-compatible copy and return SID/order modification counts."""
    result = json.loads(source.read_text(encoding="utf-8"))
    remapped, replacements = _remap_value(result)
    if replacements == 0:
        raise ValueError(f"No custom market {CUSTOM_MARKET_ID} SIDs found in {source}")

    # Report's PortfolioLooper manufactures zero-valued fees in USD while it
    # replays orders. Matching the report-only USA SID alias to a USD replay
    # account prevents a missing-currency error. Precomputed SEK charts,
    # statistics, and runtime statistics remain unchanged.
    remapped["algorithmConfiguration"]["accountCurrency"] = "USD"

    # PortfolioLooper cannot register custom markets and its private result
    # handler leaves TradingDaysPerYear unset. Omitting orders bypasses that
    # replay bug while preserving the result's closed trades, charts,
    # statistics, runtime statistics, and parameters. The allocation chart is
    # the only report section that loses its reconstructed input.
    removed_orders = 0
    if not keep_orders:
        removed_orders = len(remapped.get("orders", {}))
        remapped["orders"] = {}

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(remapped, separators=(",", ":")), encoding="utf-8")
    return replacements, removed_orders


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Original LEAN backtest result JSON")
    parser.add_argument("destination", type=Path, help="Report-compatible output JSON")
    parser.add_argument(
        "--keep-orders",
        action="store_true",
        help="Keep orders for allocation replay (may trigger Report replay warnings)",
    )
    args = parser.parse_args()

    replacements, removed_orders = prepare_report_result(
        args.source,
        args.destination,
        keep_orders=args.keep_orders,
    )
    print(
        f"Remapped {replacements} custom-market SIDs in report copy: "
        f"{args.destination}"
    )
    if removed_orders:
        print(
            f"Omitted {removed_orders} orders to bypass LEAN Report's "
            "custom-market portfolio replay; closed trades and statistics remain."
        )


if __name__ == "__main__":
    main()