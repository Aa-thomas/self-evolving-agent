"""Primitive 5 starter: capability-scoped file tools.

Copy this scaffold into ``05_sandboxed_file_tools.py`` and implement the seven
withheld functions.  Primitive 4 has already validated tool names and argument
types; this primitive owns path authorization, filesystem preconditions, and
normalized tool observations.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeAlias

from result import Result


MAX_FILE_BYTES = 100_000
MAX_CONTENT_BYTES = 100_000


@dataclass(frozen=True, slots=True)
class SandboxPath:
    resolved_path: Path


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


def validate_path(
    user_path: str,
    sandbox_root: Path,
) -> PathValidationResult:
    """Return a canonical path inside sandbox_root or a path-policy error.

    Establish the policy in this order: non-empty input, relative syntax,
    forbidden parent traversal, then containment after resolution.
    """
    raise NotImplementedError


def read_validated_file(
    sandbox_path: SandboxPath,
) -> ReadValidatedFileResult:
    """Check file preconditions and size, then read an authorized path."""
    raise NotImplementedError


def read_file(path: str, sandbox_root: Path) -> ReadFileResult:
    """Authorize a raw path, then compose into validated file execution."""
    raise NotImplementedError


def write_validated_file(
    sandbox_path: SandboxPath,
    content: str,
) -> WriteValidatedFileResult:
    """Bound and write content to an authorized path."""
    raise NotImplementedError


def write_file(
    path: str,
    content: str,
    sandbox_root: Path,
) -> WriteFileResult:
    """Authorize a raw path, execute the write, then build its receipt."""
    raise NotImplementedError


def list_files_at_validated_path(
    sandbox_path: SandboxPath,
) -> ListValidatedPathResult:
    """Check directory preconditions, then list an authorized path."""
    raise NotImplementedError


def list_files(path: str, sandbox_root: Path) -> ListFilesResult:
    """Authorize a raw path, then compose into validated listing."""
    raise NotImplementedError
