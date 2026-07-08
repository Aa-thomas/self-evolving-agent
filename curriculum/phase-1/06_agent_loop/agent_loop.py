from typing import Dict, Protocol


class Model(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> str: ...


def run_agent(user_task: str, model: Model, tools: Dict, max_steps: int):
    # initialize messages with the user task
    messages = [{"role": "user", "content": user_task}]
    trace = []

    for step in range(max_steps):
        # Call model
        assistant_output = model.complete(messages)
        messages.append({"role": "assistant", "content": assistant_output})

        # parse json and convert to tool request
        request = parse_and_validate(assistant_output)

        # if tool is invalid, reject, if tool is submit, stop, otherwise execute

        if request is invalid:
            observation = rejection_result(request.error_code)
            messages.append({"role": "tool", "content": observation})
            continue

        if request.tool == "submit":
            return AgentResult(
                exit_reason="submitted",
                final_answer=request.args["answer"],
                trace=trace,
            )

        if request.tool not in tools:
            observation = unknown_tool_result(request.tool)
        else:
            observation = tools[request.tool](**request.args)

        # append the tool observation
        messages.append({"role": "tool", "content": observation})

    return AgentResult(exit_reason="max_steps", final_answer=None, trace=trace)
