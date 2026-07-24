from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from enum import StrEnum
import json
from typing import TYPE_CHECKING, Any, Literal, Protocol, TypeAlias, assert_never

from pydantic import BaseModel

from validate_tool_args import (
    KnownToolName,
    SubmitArgs,
    ValidatedToolRequest,
    parse_and_validate_tool_request,
)
from result import Err, Ok, Result

if TYPE_CHECKING:
    from trace_logger import TraceLogger


## =============================================================================
## Types
## =============================================================================
class Model(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> str: ...


class ExitReason(StrEnum):
    SUBMITTED = "submitted"
    MAX_STEPS = "max_steps"


@dataclass(frozen=True, slots=True)
class AgentResult:
    exit_reason: ExitReason
    final_answer: str | None


@dataclass(frozen=True, slots=True)
class SubmitAction:
    answer: str


@dataclass(frozen=True, slots=True)
class ExecuteToolAction:
    request: ValidatedToolRequest


AgentAction: TypeAlias = SubmitAction | ExecuteToolAction


def classify_action(
    request: ValidatedToolRequest,
) -> AgentAction:
    if request.tool == "submit":
        assert isinstance(request.args, SubmitArgs)
        return SubmitAction(answer=request.args.answer)

    return ExecuteToolAction(request=request)


@dataclass(frozen=True, slots=True)
class UnavailableRuntimeToolError:
    tool: KnownToolName
    message: str
    code: Literal["RUNTIME_TOOL_UNAVAILABLE"] = "RUNTIME_TOOL_UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class ToolExceptionError:
    tool: KnownToolName
    message: str
    code: Literal["TOOL_EXCEPTION"] = "TOOL_EXCEPTION"


RuntimeToolError: TypeAlias = (
    UnavailableRuntimeToolError | ToolExceptionError
)

RuntimeToolResult: TypeAlias = Result[Any, RuntimeToolError]
ToolHandlers: TypeAlias = Mapping[str, Callable[..., Any]]


## =============================================================================
## Serialization Helpers
## =============================================================================
def to_jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump()

    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: to_jsonable(getattr(value, field.name))
            for field in fields(value)
        }

    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}

    if isinstance(value, list):
        return [to_jsonable(item) for item in value]

    return value


def result_to_dict(result: Any) -> dict[str, Any]:
    if isinstance(result, Err):
        typed_error = result.error

        if hasattr(typed_error, "code") and hasattr(typed_error, "message"):
            return {
                "ok": False,
                "error_code": to_jsonable(typed_error.code),
                "error": to_jsonable(typed_error.message),
            }

        return {
            "ok": False,
            "error_code": "UNKNOWN_ERROR",
            "error": str(typed_error),
        }

    if isinstance(result, Ok):
        return {
            "ok": True,
            "value": to_jsonable(result.value),
        }

    if hasattr(result, "error_code") and hasattr(result, "error"):
        return {
            "ok": False,
            "error_code": to_jsonable(result.error_code),
            "error": to_jsonable(result.error),
        }

    if hasattr(result, "value"):
        return {
            "ok": True,
            "value": to_jsonable(result.value),
        }

    if isinstance(result, dict) and "ok" in result:
        return to_jsonable(result)

    return {
        "ok": True,
        "value": to_jsonable(result),
    }


def observation_content(result: Any) -> str:
    return json.dumps(result_to_dict(result), sort_keys=True)


def args_to_dict(args: BaseModel) -> dict[str, Any]:
    return args.model_dump(exclude_none=True)


def unknown_tool_result(
    tool_name: KnownToolName,
) -> Result[Any, UnavailableRuntimeToolError]:
    return Err(
        UnavailableRuntimeToolError(
            tool=tool_name,
            message=f"Unknown tool: {tool_name}",
        )
    )


