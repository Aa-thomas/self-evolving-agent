import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MODULE_PATH = ROOT / "trace_logger.py"
FIXTURE_PATH = ROOT / "fixtures" / "partial-run.json"
spec = importlib.util.spec_from_file_location("trace_logger", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_partial_run_fixture_is_not_diagnostic():
    partial = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert partial == {"final_answer": None, "exit_reason": "max_steps"}
    assert "assistant_output" not in partial


def test_trace_logger_records_causal_fields_and_writes_replayable_json(tmp_path):
    logger = module.TraceLogger(initial_messages=[{"role": "user", "content": "Read notes.txt."}])
    logger.record_step(
        assistant_output='{"tool":"read_file","args":{"path":"notes.txt"}}',
        parse_result={"ok": True, "value": {"tool": "read_file", "args": {"path": "notes.txt"}}},
        validation_result={"ok": True, "value": {"tool": "read_file", "args": {"path": "notes.txt"}}},
        runtime_handler="read_file",
        tool_result={"ok": True, "value": "lesson notes"},
        exit_reason=None,
    )
    trace = logger.finish(final_answer="done", exit_reason="submitted")
    destination = tmp_path / "run-trace.json"
    logger.write_json(destination, trace)

    saved = json.loads(destination.read_text(encoding="utf-8"))
    assert saved["initial_messages"] == [{"role": "user", "content": "Read notes.txt."}]
    assert saved["steps"][0]["assistant_output"].startswith('{"tool":"read_file"')
    assert saved["steps"][0]["parse_result"]["ok"] is True
    assert saved["steps"][0]["validation_result"]["ok"] is True
    assert saved["steps"][0]["runtime_handler"] == "read_file"
    assert saved["steps"][0]["tool_result"] == {"ok": True, "value": "lesson notes"}
    assert saved["exit_reason"] == "submitted"
