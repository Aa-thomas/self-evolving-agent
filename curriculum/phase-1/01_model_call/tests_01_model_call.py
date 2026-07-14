import importlib.util
from copy import deepcopy
from pathlib import Path
import sys

import pytest


MODULE_PATH = Path(__file__).resolve().parent / "model_call.py"

spec = importlib.util.spec_from_file_location("model_call", MODULE_PATH)
module = importlib.util.module_from_spec(spec)

assert spec is not None
assert spec.loader is not None

sys.modules["model_call"] = module
spec.loader.exec_module(module)


class FakeModel:
    def __init__(self, output: str):
        self.output = output
        self.calls = []

    def complete(self, messages):
        self.calls.append(deepcopy(messages))
        return self.output


class FakeUsage:
    prompt_tokens = 7
    completion_tokens = 11
    total_tokens = 18


class FakeModelWithUsage(FakeModel):
    def complete(self, messages):
        self.last_usage = FakeUsage()
        return super().complete(messages)


class FakeModelWithDictUsage(FakeModel):
    def complete(self, messages):
        self.last_usage = {
            "prompt_tokens": 3,
            "completion_tokens": 5,
            "total_tokens": 8,
        }
        return super().complete(messages)


class BadModel:
    def complete(self, messages):
        return {"content": "not a string"}


def test_call_model_sends_single_user_message_and_returns_output_record():
    model = FakeModel(output="pong")

    record = module.call_model(prompt="ping", model=model)

    assert model.calls == [[{"role": "user", "content": "ping"}]]
    assert isinstance(record, module.ModelCallRecord)
    assert record.output_text == "pong"
    assert record.latency_seconds >= 0


def test_call_model_does_not_print(capsys):
    model = FakeModel(output="pong")

    module.call_model(prompt="ping", model=model)

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_call_model_estimates_token_usage_when_provider_usage_is_absent():
    model = FakeModel(output="pong")

    record = module.call_model(prompt="ping", model=model)

    assert record.usage_source == "estimate"
    assert record.prompt_tokens is None
    assert record.completion_tokens is None
    assert record.total_tokens is None
    assert record.estimated_prompt_tokens > 0
    assert record.estimated_completion_tokens > 0
    assert record.estimated_total_tokens == (
        record.estimated_prompt_tokens + record.estimated_completion_tokens
    )
    assert record.input_tokens == record.estimated_prompt_tokens
    assert record.output_tokens == record.estimated_completion_tokens


def test_call_model_records_provider_usage_from_object_attributes():
    model = FakeModelWithUsage(output="pong")

    record = module.call_model(prompt="ping", model=model)

    assert record.usage_source == "provider"
    assert record.prompt_tokens == 7
    assert record.completion_tokens == 11
    assert record.total_tokens == 18
    assert record.input_tokens == 7
    assert record.output_tokens == 11


def test_call_model_records_provider_usage_from_dict():
    model = FakeModelWithDictUsage(output="pong")

    record = module.call_model(prompt="ping", model=model)

    assert record.usage_source == "provider"
    assert record.prompt_tokens == 3
    assert record.completion_tokens == 5
    assert record.total_tokens == 8


def test_call_model_rejects_non_string_model_output():
    model = BadModel()

    with pytest.raises(TypeError, match="must return a string"):
        module.call_model(prompt="ping", model=model)
