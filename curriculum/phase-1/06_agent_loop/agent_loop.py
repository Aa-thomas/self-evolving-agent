from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
import json
from typing import Any, Callable, Generic, Literal, Protocol, TypeAlias, TypeVar

from pydantic import BaseModel, ConfigDict, StrictStr, ValidationError


## =============================================================================
## Types
## =============================================================================
class Model(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> str: ...


T = TypeVar("T")


@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T
    ok: Literal[True] = field(default=True, init=False)


@dataclass(frozen=True)
class Err:
    error: str
    error_code: str
    ok: Literal[False] = field(default=False, init=False)


Result: TypeAlias = Ok[T] | Err
ExitReason: TypeAlias = Literal["submitted", "max_steps"]


@dataclass(frozen=True)
class AgentResult:
    exit_reason: ExitReason
    final_answer: str | None
    trace: list[dict[str, Any]]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ToolRequest(StrictModel):
    tool: StrictStr
    args: dict[str, Any]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    args_schema: type[BaseModel]


@dataclass(frozen=True)
class ValidatedToolRequest:
    tool: str
    args: BaseModel


## =============================================================================
## Tool Arg Schemas
## =============================================================================
class ReadFileArgs(StrictModel):
    path: StrictStr


class WriteFileArgs(StrictModel):
    path: StrictStr
    content: StrictStr


class ListFilesArgs(StrictModel):
    path: StrictStr | None = None


class SubmitArgs(StrictModel):
    answer: StrictStr


TOOL_REGISTRY: dict[str, ToolSpec] = {
    "read_file": ToolSpec(name="read_file", args_schema=ReadFileArgs),
    "write_file": ToolSpec(name="write_file", args_schema=WriteFileArgs),
    "list_files": ToolSpec(name="list_files", args_schema=ListFilesArgs),
    "submit": ToolSpec(name="submit", args_schema=SubmitArgs),
}


## =============================================================================
## Validation Helpers
## =============================================================================
def parse_json(raw_text: str) -> Result[Any]:
    try:
        return Ok(json.loads(raw_text))
    except json.JSONDecodeError as error:
        return Err(
            error=str(error),
            error_code="INVALID_JSON",
        )


def validate_tool_request_shape(data: Any) -> Result[ToolRequest]:
    try:
        return Ok(ToolRequest.model_validate(data))
    except ValidationError as error:
        return Err(
            error=str(error),
            error_code="INVALID_TOOL_REQUEST_SHAPE",
        )


def validate_tool_exists(tool_request: ToolRequest) -> Result[ToolRequest]:
    if tool_request.tool not in TOOL_REGISTRY:
        return Err(
            error=f"Unknown tool: {tool_request.tool}",
            error_code="UNKNOWN_TOOL",
        )

    return Ok(tool_request)


def validate_tool_args(tool_request: ToolRequest) -> Result[ValidatedToolRequest]:
    try:
        tool_spec = TOOL_REGISTRY[tool_request.tool]
        validated_args = tool_spec.args_schema.model_validate(tool_request.args)
        return Ok(
            ValidatedToolRequest(
                tool=tool_request.tool,
                args=validated_args,
            )
        )
    except ValidationError as error:
        return Err(
            error=str(error),
            error_code="INVALID_TOOL_ARGS",
        )


def validate_tool_request(raw_text: str) -> Result[ValidatedToolRequest]:
    json_result = parse_json(raw_text)

    if isinstance(json_result, Err):
        return json_result

    shape_result = validate_tool_request_shape(json_result.value)

    if isinstance(shape_result, Err):
        return shape_result

    exists_result = validate_tool_exists(shape_result.value)

    if isinstance(exists_result, Err):
        return exists_result

    return validate_tool_args(exists_result.value)


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
        return {
            "ok": False,
            "error_code": result.error_code,
            "error": result.error,
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


def request_to_dict(request: ValidatedToolRequest) -> dict[str, Any]:
    return {
        "tool": request.tool,
        "args": args_to_dict(request.args),
    }


def unknown_tool_result(tool_name: str) -> Err:
    return Err(
        error=f"Unknown tool: {tool_name}",
        error_code="UNKNOWN_TOOL",
    )


## =============================================================================
## Agent Loop
## =============================================================================
def run_agent(
    user_task: str,
    model: Model,
    tools: dict[str, Callable[..., Any]],
    max_steps: int,
) -> AgentResult:
    messages = [{"role": "user", "content": user_task}]
    trace: list[dict[str, Any]] = []

    for step in range(max_steps):
        assistant_output = model.complete(messages)
        messages.append({"role": "assistant", "content": assistant_output})

        step_record: dict[str, Any] = {
            "step": step,
            "assistant_output": assistant_output,
            "parsed_action": None,
            "tool_result": None,
            "exit_reason": None,
        }

        request_result = validate_tool_request(assistant_output)

        if isinstance(request_result, Err):
            step_record["tool_result"] = result_to_dict(request_result)
            trace.append(step_record)
            messages.append(
                {"role": "tool", "content": observation_content(request_result)}
            )
            continue

        request = request_result.value
        step_record["parsed_action"] = request_to_dict(request)

        if request.tool == "submit":
            final_answer = request.args.model_dump()["answer"]
            step_record["exit_reason"] = "submitted"
            trace.append(step_record)
            return AgentResult(
                exit_reason="submitted",
                final_answer=final_answer,
                trace=trace,
            )

        if request.tool not in tools:
            tool_result = unknown_tool_result(request.tool)
        else:
            try:
                tool_result = tools[request.tool](**args_to_dict(request.args))
            except Exception as error:
                tool_result = Err(
                    error=str(error),
                    error_code="TOOL_EXCEPTION",
                )

        step_record["tool_result"] = result_to_dict(tool_result)
        trace.append(step_record)
        messages.append({"role": "tool", "content": observation_content(tool_result)})

    if trace:
        trace[-1]["exit_reason"] = "max_steps"

    return AgentResult(
        exit_reason="max_steps",
        final_answer=None,
        trace=trace,
    )
