from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Literal, TypeAlias

from pydantic import (
    BaseModel,
    ConfigDict,
    JsonValue,
    StrictStr,
    ValidationError,
)

from result import Err, Ok, Result


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ToolRequest(StrictModel):
    tool: StrictStr
    args: dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class InvalidJsonError:
    message: str
    line: int
    column: int
    code: Literal["INVALID_JSON"] = "INVALID_JSON"


@dataclass(frozen=True, slots=True)
class InvalidToolRequestShapeError:
    message: str
    code: Literal["INVALID_TOOL_REQUEST_SHAPE"] = "INVALID_TOOL_REQUEST_SHAPE"


ParseToolRequestError: TypeAlias = (
    InvalidJsonError | InvalidToolRequestShapeError
)

ParseJsonResult: TypeAlias = Result[JsonValue, InvalidJsonError]

ValidateToolRequestShapeResult: TypeAlias = Result[
    ToolRequest,
    InvalidToolRequestShapeError,
]

ParseToolRequestResult: TypeAlias = Result[
    ToolRequest,
    ParseToolRequestError,
]


def parse_json(raw_text: str) -> ParseJsonResult:
    try:
        data: JsonValue = json.loads(raw_text)
        return Ok(data)

    except json.JSONDecodeError as error:
        return Err(
            InvalidJsonError(
                message=error.msg,
                line=error.lineno,
                column=error.colno,
            )
        )


def validate_tool_request_shape(
    data: JsonValue,
) -> ValidateToolRequestShapeResult:
    try:
        tool_request = ToolRequest.model_validate(data)
        return Ok(tool_request)

    except ValidationError as error:
        return Err(
            InvalidToolRequestShapeError(
                message=str(error),
            )
        )


def parse_tool_request(raw_text: str) -> ParseToolRequestResult:
    return parse_json(raw_text).and_then(validate_tool_request_shape)


# Kept as a transitional spelling for the original Lesson 03 exercise.
validate_tool_request = validate_tool_request_shape
