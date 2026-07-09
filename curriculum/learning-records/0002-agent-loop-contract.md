# Agent loop contract and observations

The user understands that the model only emits untrusted text, while the harness owns parsing, validation, tool execution, rejection, observations, and stop conditions. Future lessons can assume the user knows that `submit` is valid protocol but not an executable tool, and that `Ok` / `Err` are internal result shapes that must still be serialized into `tool` observations before the next model call.

**Evidence:** The user identified the need for Pydantic at the trust boundary, asked whether `Ok` / `Err` could simplify observation handling, and implemented the full Project 1A loop with invariant tests.

**Implications:** Future lessons can move from "what is the loop?" to trace quality, eval design, and debugging failed trajectories.
