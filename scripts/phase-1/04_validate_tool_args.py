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


## =============================================================================
## Application
## =============================================================================


# =============================================================================
## Program Init
## =============================================================================
if __name__ == "__main__":
    app()
