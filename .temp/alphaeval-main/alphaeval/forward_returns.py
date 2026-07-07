from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = {"datetime", "instrument_id", "return", "y_pred"}
VALID_RETURN_TYPES = {"simple", "log"}
VALID_PREDICTIONS = {-1, 0, 1}


def validate_data(data: pd.DataFrame, return_type: str) -> None:
    """Validate the input DataFrame and parameters."""
    missing = REQUIRED_COLUMNS - set(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if return_type not in VALID_RETURN_TYPES:
        raise ValueError(f"return_type must be one of {VALID_RETURN_TYPES}, got '{return_type}'")

    invalid_preds = set(data["y_pred"].dropna().unique()) - VALID_PREDICTIONS
    if invalid_preds:
        raise ValueError(f"y_pred must contain only -1, 0, 1. Found invalid values: {invalid_preds}")

    dupes = data.duplicated(subset=["datetime", "instrument_id"], keep=False)
    if dupes.any():
        n = dupes.sum()
        raise ValueError(f"Found {n} duplicate (datetime, instrument_id) pairs. " "Each instrument must have one row per datetime.")


def compute_forward_returns(
    data: pd.DataFrame,
    horizons: list[int],
    return_type: str,
) -> pd.DataFrame:
    """Compute forward returns at each horizon for every observation.

    Parameters
    ----------
    data : pd.DataFrame
        Must contain columns: datetime, instrument_id, return, y_pred.
    horizons : list[int]
        Forward horizons in trading days, e.g. [1, 5, 10].
    return_type : str
        'simple' for compounded returns, 'log' for additive.

    Returns
    -------
    pd.DataFrame
        Copy of input data with additional columns ``fwd_return_{h}`` for
        each horizon *h*. Rows where any horizon cannot be computed are
        dropped.
    """
    validate_data(data, return_type)

    df = data.copy()
    df = df.sort_values(["instrument_id", "datetime"]).reset_index(drop=True)

    max_horizon = max(horizons)
    total_before = len(df)

    for h in horizons:
        col = f"fwd_return_{h}"
        df[col] = np.nan

    for _instr_id, group in df.groupby("instrument_id"):
        idx = group.index
        returns = group["return"].values

        for h in horizons:
            col = f"fwd_return_{h}"
            fwd = np.full(len(returns), np.nan)

            for i in range(len(returns) - h):
                window = returns[i + 1 : i + 1 + h]
                if return_type == "simple":
                    fwd[i] = np.prod(1.0 + window) - 1.0
                else:  # log
                    fwd[i] = np.sum(window)

            df.loc[idx, col] = fwd

    # Drop rows where primary horizon (first) is NaN
    primary_col = f"fwd_return_{horizons[0]}"
    dropped = df[primary_col].isna().sum()
    df = df.dropna(subset=[primary_col]).reset_index(drop=True)

    if dropped > 0:
        warnings.warn(
            f"Dropped {dropped}/{total_before} rows where forward return " f"(horizon={horizons[0]}) could not be computed (end of series).",
            stacklevel=2,
        )

    return df
