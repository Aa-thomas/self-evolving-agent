from __future__ import annotations

"""Validate arguments for a ToolRequest already produced by Primitive 3."""

from collections.abc import Callable
from dataclasses import dataclass, field
import importlib.util
import json
from pathlib import Path
import sys
from typing import Generic, Literal, TypeAlias, TypeVar, assert_never

import typer
from pydantic import BaseModel, ConfigDict, StrictStr, ValidationError


app = typer.Typer()
T = TypeVar("T", covariant=True)
E = TypeVar("E", covariant=True)


@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    value: T


@dataclass(frozen=True, slots=True)
class Err(Generic[E]):
    error: E


Result: TypeAlias = Ok[T] | Err[E]


def load_parser_module():
    """Load Primitive 3's concrete output contract without duplicating it here."""
    path = Path(__file__).resolve().parents[1] / "03_parse_tool_request.py"
    spec = importlib.util.spec_from_file_location("parse_tool_request_primitive", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load Primitive 3's ToolRequest contract.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


parser = load_parser_module()
ToolRequest = parser.ToolRequest


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReadFileArgs(StrictModel):
    path: StrictStr


class WriteFileArgs(StrictModel):
    path: StrictStr
    content: StrictStr


class ListFilesArgs(StrictModel):
    path: StrictStr | None = None


class SubmitArgs(StrictModel):
    answer: StrictStr


@dataclass(frozen=True, slots=True)
class ReadFileRequest:
    args: ReadFileArgs
    tool: Literal["read_file"] = field(default="read_file", init=False)


@dataclass(frozen=True, slots=True)
class WriteFileRequest:
    args: WriteFileArgs
    tool: Literal["write_file"] = field(default="write_file", init=False)


@dataclass(frozen=True, slots=True)
class ListFilesRequest:
    args: ListFilesArgs
    tool: Literal["list_files"] = field(default="list_files", init=False)


@dataclass(frozen=True, slots=True)
class SubmitRequest:
    args: SubmitArgs
    tool: Literal["submit"] = field(default="submit", init=False)


ValidatedToolRequest: TypeAlias = (
    ReadFileRequest | WriteFileRequest | ListFilesRequest | SubmitRequest
)


@dataclass(frozen=True, slots=True)
class UnknownTool:
    tool: str
    error_code: Literal["UNKNOWN_TOOL"] = field(default="UNKNOWN_TOOL", init=False)


@dataclass(frozen=True, slots=True)
class InvalidToolArgs:
    tool: str
    details: str
    error_code: Literal["INVALID_TOOL_ARGS"] = field(default="INVALID_TOOL_ARGS", init=False)


ValidationErrorResult: TypeAlias = UnknownTool | InvalidToolArgs
ToolArgsParser: TypeAlias = Callable[[dict[str, object]], ValidatedToolRequest]


@dataclass(frozen=True, slots=True)
class ToolSpec:
    parse_args: ToolArgsParser


def parse_read_file_args(raw_args: dict[str, object]) -> ReadFileRequest:
    return ReadFileRequest(args=ReadFileArgs.model_validate(raw_args))


def parse_write_file_args(raw_args: dict[str, object]) -> WriteFileRequest:
    return WriteFileRequest(args=WriteFileArgs.model_validate(raw_args))


def parse_list_files_args(raw_args: dict[str, object]) -> ListFilesRequest:
    return ListFilesRequest(args=ListFilesArgs.model_validate(raw_args))


def parse_submit_args(raw_args: dict[str, object]) -> SubmitRequest:
    return SubmitRequest(args=SubmitArgs.model_validate(raw_args))


tool_registry: dict[str, ToolSpec] = {
    "read_file": ToolSpec(parse_args=parse_read_file_args),
    "write_file": ToolSpec(parse_args=parse_write_file_args),
    "list_files": ToolSpec(parse_args=parse_list_files_args),
    "submit": ToolSpec(parse_args=parse_submit_args),
}


def validate_tool_args(request: ToolRequest) -> Result[ValidatedToolRequest, ValidationErrorResult]:
    """Validate tool existence and tool-specific arguments, never raw model text."""
    tool_spec = tool_registry.get(request.tool)
    if tool_spec is None:
        return Err(UnknownTool(tool=request.tool))
    try:
        return Ok(tool_spec.parse_args(request.args))
    except ValidationError as error:
        return Err(InvalidToolArgs(tool=request.tool, details=str(error)))


def validated_request_to_dict(request: ValidatedToolRequest) -> dict[str, object]:
    match request:
        case ReadFileRequest(args=args) | WriteFileRequest(args=args) | ListFilesRequest(args=args) | SubmitRequest(args=args):
            return {"tool": request.tool, "args": args.model_dump()}
        case unreachable:
            assert_never(unreachable)


def error_to_dict(error: ValidationErrorResult) -> dict[str, object]:
    match error:
        case UnknownTool(tool=tool):
            return {"error_code": error.error_code, "error": f"Unknown tool: {tool}"}
        case InvalidToolArgs(tool=tool, details=details):
            return {"error_code": error.error_code, "error": f"Invalid arguments for {tool}: {details}"}
        case unreachable:
            assert_never(unreachable)


def result_to_dict(result: Result[ValidatedToolRequest, ValidationErrorResult]) -> dict[str, object]:
    if isinstance(result, Err):
        return {"ok": False, **error_to_dict(result.error)}
    return {"ok": True, "value": validated_request_to_dict(result.value)}


@app.command()
def main(raw_text: str) -> None:
    """Compose P3 then P4 for CLI exploration while preserving boundary ownership."""
    parsed = parser.parse_tool_request(raw_text)
    if isinstance(parsed, parser.Err):
        typer.echo(json.dumps({"ok": False, "error_code": parsed.error.code, "error": parsed.error.message}, indent=2))
        raise typer.Exit(code=1)
    typer.echo(json.dumps(result_to_dict(validate_tool_args(parsed.value)), indent=2))


if __name__ == "__main__":
    app()
