## =============================================================================
## imports
## =============================================================================
from copy import deepcopy
from dataclasses import FrozenInstanceError, dataclass
import json
from pathlib import Path
import sys

from hypothesis import given
from hypothesis import strategies as st
import pytest


PHASE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PHASE_ROOT))

import agent_loop
from agent_loop import (
    Err,
    ExecuteToolAction,
    ExitReason,
    Ok,
    SubmitAction,
    classify_action,
    execute_tool_action,
    run_agent,
)
from primitive_04_validate_tool_args import (
    SubmitArgs,
    ValidatedToolRequest,
)
from result import Err as SharedErr
from result import Ok as SharedOk


## =============================================================================
## helpers
## =============================================================================
class FakeModel:
    """
    Fake replacement for the real LLM.

    It returns prewritten model outputs in order.
    It also records every message list the loop sent to the model.
    """

    def __init__(self, outputs: list[str]):
        self.outputs = outputs
        self.calls = []

    def complete(self, messages):
        self.calls.append(deepcopy(messages))

        if not self.outputs:
            raise AssertionError("FakeModel had no more outputs")

        return self.outputs.pop(0)


class FakeTool:
    """
    Fake replacement for a real tool.

    It returns a fixed result and records how it was called.
    """

    def __init__(self, result):
        self.result = result
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


class ExplodingTool:
    def __init__(self):
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        raise RuntimeError("tool exploded")


@dataclass(frozen=True, slots=True)
class TypedToolError:
    message: str
    code: str


def tool_observation(messages):
    assert messages[-1]["role"] == "tool"
    return json.loads(messages[-1]["content"])


def assert_err_observation(messages, error_code: str):
    observation = tool_observation(messages)

    assert observation["ok"] is False
    assert observation["error_code"] == error_code
    assert isinstance(observation["error"], str)
    assert observation["error"]

    return observation


def executable_action(raw_request: str):
    result = agent_loop.parse_and_validate_tool_request(raw_request)
    assert isinstance(result, SharedOk)

    action = classify_action(result.value)
    assert isinstance(action, ExecuteToolAction)
    return action


## =============================================================================
## tests
## =============================================================================
def test_agent_loop_uses_shared_result_types():
    assert Ok is SharedOk
    assert Err is SharedErr


def test_agent_loop_uses_primitive_04_validated_request():
    result = agent_loop.parse_and_validate_tool_request(
        '{"tool": "submit", "args": {"answer": "done"}}'
    )

    assert isinstance(result, SharedOk)
    assert isinstance(result.value, ValidatedToolRequest)
    assert isinstance(result.value.args, SubmitArgs)


def test_classify_action_creates_submit_action():
    result = agent_loop.parse_and_validate_tool_request(
        '{"tool": "submit", "args": {"answer": "done"}}'
    )
    assert isinstance(result, SharedOk)

    action = classify_action(result.value)

    assert action == SubmitAction(answer="done")


def test_classify_action_preserves_executable_request():
    raw_requests = [
        '{"tool": "read_file", "args": {"path": "notes.txt"}}',
        (
            '{"tool": "write_file", "args": '
            '{"path": "answer.txt", "content": "done"}}'
        ),
        '{"tool": "list_files", "args": {}}',
    ]

    for raw_request in raw_requests:
        result = agent_loop.parse_and_validate_tool_request(raw_request)
        assert isinstance(result, SharedOk)
        request = result.value

        action = classify_action(request)

        assert isinstance(action, ExecuteToolAction)
        assert action.request is request


def test_execute_tool_action_calls_registered_handler():
    action = executable_action(
        '{"tool": "read_file", "args": {"path": "notes.txt"}}'
    )
    tool_result = Ok("file contents")
    read_file = FakeTool(result=tool_result)

    result = execute_tool_action(
        action,
        {"read_file": read_file},
    )

    assert result is tool_result
    assert read_file.calls == [{"path": "notes.txt"}]


def test_execute_tool_action_rejects_missing_handler():
    action = executable_action(
        '{"tool": "read_file", "args": {"path": "notes.txt"}}'
    )

    result = execute_tool_action(action, {})

    assert isinstance(result, Err)
    assert result.error.code == "UNKNOWN_TOOL"
    assert result.error.tool == "read_file"


def test_execute_tool_action_normalizes_handler_exception():
    action = executable_action(
        '{"tool": "read_file", "args": {"path": "notes.txt"}}'
    )
    read_file = ExplodingTool()

    result = execute_tool_action(
        action,
        {"read_file": read_file},
    )

    assert isinstance(result, Err)
    assert result.error.code == "TOOL_EXCEPTION"
    assert result.error.message == "tool exploded"
    assert read_file.calls == [{"path": "notes.txt"}]


