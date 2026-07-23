# Harness Engineering Resources

## Knowledge

- [Local curriculum: Harness Engineering Curriculum](./Harness%20Engineering%20curriculum%20-%20rewritten.md)
  Primary learning plan for this workspace. Use for project scope, stop conditions, must-not-build lists, and evidence requirements.
- [OpenAI docs: Function calling](https://developers.openai.com/api/docs/guides/function-calling)
  Use for the core tool-calling flow: model emits a tool call, application code executes it, then returns tool output to the model.
- [OpenAI docs: Conversation state](https://developers.openai.com/api/docs/guides/conversation-state)
  Use for stateless requests, manually carried conversation history, and the distinction between provider-managed and application-managed state.
- [Python docs: Classes](https://docs.python.org/3/tutorial/classes.html)
  Use for class syntax, instance attributes, `__init__`, and method calls such as `model.complete(messages)`.
- [Python docs: typing.Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)
  Use for expressing "any object with a `.complete(messages) -> str` method" without forcing inheritance.
- [Python docs: json](https://docs.python.org/3/library/json.html)
  Use for the exact decoding boundary between untrusted JSON text and Python values.
- [RFC 8259: The JavaScript Object Notation Data Interchange Format](https://www.rfc-editor.org/rfc/rfc8259.html)
  Use for the language-independent JSON grammar and interoperability constraints behind the parser primitive.
- [Pydantic docs: Models](https://docs.pydantic.dev/latest/concepts/models/)
  Use for typed model validation, structured errors, and separating parsed values from validated domain objects.
- [Pydantic docs: Strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/)
  Use for deciding when coercion would weaken a trust boundary.
- [Python docs: pathlib.Path.resolve](https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve)
  Use for canonicalizing file paths before enforcing sandbox containment.
- [MITRE CWE-22: Improper Limitation of a Pathname to a Restricted Directory](https://cwe.mitre.org/data/definitions/22.html)
  Use for the security failure class behind traversal and path-containment tests.
- [OpenAI docs: Agents SDK](https://platform.openai.com/docs/guides/agents)
  Use later for framework anatomy: where an SDK places agents, tools, state, guardrails, and traces.
- [OpenAI Agents SDK: Tracing](https://openai.github.io/openai-agents-python/tracing/)
  Use after building the local primitive to compare its step evidence with a production tracing system's traces, spans, tool calls, and sensitive-data controls.
- [OpenTelemetry docs: Traces](https://opentelemetry.io/docs/concepts/signals/traces/)
  Use for broader trace/span vocabulary and causal operation structure; it is not the schema specification for this course's agent trace.
- [OpenTelemetry specification: Versioning and stability](https://opentelemetry.io/docs/specs/otel/versioning-and-stability/)
  Use for compatibility thinking when a persisted telemetry contract evolves.
- [Anthropic engineering: Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)
  Use for the principle of starting with the simplest viable workflow and adding agentic complexity only when the task needs it.
- [OpenAI docs: Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)
  Use for the objective → dataset → metric → comparison workflow, task-specific eval design, and the distinction between interpretable case evidence and a score alone.
- [OpenAI docs: Agent evals](https://developers.openai.com/api/docs/guides/agent-evals)
  Use for connecting trace-level inspection to repeatable datasets, runs, and workflow-level evaluation.
- [pytest docs: Assertions](https://docs.pytest.org/en/stable/how-to/assert.html)
  Use for local executable pass/fail mechanics and readable failure evidence.

## Wisdom (Communities)

- [OpenAI Developer Community](https://community.openai.com/)
  Use for practical API/tool-calling questions once a small reproducible example exists.
- [Latent Space Discord](https://www.latent.space/p/discord)
  Use for applied AI engineering discussion and feedback on agent/eval design.

## Gaps

- No external source above specifies this course's typed, versioned causal agent-step schema. The tracing sources provide comparisons and design vocabulary; the repository's trace types and proofs remain authoritative for Project 1A.
