
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
