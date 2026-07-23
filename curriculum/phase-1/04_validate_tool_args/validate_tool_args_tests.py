import sys
from pathlib import Path


PHASE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PHASE_ROOT))

from primitive_03_parse_tool_request import (
    Err,
    InvalidJsonError,
    InvalidToolRequestShapeError,
    Ok,
    parse_tool_request,
)
from primitive_04_validate_tool_args import (
    InvalidToolArgsError,
    ReadFileArgs,
    UnknownToolError,
    parse_and_validate_tool_request,
    validate_tool_args,
)


def parsed_request(payload: str):
    result = parse_tool_request(payload)
    assert isinstance(result, Ok)
    return result.value


def test_valid_read_file_request_passes() -> None:
    result = validate_tool_args(
        parsed_request('{"tool": "read_file", "args": {"path": "notes.txt"}}')
    )

    assert isinstance(result, Ok)
    assert result.value.tool == "read_file"
    assert result.value.args == ReadFileArgs(path="notes.txt")


def test_rejects_invalid_json() -> None:
    result = parse_tool_request('{"tool": "read_file", "args": ')

    assert isinstance(result, Err)
    assert isinstance(result.error, InvalidJsonError)


def test_rejects_invalid_request_shape() -> None:
    result = parse_tool_request('{"tool": "read_file"}')

    assert isinstance(result, Err)
    assert isinstance(result.error, InvalidToolRequestShapeError)


def test_rejects_unknown_tool() -> None:
    result = parse_and_validate_tool_request(
        '{"tool": "delete_everything", "args": {}}'
    )

    assert isinstance(result, Err)
    assert isinstance(result.error, UnknownToolError)


def test_rejects_invalid_tool_args() -> None:
    result = parse_and_validate_tool_request(
        '{"tool": "read_file", "args": {}}'
    )

    assert isinstance(result, Err)
    assert isinstance(result.error, InvalidToolArgsError)


def test_wrong_tool_arg_type_is_rejected() -> None:
    result = parse_and_validate_tool_request(
        '{"tool": "read_file", "args": {"path": 123}}'
    )

    assert isinstance(result, Err)
    assert isinstance(result.error, InvalidToolArgsError)


def test_extra_tool_arg_is_rejected() -> None:
    result = parse_and_validate_tool_request(
        '{"tool": "read_file", "args": {"path": "notes.txt", "random": true}}'
    )

    assert isinstance(result, Err)
    assert isinstance(result.error, InvalidToolArgsError)


def test_accepts_valid_tool_request() -> None:
    result = parse_and_validate_tool_request(
        '''
        {
            "tool": "read_file",
            "args": {
                "path": "notes.txt"
            }
        }
        '''
    )

    assert isinstance(result, Ok)
    assert result.value.tool == "read_file"
    assert result.value.args == ReadFileArgs(path="notes.txt")


def test_submit_is_protocol_valid_but_returns_a_control_request() -> None:
    result = parse_and_validate_tool_request(
        '{"tool": "submit", "args": {"answer": "done"}}'
    )

    assert isinstance(result, Ok)
    assert result.value.tool == "submit"