def test_run_agent_routes_decisions_through_classify_action(monkeypatch):
    model = FakeModel(
        outputs=[
            '{"tool": "read_file", "args": {"path": "notes.txt"}}',
        ]
    )
    read_file = FakeTool(result=Ok("this should not be read"))
    classified_requests = []

    def classify_as_submit(request):
        classified_requests.append(request)
        return SubmitAction(answer="classified answer")

    monkeypatch.setattr(
        agent_loop,
        "classify_action",
        classify_as_submit,
    )

    result = run_agent(
        user_task="Read notes.txt.",
        model=model,
        tools={"read_file": read_file},
        max_steps=1,
    )

    assert result.exit_reason == "submitted"
    assert result.exit_reason is ExitReason.SUBMITTED
    assert result.final_answer == "classified answer"
    assert len(classified_requests) == 1
    assert read_file.calls == []


def test_submit_stops_loop():
    model = FakeModel(
        outputs=[
            '{"tool": "submit", "args": {"answer": "done"}}',
        ]
    )

    read_file = FakeTool(result=Ok("this should not be read"))
    submit = FakeTool(result=Ok("this should not be called"))

    tools = {
        "read_file": read_file,
        "submit": submit,
    }

    result = run_agent(
        user_task="Finish the task.",
        model=model,
        tools=tools,
        max_steps=5,
    )

    assert result.exit_reason == "submitted"
    assert result.exit_reason is ExitReason.SUBMITTED
    assert result.final_answer == "done"
    assert not hasattr(result, "__dict__")

    with pytest.raises(FrozenInstanceError):
        setattr(result, "final_answer", "changed")

    assert len(model.calls) == 1
    assert read_file.calls == []
    assert submit.calls == []


def test_tool_result_is_appended_before_next_model_call():
    model = FakeModel(
        outputs=[
            '{"tool": "read_file", "args": {"path": "notes.txt"}}',
            '{"tool": "submit", "args": {"answer": "done"}}',
        ]
    )
    read_file = FakeTool(result=Ok("file contents"))

    result = run_agent(
        user_task="Read notes.txt.",
        model=model,
        tools={"read_file": read_file},
        max_steps=5,
    )

    assert result.exit_reason == "submitted"
    assert read_file.calls == [{"path": "notes.txt"}]

    assert len(model.calls) == 2
    second_model_call_messages = model.calls[1]
    assert [message["role"] for message in second_model_call_messages] == [
        "user",
        "assistant",
        "tool",
    ]
    assert tool_observation(second_model_call_messages) == {
        "ok": True,
        "value": "file contents",
    }


def test_max_steps_stops_infinite_loop():
    model = FakeModel(
        outputs=[
            '{"tool": "list_files", "args": {}}',
            '{"tool": "list_files", "args": {}}',
        ]
    )
    list_files = FakeTool(result=Ok(["a.txt", "b.txt"]))

    result = run_agent(
        user_task="Keep listing files.",
        model=model,
        tools={"list_files": list_files},
        max_steps=2,
    )

    assert result.exit_reason == "max_steps"
    assert result.exit_reason is ExitReason.MAX_STEPS
    assert result.final_answer is None

    assert len(model.calls) == 2
    assert list_files.calls == [{}, {}]


NON_TERMINAL_OUTPUTS = st.sampled_from(
    [
        '{"tool": "read_file", "args": ',
        '{"tool": "read_file", "args": {}}',
        '{"tool": "list_files", "args": {}}',
    ]
)


@given(
    max_steps=st.integers(min_value=0, max_value=25),
    assistant_output=NON_TERMINAL_OUTPUTS,
)
def test_model_calls_never_exceed_max_steps(
    max_steps: int,
    assistant_output: str,
):
    model = FakeModel(outputs=[assistant_output] * max_steps)
    list_files = FakeTool(result=Ok([]))

    result = run_agent(
        user_task="Do not submit.",
        model=model,
        tools={"list_files": list_files},
        max_steps=max_steps,
    )

    assert len(model.calls) <= max_steps
    assert len(model.calls) == max_steps
    assert result.exit_reason is ExitReason.MAX_STEPS


