"""Compatibility entry point for the original numbered Lesson 03 artifact.

Use :mod:`primitive_03_parse_tool_request` from Python code.  A module whose
filename starts with a number cannot be imported with a normal import statement.
"""

from pathlib import Path
import sys


PHASE_ROOT = Path(__file__).resolve().parent
if str(PHASE_ROOT) not in sys.path:
    sys.path.insert(0, str(PHASE_ROOT))

from primitive_03_parse_tool_request import (  # noqa: E402
    Err,
    InvalidJsonError,
    InvalidToolRequestShapeError,
    Ok,
    ParseJsonResult,
    ParseToolRequestError,
    ParseToolRequestResult,
    Result,
    StrictModel,
    ToolRequest,
    ValidateToolRequestShapeResult,
    parse_json,
    parse_tool_request,
    validate_tool_request,
    validate_tool_request_shape,
)
