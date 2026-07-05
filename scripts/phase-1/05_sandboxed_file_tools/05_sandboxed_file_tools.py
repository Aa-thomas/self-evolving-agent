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
    # Validates the path is inside sandbox
    path_result = validate_path(path, sandbox_root)

    if isinstance(path_result, Err):
        return path_result

    # Validates the path exists
    safe_path = path_result.value

    if not safe_path.exists():
        return Err(
            error_code="FILE_NOT_FOUND",
            error="File does not exist.",
        )

    # Validates the path is a file
    if not safe_path.is_file():
        return Err(
            error_code="NOT_A_FILE",
            error="Path is not a file.",
        )

    # Validates file is not too large
    MAX_FILE_BYTES = 100_000

    if safe_path.stat().st_size > MAX_FILE_BYTES:
        return Err(
            error_code="CONTENT_TOO_LARGE",
            error="File is too large to read.",
        )

    # If all validators pass, read the file.
    try:
        content = safe_path.read_text(encoding="utf-8")
    except OSError as exc:
        return Err(
            error_code="READ_ERROR",
            error=str(exc),
        )

    return Ok(value=content)


def write_file(path: str, content: str, sandbox_root: Path) -> Result:
    # Validate the path is inside sandbox.
    path_result = validate_path(path, sandbox_root)

    if isinstance(path_result, Err):
        return path_result

    safe_path = path_result.value

    # Validate content is not too large.
    MAX_CONTENT_BYTES = 100_000

    content_size = len(content.encode("utf-8"))

    if content_size > MAX_CONTENT_BYTES:
        return Err(
            error_code="CONTENT_TOO_LARGE",
            error="Content is too large to write.",
        )

    # Reject writing to an existing directory.
    if safe_path.exists() and safe_path.is_dir():
        return Err(
            error_code="IS_DIRECTORY",
            error="Cannot write file content to a directory.",
        )

    # Validate parent folder exists.
    parent = safe_path.parent

    if not parent.exists():
        return Err(
            error_code="NOT_A_DIRECTORY",
            error="Parent directory does not exist.",
        )

    # Validate parent is actually a directory.
    if not parent.is_dir():
        return Err(
            error_code="NOT_A_DIRECTORY",
            error="Parent path is not a directory.",
        )

    # If all validators pass, write the file.
    try:
        safe_path.write_text(content, encoding="utf-8")
    except OSError as exc:
        return Err(
            error_code="WRITE_ERROR",
            error=str(exc),
        )

    return Ok(value=str(safe_path))


def list_files(path: str, sandbox_root: Path) -> Result:
    # Validate the path is inside sandbox.
    path_result = validate_path(path, sandbox_root)

    if isinstance(path_result, Err):
        return path_result

    safe_path = path_result.value

    # Validate the path exists.
    if not safe_path.exists():
        return Err(
            error_code="FILE_NOT_FOUND",
            error="Directory does not exist.",
        )

    # Validate the path is a directory.
    if not safe_path.is_dir():
        return Err(
            error_code="NOT_A_DIRECTORY",
            error="Path is not a directory.",
        )

    # If all validators pass, list the directory.
    try:
        files = [item.name for item in safe_path.iterdir()]
    except OSError as exc:
        return Err(
            error_code="LIST_ERROR",
            error=str(exc),
        )

    return Ok(value=files)


### =============================================================================
## Program Init
## =============================================================================
# if __name__ == "__main__":
##    app()