def test_unregistered_runtime_tool_is_rejected_without_execution():
    model = FakeModel(
        outputs=[
            '{"tool": "read_file", "args": {"path": "notes.txt"}}',
            '{"tool": "submit", "args": {"answer": "done"}}',
        ]
    )

    result = run_agent(
        user_task="Read notes.txt.",
        model=model,
        tools={},
        max_steps=5,
    )

    assert result.exit_reason == "submitted"

    assert len(model.calls) == 2
    observation = assert_err_observation(model.calls[1], "UNKNOWN_TOOL")
    assert observation["error"] == "Unknown tool: read_file"


def test_unknown_protocol_tool_is_rejected_without_execution():
    model = FakeModel(
        outputs=[
            '{"tool": "delete_file", "args": {"path": "notes.txt"}}',
            '{"tool": "submit", "args": {"answer": "done"}}',
        ]
    )
    read_file = FakeTool(result=Ok("this should not be read"))

    result = run_agent(
        user_task="Delete notes.txt.",
        model=model,
        tools={"read_file": read_file},
        max_steps=5,
    )

    assert result.exit_reason == "submitted"
    assert read_file.calls == []

    assert len(model.calls) == 2
    observation = assert_err_observation(model.calls[1], "UNKNOWN_TOOL")
    assert observation["error"] == "Unknown tool: delete_file"


def test_malformed_json_is_rejected_without_execution():
    model = FakeModel(
        outputs=[
            '{"tool": "read_file", "args": ',
            '{"tool": "submit", "args": {"answer": "done"}}',
        ]
    )
    read_file = FakeTool(result=Ok("this should not be read"))

    result = run_agent(
        user_task="Read notes.txt.",
        model=model,
        tools={"read_file": read_file},
        max_steps=5,
    )

    assert result.exit_reason == "submitted"
    assert read_file.calls == []

    assert len(model.calls) == 2
    assert_err_observation(model.calls[1], "INVALID_JSON")


def test_invalid_tool_request_shape_is_rejected_without_execution():
    model = FakeModel(
        outputs=[
            '{"tool": "read_file"}',
            '{"tool": "submit", "args": {"answer": "done"}}',
        ]
    )
    read_file = FakeTool(result=Ok("this should not be read"))

    result = run_agent(
        user_task="Read notes.txt.",
        model=model,
        tools={"read_file": read_file},
        max_steps=5,
    )

    assert result.exit_reason == "submitted"
    assert read_file.calls == []

    assert len(model.calls) == 2
    assert_err_observation(model.calls[1], "INVALID_TOOL_REQUEST_SHAPE")


def test_invalid_tool_args_are_rejected_without_execution():
    model = FakeModel(
        outputs=[
            '{"tool": "read_file", "args": {}}',
            '{"tool": "submit", "args": {"answer": "done"}}',
        ]
    )
    read_file = FakeTool(result=Ok("this should not be read"))

    result = run_agent(
        user_task="Read notes.txt.",
        model=model,
        tools={"read_file": read_file},
        max_steps=5,
    )

    assert result.exit_reason == "submitted"
    assert read_file.calls == []

    assert len(model.calls) == 2
    assert_err_observation(model.calls[1], "INVALID_TOOL_ARGS")


def test_typed_tool_error_becomes_observation():
    model = FakeModel(
        outputs=[
            '{"tool": "read_file", "args": {"path": "missing.txt"}}',
            '{"tool": "submit", "args": {"answer": "done"}}',
        ]
    )
    read_file = FakeTool(
        result=Err(
            TypedToolError(
                message="File does not exist.",
                code="FILE_NOT_FOUND",
            )
        )
    )

    result = run_agent(
        user_task="Read missing.txt.",
        model=model,
        tools={"read_file": read_file},
        max_steps=5,
    )

    assert result.exit_reason == "submitted"
    assert tool_observation(model.calls[1]) == {
        "ok": False,
        "error_code": "FILE_NOT_FOUND",
        "error": "File does not exist.",
    }


def test_tool_exception_becomes_observation():
    model = FakeModel(
        outputs=[
            '{"tool": "read_file", "args": {"path": "notes.txt"}}',
            '{"tool": "submit", "args": {"answer": "done"}}',
        ]
    )
    read_file = ExplodingTool()

    result = run_agent(
        user_task="Read notes.txt.",
        model=model,
        tools={"read_file": read_file},
        max_steps=5,
    )

    assert result.exit_reason == "submitted"
    assert read_file.calls == [{"path": "notes.txt"}]

    assert tool_observation(model.calls[1]) == {
        "ok": False,
        "error_code": "TOOL_EXCEPTION",
        "error": "tool exploded",
    }
