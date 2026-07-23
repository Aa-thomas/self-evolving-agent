from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias, cast

from pydantic import BaseModel, ConfigDict, ValidationError

from parse_tool_request import (
    ParseToolRequestError,
    ToolRequest,
    parse_tool_request,
)
from result import Err, Ok, Result


class StrictArgsModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )


class ReadFileArgs(StrictArgsModel):
    path: str


class WriteFileArgs(StrictArgsModel):
    path: str
    content: str


class ListFilesArgs(StrictArgsModel):
    path: str | None = None


class SubmitArgs(StrictArgsModel):
    answer: str


KnownToolName: TypeAlias = Literal[
    "read_file",
    "write_file",
    "list_files",
    "submit",
]

ToolArgs: TypeAlias = (
    ReadFileArgs | WriteFileArgs | ListFilesArgs | SubmitArgs
)

ToolArgsSchema: TypeAlias = (
    type[ReadFileArgs]
    | type[WriteFileArgs]
    | type[ListFilesArgs]
    | type[SubmitArgs]
)


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: KnownToolName
    args_schema: ToolArgsSchema


@dataclass(frozen=True, slots=True)
class ValidatedToolRequest:
    tool: KnownToolName
    args: ToolArgs


TOOL_SPECS: dict[str, ToolSpec] = {
    "read_file": ToolSpec(
        name="read_file",
        args_schema=ReadFileArgs,
    ),
    "write_file": ToolSpec(
        name="write_file",
        args_schema=WriteFileArgs,
    ),
    "list_files": ToolSpec(
        name="list_files",
        args_schema=ListFilesArgs,
    ),
    "submit": ToolSpec(
        name="submit",
        args_schema=SubmitArgs,
    ),
}


@dataclass(frozen=True, slots=True)
class UnknownToolError:
    tool: str
    message: str
    code: Literal["UNKNOWN_TOOL"] = "UNKNOWN_TOOL"


@dataclass(frozen=True, slots=True)
class InvalidToolArgsError:
    tool: KnownToolName
    message: str
    code: Literal["INVALID_TOOL_ARGS"] = "INVALID_TOOL_ARGS"


ValidateToolArgsError: TypeAlias = UnknownToolError | InvalidToolArgsError

ValidateToolArgsResult: TypeAlias = Result[
    ValidatedToolRequest,
    ValidateToolArgsError,
]

ParseAndValidateError: TypeAlias = (
    ParseToolRequestError | ValidateToolArgsError
)

ParseAndValidateResult: TypeAlias = Result[
    ValidatedToolRequest,
    ParseAndValidateError,
]


def validate_tool_args(request: ToolRequest) -> ValidateToolArgsResult:
    spec = TOOL_SPECS.get(request.tool)

    if spec is None:
        return Err(
            UnknownToolError(
                tool=request.tool,
                message=f"Unknown tool: {request.tool}",
            )
        )

    try:
        validated_args = spec.args_schema.model_validate(request.args)

    except ValidationError as error:
        return Err(
            InvalidToolArgsError(
                tool=spec.name,
                message=str(error),
            )
        )

    return Ok(
        ValidatedToolRequest(
            tool=spec.name,
            args=cast(ToolArgs, validated_args),
        )
    )


def parse_and_validate_tool_request(raw_text: str) -> ParseAndValidateResult:
    return parse_tool_request(raw_text).and_then(validate_tool_args)
