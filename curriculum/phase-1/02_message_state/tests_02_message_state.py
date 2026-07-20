import importlib.util
from copy import deepcopy
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parent / "message_state.py"
spec = importlib.util.spec_from_file_location("message_state", MODULE_PATH)
module = importlib.util.module_from_spec(spec)

assert spec is not None
assert spec.loader is not None
spec.loader.exec_module(module)


class FakeModel:
    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.calls = []

    def complete(self, messages):
        self.calls.append(deepcopy(messages))
        return next(self.outputs)


def test_second_primitive_one_call_receives_the_tool_observation():
    messages = []
    model = FakeModel(
        [
            '{"tool": "read_file", "args": {"path": "notes.txt"}}',
            '{"tool": "submit", "args": {"answer": "done"}}',
        ]
    )

    module.update_message_state(messages, role="user", content="Read notes.txt.")
    module.run_model_turn(messages, model)
    module.append_tool_observation(
        messages,
        {"ok": True, "value": "file contents"},
    )
    module.run_model_turn(messages, model)

    second_call = model.calls[1]
    assert [message["role"] for message in second_call] == ["user", "assistant", "tool"]
    assert module.decode_tool_observation(second_call[-1]) == {
        "ok": True,
        "value": "file contents",
    }


def test_update_message_state_preserves_existing_message_order():
    messages = [{"role": "user", "content": "first"}]

    module.update_message_state(messages, role="assistant", content="second")

    assert messages == [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "second"},
    ]


def test_run_model_turn_appends_assistant_output_after_call():
    messages = [{"role": "user", "content": "Read notes.txt."}]
    model = FakeModel(['{"tool": "read_file", "args": {"path": "notes.txt"}}'])

    record = module.run_model_turn(messages, model)

    assert model.calls == [[{"role": "user", "content": "Read notes.txt."}]]
    assert record.output_text == '{"tool": "read_file", "args": {"path": "notes.txt"}}'
    assert messages == [
        {"role": "user", "content": "Read notes.txt."},
        {
            "role": "assistant",
            "content": '{"tool": "read_file", "args": {"path": "notes.txt"}}',
        },
    ]


def test_append_tool_observation_serializes_structured_result():
    messages = []

    module.append_tool_observation(messages, {"value": "file contents", "ok": True})

    assert messages == [
        {
            "role": "tool",
            "content": '{"ok": true, "value": "file contents"}',
        }
    ]
    assert module.decode_tool_observation(messages[0]) == {
        "ok": True,
        "value": "file contents",
    }


def test_update_message_state_rejects_unsupported_role():
    with pytest.raises(ValueError, match="unsupported message role"):
        module.update_message_state([], role="system", content="hidden")


def test_update_message_state_rejects_non_string_content():
    with pytest.raises(TypeError, match="message content must be a string"):
        module.update_message_state([], role="tool", content={"ok": True})


def test_decode_tool_observation_rejects_non_tool_message():
    with pytest.raises(ValueError, match="only tool messages"):
        module.decode_tool_observation({"role": "assistant", "content": "{}"})
