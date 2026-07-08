
## Parse Tool Request
- the model does not execute tools. The harness executes tools. The model just makes requests and its up to your harness to decide if that request is valid and what to do with it.
- Goal: Given raw assistant output, I can convert a valid tool request into a structured internal representation, and I can reject invalid requests clearly.

What I built:
A manual parser for model-produced tool requests. It takes raw assistant text, checks whether it is valid JSON, then validates whether the parsed JSON matches the expected tool-request shape: a tool string and an args object. I also wrapped the result in a structured Result object with ok, value, error, and error_code.

What failed:
My first mental model for args was too loose. I thought args could be str | number, but it should be an object/dict because different tools need different argument shapes. I also initially mixed CLI logic with core parser logic by putting @app.command() directly on the reusable parser function. Another issue was returning inconsistent types: sometimes returning Result, sometimes returning the validated ToolRequest directly.

What I misunderstood:
I misunderstood the difference between valid JSON and a valid tool request. Valid JSON can still be a string, number, list, or wrongly shaped object. The parser needs two separate checks: first, “can this text be parsed as JSON?” and second, “does this parsed data match the tool-request protocol?” I also clarified that the model is not actually calling a tool. It is only producing a request, and the harness is responsible for validating and eventually executing or rejecting that request.

What test now proves it:
Tests now prove that valid JSON parses successfully, malformed JSON returns a structured INVALID_JSON rejection, valid tool-request objects pass Pydantic validation, and invalid shapes such as missing tool, missing args, non-dict args, or non-object JSON return INVALID_TOOL_REQUEST_SHAPE.

## Validate Tool args
-create a list of valid tools
- create a function that checks if the requested tool is in the list of valid tools
- validate the schema of that tool
- return OK or return structured error/ rejection reason

What I built

A tool-request validation layer for Project 1A.

It takes raw model-produced JSON, parses it, validates the outer tool-request shape, checks whether the requested tool exists in the registry, validates that tool’s args with Pydantic, and returns either a structured success or structured rejection.

This matches the Project 1A requirement to reject malformed JSON, wrong schemas, unknown tools, and bad arguments before any tool execution happens.

What failed

The first version mixed several concepts:

Typer CLI input
Pydantic ToolRequest models
tool registry lookup
Result return values

The main failures were:

Typer could not accept ToolRequest directly as a CLI argument.
The registry lookup checked the whole ToolRequest object instead of tool_request.tool.
validate_tool_exists printed instead of returning a structured result.
validate_tool_args accidentally validated tool_request.tool instead of tool_request.args.
The Ok/Err version added more type complexity than the project needed.
What I misunderstood

I misunderstood the difference between these stages:

Parsing JSON is not the same as validating a tool request.

Validating the outer ToolRequest shape is not the same as validating tool-specific args.

Checking that a tool exists is not the same as proving its args are valid.

I also misunderstood where Pydantic should sit:

Pydantic validates untrusted model-produced input.
The ToolSpec registry is internal harness configuration.
The CLI should receive simple strings, not custom Pydantic objects.
What test now proves it

The tests now prove that the validator accepts and rejects the right cases:

Valid read_file request passes.
Malformed JSON returns INVALID_JSON.
Missing args returns INVALID_TOOL_REQUEST_SHAPE.
Unknown tool returns UNKNOWN_TOOL.
read_file with missing path returns INVALID_TOOL_ARGS.
read_file with path as a number returns INVALID_TOOL_ARGS.
read_file with extra random args returns INVALID_TOOL_ARGS.
list_files can omit optional path.

The key regression test is:

read_file with missing path returns INVALID_TOOL_ARGS.

That proves the harness is not merely parsing JSON; it is enforcing the specific tool contract before execution.

## Sandboxed File Tools

## Agent Loop
Function name:
run_agent

Purpose:
The loop must support max steps, toolobservations appended to messages,and stop on submit

Inputs:
- user task: The task from the user
- model: An object with a .complete(messages) method
- tools: A dictionary mapping tool names to callable functions
- max steps: The maximum number of model/tool cycles allowed

Outputs:
...

Allowed behavior:
...

Forbidden behavior:
...

Invariants:
1.
2.
3.
4.
5.

Failure cases:
1.
2.
3.
4.
5.

Tests this must satisfy:
1.
2.
3.
4.
5.
