# Mission: Harness Engineering

## Why
Build production-shaped AI agents from first principles, with enough evidence to be credible for applied AI, agent engineering, and AI reliability roles. The immediate goal is Project 1A: understand and implement the minimal agent loop before using agent frameworks or benchmark harnesses.

## Success looks like
- Implement a small file-agent loop that stops on `submit`, enforces `max_steps`, executes only registered tools, and appends tool observations to message state.
- Explain why the model requests tools but the harness executes or rejects them.
- Produce runnable evidence: tests, traces, evals, and short failure explanations.
- Rebuild the Project 1A loop from a skeleton without copying a framework.

## Constraints
- Stay focused on the curriculum's primitive -> micro-system -> benchmarked harness path.
- Prefer small runnable artifacts over broad reading.
- Teach one tight Project 1A concept at a time.

## Out of scope
- Agent frameworks.
- RAG.
- web UI or service wrapper.
- multi-agent behavior.
- long-term memory.