def execute_tool_action(
    action: ExecuteToolAction,
    tools: ToolHandlers,
) -> Any:
    request = action.request

    if request.tool not in tools:
        return unknown_tool_result(request.tool)

    try:
        return tools[request.tool](**args_to_dict(request.args))
    except Exception as error:
        return Err(
            ToolExceptionError(
                tool=request.tool,
                message=str(error),
            )
        )


## =============================================================================
## Agent Loop
## =============================================================================
def run_agent(
    user_task: str,
    model: Model,
    tools: ToolHandlers,
    max_steps: int,
    trace_logger: TraceLogger | None = None,
) -> AgentResult:
    messages = [{"role": "user", "content": user_task}]

    if trace_logger is not None:
        from trace_logger import (
            ExecuteToolSelected,
            SubmitSelected,
            ToolFailed,
            ToolSucceeded,
            exit_reason_to_trace,
            request_result_to_trace,
        )

        trace_logger.start(messages)

    for step_index in range(max_steps):
        assistant_output = model.complete(messages)
        messages.append({"role": "assistant", "content": assistant_output})

        request_result = parse_and_validate_tool_request(assistant_output)

        if isinstance(request_result, Err):
            if trace_logger is not None:
                trace_exit_reason = (
                    exit_reason_to_trace(ExitReason.MAX_STEPS)
                    if step_index == max_steps - 1
                    else None
                )
                trace_logger.record_step(
                    assistant_output=assistant_output,
                    request_outcome=request_result_to_trace(request_result),
                    action=None,
                    tool_outcome=None,
                    exit_reason=trace_exit_reason,
                )

            messages.append(
                {"role": "tool", "content": observation_content(request_result)}
            )
            continue

        if not isinstance(request_result, Ok):
            raise TypeError(
                f"Unsupported Result variant: {type(request_result).__name__}"
            )

        action = classify_action(request_result.value)

        match action:
            case SubmitAction(answer=answer):
                if trace_logger is not None:
                    trace_exit_reason = exit_reason_to_trace(
                        ExitReason.SUBMITTED
                    )
                    trace_logger.record_step(
                        assistant_output=assistant_output,
                        request_outcome=request_result_to_trace(request_result),
                        action=SubmitSelected(answer=answer),
                        tool_outcome=None,
                        exit_reason=trace_exit_reason,
                    )
                    trace_logger.finish(
                        final_answer=answer,
                        exit_reason=trace_exit_reason,
                    )

                return AgentResult(
                    exit_reason=ExitReason.SUBMITTED,
                    final_answer=answer,
                )

            case ExecuteToolAction():
                tool_result = execute_tool_action(action, tools)

                if trace_logger is not None:
                    if isinstance(tool_result, Err):
                        error = tool_result.unwrap_err()
                        tool_outcome = ToolFailed(
                            tool=action.request.tool,
                            code=getattr(error, "code", "UNKNOWN_ERROR"),
                            message=getattr(error, "message", str(error)),
                        )
                    else:
                        tool_value = (
                            tool_result.unwrap()
                            if isinstance(tool_result, Ok)
                            else tool_result
                        )
                        tool_outcome = ToolSucceeded(
                            tool=action.request.tool,
                            value=to_jsonable(tool_value),
                        )

                    trace_exit_reason = (
                        exit_reason_to_trace(ExitReason.MAX_STEPS)
                        if step_index == max_steps - 1
                        else None
                    )
                    trace_logger.record_step(
                        assistant_output=assistant_output,
                        request_outcome=request_result_to_trace(request_result),
                        action=ExecuteToolSelected(
                            tool=action.request.tool
                        ),
                        tool_outcome=tool_outcome,
                        exit_reason=trace_exit_reason,
                    )

                messages.append(
                    {
                        "role": "tool",
                        "content": observation_content(tool_result),
                    }
                )

            case _:
                assert_never(action)

    if trace_logger is not None:
        trace_logger.finish(
            final_answer=None,
            exit_reason=exit_reason_to_trace(ExitReason.MAX_STEPS),
        )

    return AgentResult(
        exit_reason=ExitReason.MAX_STEPS,
        final_answer=None,
    )
