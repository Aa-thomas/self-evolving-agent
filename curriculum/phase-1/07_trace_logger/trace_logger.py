"""Starter contract for Primitive 7: capture replayable agent-run evidence.

Runtime domain objects are deliberately adapted into trace-owned records before
they cross the persistence boundary.  The learner implements the logger and the
narrow agent-loop hook during the trace-logger lab; this starter supplies the
stable schema without supplying the finished logging mechanism.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Literal, TypeAlias, assert_never

from pydantic import JsonValue

from parse_tool_request import (
    InvalidJsonError,
    InvalidToolRequestShapeError,
)
from validate_tool_args import (
    InvalidToolArgsError,
    KnownToolName,
    ParseAndValidateResult,
    UnknownToolError,
)
from result import Err, Ok


## =============================================================================
## Stable Trace Types
## =============================================================================
class RequestStage(StrEnum):
    JSON = "json"
    REQUEST_SHAPE = "request_shape"
    TOOL_LOOKUP = "tool_lookup"
    TOOL_ARGUMENTS = "tool_arguments"


class TraceExitReason(StrEnum):
    SUBMITTED = "submitted"
    MAX_STEPS = "max_steps"


@dataclass(frozen=True, slots=True)
class TraceMessage:
    role: str
    content: str


@dataclass(frozen=True, slots=True)
class RequestAccepted:
    tool: KnownToolName
    kind: Literal["accepted"] = "accepted"


@dataclass(frozen=True, slots=True)
class RequestRejected:
    stage: RequestStage
    code: str
    message: str
    kind: Literal["rejected"] = "rejected"


RequestOutcome: TypeAlias = RequestAccepted | RequestRejected


@dataclass(frozen=True, slots=True)
class ExecuteToolSelected:
    tool: KnownToolName
    kind: Literal["execute_tool"] = "execute_tool"


@dataclass(frozen=True, slots=True)
class SubmitSelected:
    answer: str
    kind: Literal["submit"] = "submit"


TraceAction: TypeAlias = ExecuteToolSelected | SubmitSelected


@dataclass(frozen=True, slots=True)
class ToolSucceeded:
    tool: KnownToolName
    value: JsonValue
    kind: Literal["succeeded"] = "succeeded"


@dataclass(frozen=True, slots=True)
class ToolFailed:
    tool: KnownToolName
    code: str
    message: str
    kind: Literal["failed"] = "failed"


ToolOutcome: TypeAlias = ToolSucceeded | ToolFailed


@dataclass(frozen=True, slots=True)
class TraceStep:
    step_number: int
    assistant_output: str
    request_outcome: RequestOutcome
    action: TraceAction | None
    tool_outcome: ToolOutcome | None
    exit_reason: TraceExitReason | None


@dataclass(frozen=True, slots=True)
class AgentTrace:
    initial_messages: tuple[TraceMessage, ...]
    steps: tuple[TraceStep, ...]
    final_answer: str | None
    exit_reason: TraceExitReason
    schema_version: Literal[1] = 1


## =============================================================================
## Runtime-to-Trace Adapters
## =============================================================================
def request_result_to_trace(
    result: ParseAndValidateResult,
) -> RequestOutcome:
    """Remove runtime Result/error types before an outcome is persisted."""
    if isinstance(result, Ok):
        return RequestAccepted(tool=result.value.tool)

    if not isinstance(result, Err):
        raise TypeError(
            f"Unsupported Result variant: {type(result).__name__}"
        )

    error = result.error

    if isinstance(error, InvalidJsonError):
        return RequestRejected(
            stage=RequestStage.JSON,
            code=error.code,
            message=error.message,
        )

    if isinstance(error, InvalidToolRequestShapeError):
        return RequestRejected(
            stage=RequestStage.REQUEST_SHAPE,
            code=error.code,
            message=error.message,
        )

    if isinstance(error, UnknownToolError):
        return RequestRejected(
            stage=RequestStage.TOOL_LOOKUP,
            code=error.code,
            message=error.message,
        )

    if isinstance(error, InvalidToolArgsError):
        return RequestRejected(
            stage=RequestStage.TOOL_ARGUMENTS,
            code=error.code,
            message=error.message,
        )

    assert_never(error)


def exit_reason_to_trace(exit_reason: str) -> TraceExitReason:
    """Translate a runtime exit value into the versioned trace vocabulary."""
    return TraceExitReason(exit_reason)


## =============================================================================
## Learner-Build Logger
## =============================================================================
@dataclass
class TraceLogger:
    """Collect causal steps from an agent run and write versioned JSON."""

    initial_messages: list[TraceMessage] = field(default_factory=list)
    steps: list[TraceStep] = field(default_factory=list)
    trace: AgentTrace | None = None

    def start(self, initial_messages: list[dict[str, str]]) -> None:
        """Record the exact message state supplied to the first model call."""
        raise NotImplementedError("Implement trace initialization in this lesson.")

    def record_step(
        self,
        *,
        assistant_output: str,
        request_outcome: RequestOutcome,
        action: TraceAction | None,
        tool_outcome: ToolOutcome | None,
        exit_reason: TraceExitReason | None,
    ) -> None:
        raise NotImplementedError("Implement causal trace-step capture in this lesson.")

    def finish(
        self,
        *,
        final_answer: str | None,
        exit_reason: TraceExitReason,
    ) -> AgentTrace:
        raise NotImplementedError("Implement trace finalization in this lesson.")

    def write_json(self, destination: Path, trace: AgentTrace) -> None:
        raise NotImplementedError("Implement replayable trace serialization in this lesson.")
