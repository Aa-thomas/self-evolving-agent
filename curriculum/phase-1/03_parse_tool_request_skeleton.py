"""Starter scaffold for Primitive 3: strict tool-request parsing.

Build this primitive from the contracts below.  The completed implementation
is deliberately not included here: the learner should make the parser's two
claims explicit, then use the focused tests as proof.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Generic, Literal, TypeAlias, TypeVar

import typer
from pydantic import BaseModel, ConfigDict, JsonValue, StrictStr, ValidationError


app = typer.Typer()

T_co = TypeVar("T_co", covariant=True)
E_co = TypeVar("E_co", covariant=True)


@dataclass(frozen=True, slots=True)
class Ok(Generic[T_co]):
    value: T_co


@dataclass(frozen=True, slots=True)
class Err(Generic[E_co]):
    error: E_co


Result: TypeAlias = Ok[T_co] | Err[E_co]


@dataclass(frozen=True, slots=True)
class InvalidJsonError:
    message: str
    code: Literal["INVALID_JSON"] = "INVALID_JSON"


@dataclass(frozen=True, slots=True)
class InvalidToolRequestShapeError:
    message: str
    code: Literal["INVALID_TOOL_REQUEST_SHAPE"] = "INVALID_TOOL_REQUEST_SHAPE"


ParseToolRequestError: TypeAlias = InvalidJsonError | InvalidToolRequestShapeError


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ToolRequest(StrictModel):
    """The outer protocol shape established by this primitive."""

    tool: StrictStr
    args: dict[str, JsonValue]


ParseJsonResult: TypeAlias = Result[JsonValue, InvalidJsonError]
ValidateToolRequestResult: TypeAlias = Result[
    ToolRequest,
    InvalidToolRequestShapeError,
]
ParseToolRequestResult: TypeAlias = Result[
    ToolRequest,
    ParseToolRequestError,
]


def parse_json(raw_text: str) -> ParseJsonResult:
    """Decode exactly one complete JSON document or return INVALID_JSON."""
    raise NotImplementedError


def validate_tool_request(data: JsonValue) -> ValidateToolRequestResult:
    """Establish only ToolRequest's outer shape, not tool executability."""
    raise NotImplementedError


def parse_tool_request(raw_text: str) -> ParseToolRequestResult:
    """Compose decoding and outer-shape validation without skipping a gate."""
    raise NotImplementedError


@app.command()
def main(raw_text: str) -> None:
    """Print a parsed request or a structured parser error."""
    result = parse_tool_request(raw_text)

    if isinstance(result, Ok):
        typer.echo(result.value.model_dump_json(indent=2))
        return

    typer.echo(
        json.dumps(
            {"error_code": result.error.code, "error": result.error.message},
            indent=2,
        )
    )
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
