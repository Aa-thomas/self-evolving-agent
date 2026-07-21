import importlib.util
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parent / "05_sandboxed_file_tools.py"

spec = importlib.util.spec_from_file_location("sandboxed_file_tools", MODULE_PATH)
module = importlib.util.module_from_spec(spec)

assert spec is not None
assert spec.loader is not None

spec.loader.exec_module(module)


# =============================================================================
# Adapter helpers
# =============================================================================
# Adjust ONLY these wrappers if your function signatures are different.
# Keep the tests below unchanged.


def read_file(path: str, sandbox_root: Path):
    return module.read_file(path=path, sandbox_root=sandbox_root)


def write_file(path: str, content: str, sandbox_root: Path):
    return module.write_file(path=path, content=content, sandbox_root=sandbox_root)


def list_files(path: str, sandbox_root: Path):
    return module.list_files(path=path, sandbox_root=sandbox_root)


# =============================================================================
# Result helpers
# =============================================================================


def assert_ok(result):
    assert isinstance(result, module.Ok)


def assert_rejected(result, expected_error_code: str):
    assert isinstance(result, module.Err)
    assert result.error_code == expected_error_code


# =============================================================================
# Fixtures
# =============================================================================
# This is where the sandbox comes from.
# tmp_path is a temporary folder pytest creates for that test run.


@pytest.fixture
def sandbox_root(tmp_path):
    root = tmp_path / "sandbox"
    root.mkdir()
    return root


# =============================================================================
# read_file tests
# =============================================================================


def test_empty_path_rejected(sandbox_root):
    result = read_file("", sandbox_root)

    assert_rejected(result, "EMPTY_PATH")


def test_read_existing_file_passes(sandbox_root):
    target = sandbox_root / "notes.txt"
    target.write_text("hello from sandbox", encoding="utf-8")

    result = read_file("notes.txt", sandbox_root)

    assert_ok(result)
    assert result.value == "hello from sandbox"


def test_read_nested_file_passes(sandbox_root):
    notes = sandbox_root / "notes"
    notes.mkdir()
    (notes / "today.txt").write_text("nested evidence", encoding="utf-8")

    result = read_file("notes/today.txt", sandbox_root)

    assert_ok(result)
    assert result.value == "nested evidence"


def test_read_forbidden_parent_path_rejected(sandbox_root):
    secret = sandbox_root.parent / "secret.txt"
    secret.write_text("do not read this", encoding="utf-8")

    result = read_file("../secret.txt", sandbox_root)

    assert_rejected(result, "FORBIDDEN_PATH")


def test_read_absolute_path_rejected(sandbox_root):
    outside_file = sandbox_root.parent / "outside.txt"
    outside_file.write_text("outside sandbox", encoding="utf-8")

    result = read_file(str(outside_file.resolve()), sandbox_root)

    assert_rejected(result, "FORBIDDEN_PATH")


def test_parent_syntax_rejected_even_when_result_would_be_inside(sandbox_root):
    notes = sandbox_root / "notes"
    notes.mkdir()
    (sandbox_root / "safe.txt").write_text("still inside", encoding="utf-8")

    result = read_file("notes/../safe.txt", sandbox_root)

    assert_rejected(result, "FORBIDDEN_PATH")


def test_read_symlink_resolving_outside_sandbox_rejected(sandbox_root):
    outside_file = sandbox_root.parent / "outside-via-link.txt"
    outside_file.write_text("outside sandbox", encoding="utf-8")
    (sandbox_root / "linked.txt").symlink_to(outside_file)

    result = read_file("linked.txt", sandbox_root)

    assert_rejected(result, "FORBIDDEN_PATH")


def test_read_missing_file_returns_file_not_found(sandbox_root):
    result = read_file("missing.txt", sandbox_root)

    assert_rejected(result, "FILE_NOT_FOUND")


def test_read_directory_returns_not_a_file(sandbox_root):
    (sandbox_root / "notes").mkdir()

    result = read_file("notes", sandbox_root)

    assert_rejected(result, "NOT_A_FILE")


def test_read_oversized_file_rejected(sandbox_root):
    target = sandbox_root / "big.txt"
    target.write_text("x" * 100_001, encoding="utf-8")

    result = read_file("big.txt", sandbox_root)

    assert_rejected(result, "CONTENT_TOO_LARGE")


# =============================================================================
# write_file tests
# =============================================================================


def test_write_inside_sandbox_passes(sandbox_root):
    result = write_file("answer.txt", "correct answer", sandbox_root)

    assert_ok(result)

    written_file = sandbox_root / "answer.txt"
    assert written_file.exists()
    assert written_file.read_text(encoding="utf-8") == "correct answer"


def test_write_inside_existing_nested_directory_passes(sandbox_root):
    (sandbox_root / "notes").mkdir()

    result = write_file("notes/answer.txt", "nested answer", sandbox_root)

    assert_ok(result)
    assert result.value == {"path": "notes/answer.txt", "bytes_written": 13}
    assert (sandbox_root / "notes" / "answer.txt").read_text(encoding="utf-8") == "nested answer"


def test_write_to_forbidden_path_rejected(sandbox_root):
    result = write_file("../secret.txt", "leaked content", sandbox_root)

    assert_rejected(result, "FORBIDDEN_PATH")

    forbidden_file = sandbox_root.parent / "secret.txt"
    assert not forbidden_file.exists()


def test_write_to_existing_directory_rejected(sandbox_root):
    (sandbox_root / "notes").mkdir()

    result = write_file("notes", "replacement", sandbox_root)

    assert_rejected(result, "IS_DIRECTORY")


def test_write_with_missing_parent_rejected(sandbox_root):
    result = write_file("missing/answer.txt", "answer", sandbox_root)

    assert_rejected(result, "NOT_A_DIRECTORY")
    assert not (sandbox_root / "missing").exists()


def test_write_oversized_content_rejected(sandbox_root):
    result = write_file("answer.txt", "x" * 100_001, sandbox_root)

    assert_rejected(result, "CONTENT_TOO_LARGE")
    assert not (sandbox_root / "answer.txt").exists()


# =============================================================================
# list_files tests
# =============================================================================


def test_list_files_inside_sandbox_passes(sandbox_root):
    (sandbox_root / "a.txt").write_text("A", encoding="utf-8")
    (sandbox_root / "b.txt").write_text("B", encoding="utf-8")

    result = list_files(".", sandbox_root)

    assert_ok(result)

    assert result.value == ["a.txt", "b.txt"]


def test_list_forbidden_path_rejected(sandbox_root):
    result = list_files("..", sandbox_root)

    assert_rejected(result, "FORBIDDEN_PATH")


def test_list_missing_directory_returns_file_not_found(sandbox_root):
    result = list_files("missing", sandbox_root)

    assert_rejected(result, "FILE_NOT_FOUND")


def test_list_file_returns_not_a_directory(sandbox_root):
    (sandbox_root / "notes.txt").write_text("not a directory", encoding="utf-8")

    result = list_files("notes.txt", sandbox_root)

    assert_rejected(result, "NOT_A_DIRECTORY")
