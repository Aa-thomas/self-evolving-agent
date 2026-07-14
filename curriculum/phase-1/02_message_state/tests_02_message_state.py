import importlib.util
from copy import deepcopy
from pathlib import Path


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


# The assertion here proves the second call includes the right message sequence. User message, then, assistant message, then tool message
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


# The assertion here proves that The tool result in that sequence is the actual file content.
def test_update_message_state_preserves_existing_message_order():
    messages = [{"role": "user", "content": "first"}]

    module.update_message_state(messages, role="assistant", content="second")

    assert messages == [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "second"},
    ]
