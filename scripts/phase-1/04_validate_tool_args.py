### =============================================================================
## Imports
## =============================================================================
from dataclasses import dataclass
import typer
from openai import OpenAI
from dotenv import load_dotenv
import os
from pydantic import BaseModel, ValidationError
from typing import Any
import json

## =============================================================================
## Setup
## =============================================================================
load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

app = typer.Typer()


## =============================================================================
## Types
## =============================================================================


# ToolRequest
class ToolRequest(BaseModel):
    tool: str
    args: dict[str, Any]


# Tool Spec
@dataclass
class ToolSpec:
    name: str
    args_schema: type[BaseModel]


# Specific Tool Schemas
class ReadFileArgs(BaseModel):
    path: str


class WriteFileArgs(BaseModel):
    path: str
    content: str


class ListFilesArgs(BaseModel):
    path: str | None = None


class SubmitArgs(BaseModel):
    answer: str


@dataclass
class Result:
    ok: bool
    value: Any = None
    error: str | None = None
    error_code: str | None = None


# Tool Registry
tool_registry = {
    "read_file": ToolSpec(name="read_file", args_schema=ReadFileArgs),
    "write_file": ToolSpec(name="write_file", args_schema=WriteFileArgs),
    "list_files": ToolSpec(name="list_files", args_schema=ListFilesArgs),
    "submit": ToolSpec(name="submit", args_schema=SubmitArgs),
}


## =============================================================================
## Helper Functions
## =============================================================================
def parse_json(raw_text: str) -> Result:
    try:
        data = json.loads(raw_text)
        return Result(ok=True, value=data)
    except json.JSONDecodeError as error:
        return Result(ok=False, error=str(error), error_code="INVALID_JSON")


def validate_tool_request(data: Any) -> Result:
    try:
        tool_request = ToolRequest.model_validate(data)
        return Result(ok=True, value=tool_request)
    except ValidationError as error:
        return Result(
            ok=False, error=str(error), error_code="INVALID_TOOL_REQUEST_SHAPE"
        )


def validate_tool_exists(tool_request: ToolRequest) -> Result:
    if tool_request.tool not in tool_registry:
        return Result(
            ok=False,
            error=f"Unknown tool: {tool_request.tool}",
            error_code="UNKNOWN_TOOL",
        )

    return Result(ok=True, value=tool_request)


## =============================================================================
## Application
## =============================================================================
@app.command()
def parse_tool_request(raw_text: str):
    json_result = parse_json(raw_text)

    if not json_result.ok:
        return json_result

    validation_result = validate_tool_request(json_result.value)

    if not validation_result.ok:
        return validation_result

    tool_exists = validate_tool_exists(validation_result.value)

    if tool_exists.ok:
        print("parse_tool_request: success ")
    else:
        print("parse_tool_request: fail")


# =============================================================================
## Program Init
## =============================================================================
if __name__ == "__main__":
    app()
