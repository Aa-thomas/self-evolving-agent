import sys
from pathlib import Path


PHASE_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PHASE_ROOT))

from parse_tool_request import (
    Err,
    InvalidJsonError,
    InvalidToolRequestShapeError,
    Ok,
    parse_tool_request,
)


def test_valid_request_produces_tool_request() -> None:
    result = parse_tool_request(
        '{"tool": "read_file", "args": {"path": "notes.txt"}}'
    )

    assert isinstance(result, Ok)
    assert result.value.tool == "read_file"
    assert result.value.args == {"path": "notes.txt"}


def test_malformed_json_is_rejected() -> None:
    result = parse_tool_request('{"tool": "read_file", "args": ')

    assert isinstance(result, Err)
    assert isinstance(result.error, InvalidJsonError)
    assert result.error.line == 1
    assert result.error.column > 0


def test_trailing_prose_is_not_json() -> None:
    result = parse_tool_request('{"tool": "read_file", "args": {}} thanks')

    assert isinstance(result, Err)
    assert isinstance(result.error, InvalidJsonError)


def test_json_string_is_not_a_tool_request() -> None:
    result = parse_tool_request('"hello"')

    assert isinstance(result, Err)
    assert isinstance(result.error, InvalidToolRequestShapeError)


def test_missing_args_is_not_a_tool_request() -> None:
    result = parse_tool_request('{"tool": "read_file"}')

    assert isinstance(result, Err)
    assert isinstance(result.error, InvalidToolRequestShapeError)


def test_unknown_tool_name_still_produces_tool_request() -> None:
    result = parse_tool_request(
        '{"tool": "delete_file", "args": {"path": "notes.txt"}}'
    )

    assert isinstance(result, Ok)
    assert result.value.tool == "delete_file"


def test_tool_specific_argument_type_is_left_for_validation() -> None:
    result = parse_tool_request(
        '{"tool": "read_file", "args": {"path": 123}}'
    )

    assert isinstance(result, Ok)
    assert result.value.args == {"path": 123}
