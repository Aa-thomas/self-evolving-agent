"""Starter contract for Primitive 7: capture replayable agent-run evidence.

The learner implements this file during the trace-logger lab.  It deliberately
contains interfaces and no finished logging mechanism so the lesson never
reveals the solution before the diagnostic work.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TraceStep:
    step: int
    assistant_output: str
    parse_result: dict[str, Any]
    validation_result: dict[str, Any]
    runtime_handler: str | None
    tool_result: dict[str, Any] | None
    exit_reason: str | None


@dataclass(frozen=True)
class AgentTrace:
    initial_messages: list[dict[str, str]]
    steps: list[TraceStep]
    final_answer: str | None
    exit_reason: str | None


@dataclass
class TraceLogger:
    """Collect causal steps from an agent run and write a replayable JSON trace."""

    initial_messages: list[dict[str, str]]
    steps: list[TraceStep] = field(default_factory=list)

    def record_step(
        self,
        *,
        assistant_output: str,
        parse_result: dict[str, Any],
        validation_result: dict[str, Any],
        runtime_handler: str | None,
        tool_result: dict[str, Any] | None,
        exit_reason: str | None,
    ) -> None:
        raise NotImplementedError("Implement causal trace-step capture in this lesson.")

    def finish(self, *, final_answer: str | None, exit_reason: str) -> AgentTrace:
        raise NotImplementedError("Implement trace finalization in this lesson.")

    def write_json(self, destination: Path, trace: AgentTrace) -> None:
        raise NotImplementedError("Implement replayable trace serialization in this lesson.")
