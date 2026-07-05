## =============================================================================
## Imports
## =============================================================================
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, TypeAlias, Union


## =============================================================================
## Constants
## =============================================================================
MAX_FILE_BYTES = 100_000
MAX_CONTENT_BYTES = 100_000


## =============================================================================
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
    """
    Validate that a user-provided path is safe to use inside the sandbox.

    Contract:
    - user_path must be sandbox-relative
    - absolute paths are rejected
    - parent traversal syntax is rejected
    - final resolved path must remain inside sandbox_root
    """
    sandbox_root = sandbox_root.resolve()
    requested_path = Path(user_path)

    if user_path.strip() == "":
        return Err(
            error_code="EMPTY_PATH",
            error="Path cannot be empty.",
        )

    if requested_path.is_absolute():
        return Err(
            error_code="FORBIDDEN_PATH",
            error="Absolute paths are not allowed.",
        )

    if ".." in requested_path.parts:
        return Err(
            error_code="FORBIDDEN_PATH",
            error="Parent directory traversal is not allowed.",
        )

    safe_path = (sandbox_root / requested_path).resolve()

    if not safe_path.is_relative_to(sandbox_root):
        return Err(
            error_code="FORBIDDEN_PATH",
            error="Path is outside the sandbox.",
        )

    return Ok(value=safe_path)


## =============================================================================
## File Tools
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
        file_size = safe_path.stat().st_size
    except OSError as exc:
        return Err(
            error_code="READ_ERROR",
            error=str(exc),
        )

    if file_size > MAX_FILE_BYTES:
        return Err(
            error_code="CONTENT_TOO_LARGE",
            error="File is too large to read.",
        )

    try:
        content = safe_path.read_text(encoding="utf-8")
    except OSError as exc:
        return Err(
            error_code="READ_ERROR",
            error=str(exc),
        )

    return Ok(value=content)


def write_file(path: str, content: str, sandbox_root: Path) -> Result:
    path_result = validate_path(path, sandbox_root)

    if isinstance(path_result, Err):
        return path_result

    safe_path = path_result.value
    content_size = len(content.encode("utf-8"))

    if content_size > MAX_CONTENT_BYTES:
        return Err(
            error_code="CONTENT_TOO_LARGE",
            error="Content is too large to write.",
        )

    if safe_path.exists() and safe_path.is_dir():
        return Err(
            error_code="IS_DIRECTORY",
            error="Cannot write file content to a directory.",
        )

    parent = safe_path.parent

    if not parent.exists():
        return Err(
            error_code="NOT_A_DIRECTORY",
            error="Parent directory does not exist.",
        )

    if not parent.is_dir():
        return Err(
            error_code="NOT_A_DIRECTORY",
            error="Parent path is not a directory.",
        )

    try:
        safe_path.write_text(content, encoding="utf-8")
    except OSError as exc:
        return Err(
            error_code="WRITE_ERROR",
            error=str(exc),
        )

    return Ok(
        value={
            "path": path,
            "bytes_written": content_size,
        }
    )


def list_files(path: str, sandbox_root: Path) -> Result:
    path_result = validate_path(path, sandbox_root)

    if isinstance(path_result, Err):
        return path_result

    safe_path = path_result.value

    if not safe_path.exists():
        return Err(
            error_code="FILE_NOT_FOUND",
            error="Directory does not exist.",
        )

    if not safe_path.is_dir():
        return Err(
            error_code="NOT_A_DIRECTORY",
            error="Path is not a directory.",
        )

    try:
        files = sorted(item.name for item in safe_path.iterdir())
    except OSError as exc:
        return Err(
            error_code="LIST_ERROR",
            error=str(exc),
        )

    return Ok(value=files)
