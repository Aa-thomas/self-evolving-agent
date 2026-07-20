"""Starter contract for Primitive 8: evaluate composed harness behavior.

The learner implements this runner after the trace-logger primitive.  Cases
carry an executable scenario and explicit assertions so a failed workflow has
an inspectable causal artifact instead of only a boolean result.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class EvalCase:
    name: str
    run: Callable[[], dict[str, Any]]
    expected: dict[str, Any]
    trace_path: str


@dataclass(frozen=True)
class EvalCaseResult:
    name: str
    passed: bool
    actual: dict[str, Any]
    expected: dict[str, Any]
    trace_path: str
    failure_reason: str | None


@dataclass(frozen=True)
class EvalReport:
    total: int
    passed: int
    failed: int
    cases: list[EvalCaseResult]


def evaluate_case(case: EvalCase) -> EvalCaseResult:
    raise NotImplementedError("Implement one composed-case evaluation in this lesson.")


def run_eval_suite(cases: list[EvalCase]) -> EvalReport:
    raise NotImplementedError("Implement aggregate evaluation and failure reporting in this lesson.")
