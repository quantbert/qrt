"""Weighted returns for groups in long-form asset data."""

from typing import Literal

import numpy as np
import pandas as pd


FieldType = Literal["price", "simple_return", "log_return"]
Weighting = Literal[
    "equal",
    "market_cap",
    "volume",
    "inverse_volatility",
    "custom",
]


def _require_positive_integer(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")


def _resolve_returns(
    frame: pd.DataFrame,
    *,
    field: str | None,
    field_type: FieldType | None,
    symbol_field: str,
) -> pd.Series:
    if field is None:
        if field_type is not None:
            raise ValueError("field_type requires an explicit field")
        if "return" in frame.columns:
            source_field = "return"
            source_type: FieldType = "simple_return"
        elif "close" in frame.columns:
            source_field = "close"
            source_type = "price"
        else:
            raise ValueError(
                "data must contain 'return' or 'close'; otherwise specify "
                "both field and field_type"
            )
    else:
        if field_type is None:
            raise ValueError("field_type is required when field is specified")
        source_field = field
        source_type = field_type

    if source_type not in ("price", "simple_return", "log_return"):
        raise ValueError(
            "field_type must be 'price', 'simple_return', or 'log_return'"
        )
    if source_field not in frame.columns:
        raise ValueError(f"data is missing field column: {source_field!r}")
    if not pd.api.types.is_numeric_dtype(frame[source_field]):
        raise TypeError(f"{source_field!r} must contain numeric values")

    values = frame[source_field].astype(float)
    if not np.isfinite(values.dropna()).all():
        raise ValueError(f"{source_field!r} must contain only finite values")

    if source_type == "price":
        returns = frame.assign(_source=values).groupby(
            symbol_field, sort=False
        )["_source"].pct_change(fill_method=None)
        if np.isinf(returns).any():
            raise ValueError(
                f"{source_field!r} contains prices that produce infinite returns"
            )
        return returns
    if source_type == "log_return":
        with np.errstate(over="ignore"):
            returns = pd.Series(np.expm1(values), index=frame.index)
        if not np.isfinite(returns.dropna()).all():
            raise ValueError(
                f"{source_field!r} contains log returns that cannot be converted"
            )
        return returns
    if (values.dropna() < -1).any():
        raise ValueError("simple returns must be greater than or equal to -1")
    return values


def _resolve_weights(
    frame: pd.DataFrame,
    *,
    weighting: Weighting,
    weight_field: str | None,
    weight_lag: int,
    volatility_window: int,
    symbol_field: str,
) -> pd.Series:
    valid_weightings = {
        "equal",
        "market_cap",
        "volume",
        "inverse_volatility",
        "custom",
    }
    if weighting not in valid_weightings:
        raise ValueError(
            "weighting must be 'equal', 'market_cap', 'volume', "
            "'inverse_volatility', or 'custom'"
        )
    if weighting == "equal":
        if weight_field is not None:
            raise ValueError("weight_field is not used with equal weighting")
        return pd.Series(1.0, index=frame.index)

    if weighting == "inverse_volatility":
        if weight_field is not None:
            raise ValueError(
                "weight_field is not used with inverse_volatility weighting"
            )
        volatility = frame.groupby(symbol_field, sort=False)[
            "_asset_return"
        ].transform(
            lambda values: values.rolling(
                volatility_window, min_periods=volatility_window
            ).std()
        )
        raw_weights = 1 / volatility
    else:
        default_fields = {
            "market_cap": "market_cap",
            "volume": "volume",
        }
        resolved_field = weight_field or default_fields.get(weighting)
        if resolved_field is None:
            raise ValueError("weight_field is required for custom weighting")
        if resolved_field not in frame.columns:
            raise ValueError(
                f"data is missing weight column: {resolved_field!r}"
            )
        if not pd.api.types.is_numeric_dtype(frame[resolved_field]):
            raise TypeError(f"{resolved_field!r} must contain numeric values")
        raw_weights = frame[resolved_field].astype(float)
        finite_weights = raw_weights.dropna()
        if not np.isfinite(finite_weights).all():
            raise ValueError(
                f"{resolved_field!r} must contain only finite weights"
            )
        if (finite_weights < 0).any():
            raise ValueError(f"{resolved_field!r} must not contain negative weights")

    if weight_lag:
        raw_weights = raw_weights.groupby(
            frame[symbol_field], sort=False
        ).shift(weight_lag)
    if not np.isfinite(raw_weights.dropna()).all():
        raise ValueError("weighting produced non-finite weights")
    return raw_weights


def group_weighted_return(
    data: pd.DataFrame,
    *,
    group_field: str = "sectorid",
    date_field: str = "date",
    symbol_field: str = "symbol",
    field: str | None = None,
    field_type: FieldType | None = None,
    weighting: Weighting = "equal",
    weight_field: str | None = None,
    weight_lag: int = 1,
    volatility_window: int = 20,
    min_assets: int = 1,
) -> pd.DataFrame:
    """Calculate weighted simple returns for groups of assets.

    The input must contain one row per symbol and date. When ``field`` is not
    supplied, a ``return`` column is used as simple returns if present;
    otherwise returns are calculated from ``close``. Explicit fields require
    a ``field_type`` of ``"price"``, ``"simple_return"``, or ``"log_return"``.

    Args:
        data: Long-form asset observations.
        group_field: Column defining groups, such as ``sectorid``.
        date_field: Observation date or datetime column.
        symbol_field: Asset identifier column.
        field: Optional price or return column.
        field_type: Interpretation of an explicitly supplied ``field``.
        weighting: Equal, market-cap, volume, inverse-volatility, or custom
            weighting.
        weight_field: Weight column. It defaults to ``market_cap`` or
            ``volume`` for those named methods and is required for ``custom``.
        weight_lag: Observations by which non-equal weights are lagged within
            each symbol. The default prevents look-ahead bias.
        volatility_window: Trailing window for inverse-volatility weights.
        min_assets: Minimum valid assets required for a group return.

    Returns:
        A new DataFrame with the date and group columns, ``weighted_return``,
        contributing ``asset_count``, and raw ``weight_sum``.

    Raises:
        TypeError: If the input or a required numeric column has the wrong type.
        ValueError: If columns, observations, or parameters are invalid.
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError("data must be a pandas DataFrame")
    required = {date_field, symbol_field, group_field}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"data is missing required columns: {sorted(missing)}")
    if isinstance(weight_lag, bool) or not isinstance(weight_lag, int) or weight_lag < 0:
        raise ValueError("weight_lag must be a non-negative integer")
    _require_positive_integer(volatility_window, "volatility_window")
    _require_positive_integer(min_assets, "min_assets")

    frame = data.copy()
    try:
        frame[date_field] = pd.to_datetime(frame[date_field])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{date_field!r} must contain valid datetimes") from exc
    if frame[date_field].isna().any():
        raise ValueError(f"{date_field!r} must not contain missing values")
    if frame[symbol_field].isna().any():
        raise ValueError(f"{symbol_field!r} must not contain missing values")
    if frame.duplicated([symbol_field, date_field]).any():
        raise ValueError(
            f"data must contain at most one row per {symbol_field} and {date_field}"
        )

    frame[group_field] = frame[group_field].fillna("UnknownSector")
    frame = frame.sort_values([symbol_field, date_field], kind="stable")
    frame["_asset_return"] = _resolve_returns(
        frame,
        field=field,
        field_type=field_type,
        symbol_field=symbol_field,
    )
    frame["_raw_weight"] = _resolve_weights(
        frame,
        weighting=weighting,
        weight_field=weight_field,
        weight_lag=weight_lag,
        volatility_window=volatility_window,
        symbol_field=symbol_field,
    )

    valid = (
        frame["_asset_return"].notna()
        & frame["_raw_weight"].notna()
        & frame["_raw_weight"].gt(0)
    )
    frame["_valid"] = valid
    frame["_valid_weight"] = frame["_raw_weight"].where(valid)
    frame["_weighted_return"] = (
        frame["_asset_return"] * frame["_raw_weight"]
    ).where(valid)

    result = (
        frame.groupby([date_field, group_field], sort=False, dropna=False)
        .agg(
            asset_count=("_valid", "sum"),
            weight_sum=("_valid_weight", "sum"),
            _weighted_sum=("_weighted_return", "sum"),
        )
        .reset_index()
    )
    enough_assets = result["asset_count"] >= min_assets
    positive_weight = result["weight_sum"] > 0
    result["weighted_return"] = (
        result["_weighted_sum"] / result["weight_sum"]
    ).where(enough_assets & positive_weight)
    result["asset_count"] = result["asset_count"].astype(int)
    result["_group_sort"] = result[group_field].astype(str)
    result = result.sort_values(
        [date_field, "_group_sort"], kind="stable"
    ).reset_index(drop=True)
    return result[
        [date_field, group_field, "weighted_return", "asset_count", "weight_sum"]
    ]