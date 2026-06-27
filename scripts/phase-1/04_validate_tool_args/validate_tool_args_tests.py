import importlib.util
import json
import sys
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "phase-1"
    / "04_validate_tool_args.py"
)

spec = importlib.util.spec_from_file_location("validate_tool_args", MODULE_PATH)

assert spec is not None
assert spec.loader is not None

module = importlib.util.module_from_spec(spec)

sys.modules["validate_tool_args"] = module

spec.loader.exec_module(module)


def validate(payload):
    if isinstance(payload, str):
        return module.validate_tool_request(payload)

    return module.validate_tool_request(json.dumps(payload))


def assert_err(result, error_code: str):
    assert result.ok is False
    assert result.error_code == error_code


def test_valid_read_file_request_passes():
    result = validate(
        {
            "tool": "read_file",
            "args": {"path": "notes.txt"},
        }
    )

    assert result.ok is True
    assert result.value.tool == "read_file"
    assert result.value.args.path == "notes.txt"


def test_malformed_json_is_rejected():
    result = validate('{"tool": "read_file", "args": ')

    assert_err(result, "INVALID_JSON")


def test_missing_args_is_rejected_as_bad_request_shape():
    result = validate(
        {
            "tool": "read_file",
        }
    )

    assert_err(result, "INVALID_TOOL_REQUEST_SHAPE")


def test_unknown_tool_is_rejected():
    result = validate(
        {
            "tool": "delete_file",
            "args": {"path": "notes.txt"},
        }
    )

    assert_err(result, "UNKNOWN_TOOL")


def test_missing_required_tool_arg_is_rejected():
    result = validate(
        {
            "tool": "read_file",
            "args": {},
        }
    )

    assert_err(result, "INVALID_TOOL_ARGS")


def test_wrong_tool_arg_type_is_rejected():
    result = validate(
        {
            "tool": "read_file",
            "args": {"path": 123},
        }
    )

    assert_err(result, "INVALID_TOOL_ARGS")


def test_extra_tool_arg_is_rejected():
    result = validate(
        {
            "tool": "read_file",
            "args": {
                "path": "notes.txt",
                "random": True,
            },
        }
    )

    assert_err(result, "INVALID_TOOL_ARGS")


def test_list_files_can_omit_optional_path():
    result = validate(
        {
            "tool": "list_files",
            "args": {},
        }
    )

    assert result.ok is True
    assert result.value.tool == "list_files"
    assert result.value.args.path is None
