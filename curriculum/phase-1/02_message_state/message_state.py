"""The ordered message state passed to each model call."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Literal, TypedDict

import typer
from dotenv import load_dotenv
from model_call import Model, ModelCallRecord, OpenRouterModel, call_model


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
    """Append one model-visible event without changing earlier history.

    The caller owns *when* to call the model.  In particular, a tool result
    must be appended before the next call so the model can use that result.
    """
    if role not in {"user", "assistant", "tool"}:
        raise ValueError(f"unsupported message role: {role!r}")
    if not isinstance(content, str):
        raise TypeError("message content must be a string")

    messages.append({"role": role, "content": content})


def append_tool_observation(
    messages: list[Message], observation: Mapping[str, Any]) -> None:
    """Serialize a harness result into the tool message the model can see."""
    update_message_state(
        messages,
        role="tool",
        content=json.dumps(dict(observation), sort_keys=True),
    )


def decode_tool_observation(message: Message) -> dict[str, Any]:
    """Read the structured tool result back from a tool message for a test."""
    if message["role"] != "tool":
        raise ValueError("only tool messages contain tool observations")

    observation = json.loads(message["content"])
    if not isinstance(observation, dict):
        raise ValueError("tool observation must decode to a JSON object")
    return observation


def run_model_turn(messages: list[Message], model: Model) -> ModelCallRecord:
    """Call Primitive 1 with current state, then record its assistant output."""
    record = call_model(model=model, messages=messages)
    update_message_state(messages, role="assistant", content=record.output_text)
    return record


app = typer.Typer()


@app.command()
def message_state(new_message: str) -> None:
    """Make one user/assistant exchange and display its ordered context."""
    load_dotenv()

    messages: list[Message] = []
    update_message_state(messages, role="user", content=new_message)

    model = OpenRouterModel(model_name="cohere/north-mini-code:free")
    run_model_turn(messages, model)

    typer.echo(json.dumps(messages, indent=2))


if __name__ == "__main__":
    app()
