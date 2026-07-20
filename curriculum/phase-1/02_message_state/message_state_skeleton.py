"""Primitive 2 reconstruction scaffold.

Primitive 1 already gives you ``call_model`` and ``ModelCallRecord``. Copy this
scaffold into your working ``message_state.py`` and implement only the ordered
message-state transitions described by the tests.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, TypedDict

from model_call import Model, ModelCallRecord, call_model


Role = Literal["user", "assistant", "tool"]


class Message(TypedDict):
    role: Role
    content: str


def update_message_state(
    messages: list[Message],
    *,
    role: Role,
    content: str,
) -> None:
    """Append one valid model-visible event without reordering history."""
    raise NotImplementedError("Append one validated message event.")


def append_tool_observation(
    messages: list[Message], observation: Mapping[str, Any]
) -> None:
    """Serialize a structured harness result into a tool-role message."""
    raise NotImplementedError("Encode and append one tool observation.")


def decode_tool_observation(message: Message) -> dict[str, Any]:
    """Decode a tool message so tests can inspect the structured observation."""
    raise NotImplementedError("Validate and decode one tool message.")


def run_model_turn(messages: list[Message], model: Model) -> ModelCallRecord:
    """Call Primitive 1 with current state, then append its assistant output."""
    raise NotImplementedError("Call the model once and record its output in order.")
