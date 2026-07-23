from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeAlias

from result import Err, Ok, Result


## =============================================================================
## Constants
## =============================================================================
MAX_FILE_BYTES = 100_000
MAX_CONTENT_BYTES = 100_000


## =============================================================================
## Domain Types
## =============================================================================
@dataclass(frozen=True, slots=True)
class SandboxPath:
    resolved_path: Path


## =============================================================================
## Error Types
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


@dataclass(frozen=True, slots=True)
class EmptyPathError:
    message: str = "Path cannot be empty."
    code: Literal["EMPTY_PATH"] = "EMPTY_PATH"


@dataclass(frozen=True, slots=True)
class ForbiddenPathError:
    message: str
    code: Literal["FORBIDDEN_PATH"] = "FORBIDDEN_PATH"


@dataclass(frozen=True, slots=True)
class FileNotFoundToolError:
    message: str
    code: Literal["FILE_NOT_FOUND"] = "FILE_NOT_FOUND"


@dataclass(frozen=True, slots=True)
class NotAFileError:
    message: str
    code: Literal["NOT_A_FILE"] = "NOT_A_FILE"


@dataclass(frozen=True, slots=True)
class NotADirectoryError:
    message: str
    code: Literal["NOT_A_DIRECTORY"] = "NOT_A_DIRECTORY"


@dataclass(frozen=True, slots=True)
class IsDirectoryError:
    message: str
    code: Literal["IS_DIRECTORY"] = "IS_DIRECTORY"


@dataclass(frozen=True, slots=True)
class ContentTooLargeError:
    message: str
    code: Literal["CONTENT_TOO_LARGE"] = "CONTENT_TOO_LARGE"


@dataclass(frozen=True, slots=True)
class ReadOperationError:
    message: str
    code: Literal["READ_ERROR"] = "READ_ERROR"


@dataclass(frozen=True, slots=True)
class WriteOperationError:
    message: str
    code: Literal["WRITE_ERROR"] = "WRITE_ERROR"


@dataclass(frozen=True, slots=True)
class ListOperationError:
    message: str
    code: Literal["LIST_ERROR"] = "LIST_ERROR"


## =============================================================================
## Result Contracts
## =============================================================================
PathValidationError: TypeAlias = EmptyPathError | ForbiddenPathError

ReadFileError: TypeAlias = (
    FileNotFoundToolError
    | NotAFileError
    | ContentTooLargeError
    | ReadOperationError
)

WriteFileError: TypeAlias = (
    ContentTooLargeError
    | IsDirectoryError
    | NotADirectoryError
    | WriteOperationError
)

ListFilesError: TypeAlias = (
    FileNotFoundToolError | NotADirectoryError | ListOperationError
)

WriteFileReceipt: TypeAlias = dict[str, str | int]

PathValidationResult: TypeAlias = Result[SandboxPath, PathValidationError]
ReadValidatedFileResult: TypeAlias = Result[str, ReadFileError]
ReadFileResult: TypeAlias = Result[
    str,
    PathValidationError | ReadFileError,
]
WriteValidatedFileResult: TypeAlias = Result[int, WriteFileError]
WriteFileResult: TypeAlias = Result[
    WriteFileReceipt,
    PathValidationError | WriteFileError,
]
ListValidatedPathResult: TypeAlias = Result[list[str], ListFilesError]
ListFilesResult: TypeAlias = Result[
    list[str],
    PathValidationError | ListFilesError,
]


## =============================================================================
## Helpers
## =============================================================================
def validate_path(
    user_path: str,
    sandbox_root: Path,
) -> PathValidationResult:
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
        return Err(EmptyPathError())

    if requested_path.is_absolute():
        return Err(
            ForbiddenPathError(
                message="Absolute paths are not allowed.",
            )
        )

    if ".." in requested_path.parts:
        return Err(
            ForbiddenPathError(
                message="Parent directory traversal is not allowed.",
            )
        )

    safe_path = (sandbox_root / requested_path).resolve()

    if not safe_path.is_relative_to(sandbox_root):
        return Err(
            ForbiddenPathError(
                message="Path is outside the sandbox.",
            )
        )

    return Ok(
        SandboxPath(
            resolved_path=safe_path,
        )
    )


## =============================================================================
## File Tools
## =============================================================================
def read_validated_file(
    sandbox_path: SandboxPath,
) -> ReadValidatedFileResult:
    safe_path = sandbox_path.resolved_path

    if not safe_path.exists():
        return Err(
            FileNotFoundToolError(
                message="File does not exist.",
            )
        )

    if not safe_path.is_file():
        return Err(
            NotAFileError(
                message="Path is not a file.",
            )
        )

    try:
        file_size = safe_path.stat().st_size
    except OSError as exc:
        return Err(
            ReadOperationError(
                message=str(exc),
            )
        )

    if file_size > MAX_FILE_BYTES:
        return Err(
            ContentTooLargeError(
                message="File is too large to read.",
            )
        )

    try:
        content = safe_path.read_text(encoding="utf-8")
    except OSError as exc:
        return Err(
            ReadOperationError(
                message=str(exc),
            )
        )

    return Ok(content)


def read_file(path: str, sandbox_root: Path) -> ReadFileResult:
    return validate_path(path, sandbox_root).and_then(
        read_validated_file
    )


def write_validated_file(
    sandbox_path: SandboxPath,
    content: str,
) -> WriteValidatedFileResult:
    safe_path = sandbox_path.resolved_path
    content_size = len(content.encode("utf-8"))

    if content_size > MAX_CONTENT_BYTES:
        return Err(
            ContentTooLargeError(
                message="Content is too large to write.",
            )
        )

    if safe_path.exists() and safe_path.is_dir():
        return Err(
            IsDirectoryError(
                message="Cannot write file content to a directory.",
            )
        )

    parent = safe_path.parent

    if not parent.exists():
        return Err(
            NotADirectoryError(
                message="Parent directory does not exist.",
            )
        )

    if not parent.is_dir():
        return Err(
            NotADirectoryError(
                message="Parent path is not a directory.",
            )
        )

    try:
        safe_path.write_text(content, encoding="utf-8")
    except OSError as exc:
        return Err(
            WriteOperationError(
                message=str(exc),
            )
        )

    return Ok(content_size)


def write_file(
    path: str,
    content: str,
    sandbox_root: Path,
) -> WriteFileResult:
    return (
        validate_path(path, sandbox_root)
        .and_then(
            lambda sandbox_path: write_validated_file(
                sandbox_path,
                content,
            )
        )
        .map(
            lambda bytes_written: {
                "path": path,
                "bytes_written": bytes_written,
            }
        )
    )


def list_files_at_validated_path(
    sandbox_path: SandboxPath,
) -> ListValidatedPathResult:
    safe_path = sandbox_path.resolved_path

    if not safe_path.exists():
        return Err(
            FileNotFoundToolError(
                message="Directory does not exist.",
            )
        )

    if not safe_path.is_dir():
        return Err(
            NotADirectoryError(
                message="Path is not a directory.",
            )
        )

    try:
        files = sorted(item.name for item in safe_path.iterdir())
    except OSError as exc:
        return Err(
            ListOperationError(
                message=str(exc),
            )
        )

    return Ok(files)


def list_files(path: str, sandbox_root: Path) -> ListFilesResult:
    return validate_path(path, sandbox_root).and_then(
        list_files_at_validated_path
    )
