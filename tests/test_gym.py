import numpy as np
import pandas as pd
import pytest
from gymnasium.utils.env_checker import check_env
from ray.rllib.algorithms.ppo import PPOConfig
from ray.rllib.env.env_context import EnvContext

import qrt as q


def test_financial_env_passes_gymnasium_checker():
    returns = pd.Series(np.linspace(-0.02, 0.02, 30))
    environment = q.gym.FinancialEnv(returns, window_size=5)

    check_env(environment)


def test_financial_env_accounts_for_target_position_turnover():
    index = pd.date_range("2026-01-01", periods=4)
    returns = pd.Series([0.0, 0.0, 0.10, -0.05], index=index)
    features = pd.DataFrame(
        {"return": returns, "signal": [1.0, 2.0, 3.0, 4.0]}, index=index
    )
    environment = q.gym.FinancialEnv(
        returns,
        features,
        window_size=2,
        transaction_cost=0.01,
    )

    observation, info = environment.reset()

    assert environment.observation_space.contains(observation)
    assert observation["market"].tolist() == [[0.0, 1.0], [0.0, 2.0]]
    assert info["account"]["equity"] == 1.0

    observation, reward, terminated, truncated, info = environment.step(
        np.array([1.0], dtype=np.float32)
    )

    assert reward == pytest.approx(0.09)
    assert environment.account.equity == pytest.approx(1.09)
    assert info["turnover"] == 1.0
    assert info["cost"] == pytest.approx(0.01)
    assert not terminated
    assert not truncated

    _, reward, terminated, truncated, info = environment.step(
        np.array([-1.0], dtype=np.float32)
    )

    assert reward == pytest.approx(0.03)
    assert environment.account.equity == pytest.approx(1.1227)
    assert environment.account.cumulative_cost == pytest.approx(0.0318)
    assert info["timestamp"] == index[-1]
    assert not terminated
    assert truncated


def test_financial_env_terminates_at_drawdown_constraint():
    environment = q.gym.FinancialEnv(
        [0.0, 0.0, -0.2, 0.1], window_size=2, max_drawdown=0.1
    )
    environment.reset()

    _, _, terminated, truncated, _ = environment.step(
        np.array([1.0], dtype=np.float32)
    )

    assert terminated
    assert not truncated
    assert environment.account.drawdown == pytest.approx(-0.2)
    with pytest.raises(RuntimeError, match=r"call reset\(\)"):
        environment.step(np.array([0.0], dtype=np.float32))


def test_financial_env_accepts_rllib_env_context():
    context = EnvContext(
        {
            "returns": [0.0, 0.01, -0.01, 0.02],
            "window_size": 2,
            "episode_length": 2,
        },
        worker_index=1,
        vector_index=0,
        num_workers=2,
        remote=False,
    )

    environment = q.gym.FinancialEnv(context)
    observation, _ = environment.reset(seed=7)

    assert environment.observation_space.contains(observation)
    assert environment.window_size == 2
    assert environment.episode_length == 2


def test_rllib_ppo_config_uses_financial_env():
    env_config = {
        "returns": [0.0, 0.01, -0.01, 0.02],
        "window_size": 2,
        "episode_length": 2,
    }

    config = (
        PPOConfig()
        .environment(q.gym.FinancialEnv, env_config=env_config)
        .env_runners(num_env_runners=0)
    )

    assert config.env is q.gym.FinancialEnv
    assert config.env_config == env_config
    assert config.num_env_runners == 0


def test_random_episode_starts_are_seeded():
    config = {
        "returns": np.linspace(-0.01, 0.01, 20),
        "window_size": 3,
        "episode_length": 5,
        "random_start": True,
    }
    first = q.gym.FinancialEnv(config)
    second = q.gym.FinancialEnv(config)

    first_observation, _ = first.reset(seed=42)
    second_observation, _ = second.reset(seed=42)

    np.testing.assert_array_equal(
        first_observation["market"], second_observation["market"]
    )