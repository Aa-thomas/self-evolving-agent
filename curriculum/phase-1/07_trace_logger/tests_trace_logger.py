import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent
PHASE_ROOT = ROOT.parent
sys.path.insert(0, str(PHASE_ROOT))

MODULE_PATH = ROOT / "trace_logger.py"
FIXTURE_PATH = ROOT / "fixtures" / "partial-run.json"
AGENT_LOOP_PATH = PHASE_ROOT / "06_agent_loop" / "agent_loop.py"
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


@pytest.mark.parametrize(
    ("raw_output", "expected_stage", "expected_code"),
    [
        ('{"tool":', module.RequestStage.JSON, "INVALID_JSON"),
        (
            '{"tool":"read_file"}',
            module.RequestStage.REQUEST_SHAPE,
            "INVALID_TOOL_REQUEST_SHAPE",
        ),
        (
            '{"tool":"delete_file","args":{}}',
            module.RequestStage.TOOL_LOOKUP,
            "UNKNOWN_TOOL",
        ),
        (
            '{"tool":"read_file","args":{}}',
            module.RequestStage.TOOL_ARGUMENTS,
            "INVALID_TOOL_ARGS",
        ),
    ],
)
def test_request_adapter_preserves_the_first_failed_stage(
    raw_output,
    expected_stage,
    expected_code,
):
    runtime_result = agent_loop.parse_and_validate_tool_request(raw_output)

    outcome = module.request_result_to_trace(runtime_result)

    assert isinstance(outcome, module.RequestRejected)
    assert outcome.stage is expected_stage
    assert outcome.code == expected_code


def test_request_adapter_removes_runtime_result_details_on_success():
    runtime_result = agent_loop.parse_and_validate_tool_request(
        '{"tool":"read_file","args":{"path":"notes.txt"}}'
    )

    outcome = module.request_result_to_trace(runtime_result)

    assert outcome == module.RequestAccepted(tool="read_file")
    assert not hasattr(outcome, "value")


def test_trace_logger_records_typed_causal_outcomes_and_writes_versioned_json(
    tmp_path,
):
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
    assert saved["schema_version"] == 1
    assert saved["initial_messages"] == [{"role": "user", "content": "Read notes.txt."}]
    assert saved["steps"][0]["assistant_output"].startswith('{"tool":"read_file"')
    assert saved["steps"][0]["request_outcome"] == {
        "kind": "accepted",
        "tool": "read_file",
    }
    assert saved["steps"][0]["action"] == {
        "kind": "execute_tool",
        "tool": "read_file",
    }
    assert saved["steps"][0]["tool_outcome"] == {
        "kind": "succeeded",
        "tool": "read_file",
        "value": "lesson notes",
    }
    assert saved["steps"][1]["request_outcome"] == {
        "kind": "accepted",
        "tool": "submit",
    }
    assert saved["steps"][1]["action"] == {
        "answer": "done",
        "kind": "submit",
    }
    assert saved["steps"][1]["tool_outcome"] is None
    assert saved["steps"][1]["exit_reason"] == "submitted"
    assert saved["exit_reason"] == "submitted"


def test_trace_distinguishes_missing_runtime_handler_from_unknown_tool():
    logger = module.TraceLogger()

    agent_loop.run_agent(
        user_task="Read notes.txt.",
        model=FakeModel([
            '{"tool":"read_file","args":{"path":"notes.txt"}}',
            '{"tool":"submit","args":{"answer":"done"}}',
        ]),
        tools={},
        max_steps=3,
        trace_logger=logger,
    )

    assert logger.trace is not None
    first_step = logger.trace.steps[0]

    assert first_step.request_outcome == module.RequestAccepted(
        tool="read_file"
    )
    assert first_step.action == module.ExecuteToolSelected(tool="read_file")
    assert first_step.tool_outcome == module.ToolFailed(
        tool="read_file",
        code="RUNTIME_TOOL_UNAVAILABLE",
        message="Unknown tool: read_file",
    )


def test_trace_marks_the_final_step_and_run_when_max_steps_is_exhausted():
    logger = module.TraceLogger()

    result = agent_loop.run_agent(
        user_task="Read notes.txt.",
        model=FakeModel([
            '{"tool":"read_file","args":{"path":"notes.txt"}}',
        ]),
        tools={"read_file": read_file},
        max_steps=1,
        trace_logger=logger,
    )

    assert result.exit_reason == "max_steps"
    assert logger.trace is not None
    assert logger.trace.steps[-1].exit_reason is module.TraceExitReason.MAX_STEPS
    assert logger.trace.final_answer is None
    assert logger.trace.exit_reason is module.TraceExitReason.MAX_STEPS
