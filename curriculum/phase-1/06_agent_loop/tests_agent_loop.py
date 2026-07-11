## =============================================================================
## imports
## =============================================================================
from copy import deepcopy
import json

from agent_loop import Err, Ok, run_agent


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


def tool_observation(messages):
    assert messages[-1]["role"] == "tool"
    return json.loads(messages[-1]["content"])


## =============================================================================
## tests
## =============================================================================
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
    assert result.final_answer == "done"

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
    assert result.final_answer is None

    assert len(model.calls) == 2
    assert list_files.calls == [{}, {}]


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
    assert tool_observation(model.calls[1])["error_code"] == "UNKNOWN_TOOL"


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
    assert tool_observation(model.calls[1])["error_code"] == "UNKNOWN_TOOL"


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
    assert tool_observation(model.calls[1])["error_code"] == "INVALID_JSON"


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
    assert tool_observation(model.calls[1])["error_code"] == (
        "INVALID_TOOL_REQUEST_SHAPE"
    )


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
    assert tool_observation(model.calls[1])["error_code"] == "INVALID_TOOL_ARGS"


def test_tool_error_becomes_observation():
    model = FakeModel(
        outputs=[
            '{"tool": "read_file", "args": {"path": "missing.txt"}}',
            '{"tool": "submit", "args": {"answer": "done"}}',
        ]
    )
    read_file = FakeTool(
        result=Err(
            error="File does not exist.",
            error_code="FILE_NOT_FOUND",
        )
    )

    result = run_agent(
        user_task="Read missing.txt.",
        model=model,
        tools={"read_file": read_file},
        max_steps=5,
    )

    assert result.exit_reason == "submitted"
    assert read_file.calls == [{"path": "missing.txt"}]

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
