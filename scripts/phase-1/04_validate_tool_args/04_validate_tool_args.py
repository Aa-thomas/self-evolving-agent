### =============================================================================
## Imports
## =============================================================================
from dataclasses import dataclass, fields, is_dataclass
import json
from typing import Any, Literal, TypeAlias

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


@dataclass(frozen=True)
class Result:
    ok: bool
    value: Any = None
    error: str | None = None
    error_code: ErrorCode | None = None


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
def parse_json(raw_text: str) -> Result:
    try:
        data = json.loads(raw_text)
        return Result(ok=True, value=data)

    except json.JSONDecodeError as error:
        return Result(
            ok=False,
            error=str(error),
            error_code="INVALID_JSON",
        )


def validate_tool_request_shape(data: Any) -> Result:
    try:
        tool_request = ToolRequest.model_validate(data)
        return Result(ok=True, value=tool_request)

    except ValidationError as error:
        return Result(
            ok=False,
            error=str(error),
            error_code="INVALID_TOOL_REQUEST_SHAPE",
        )


def validate_tool_exists(tool_request: ToolRequest) -> Result:
    if tool_request.tool not in tool_registry:
        return Result(
            ok=False,
            error=f"Unknown tool: {tool_request.tool}",
            error_code="UNKNOWN_TOOL",
        )

    return Result(ok=True, value=tool_request)


def validate_tool_args(tool_request: ToolRequest) -> Result:
    try:
        tool_spec = tool_registry[tool_request.tool]
        validated_args = tool_spec.args_schema.model_validate(tool_request.args)

        validated_tool_request = ValidatedToolRequest(
            tool=tool_request.tool,
            args=validated_args,
        )

        return Result(ok=True, value=validated_tool_request)

    except ValidationError as error:
        return Result(
            ok=False,
            error=str(error),
            error_code="INVALID_TOOL_ARGS",
        )


def validate_tool_request(raw_text: str) -> Result:
    json_result = parse_json(raw_text)

    if not json_result.ok:
        return json_result

    shape_result = validate_tool_request_shape(json_result.value)

    if not shape_result.ok:
        return shape_result

    exists_result = validate_tool_exists(shape_result.value)

    if not exists_result.ok:
        return exists_result

    args_result = validate_tool_args(exists_result.value)

    if not args_result.ok:
        return args_result

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


def result_to_dict(result: Result) -> dict[str, Any]:
    if not result.ok:
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
