import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().with_name("03_parse_tool_request.py")
spec = importlib.util.spec_from_file_location("parse_tool_request", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules["parse_tool_request"] = module
spec.loader.exec_module(module)


def assert_error(raw_text: str, code: str):
    result = module.parse_tool_request(raw_text)
    assert isinstance(result, module.Err)
    assert result.error.code == code


def test_valid_request_produces_tool_request():
    result = module.parse_tool_request('{"tool": "read_file", "args": {"path": "notes.txt"}}')

    assert isinstance(result, module.Ok)
    assert result.value.tool == "read_file"
    assert result.value.args == {"path": "notes.txt"}


def test_malformed_json_is_rejected():
    assert_error('{"tool": "read_file", "args": ', "INVALID_JSON")


def test_json_string_is_not_a_tool_request():
    assert_error('"hello"', "INVALID_TOOL_REQUEST_SHAPE")


def test_json_array_is_not_a_tool_request():
    assert_error(
        '[{"tool": "read_file", "args": {"path": "notes.txt"}}]',
        "INVALID_TOOL_REQUEST_SHAPE",
    )


def test_missing_args_is_not_a_tool_request():
    assert_error('{"tool": "read_file"}', "INVALID_TOOL_REQUEST_SHAPE")


def test_function_syntax_is_not_json():
    assert_error('read_file(path="notes.txt")', "INVALID_JSON")


def test_multiple_json_objects_are_not_one_request():
    assert_error('{"tool": "read_file", "args": {}} {"tool": "submit", "args": {"answer": "done"}}', "INVALID_JSON")


def test_trailing_prose_is_not_json():
    assert_error('{"tool": "read_file", "args": {}} thanks', "INVALID_JSON")


def test_unknown_tool_name_still_produces_tool_request():
    result = module.parse_tool_request(
        '{"tool": "delete_file", "args": {"path": "notes.txt"}}'
    )

    assert isinstance(result, module.Ok)
    assert result.value.tool == "delete_file"


def test_tool_specific_argument_type_is_left_for_validation():
    result = module.parse_tool_request(
        '{"tool": "read_file", "args": {"path": 123}}'
    )

    assert isinstance(result, module.Ok)
    assert result.value.args == {"path": 123}
