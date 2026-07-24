import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm

import qrt as q


def _returns() -> pd.Series:
    return pd.Series([-0.10, -0.05, 0.00, 0.02, 0.03])


def test_risk_api_is_consolidated_under_stats():
    assert not hasattr(q, "risk")
    assert not hasattr(q.stats, "value_at_risk")
    assert not hasattr(q.stats, "conditional_value_at_risk")


def test_var_expected_shortfall_and_tce_are_positive_historical_losses():
    returns = _returns()

    assert q.stats.historical_value_at_risk(
        returns, confidence=0.8
    ) == pytest.approx(0.06)
    assert q.stats.historical_expected_shortfall(
        returns, confidence=0.8
    ) == pytest.approx(0.10)
    assert q.stats.tail_conditional_expectation(
        returns, confidence=0.8
    ) == pytest.approx(0.10)


def test_historical_expected_shortfall_uses_fractional_tail_mass():
    result = q.stats.historical_expected_shortfall(_returns(), confidence=0.7)

    assert result == pytest.approx((0.10 + 0.5 * 0.05) / 1.5)


def test_evar_bounds_var_and_is_no_more_than_worst_observed_loss():
    returns = _returns()

    result = q.stats.entropic_value_at_risk(returns, confidence=0.8)

    assert result >= q.stats.historical_value_at_risk(returns, confidence=0.8)
    assert result <= 0.10 + 1e-8


def test_evar_handles_constant_returns():
    assert q.stats.entropic_value_at_risk(pd.Series([-0.02] * 5)) == pytest.approx(0.02)
    assert q.stats.entropic_value_at_risk(pd.Series([0.02] * 5)) == 0.0


def test_gaussian_var_and_expected_shortfall_use_closed_form_losses():
    returns = _returns()
    confidence = 0.8
    loss_mean = -returns.mean()
    loss_std = returns.std(ddof=1)
    quantile = norm.ppf(confidence)

    assert q.stats.gaussian_value_at_risk(
        returns, confidence=confidence
    ) == pytest.approx(max(0.0, loss_mean + loss_std * quantile))
    assert q.stats.gaussian_expected_shortfall(
        returns, confidence=confidence
    ) == pytest.approx(
        max(0.0, loss_mean + loss_std * norm.pdf(quantile) / (1.0 - confidence))
    )


def test_maximum_observed_dollar_loss_scales_the_worst_loss():
    assert q.stats.maximum_observed_dollar_loss(
        _returns(), notional=1_000_000
    ) == pytest.approx(100_000)


def test_netto_number_matches_published_example_and_is_scale_invariant():
    dollars = q.stats.netto_number(
        100_000,
        unit_of_risk=1_000_000,
        max_adverse_excursion=500_000,
    )
    fractions = q.stats.netto_number(
        0.10,
        unit_of_risk=1.0,
        max_adverse_excursion=0.5,
    )

    assert dollars == pytest.approx(2 * 100_000 / 1_500_000)
    assert fractions == pytest.approx(dollars)


def test_netto_number_preserves_profit_sign():
    assert q.stats.netto_number(
        0.0, unit_of_risk=0.10, max_adverse_excursion=0.0
    ) == 0.0
    assert q.stats.netto_number(
        -0.05, unit_of_risk=0.10, max_adverse_excursion=0.08
    ) < 0.0


def test_netto_number_can_rank_worse_adversity_higher_for_a_loss():
    less_adverse = q.stats.netto_number(
        -0.10, unit_of_risk=1.0, max_adverse_excursion=0.10
    )
    more_adverse = q.stats.netto_number(
        -0.10, unit_of_risk=1.0, max_adverse_excursion=0.90
    )

    assert more_adverse > less_adverse


@pytest.mark.parametrize(
    ("kwargs", "error", "message"),
    [
        ({"profit": np.nan}, ValueError, "profit must be finite"),
        ({"unit_of_risk": 0.0}, ValueError, "unit_of_risk must be positive"),
        (
            {"max_adverse_excursion": -0.01},
            ValueError,
            "max_adverse_excursion must be non-negative",
        ),
        ({"profit": [0.1]}, TypeError, "profit must be a scalar"),
    ],
)
def test_netto_number_rejects_invalid_inputs(kwargs, error, message):
    inputs = {
        "profit": 0.10,
        "unit_of_risk": 0.20,
        "max_adverse_excursion": 0.05,
    }
    inputs.update(kwargs)

    with pytest.raises(error, match=message):
        q.stats.netto_number(**inputs)


def test_lower_partial_moments_support_probability_and_magnitude():
    returns = pd.Series([-0.02, -0.01, 0.01, 0.02])

    assert q.stats.lower_partial_moment(returns, order=0) == pytest.approx(0.5)
    assert q.stats.lower_partial_moment(returns, order=1) == pytest.approx(0.0075)
    assert q.stats.lower_partial_moment(returns, order=2) == pytest.approx(0.000125)


def test_tail_risk_is_zero_when_no_observation_loses_money():
    returns = pd.Series([0.01, 0.02, 0.03])

    assert q.stats.historical_value_at_risk(returns) == 0.0
    assert q.stats.historical_expected_shortfall(returns) == 0.0
    assert q.stats.tail_conditional_expectation(returns) == 0.0
    assert q.stats.maximum_observed_dollar_loss(returns, notional=100.0) == 0.0


@pytest.mark.parametrize("confidence", [0.0, 1.0, np.nan])
def test_risk_metrics_reject_invalid_confidence(confidence):
    with pytest.raises(ValueError, match="between 0 and 1"):
        q.stats.historical_value_at_risk(_returns(), confidence=confidence)


def test_risk_metrics_reject_invalid_inputs():
    with pytest.raises(TypeError, match="pandas Series"):
        q.stats.historical_value_at_risk([-0.1, 0.1])
    with pytest.raises(ValueError, match="notional must be positive"):
        q.stats.maximum_observed_dollar_loss(_returns(), notional=0.0)
    with pytest.raises(ValueError, match="order must be non-negative"):
        q.stats.lower_partial_moment(_returns(), order=-1)


def test_risk_metrics_accept_equivalent_log_returns():
    simple = _returns()
    log = np.log1p(simple)

    assert q.stats.historical_value_at_risk(
        log, return_type="log", confidence=0.8
    ) == pytest.approx(q.stats.historical_value_at_risk(simple, confidence=0.8))