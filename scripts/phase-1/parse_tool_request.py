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
class ToolRequest(BaseModel):
    tool: str
    args: dict[str, Any]


@dataclass
class Result:
    ok: bool
    value: Any = None
    error: str | None = None
    error_code: str | None = None


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


## =============================================================================
## Application
## =============================================================================
@app.command()
def parse_tool_request(raw_text: str) -> Result:
    json_result = parse_json(raw_text)

    if not json_result.ok:
        return json_result

    validation_result = validate_tool_request(json_result.value)

    return validation_result


#
#
#
#
#
#
# =============================================================================
## Program Init
## =============================================================================
if __name__ == "__main__":
    app()
