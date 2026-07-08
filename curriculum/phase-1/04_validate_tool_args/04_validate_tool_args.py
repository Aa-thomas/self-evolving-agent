### =============================================================================
## Imports
## =============================================================================
from dataclasses import dataclass, field, fields, is_dataclass
import json
from typing import Any, Generic, Literal, TypeAlias, TypeVar

import typer
from pydantic import BaseModel, ConfigDict, StrictStr, ValidationError


### =============================================================================
## Setup
## =============================================================================
app = typer.Typer()


### =============================================================================
## Types
## =============================================================================
ErrorCode: TypeAlias = Literal[
    "INVALID_JSON",
    "INVALID_TOOL_REQUEST_SHAPE",
    "UNKNOWN_TOOL",
    "INVALID_TOOL_ARGS",
]

T = TypeVar("T")


@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T
    ok: Literal[True] = field(default=True, init=False)


@dataclass(frozen=True)
class Err:
    error: str
    error_code: ErrorCode
    ok: Literal[False] = field(default=False, init=False)


Result: TypeAlias = Ok[T] | Err


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


### =============================================================================
## Tool Args Schemas
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


### =============================================================================
## Tool Registry
## =============================================================================
tool_registry: dict[str, ToolSpec] = {
    "read_file": ToolSpec(name="read_file", args_schema=ReadFileArgs),
    "write_file": ToolSpec(name="write_file", args_schema=WriteFileArgs),
    "list_files": ToolSpec(name="list_files", args_schema=ListFilesArgs),
    "submit": ToolSpec(name="submit", args_schema=SubmitArgs),
}


### =============================================================================
## Validation Helpers
## =============================================================================
def parse_json(raw_text: str) -> Result[Any]:
    try:
        data = json.loads(raw_text)
        return Ok(data)

    except json.JSONDecodeError as error:
        return Err(
            error=str(error),
            error_code="INVALID_JSON",
        )


def validate_tool_request_shape(data: Any) -> Result[ToolRequest]:
    try:
        tool_request = ToolRequest.model_validate(data)
        return Ok(tool_request)

    except ValidationError as error:
        return Err(
            error=str(error),
            error_code="INVALID_TOOL_REQUEST_SHAPE",
        )


def validate_tool_exists(tool_request: ToolRequest) -> Result[ToolRequest]:
    if tool_request.tool not in tool_registry:
        return Err(
            error=f"Unknown tool: {tool_request.tool}",
            error_code="UNKNOWN_TOOL",
        )

    return Ok(tool_request)


def validate_tool_args(tool_request: ToolRequest) -> Result[ValidatedToolRequest]:
    try:
        tool_spec = tool_registry[tool_request.tool]
        validated_args = tool_spec.args_schema.model_validate(tool_request.args)

        validated_tool_request = ValidatedToolRequest(
            tool=tool_request.tool,
            args=validated_args,
        )

        return Ok(validated_tool_request)

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

    args_result = validate_tool_args(exists_result.value)

    return args_result


### =============================================================================
## Serialization Helpers
## =============================================================================
def to_jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump()

    if is_dataclass(value):
        return {
            field.name: to_jsonable(getattr(value, field.name))
            for field in fields(value)
        }

    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}

    if isinstance(value, list):
        return [to_jsonable(item) for item in value]

    return value


def result_to_dict(result: Result[Any]) -> dict[str, Any]:
    if isinstance(result, Err):
        return {
            "ok": False,
            "error": result.error,
            "error_code": result.error_code,
        }

    return {
        "ok": True,
        "value": to_jsonable(result.value),
    }


### =============================================================================
## Application
## =============================================================================
@app.command()
def parse_tool_request(raw_text: str) -> None:
    result = validate_tool_request(raw_text)
    typer.echo(json.dumps(result_to_dict(result), indent=2))


### =============================================================================
## Program Init
## =============================================================================
if __name__ == "__main__":
    app()
