import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MODULE_PATH = ROOT / "trace_logger.py"
FIXTURE_PATH = ROOT / "fixtures" / "partial-run.json"
AGENT_LOOP_PATH = ROOT.parent / "06_agent_loop" / "agent_loop.py"
spec = importlib.util.spec_from_file_location("trace_logger", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

agent_spec = importlib.util.spec_from_file_location("agent_loop_for_trace", AGENT_LOOP_PATH)
assert agent_spec is not None and agent_spec.loader is not None
agent_loop = importlib.util.module_from_spec(agent_spec)
sys.modules[agent_spec.name] = agent_loop
agent_spec.loader.exec_module(agent_loop)


class FakeModel:
    def __init__(self, outputs: list[str]):
        self.outputs = outputs

    def complete(self, messages: list[dict[str, str]]) -> str:
        return self.outputs.pop(0)


def read_file(path: str):
    assert path == "notes.txt"
    return agent_loop.Ok("lesson notes")


def test_partial_run_fixture_is_not_diagnostic():
    partial = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert partial == {"final_answer": None, "exit_reason": "max_steps"}
    assert "assistant_output" not in partial


def test_trace_logger_records_causal_fields_and_writes_replayable_json(tmp_path):
    logger = module.TraceLogger()
    result = agent_loop.run_agent(
        user_task="Read notes.txt.",
        model=FakeModel([
            '{"tool":"read_file","args":{"path":"notes.txt"}}',
            '{"tool":"submit","args":{"answer":"done"}}',
        ]),
        tools={"read_file": read_file},
        max_steps=3,
        trace_logger=logger,
    )

    assert result.exit_reason == "submitted"
    assert result.final_answer == "done"
    assert logger.trace is not None
    trace = logger.trace
    destination = tmp_path / "run-trace.json"
    logger.write_json(destination, trace)

    saved = json.loads(destination.read_text(encoding="utf-8"))
    assert saved["initial_messages"] == [{"role": "user", "content": "Read notes.txt."}]
    assert saved["steps"][0]["assistant_output"].startswith('{"tool":"read_file"')
    assert saved["steps"][0]["parse_result"]["ok"] is True
    assert saved["steps"][0]["validation_result"]["ok"] is True
    assert saved["steps"][0]["runtime_handler"] == "read_file"
    assert saved["steps"][0]["tool_result"] == {"ok": True, "value": "lesson notes"}
    assert saved["steps"][1]["exit_reason"] == "submitted"
    assert saved["exit_reason"] == "submitted"
