"""Primitive 1: make an inspectable model call."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
import os
import time
from typing import Any, Literal, Protocol

import typer
from dotenv import load_dotenv


class Model(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> str: ...


UsageSource = Literal["provider", "estimate"]


@dataclass(frozen=True)
class ModelCallRecord:
    output_text: str
    latency_seconds: float
    estimated_prompt_tokens: int
    estimated_completion_tokens: int
    estimated_total_tokens: int
    usage_source: UsageSource
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None

    @property
    def input_tokens(self) -> int:
        return self.prompt_tokens if self.prompt_tokens is not None else self.estimated_prompt_tokens

    @property
    def output_tokens(self) -> int:
        return self.completion_tokens if self.completion_tokens is not None else self.estimated_completion_tokens


def estimate_tokens(text: str) -> int:
    if text == "":
        return 0
    return max(1, math.ceil(len(text) / 4))


def usage_value(usage: Any, key: str) -> int | None:
    if usage is None:
        return None
    value = usage.get(key) if isinstance(usage, dict) else getattr(usage, key, None)
    return value if isinstance(value, int) else None


def call_model(
    *,
    model: Model,
    prompt: str | None = None,
    messages: list[dict[str, str]] | None = None,
) -> ModelCallRecord:
    """Call a model with either a new prompt or existing ordered message state."""
    if (prompt is None) == (messages is None):
        raise ValueError("provide exactly one of prompt or messages")

    if messages is None:
        assert prompt is not None
        messages = [{"role": "user", "content": prompt}]

    started_at = time.perf_counter()
    output_text = model.complete(messages)
    latency_seconds = time.perf_counter() - started_at
    if not isinstance(output_text, str):
        raise TypeError("model.complete(messages) must return a string")

    usage = getattr(model, "last_usage", None)
    prompt_tokens = usage_value(usage, "prompt_tokens")
    completion_tokens = usage_value(usage, "completion_tokens")
    total_tokens = usage_value(usage, "total_tokens")
    estimated_prompt_tokens = estimate_tokens("\n".join(message["content"] for message in messages))
    estimated_completion_tokens = estimate_tokens(output_text)

    return ModelCallRecord(
        output_text=output_text,
        latency_seconds=latency_seconds,
        estimated_prompt_tokens=estimated_prompt_tokens,
        estimated_completion_tokens=estimated_completion_tokens,
        estimated_total_tokens=estimated_prompt_tokens + estimated_completion_tokens,
        usage_source=(
            "provider"
            if any(value is not None for value in (prompt_tokens, completion_tokens, total_tokens))
            else "estimate"
        ),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )


class OpenRouterModel:
    def __init__(
        self,
        model_name: str = "cohere/north-mini-code:free",
        api_key: str | None = None,
        base_url: str = "https://openrouter.ai/api/v1",
    ):
        from openai import OpenAI

        if api_key is None:
            api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is required for the CLI model")

        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model_name = model_name
        self.last_usage = None

    def complete(self, messages: list[dict[str, str]]) -> str:
        response = self.client.chat.completions.create(model=self.model_name, messages=messages)
        self.last_usage = response.usage
        return response.choices[0].message.content or ""


app = typer.Typer()


def record_to_dict(record: ModelCallRecord) -> dict[str, Any]:
    return asdict(record) | {"input_tokens": record.input_tokens, "output_tokens": record.output_tokens}


@app.command()
def model_call(prompt: str, model_name: str = "cohere/north-mini-code:free") -> None:
    load_dotenv()
    record = call_model(prompt=prompt, model=OpenRouterModel(model_name=model_name))
    evidence = record_to_dict(record)
    evidence.pop("output_text")
    typer.echo(record.output_text)
    typer.echo(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    app()
