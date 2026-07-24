"""Versioned evaluation suites and regression reports."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from typing import Any

from pydantic import Field

from qrt.ai.types import AIModel


class EvalCase(AIModel):
    name: str
    input: Any
    expected: Any | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvalScore(AIModel):
    case: str
    scorer: str
    value: float
    details: dict[str, Any] = Field(default_factory=dict)


class EvalReport(AIModel):
    suite: str
    subject: str
    scores: tuple[EvalScore, ...]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def mean_score(self) -> float:
        return sum(score.value for score in self.scores) / len(self.scores) if self.scores else 0.0


class Suite:
    """Run deterministic or model-based scorers over held-out cases."""

    def __init__(self, name: str, cases: Sequence[EvalCase], scorers: Sequence[Callable[[Any, Any], float]]) -> None:
        self.name = name
        self.cases = tuple(cases)
        self.scorers = tuple(scorers)

    def run(self, subject: Callable[[Any], Any], *, subject_name: str) -> EvalReport:
        scores = []
        for case in self.cases:
            actual = subject(case.input)
            for scorer in self.scorers:
                scores.append(
                    EvalScore(
                        case=case.name,
                        scorer=getattr(scorer, "__name__", type(scorer).__name__),
                        value=float(scorer(actual, case.expected)),
                    )
                )
        return EvalReport(suite=self.name, subject=subject_name, scores=tuple(scores))

    def to_pydantic_dataset(self):
        from pydantic_evals import Case, Dataset

        return Dataset(
            name=self.name,
            cases=[Case(name=case.name, inputs=case.input, expected_output=case.expected, metadata=case.metadata) for case in self.cases],
        )


def exact_match(actual: Any, expected: Any) -> float:
    return float(actual == expected)