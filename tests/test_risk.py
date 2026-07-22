import numpy as np
import pandas as pd
import pytest

import qrt as q


def _returns() -> pd.Series:
    return pd.Series([-0.10, -0.05, 0.00, 0.02, 0.03])


def test_var_cvar_and_tce_are_positive_historical_losses():
    returns = _returns()

    assert q.risk.value_at_risk(returns, confidence=0.8) == pytest.approx(0.06)
    assert q.risk.conditional_value_at_risk(
        returns, confidence=0.8
    ) == pytest.approx(0.10)
    assert q.risk.tail_conditional_expectation(
        returns, confidence=0.8
    ) == pytest.approx(0.10)


def test_cvar_uses_fractional_tail_mass():
    result = q.risk.cvar(_returns(), confidence=0.7)

    assert result == pytest.approx((0.10 + 0.5 * 0.05) / 1.5)


def test_evar_bounds_var_and_is_no_more_than_worst_observed_loss():
    returns = _returns()

    result = q.risk.evar(returns, confidence=0.8)

    assert result >= q.risk.var(returns, confidence=0.8)
    assert result <= 0.10 + 1e-8


def test_evar_handles_constant_returns():
    assert q.risk.evar(pd.Series([-0.02] * 5)) == pytest.approx(0.02)
    assert q.risk.evar(pd.Series([0.02] * 5)) == 0.0


def test_worst_case_dollar_risk_scales_the_worst_loss():
    assert q.risk.wcdr(_returns(), notional=1_000_000) == pytest.approx(100_000)


def test_lower_partial_moments_support_probability_and_magnitude():
    returns = pd.Series([-0.02, -0.01, 0.01, 0.02])

    assert q.risk.lpm(returns, order=0) == pytest.approx(0.5)
    assert q.risk.lpm(returns, order=1) == pytest.approx(0.0075)
    assert q.risk.lpm(returns, order=2) == pytest.approx(0.000125)


def test_tail_risk_is_zero_when_no_observation_loses_money():
    returns = pd.Series([0.01, 0.02, 0.03])

    assert q.risk.var(returns) == 0.0
    assert q.risk.cvar(returns) == 0.0
    assert q.risk.tce(returns) == 0.0
    assert q.risk.wcdr(returns, notional=100.0) == 0.0


@pytest.mark.parametrize("confidence", [0.0, 1.0, np.nan])
def test_risk_metrics_reject_invalid_confidence(confidence):
    with pytest.raises(ValueError, match="between 0 and 1"):
        q.risk.var(_returns(), confidence=confidence)


def test_risk_metrics_reject_invalid_inputs():
    with pytest.raises(TypeError, match="pandas Series"):
        q.risk.var([-0.1, 0.1])
    with pytest.raises(ValueError, match="notional must be positive"):
        q.risk.wcdr(_returns(), notional=0.0)
    with pytest.raises(ValueError, match="order must be non-negative"):
        q.risk.lpm(_returns(), order=-1)