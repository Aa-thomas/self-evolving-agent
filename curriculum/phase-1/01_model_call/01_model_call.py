from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
import os
import time
from typing import Any, Literal, Protocol

import typer
from dotenv import load_dotenv


## =============================================================================
## Types
## =============================================================================
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
        if self.prompt_tokens is not None:
            return self.prompt_tokens

        return self.estimated_prompt_tokens

    @property
    def output_tokens(self) -> int:
        if self.completion_tokens is not None:
            return self.completion_tokens

        return self.estimated_completion_tokens


## =============================================================================
## Token Usage Helpers
## =============================================================================
def estimate_tokens(text: str) -> int:
    if text == "":
        return 0

    return max(1, math.ceil(len(text) / 4))


def usage_value(usage: Any, key: str) -> int | None:
    if usage is None:
        return None

    if isinstance(usage, dict):
        value = usage.get(key)
    else:
        value = getattr(usage, key, None)

    if isinstance(value, int):
        return value

    return None


## =============================================================================
## Model Call Primitive
## =============================================================================
def call_model(prompt: str, model: Model) -> ModelCallRecord:
    messages = [{"role": "user", "content": prompt}]

    start_time = time.perf_counter()
    output_text = model.complete(messages)
    latency_seconds = time.perf_counter() - start_time

    if not isinstance(output_text, str):
        raise TypeError("model.complete(messages) must return a string")

    usage = getattr(model, "last_usage", None)

    prompt_tokens = usage_value(usage, "prompt_tokens")
    completion_tokens = usage_value(usage, "completion_tokens")
    total_tokens = usage_value(usage, "total_tokens")

    estimated_prompt_tokens = estimate_tokens(prompt)
    estimated_completion_tokens = estimate_tokens(output_text)
    estimated_total_tokens = estimated_prompt_tokens + estimated_completion_tokens

    usage_source: UsageSource = "estimate"
    if (
        prompt_tokens is not None
        or completion_tokens is not None
        or total_tokens is not None
    ):
        usage_source = "provider"

    return ModelCallRecord(
        output_text=output_text,
        latency_seconds=latency_seconds,
        estimated_prompt_tokens=estimated_prompt_tokens,
        estimated_completion_tokens=estimated_completion_tokens,
        estimated_total_tokens=estimated_total_tokens,
        usage_source=usage_source,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )


## =============================================================================
## OpenRouter Adapter
## =============================================================================
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
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
        )

        self.last_usage = response.usage
        content = response.choices[0].message.content

        if content is None:
            return ""

        return content


## =============================================================================
## CLI
## =============================================================================
app = typer.Typer()


def record_to_dict(record: ModelCallRecord) -> dict[str, Any]:
    return asdict(record) | {
        "input_tokens": record.input_tokens,
        "output_tokens": record.output_tokens,
    }


@app.command()
def model_call(
    prompt: str,
    model_name: str = "cohere/north-mini-code:free",
) -> None:
    load_dotenv()
    model = OpenRouterModel(model_name=model_name)
    record = call_model(prompt=prompt, model=model)

    evidence = record_to_dict(record)
    evidence.pop("output_text")

    typer.echo(record.output_text)
    typer.echo(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    app()
