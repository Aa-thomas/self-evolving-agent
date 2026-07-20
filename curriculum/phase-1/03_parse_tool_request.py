from __future__ import annotations

### =============================================================================
## Imports
## =============================================================================
from dataclasses import dataclass
import json
from typing import Generic, Literal, TypeAlias, TypeVar

import typer
from pydantic import (
    BaseModel,
    ConfigDict,
    JsonValue,
    StrictStr,
    ValidationError,
)


### =============================================================================
## Setup
## =============================================================================
app = typer.Typer()


### =============================================================================
## Generic Result Types
## =============================================================================
T_co = TypeVar("T_co", covariant=True)
E_co = TypeVar("E_co", covariant=True)


@dataclass(frozen=True, slots=True)
class Ok(Generic[T_co]):
    value: T_co


@dataclass(frozen=True, slots=True)
class Err(Generic[E_co]):
    error: E_co


Result: TypeAlias = Ok[T_co] | Err[E_co]


### =============================================================================
## Domain Error Types
## =============================================================================
@dataclass(frozen=True, slots=True)
class InvalidJsonError:
    message: str
    code: Literal["INVALID_JSON"] = "INVALID_JSON"


@dataclass(frozen=True, slots=True)
class InvalidToolRequestShapeError:
    message: str
    code: Literal["INVALID_TOOL_REQUEST_SHAPE"] = "INVALID_TOOL_REQUEST_SHAPE"


ParseToolRequestError: TypeAlias = InvalidJsonError | InvalidToolRequestShapeError


### =============================================================================
## Domain Types
## =============================================================================
class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ToolRequest(StrictModel):
    tool: StrictStr
    args: dict[str, JsonValue]


### =============================================================================
## Descriptive Result Types
## =============================================================================
ParseJsonResult: TypeAlias = Result[
    JsonValue,
    InvalidJsonError,
]

ValidateToolRequestResult: TypeAlias = Result[
    ToolRequest,
    InvalidToolRequestShapeError,
]

ParseToolRequestResult: TypeAlias = Result[
    ToolRequest,
    ParseToolRequestError,
]


### =============================================================================
## Helper Functions
## =============================================================================
def parse_json(raw_text: str) -> ParseJsonResult:
    try:
        data: JsonValue = json.loads(raw_text)
        return Ok(value=data)

    except json.JSONDecodeError as error:
        return Err(
            error=InvalidJsonError(
                message=str(error),
            )
        )


def validate_tool_request(
    data: JsonValue,
) -> ValidateToolRequestResult:
    try:
        tool_request = ToolRequest.model_validate(data)
        return Ok(value=tool_request)

    except ValidationError as error:
        return Err(
            error=InvalidToolRequestShapeError(
                message=str(error),
            )
        )


### =============================================================================
## Application
## =============================================================================
def parse_tool_request(
    raw_text: str,
) -> ParseToolRequestResult:
    json_result = parse_json(raw_text)

    if isinstance(json_result, Err):
        return json_result

    return validate_tool_request(json_result.value)


### =============================================================================
## CLI
## =============================================================================
@app.command()
def main(raw_text: str) -> None:
    result = parse_tool_request(raw_text)

    if isinstance(result, Ok):
        typer.echo(result.value.model_dump_json(indent=2))
        return

    typer.echo(
        json.dumps(
            {
                "error_code": result.error.code,
                "error": result.error.message,
            },
            indent=2,
        )
    )

    raise typer.Exit(code=1)


### =============================================================================
## Program Init
## =============================================================================
if __name__ == "__main__":
    app()
