import importlib.util
import json
import sys
from pathlib import Path


PHASE_ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


parser = load_module("parse_tool_request_for_validation", PHASE_ROOT / "03_parse_tool_request.py")
validator = load_module("validate_tool_args", Path(__file__).resolve().with_name("04_validate_tool_args.py"))


def parsed_request(payload: dict[str, object]):
    result = parser.parse_tool_request(json.dumps(payload))
    assert isinstance(result, parser.Ok)
    return result.value


def assert_err(result, error_code: str):
    assert isinstance(result, validator.Err)
    assert result.error.error_code == error_code


def test_valid_read_file_request_passes():
    result = validator.validate_tool_args(parsed_request({"tool": "read_file", "args": {"path": "notes.txt"}}))

    assert isinstance(result, validator.Ok)
    assert result.value.tool == "read_file"
    assert result.value.args.path == "notes.txt"


def test_unknown_tool_is_rejected():
    result = validator.validate_tool_args(parsed_request({"tool": "delete_file", "args": {"path": "notes.txt"}}))

    assert_err(result, "UNKNOWN_TOOL")


def test_missing_required_tool_arg_is_rejected():
    result = validator.validate_tool_args(parsed_request({"tool": "read_file", "args": {}}))

    assert_err(result, "INVALID_TOOL_ARGS")


def test_wrong_tool_arg_type_is_rejected():
    result = validator.validate_tool_args(parsed_request({"tool": "read_file", "args": {"path": 123}}))

    assert_err(result, "INVALID_TOOL_ARGS")


def test_extra_tool_arg_is_rejected():
    result = validator.validate_tool_args(parsed_request({"tool": "read_file", "args": {"path": "notes.txt", "random": True}}))

    assert_err(result, "INVALID_TOOL_ARGS")


def test_list_files_can_omit_optional_path():
    result = validator.validate_tool_args(parsed_request({"tool": "list_files", "args": {}}))

    assert isinstance(result, validator.Ok)
    assert result.value.tool == "list_files"
    assert result.value.args.path is None


def test_submit_is_protocol_valid_but_returns_a_control_request():
    result = validator.validate_tool_args(parsed_request({"tool": "submit", "args": {"answer": "done"}}))

    assert isinstance(result, validator.Ok)
    assert result.value.tool == "submit"
