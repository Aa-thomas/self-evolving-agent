"""Primitive 1 reconstruction scaffold.

Copy this scaffold into your working ``model_call.py`` and implement only
``call_model``. The supplied tests are the contract; do not use the completed
reference implementation as the starting point.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import time
from typing import Any, Literal, Protocol


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
    """Implement the one-call provider-normalization boundary.

    Build in this order:
    1. Require exactly one of ``prompt`` or ``messages``.
    2. Turn a prompt into one user message; otherwise preserve message order.
    3. Time exactly one ``model.complete(messages)`` call.
    4. Reject a non-string completion before creating a record.
    5. Preserve optional provider usage when it exists; otherwise retain
       explicit estimates and their source.
    """
    raise NotImplementedError("Reconstruct call_model from the test contract.")
