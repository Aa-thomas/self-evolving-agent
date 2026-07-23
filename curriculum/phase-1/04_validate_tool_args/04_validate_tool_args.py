"""Compatibility entry point for the original numbered Lesson 04 artifact.

Use :mod:`primitive_04_validate_tool_args` from Python code.  A module whose
filename starts with a number cannot be imported with a normal import statement.
"""

from pathlib import Path
import sys


PHASE_ROOT = Path(__file__).resolve().parents[1]
if str(PHASE_ROOT) not in sys.path:
    sys.path.insert(0, str(PHASE_ROOT))

from primitive_04_validate_tool_args import (  # noqa: E402
    Err,
    InvalidToolArgsError,
    KnownToolName,
    ListFilesArgs,
    Ok,
    ParseAndValidateError,
    ParseAndValidateResult,
    ReadFileArgs,
    Result,
    StrictArgsModel,
    SubmitArgs,
    TOOL_SPECS,
    ToolArgs,
    ToolArgsSchema,
    ToolSpec,
    UnknownToolError,
    ValidateToolArgsError,
    ValidateToolArgsResult,
    ValidatedToolRequest,
    WriteFileArgs,
    parse_and_validate_tool_request,
    validate_tool_args,
)
