# Mission: Harness Engineering

## Why

Build production-shaped AI agents from first principles, with enough evidence to be credible for AI Engineer, Applied AI Engineer, Agent Engineer, Forward Deployed Engineer, and AI reliability roles. The immediate goal is Project 1A: understand and implement the minimal agent loop before using agent frameworks or benchmark harnesses.

## Success looks like

- Implement a small file-agent loop that stops on `submit`, enforces `max_steps`, executes only registered tools, and appends tool observations to message state.
- Explain why the model requests tools but the harness executes or rejects them.
- Produce runnable evidence: tests, traces, evals, and short failure explanations.
- Rebuild the Project 1A loop from a skeleton without copying a framework.

## What understanding means

Understanding is demonstrated when the learner can:

- implement the mechanism;
- identify the first bad transition in a failure;
- explain which component owns the correction;
- choose between plausible designs;
- connect a test or trace to the claimed behavior;
- state what the evidence does not prove; and
- reconstruct the mechanism from an appropriate scaffold.

Two invariants follow:

1. A learner-facing page is not itself a completed lesson.
2. A lesson cannot be treated as complete before its implementation, passing proof, and evidence artifact exist. A published learner-build lab may begin with a real starter file and a deliberately failing proof; it is an invitation to build, never a claim that the capability already works.

## Constraints

- Stay focused on the curriculum's primitive → micro-system → benchmarked harness path.
- Prefer small runnable artifacts over broad reading.
- Teach one tight Project 1A concept at a time.
- Every learner-facing HTML lesson must meet `LESSON-AUTHORING-STANDARD.md`; concise scope must not mean shallow instruction.

## Out of scope

- Agent frameworks.
- RAG.
- web UI or service wrapper.
- multi-agent behavior.
- long-term memory.
