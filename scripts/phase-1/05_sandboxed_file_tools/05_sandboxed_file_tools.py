## =============================================================================
## Imports
## =============================================================================
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, TypeAlias, Union
import typer

### =============================================================================
## Setup
## =============================================================================
## app = typer.Typer()


### =============================================================================
## Types
## =============================================================================
ErrorCode: TypeAlias = Literal[
    "FORBIDDEN_PATH",
    "EMPTY_PATH",
    "FILE_NOT_FOUND",
    "NOT_A_FILE",
    "NOT_A_DIRECTORY",
    "IS_DIRECTORY",
    "CONTENT_TOO_LARGE",
    "READ_ERROR",
    "WRITE_ERROR",
    "LIST_ERROR",
]


@dataclass(frozen=True)
class Ok:
    value: Any


@dataclass(frozen=True)
class Err:
    error_code: ErrorCode
    error: str


Result: TypeAlias = Union[Ok, Err]


## =============================================================================
## Helpers
## =============================================================================
def validate_path(user_path: str, sandbox_root: Path) -> Result:
    ## Resolves sandbox root to its absolute path
    sandbox_root = sandbox_root.resolve()

    # Check if path is empty
    if user_path.strip() == "":
        return Err(
            error_code="EMPTY_PATH",
            error="Path cannot be empty.",
        )

    safe_path = (sandbox_root / user_path).resolve()

    ## Check if path is inside sandbox
    if not safe_path.is_relative_to(sandbox_root):
        return Err(
            error_code="FORBIDDEN_PATH",
            error="Path is outside the sandbox.",
        )

    return Ok(value=safe_path)


### =============================================================================
## Application
## =============================================================================
def read_file(path: str, sandbox_root: Path) -> Result:
    path_result = validate_path(path, sandbox_root)

    if isinstance(path_result, Err):
        return path_result

    safe_path = path_result.value

    if not safe_path.exists():
        return Err(
            error_code="FILE_NOT_FOUND",
            error="File does not exist.",
        )

    if not safe_path.is_file():
        return Err(
            error_code="NOT_A_FILE",
            error="Path is not a file.",
        )

    try:
        content = safe_path.read_text(encoding="utf-8")
    except OSError as exc:
        return Err(
            error_code="READ_ERROR",
            error=str(exc),
        )

    return Ok(value=content)


### =============================================================================
## Program Init
## =============================================================================
# if __name__ == "__main__":
##    app()
