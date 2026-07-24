"""Gymnasium environments for financial reinforcement learning."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

import gymnasium as gymnasium
import numpy as np
import pandas as pd
from gymnasium import spaces


@dataclass(frozen=True)
class AccountState:
    """Immutable account snapshot after an environment transition."""

    equity: float
    peak_equity: float
    drawdown: float
    position: float
    cumulative_cost: float
    steps: int


class FinancialEnv(gymnasium.Env[dict[str, np.ndarray], np.ndarray]):
    """Single-asset financial environment with target-position actions.

    Each action is a target exposure from ``-1`` (fully short) through ``0``
    (flat) to ``1`` (fully long). The environment charges proportional costs
    on absolute position turnover, then applies the next simple return. Market
    observations contain only periods preceding the return being traded.

    The first argument may also be an RLlib ``env_config`` mapping containing
    ``returns`` and any constructor keyword arguments.

    Args:
        returns: Simple asset returns or an RLlib environment configuration.
        features: Market features aligned one-to-one with ``returns``. The
            return itself is used as the sole feature when omitted.
        window_size: Number of historical feature rows in each observation.
        transaction_cost: Proportional cost per unit of position turnover.
        max_drawdown: Positive drawdown magnitude that terminates an episode.
            Set to ``None`` to disable the constraint.
        episode_length: Number of transitions per episode. By default, an
            episode consumes all available returns after the initial window.
        random_start: Whether resets sample a valid episode start. This
            requires ``episode_length`` so every sampled episode is equal.
        render_mode: ``"ansi"`` for a text account summary, otherwise ``None``.
    """

    metadata = {"render_modes": ["ansi"]}

    def __init__(
        self,
        returns: pd.Series | np.ndarray | list[float] | Mapping[str, Any],
        features: pd.DataFrame | pd.Series | np.ndarray | None = None,
        *,
        window_size: int = 20,
        transaction_cost: float = 0.0,
        max_drawdown: float | None = None,
        episode_length: int | None = None,
        random_start: bool = False,
        render_mode: str | None = None,
    ) -> None:
        if isinstance(returns, Mapping):
            config = dict(returns)
            try:
                returns = config.pop("returns")
            except KeyError:
                raise ValueError("env_config must contain 'returns'") from None
            features = config.pop("features", features)
            window_size = config.pop("window_size", window_size)
            transaction_cost = config.pop("transaction_cost", transaction_cost)
            max_drawdown = config.pop("max_drawdown", max_drawdown)
            episode_length = config.pop("episode_length", episode_length)
            random_start = config.pop("random_start", random_start)
            render_mode = config.pop("render_mode", render_mode)
            if config:
                names = ", ".join(sorted(config))
                raise ValueError(f"Unknown env_config option(s): {names}")

        self._returns = self._validate_returns(returns)
        self._features = self._validate_features(features)
        self.window_size = self._positive_integer(window_size, "window_size")
        if self.window_size >= len(self._returns):
            raise ValueError("window_size must be smaller than the number of returns")
        if not np.isfinite(transaction_cost) or transaction_cost < 0:
            raise ValueError("transaction_cost must be a non-negative finite number")
        if max_drawdown is not None and (
            not np.isfinite(max_drawdown) or not 0 < max_drawdown <= 1
        ):
            raise ValueError("max_drawdown must be in (0, 1] or None")
        if episode_length is not None:
            episode_length = self._positive_integer(episode_length, "episode_length")
            if episode_length > len(self._returns) - self.window_size:
                raise ValueError("episode_length exceeds the available return history")
        if random_start and episode_length is None:
            raise ValueError("random_start requires episode_length")
        if render_mode not in self.metadata["render_modes"] + [None]:
            raise ValueError("render_mode must be 'ansi' or None")

        self.transaction_cost = float(transaction_cost)
        self.max_drawdown = max_drawdown
        self.episode_length = episode_length
        self.random_start = bool(random_start)
        self.render_mode = render_mode

        feature_count = self._features.shape[1]
        self.action_space = spaces.Box(-1.0, 1.0, shape=(1,), dtype=np.float32)
        self.observation_space = spaces.Dict(
            {
                "market": spaces.Box(
                    -np.inf,
                    np.inf,
                    shape=(self.window_size, feature_count),
                    dtype=np.float32,
                ),
                "account": spaces.Box(
                    -np.inf,
                    np.inf,
                    shape=(4,),
                    dtype=np.float32,
                ),
            }
        )
        self._cursor = self.window_size
        self._end = len(self._returns)
        self._episode_done = False
        self._account = self._initial_account()

    @staticmethod
    def _positive_integer(value: Any, name: str) -> int:
        if not isinstance(value, (int, np.integer)) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
        return int(value)

    @staticmethod
    def _validate_returns(
        values: pd.Series | np.ndarray | list[float],
    ) -> pd.Series:
        if isinstance(values, pd.Series):
            series = values.astype(float).copy()
        else:
            array = np.asarray(values, dtype=float)
            if array.ndim != 1:
                raise ValueError("returns must be one-dimensional")
            series = pd.Series(array, name="return")
        if series.empty or not np.isfinite(series.to_numpy()).all():
            raise ValueError("returns must contain finite values")
        if (series <= -1).any():
            raise ValueError("simple returns must be greater than -1")
        return series

    def _validate_features(
        self,
        values: pd.DataFrame | pd.Series | np.ndarray | None,
    ) -> pd.DataFrame:
        if values is None:
            frame = self._returns.to_frame(name=self._returns.name or "return")
        elif isinstance(values, pd.Series):
            frame = values.to_frame(name=values.name or "feature")
        elif isinstance(values, pd.DataFrame):
            frame = values.copy()
        else:
            array = np.asarray(values, dtype=float)
            if array.ndim == 1:
                array = array[:, None]
            if array.ndim != 2:
                raise ValueError("features must be one- or two-dimensional")
            frame = pd.DataFrame(array, index=self._returns.index)
        if len(frame) != len(self._returns):
            raise ValueError("features and returns must have the same length")
        if not frame.index.equals(self._returns.index):
            raise ValueError("features and returns must have identical indexes")
        try:
            frame = frame.astype(float)
        except (TypeError, ValueError):
            raise ValueError("features must be numeric") from None
        if frame.shape[1] == 0 or not np.isfinite(frame.to_numpy()).all():
            raise ValueError("features must contain finite numeric values")
        return frame

    @staticmethod
    def _initial_account() -> AccountState:
        return AccountState(
            equity=1.0,
            peak_equity=1.0,
            drawdown=0.0,
            position=0.0,
            cumulative_cost=0.0,
            steps=0,
        )

    @property
    def account(self) -> AccountState:
        """Current immutable account snapshot."""
        return self._account

    @property
    def feature_names(self) -> tuple[Any, ...]:
        """Feature column names in market-observation order."""
        return tuple(self._features.columns)

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
        """Reset account state and select the next episode range."""
        super().reset(seed=seed)
        options = options or {}
        unknown = options.keys() - {"start_index"}
        if unknown:
            names = ", ".join(sorted(unknown))
            raise ValueError(f"Unknown reset option(s): {names}")

        latest_start = len(self._returns) - (self.episode_length or 1)
        if "start_index" in options:
            start = self._positive_integer(options["start_index"], "start_index")
        elif self.random_start:
            start = int(self.np_random.integers(self.window_size, latest_start + 1))
        else:
            start = self.window_size
        if start < self.window_size or start > latest_start:
            raise ValueError("start_index does not leave enough history for the episode")

        self._cursor = start
        self._end = (
            start + self.episode_length
            if self.episode_length is not None
            else len(self._returns)
        )
        self._episode_done = False
        self._account = self._initial_account()
        return self._observation(), self._info()

    def step(
        self, action: np.ndarray
    ) -> tuple[dict[str, np.ndarray], float, bool, bool, dict[str, Any]]:
        """Execute a target position and apply the next market return."""
        if self._episode_done:
            raise RuntimeError("step() called after the episode ended; call reset()")
        if not self.action_space.contains(action):
            raise ValueError("action must be a finite float32 array in [-1, 1]")

        target_position = float(action[0])
        turnover = abs(target_position - self._account.position)
        cost_rate = turnover * self.transaction_cost
        market_return = float(self._returns.iloc[self._cursor])
        gross_return = target_position * market_return
        reward = gross_return - cost_rate
        previous_equity = self._account.equity
        equity = max(0.0, previous_equity * (1.0 + reward))
        peak_equity = max(self._account.peak_equity, equity)
        drawdown = equity / peak_equity - 1.0
        self._account = AccountState(
            equity=equity,
            peak_equity=peak_equity,
            drawdown=drawdown,
            position=target_position,
            cumulative_cost=(
                self._account.cumulative_cost + previous_equity * cost_rate
            ),
            steps=self._account.steps + 1,
        )
        timestamp = self._returns.index[self._cursor]
        self._cursor += 1

        insolvent = equity <= 0
        risk_breach = (
            self.max_drawdown is not None and drawdown <= -self.max_drawdown
        )
        terminated = bool(insolvent or risk_breach)
        truncated = bool(not terminated and self._cursor >= self._end)
        self._episode_done = terminated or truncated
        info = self._info(
            timestamp=timestamp,
            market_return=market_return,
            gross_return=gross_return,
            turnover=turnover,
            cost=previous_equity * cost_rate,
        )
        return self._observation(), float(reward), terminated, truncated, info

    def _observation(self) -> dict[str, np.ndarray]:
        market = self._features.iloc[
            self._cursor - self.window_size : self._cursor
        ].to_numpy(dtype=np.float32)
        account = np.asarray(
            [
                self._account.position,
                self._account.equity,
                self._account.drawdown,
                self._account.cumulative_cost,
            ],
            dtype=np.float32,
        )
        return {"market": market, "account": account}

    def _info(self, **transition: Any) -> dict[str, Any]:
        return {"account": asdict(self._account), **transition}

    def render(self) -> str | None:
        """Return a compact account summary in ANSI mode."""
        if self.render_mode != "ansi":
            return None
        return (
            f"step={self._account.steps} equity={self._account.equity:.6f} "
            f"position={self._account.position:+.3f} "
            f"drawdown={self._account.drawdown:.2%}"
        )
