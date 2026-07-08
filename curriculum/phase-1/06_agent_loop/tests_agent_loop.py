## =============================================================================
## imports
## =============================================================================
from copy import deepcopy
from agent_loop import run_agent


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


## =============================================================================
## tests
## =============================================================================


def test_submit_stops_loop():
    model = FakeModel(
        outputs=[
            '{"tool": "submit", "args": {"answer": "done"}}',
        ]
    )

    read_file = FakeTool(
        result={
            "ok": True,
            "content": "this should not be read",
        }
    )

    tools = {
        "read_file": read_file,
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


# def test_tool_result_is_appended_before_next_model_call(): ...
#
#
# def test_max_steps_stops_infinite_loop(): ...
#
#
# def test_unknown_tool_is_rejected_without_execution(): ...
#
#
# def test_malformed_json_is_rejected_without_execution(): ...
#
#
# def test_tool_error_becomes_observation(): ...
#
#
# def test_trace_contains_step_records(): ...
