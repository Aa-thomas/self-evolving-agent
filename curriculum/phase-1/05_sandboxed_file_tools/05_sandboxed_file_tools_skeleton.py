"""Primitive 5 starter: capability-scoped file tools.

Copy this scaffold into ``05_sandboxed_file_tools.py`` and implement the four
withheld functions.  Primitive 4 has already validated tool names and argument
types; this primitive owns path authorization, filesystem preconditions, and
normalized tool observations.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, TypeAlias, Union


MAX_FILE_BYTES = 100_000
MAX_CONTENT_BYTES = 100_000


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


def validate_path(user_path: str, sandbox_root: Path) -> Result:
    """Return a canonical path inside sandbox_root or a path-policy error.

    Establish the policy in this order: non-empty input, relative syntax,
    forbidden parent traversal, then containment after resolution.
    """
    raise NotImplementedError


def read_file(path: str, sandbox_root: Path) -> Result:
    """Authorize, check file preconditions and size, then return text or Err."""
    raise NotImplementedError


def write_file(path: str, content: str, sandbox_root: Path) -> Result:
    """Authorize and bound the write without creating missing directories."""
    raise NotImplementedError


def list_files(path: str, sandbox_root: Path) -> Result:
    """Authorize a directory path and return a deterministic name listing."""
    raise NotImplementedError
